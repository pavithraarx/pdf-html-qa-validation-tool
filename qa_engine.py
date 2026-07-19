"""
qa_engine.py — Core PDF → HTML QA comparison engine

Goals:
- Compare PDF visible text against HTML visible text token-by-token.
- Catch changed words, missing words, extra words, punctuation changes.
- Catch missing bold/strong tags where PDF text is bold.
- Catch missing heading tags where PDF text looks like a heading.
- Catch visible text outside expected semantic tags.
- Ignore Mytonomy footer/copyright boilerplate.
- Ignore DOCTYPE/head/script/style/meta/link/title.
- Ignore logo.png and blank/header logo placeholders.
- Compare non-logo images by perceptual hash.
"""

import os
import re
import math
import difflib
from dataclasses import dataclass

import pdfplumber
from bs4 import BeautifulSoup, NavigableString
from bs4.element import Comment, Doctype, Declaration, ProcessingInstruction
from PIL import Image
import numpy as np
import imagehash
from html.parser import HTMLParser


# ── Regex / constants ────────────────────────────────────────────────────────

WS = re.compile(r"\s+")
TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*|[^\w\s]")

MOJIBAKE = re.compile(r"Ã.|â€™|â€œ|â€\x9d|\ufffd")

PLACEHOLDER = re.compile(
    r"(lorem ipsum|\btbd\b|\btodo\b|insert (text|image|video) here"
    r"|\[placeholder\]|\bxxx\b|<<[^>]*>>)",
    re.IGNORECASE,
)

EXPECTED_BULLET_MARKER = "•"

BOILERPLATE_PATTERNS = [
    # PDF footer:
    # © 2026 Mytonomy, Inc. All Rights Reserved. Page 1
    r"(?:©\s*)?20\d{2}\s+Mytonomy,\s*Inc\.?\s+All\s+Rights\s+Reserved\.?(?:\s+Page\s+\d+)?",

    # HTML footer:
    # © 2026 Mytonomy, Inc. All rights reserved.
    r"(?:©\s*)?20\d{2}\s+Mytonomy,\s*Inc\.?\s+All\s+rights\s+reserved\.?",

    # Common generated page labels
    r"\bPage\s+\d+\b",
]

IGNORE_IMAGES = {
    "logo.png",
    "company_logo.png",
    "brand_logo.png",
}

_IMG_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"}

SKIP_TEXT_PARENT_TAGS = {
    "script",
    "style",
    "head",
    "title",
    "meta",
    "link",
    "noscript",
    "template",
}

ALLOWED_TEXT_BLOCKS = {
    "p",
    "li",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "td",
    "th",
    "figcaption",
    "caption",
    "blockquote",
    "dt",
    "dd",
}

LANG_TRIGRAMS = {
    "French": ["es ", "de ", "ent", "les", "on ", "la ", "ons", "que", "tion", "le "],
    "German": ["en ", "der", "ie ", "die", "und", "ein", "ich", "das", "sch", "ng "],
    "Spanish": ["de ", "es ", "en ", "que", "la ", "el ", "ón ", "ion", "os ", "con"],
    "Portuguese": ["de ", "os ", "as ", "que", "em ", "do ", "da ", "ão ", "es ", "ar "],
    "Italian": ["del", "che", "la ", "di ", "le ", "in ", "ne ", "on ", "per", "una"],
    "Dutch": ["en ", "de ", "het", "van", "ing", "ge ", "een", "te ", "dat", "ij "],
    "English": ["the", " th", "he ", "ing", "and", "ion", "ed ", "ent", "or ", "al "],
}

HEADER_LOGO_MAX_TOP_RATIO = 0.14
HEADER_LOGO_MAX_LEFT_RATIO = 0.22
HEADER_LOGO_MAX_HEIGHT_RATIO = 0.15
HEADER_LOGO_MAX_WIDTH_RATIO = 0.45

VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr"
}

HYPHEN_TOKENS = {"-", "‐", "-", "‒", "–", "—"}

HYPHEN_CHARS_FOR_QA = "-‐-‒–—−"

OPTIONAL_CLOSE_TAGS = set()  # keep strict because your HTML is XHTML-like


# ── Dataclasses ──────────────────────────────────────────────────────────────

@dataclass
class Issue:
    category: str
    severity: str
    line: object
    message: str
    snippet: str = ""
    expected: str = ""
    actual: str = ""


@dataclass
class TextToken:
    text: str
    norm: str
    line: object = None
    tag: object = None
    bold: bool = False
    italic: bool = False
    heading_level: int = 0
    in_allowed_block: bool = True

class RawHTMLTagValidator(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.stack = []
        self.issues = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()

        if tag in VOID_TAGS:
            return

        self.stack.append((tag, self.getpos()[0]))

    def handle_startendtag(self, tag, attrs):
        # Handles <br />, <img />, etc.
        return

    def handle_endtag(self, tag):
        tag = tag.lower()
        line = self.getpos()[0]

        if tag in VOID_TAGS:
            return

        if not self.stack:
            self.issues.append(Issue(
                "Unexpected Closing Tag",
                "error",
                line,
                f'Found closing tag </{tag}> without a matching opening tag.',
                expected=f"<{tag}> before </{tag}>",
                actual=f"</{tag}>",
            ))
            return

        top_tag, top_line = self.stack[-1]

        if top_tag == tag:
            self.stack.pop()
            return

        # Search deeper in stack to see if this tag exists but nesting is wrong.
        matching_index = None
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                matching_index = i
                break

        if matching_index is None:
            self.issues.append(Issue(
                "Unexpected Closing Tag",
                "error",
                line,
                f'Found closing tag </{tag}> but current open tag is <{top_tag}> from line {top_line}.',
                expected=f"</{top_tag}>",
                actual=f"</{tag}>",
            ))
            return

        # Example: <p><strong>Text</p></strong>
        unclosed = self.stack[matching_index + 1:]

        for unclosed_tag, unclosed_line in reversed(unclosed):
            self.issues.append(Issue(
                "Tag Nesting Mismatch",
                "error",
                line,
                f'Tag <{unclosed_tag}> opened on line {unclosed_line} was not closed before </{tag}>.',
                expected=f"</{unclosed_tag}> before </{tag}>",
                actual=f"</{tag}>",
            ))

        # Remove matched tag and wrongly nested children from stack.
        self.stack = self.stack[:matching_index]

    def close(self):
        super().close()

        for tag, line in reversed(self.stack):
            if tag in OPTIONAL_CLOSE_TAGS:
                continue

            self.issues.append(Issue(
                "Unclosed Tag",
                "error",
                line,
                f'Opening tag <{tag}> on line {line} was not closed.',
                expected=f"</{tag}>",
                actual="missing closing tag",
            ))


def check_raw_html_tags(html_path: str):
    with open(html_path, "r", encoding="utf-8", errors="replace") as f:
        raw_html = f.read()

    validator = RawHTMLTagValidator()

    try:
        validator.feed(raw_html)
        validator.close()
    except Exception as e:
        validator.issues.append(Issue(
            "HTML Parse Error",
            "error",
            None,
            f"HTML parser failed while checking raw tags: {e}",
            expected="Valid HTML",
            actual="Parse failure",
        ))

    return validator.issues

# ── Basic text helpers ───────────────────────────────────────────────────────

def norm_text(text: str) -> str:
    return WS.sub(" ", text).strip().lower().rstrip(".")


def norm_token(text: str) -> str:
    text = text.replace("’", "'").replace("‘", "'")
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("–", "-").replace("—", "-")
    text = text.replace("\u00a0", " ")
    return text.lower()


def strip_boilerplate_text(text: str) -> str:
    for pattern in BOILERPLATE_PATTERNS:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)
    return WS.sub(" ", text).strip()


def is_boilerplate_line(text: str) -> bool:
    raw = WS.sub(" ", text or "").strip()
    if not raw:
        return True

    cleaned = strip_boilerplate_text(raw)
    if not cleaned:
        return True

    if re.fullmatch(r"Page\s+\d+", raw, flags=re.IGNORECASE):
        return True

    return False


def detect_language(text: str) -> str:
    sample = text[:3000].lower()

    if len(re.findall(r"[\u0400-\u04FF]", sample)) > 20:
        return "Russian"
    if len(re.findall(r"[\u0600-\u06FF]", sample)) > 20:
        return "Arabic"
    if len(re.findall(r"[\u0900-\u097F]", sample)) > 20:
        return "Hindi"
    if len(re.findall(r"[\u4E00-\u9FFF]", sample)) > 20:
        return "Chinese"
    if len(re.findall(r"[\u3040-\u30FF]", sample)) > 20:
        return "Japanese"
    if len(re.findall(r"[\uAC00-\uD7AF]", sample)) > 20:
        return "Korean"

    scores = {
        lang: sum(sample.count(t) for t in tgrams)
        for lang, tgrams in LANG_TRIGRAMS.items()
    }

    diacritics = len(re.findall(r"[àáâãäåæçèéêëìíîïðñòóôõöùúûüý]", sample))
    if diacritics < 5:
        scores["English"] = scores.get("English", 0) * 1.5

    return max(scores, key=scores.get)


def context(tokens, idx, radius=8) -> str:
    if not tokens:
        return ""

    idx = max(0, min(idx, len(tokens) - 1))
    start = max(0, idx - radius)
    end = min(len(tokens), idx + radius + 1)

    return " ".join(t.text for t in tokens[start:end])


def is_punctuation(token: str) -> bool:
    return bool(re.fullmatch(r"[^\w\s]", token or ""))


def should_ignore_token(token: str) -> bool:
    return token in {"•", "●", "◦", "▪", "▫"}


# ── HTML extraction ──────────────────────────────────────────────────────────

def load_html(path: str) -> BeautifulSoup:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return BeautifulSoup(
            f.read(),
            "html.parser",
            store_line_numbers=True,
        )


def is_visible_text_node(node) -> bool:
    if not isinstance(node, NavigableString):
        return False

    if isinstance(node, (Comment, Doctype, Declaration, ProcessingInstruction)):
        return False

    if not str(node).strip():
        return False

    parent = node.parent

    while parent is not None and getattr(parent, "name", None):
        name = parent.name.lower()

        if name in SKIP_TEXT_PARENT_TAGS:
            return False

        if parent.get("aria-hidden") == "true":
            return False

        style = parent.get("style", "")
        style_norm = style.replace(" ", "").lower()

        if "display:none" in style_norm or "visibility:hidden" in style_norm:
            return False

        parent = parent.parent

    return True


def has_bold_ancestor(node) -> bool:
    parent = node.parent

    while parent is not None and getattr(parent, "name", None):
        name = parent.name.lower()

        if name in ("strong", "b", "h1", "h2", "h3", "h4", "h5", "h6"):
            return True

        style = parent.get("style", "")
        style_norm = style.replace(" ", "").lower()

        if (
            "font-weight:bold" in style_norm
            or "font-weight:700" in style_norm
            or "font-weight:800" in style_norm
            or "font-weight:900" in style_norm
        ):
            return True

        parent = parent.parent

    return False


def has_italic_ancestor(node) -> bool:
    parent = node.parent

    while parent is not None and getattr(parent, "name", None):
        name = parent.name.lower()

        if name in ("em", "i"):
            return True

        style = parent.get("style", "")
        style_norm = style.replace(" ", "").lower()

        if "font-style:italic" in style_norm:
            return True

        parent = parent.parent

    return False


def get_heading_level(node) -> int:
    parent = node.parent

    while parent is not None and getattr(parent, "name", None):
        name = parent.name.lower()

        if name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            return int(name[1])

        parent = parent.parent

    return 0


def is_inside_allowed_block(node) -> bool:
    parent = node.parent

    while parent is not None and getattr(parent, "name", None):
        if parent.name.lower() in ALLOWED_TEXT_BLOCKS:
            return True
        parent = parent.parent

    return False


def extract_html_tokens(soup: BeautifulSoup):
    tokens = []

    for node in soup.find_all(string=True):
        if not is_visible_text_node(node):
            continue

        text = strip_boilerplate_text(str(node))
        if not text:
            continue

        line = getattr(node.parent, "sourceline", None)

        for m in TOKEN_RE.finditer(text):
            raw = m.group(0)

            if should_ignore_token(raw):
                continue

            tokens.append(
                TextToken(
                    text=raw,
                    norm=norm_token(raw),
                    line=line,
                    tag=node.parent,
                    bold=has_bold_ancestor(node),
                    italic=has_italic_ancestor(node),
                    heading_level=get_heading_level(node),
                    in_allowed_block=is_inside_allowed_block(node),
                )
            )

    return tokens


def extract_html_images(soup: BeautifulSoup, html_path: str):
    """
    No folder walking.
    Only checks the exact src path after server.py rewrites uploaded image paths.
    """
    base = os.path.dirname(os.path.abspath(html_path))
    results = []

    for tag in soup.find_all("img"):
        src = tag.get("src", "")
        resolved = ""
        pil = None

        if src and not src.startswith(("http://", "https://", "data:", "#")):
            resolved = os.path.normpath(os.path.join(base, src))

            if os.path.exists(resolved):
                try:
                    pil = Image.open(resolved).convert("RGB")
                except Exception:
                    pil = None

        results.append((tag, pil, resolved))

    return results


# ── PDF extraction ───────────────────────────────────────────────────────────

def _line_boxes_to_ignore(page):
    boxes = []

    for line in page.extract_text_lines() or []:
        text = line.get("text", "")

        if is_boilerplate_line(text):
            boxes.append(
                (
                    float(line.get("top", 0)),
                    float(line.get("bottom", 0)),
                )
            )

    return boxes


def _is_inside_ignored_line_box(word, boxes) -> bool:
    top = float(word.get("top", 0))
    bottom = float(word.get("bottom", 0))

    for b_top, b_bottom in boxes:
        if top >= b_top - 2 and bottom <= b_bottom + 2:
            return True

    return False


def extract_pdf_text(pdf_path: str) -> str:
    parts = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for line in page.extract_text_lines() or []:
                text = line.get("text", "")
                text = strip_boilerplate_text(text)

                if not text:
                    continue

                parts.append(text)

    return "\n".join(parts)


def extract_pdf_tokens(pdf_path: str):
    tokens = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            ignored_boxes = _line_boxes_to_ignore(page)

            chars = page.chars or []
            usable_chars = [
                c for c in chars
                if not _is_inside_ignored_line_box(c, ignored_boxes)
            ]

            sizes = [round(float(c["size"])) for c in usable_chars if "size" in c]
            body_size = max(set(sizes), key=sizes.count) if sizes else 10

            try:
                words = page.extract_words(
                    keep_blank_chars=False,
                    use_text_flow=True,
                    extra_attrs=["fontname", "size"],
                )
            except Exception:
                words = page.extract_words(
                    keep_blank_chars=False,
                    use_text_flow=True,
                )

            for w in words:
                if _is_inside_ignored_line_box(w, ignored_boxes):
                    continue

                raw_word = strip_boilerplate_text(w.get("text", ""))
                if not raw_word:
                    continue

                fontname = str(w.get("fontname", "")).lower()

                try:
                    size = float(w.get("size", body_size))
                except Exception:
                    size = body_size

                is_bold = (
                    "bold" in fontname
                    or "black" in fontname
                    or "heavy" in fontname
                    or "semibold" in fontname
                )

                heading_level = 0
                if size >= body_size * 1.55:
                    heading_level = 1
                elif size >= body_size * 1.30:
                    heading_level = 2
                elif size >= body_size * 1.15:
                    heading_level = 3

                for m in TOKEN_RE.finditer(raw_word):
                    raw = m.group(0)

                    if should_ignore_token(raw):
                        continue

                    tokens.append(
                        TextToken(
                            text=raw,
                            norm=norm_token(raw),
                            line=None,
                            tag=None,
                            bold=is_bold,
                            heading_level=heading_level,
                            in_allowed_block=True,
                        )
                    )

    return tokens


# ── Image extraction / comparison ────────────────────────────────────────────

def is_blank_or_logo_placeholder(img: Image.Image) -> bool:
    try:
        small = img.convert("RGB").resize((64, 64))
        arr = np.asarray(small)

        white_ratio = np.mean(np.all(arr > 245, axis=2))
        if white_ratio > 0.92:
            return True

        if arr.std() < 8:
            return True

        return False
    except Exception:
        return False


def extract_pdf_images(pdf_path: str):
    page_imgs = []

    with pdfplumber.open(pdf_path) as pdf:
        num_pages = len(pdf.pages)

        for page_idx, page in enumerate(pdf.pages):
            for obj in page.images:
                try:
                    width = obj["x1"] - obj["x0"]
                    height = obj["y1"] - obj["y0"]
                    top = page.height - obj["y1"]

                    # Ignore header logo / blank logo placeholder area.
                    if (
                        obj["x0"] <= page.width * HEADER_LOGO_MAX_LEFT_RATIO
                        and top <= page.height * HEADER_LOGO_MAX_TOP_RATIO
                        and width <= page.width * HEADER_LOGO_MAX_WIDTH_RATIO
                        and height <= page.height * HEADER_LOGO_MAX_HEIGHT_RATIO
                    ):
                        continue

                    bbox = (
                        obj["x0"],
                        page.height - obj["y1"],
                        obj["x1"],
                        page.height - obj["y0"],
                    )

                    cropped = page.crop(bbox).to_image(resolution=100).original
                    cropped = cropped.convert("RGB")

                    if is_blank_or_logo_placeholder(cropped):
                       continue

# Store original PDF display dimensions.
# These are the width/height of the image placement inside the PDF page.
                    cropped._qa_pdf_display_width = float(width)
                    cropped._qa_pdf_display_height = float(height)

                    page_imgs.append((page_idx, cropped))

                    

                except Exception:
                    continue

    if not page_imgs:
        return []

    repeat_threshold = max(2, math.ceil(num_pages / 2))
    groups = []

    for page_idx, img in page_imgs:
        try:
            h = imagehash.phash(img)
        except Exception:
            continue

        for group in groups:
            if (h - group[0]) <= 8:
                group[1].add(page_idx)
                break
        else:
            groups.append((h, {page_idx}, img))

    return [img for _, pages, img in groups if len(pages) < repeat_threshold]
    
def parse_css_length(value):
    if value is None:
        return None

    value = str(value).strip().lower()

    m = re.search(r"([0-9]+(?:\.[0-9]+)?)", value)
    if not m:
        return None

    try:
        return float(m.group(1))
    except Exception:
        return None


def get_img_declared_dimensions(tag):
    style = parse_inline_style(tag.get("style", ""))

    width = parse_css_length(tag.get("width"))
    height = parse_css_length(tag.get("height"))

    if width is None:
        width = parse_css_length(style.get("width"))

    if height is None:
        height = parse_css_length(style.get("height"))

    return width, height


def _ratio_error(actual, expected):
    if not actual or not expected:
        return 0.0

    return abs(actual - expected) / expected


def check_image_dimensions(tag, matched_pdf_img, html_img, line):
    issues = []

    declared_w, declared_h = get_img_declared_dimensions(tag)

    # No declared width/height means there is nothing to validate.
    if declared_w is None and declared_h is None:
        return issues

    expected_w = getattr(matched_pdf_img, "_qa_pdf_display_width", None)
    expected_h = getattr(matched_pdf_img, "_qa_pdf_display_height", None)

    # Fallback to image pixel ratio if PDF display size is unavailable.
    if not expected_w or not expected_h:
        expected_w = matched_pdf_img.width
        expected_h = matched_pdf_img.height

    expected_ratio = expected_w / expected_h

    # 8% tolerance for PDF-point vs HTML-pixel conversion differences.
    size_tolerance = 0.08

    size_mismatch = False
    mismatch_parts = []

    if declared_w is not None:
        w_error = _ratio_error(declared_w, expected_w)

        if w_error > size_tolerance:
            size_mismatch = True
            mismatch_parts.append(
                f"width expected about {expected_w:.1f}, got {declared_w:.1f}"
            )

    if declared_h is not None:
        h_error = _ratio_error(declared_h, expected_h)

        if h_error > size_tolerance:
            size_mismatch = True
            mismatch_parts.append(
                f"height expected about {expected_h:.1f}, got {declared_h:.1f}"
            )

    if size_mismatch:
        issues.append(Issue(
            "Image Display Size Mismatch",
            "error",
            line,
            "HTML image declared width/height differs from the image size in the PDF.",
            snippet=str(tag)[:300],
            expected=f"{expected_w:.1f} x {expected_h:.1f}",
            actual=(
                f"{declared_w if declared_w is not None else 'not set'} x "
                f"{declared_h if declared_h is not None else 'not set'}"
            ),
        ))

    # If both width and height are declared, also check distortion/aspect ratio.
    if declared_w is not None and declared_h is not None and declared_h != 0:
        declared_ratio = declared_w / declared_h
        ratio_error = _ratio_error(declared_ratio, expected_ratio)

        if ratio_error > 0.03:
            issues.append(Issue(
                "Image Aspect Ratio Mismatch",
                "error",
                line,
                "HTML image width/height changes the expected image aspect ratio.",
                snippet=str(tag)[:300],
                expected=f"aspect ratio about {expected_ratio:.3f}",
                actual=f"{declared_w:.1f} x {declared_h:.1f}, ratio {declared_ratio:.3f}",
            ))

    # Check actual image file ratio too.
    if html_img and html_img.height:
        actual_file_ratio = html_img.width / html_img.height
        file_ratio_error = _ratio_error(actual_file_ratio, expected_ratio)

        if file_ratio_error > 0.03:
            issues.append(Issue(
                "Image File Aspect Ratio Mismatch",
                "error",
                line,
                "HTML image file aspect ratio differs from the matched PDF image.",
                snippet=str(tag)[:300],
                expected=f"aspect ratio about {expected_ratio:.3f}",
                actual=f"{html_img.width} x {html_img.height}, ratio {actual_file_ratio:.3f}",
            ))

    return issues
    
def check_title(pdf_path: str, soup: BeautifulSoup):
    issues = []

    expected_title = extract_pdf_title(pdf_path)
    title_tag = soup.find("title")

    if not expected_title:
        return issues

    if not title_tag:
        issues.append(Issue(
            "Missing Title Tag",
            "warning",
            None,
            "HTML is missing a <title> tag.",
            expected=expected_title,
            actual="",
        ))
        return issues

    actual_title = title_tag.get_text(" ", strip=True)

    if norm_text(expected_title) != norm_text(actual_title):
        issues.append(Issue(
            "Title Mismatch",
            "error",
            getattr(title_tag, "sourceline", None),
            f'Expected HTML title "{expected_title}" but found "{actual_title}".',
            expected=expected_title,
            actual=actual_title,
            snippet=f"<title>{actual_title}</title>",
        ))

    return issues


def _hash_image(img: Image.Image):
    img = img.convert("RGB")
    return imagehash.phash(img), imagehash.colorhash(img)


def check_images(source_imgs, html_img_entries, hash_threshold=18, color_threshold=15):
    issues = []

    for tag, pil, resolved in html_img_entries:
        src = tag.get("src", "(no src)")
        basename = os.path.basename(src).lower()

        if basename in IGNORE_IMAGES:
            continue

        if pil is None:
            line = getattr(tag, "sourceline", None)
            issues.append(
                Issue(
                    "Broken Image",
                    "error",
                    line,
                    f"Image file not found on disk: {src}",
                    expected="Existing image file",
                    actual=src,
                )
            )

    if not source_imgs:
        return issues

    valid_html = []

    for tag, pil, resolved in html_img_entries:
        src = tag.get("src", "")
        basename = os.path.basename(src).lower()

        if basename in IGNORE_IMAGES:
            continue

        if pil is not None:
            valid_html.append((tag, pil, resolved))

    src_hashes = [_hash_image(img) for img in source_imgs]
    html_hashes = [_hash_image(pil) for _, pil, _ in valid_html]

    src_phashes = [h[0] for h in src_hashes]
    src_colorhashes = [h[1] for h in src_hashes]

    matched_src = set()
    order_seq = []

    for (tag, pil, resolved), (h_p, h_c) in zip(valid_html, html_hashes):
        if not src_phashes:
            continue

        p_dists = [h_p - sh for sh in src_phashes]
        best_i = int(np.argmin(p_dists))
        best_p_dist = p_dists[best_i]
        c_dist = h_c - src_colorhashes[best_i]
        line = getattr(tag, "sourceline", None)

        if best_p_dist <= hash_threshold and c_dist <= color_threshold:
            matched_src.add(best_i)
            order_seq.append((best_i, tag, line))
            
            issues += check_image_dimensions(
            tag=tag,
            matched_pdf_img=source_imgs[best_i],
            html_img=pil,
            line=line,
    )

        elif best_p_dist <= hash_threshold:
            issues.append(
                Issue(
                    "Image Possibly Wrong",
                    "warning",
                    line,
                    "Image structure matches a source image, but colors differ. Please verify manually.",
                    snippet=resolved,
                    expected="PDF image color profile",
                    actual="HTML image color profile differs",
                )
            )
            matched_src.add(best_i)
            order_seq.append((best_i, tag, line))
            
            matched_src.add(best_i)
            order_seq.append((best_i, tag, line))

            issues += check_image_dimensions(
            tag=tag,
            matched_pdf_img=source_imgs[best_i],
            html_img=pil,
            line=line,
        )

        else:
            similarity = max(0.0, 1.0 - best_p_dist / 64.0)
            issues.append(
                Issue(
                    "Image Doesn't Match Source",
                    "error",
                    line,
                    f"This image does not match any image in the source PDF. Best visual similarity: {similarity:.0%}.",
                    snippet=resolved,
                    expected="Matching source PDF image",
                    actual=os.path.basename(resolved),
                )
            )

    for idx in range(len(source_imgs)):
        if idx not in matched_src:
            issues.append(
                Issue(
                    "Missing Image",
                    "error",
                    None,
                    f"Source PDF image #{idx + 1} was not found in the HTML.",
                    expected=f"PDF image #{idx + 1}",
                    actual="Missing in HTML",
                )
            )

    last = -1
    for idx, tag, line in order_seq:
        if idx < last - 1:
            issues.append(
                Issue(
                    "Image Order Mismatch",
                    "warning",
                    line,
                    f"This image appears after source image #{last + 1}, but it maps to source image #{idx + 1}.",
                    expected="PDF image order",
                    actual="HTML image order differs",
                )
            )

        last = max(last, idx)

    return issues
    
def has_b_or_strong_descendant(tag) -> bool:
    if not tag:
        return False

    # If the tag itself is b/strong
    if getattr(tag, "name", "").lower() in ("b", "strong"):
        return True

    return tag.find(["b", "strong"]) is not None


def text_prefix_before_colon(text: str) -> str:
    """
    Returns label prefix like:
      'Pituitary tumor:'
      'Blood tests:'
    """
    text = WS.sub(" ", text or "").strip()

    m = re.match(r"^(.{1,90}?:)", text)
    if not m:
        return ""

    return m.group(1).strip()
    
def check_required_b_tags_by_company_spec(soup: BeautifulSoup):
    """
    Company-structure rule:
    Only label-style text inside list paragraphs should require <b>/<strong>.

    Example:
      <p><b>Blood tests:</b> remaining text</p>
    """
    issues = []
    seen = set()

    def add_issue(tag, message, expected="", actual=""):
        line = getattr(tag, "sourceline", None)
        snippet = str(tag)[:350]
        key = ("Missing B Tag", line, snippet, expected, actual)

        if key in seen:
            return

        seen.add(key)
        issues.append(Issue(
            "Missing B Tag",
            "error",
            line,
            message,
            snippet=snippet,
            expected=expected,
            actual=actual,
        ))

    for li in soup.find_all("li"):
        for p in li.find_all("p", recursive=True):
            text = p.get_text(" ", strip=True)
            label = text_prefix_before_colon(text)

            if not label:
                continue

            label_is_bold = False

            for btag in p.find_all(["b", "strong"]):
                bold_text = btag.get_text(" ", strip=True)

                if label.lower() == bold_text.lower():
                    label_is_bold = True
                    break

            if not label_is_bold:
                add_issue(
                    p,
                    f'List label "{label}" should be wrapped in <b>/<strong>.',
                    expected=f"<b>{label}</b>",
                    actual=label,
                )

    return issues

def check_missing_b_tags_strict(soup: BeautifulSoup):
    """
    Strict company HTML structure check for removed <b>/<strong> tags.

    Only checks h1/h2/h3 headings. It does NOT check every colon label,
    because labels like "Benefits:" and "Call your care team if:" are valid
    converter output in your current files and should not create noise.

    Catches:
      <h2><b>Before the Procedure</b></h2>
    changed to:
      <h2>Before the Procedure</h2>
    """
    issues = []
    seen = set()

    def add_issue(tag, message, expected, actual):
        line = getattr(tag, "sourceline", None)
        snippet = str(tag)[:350]
        key = ("Missing B Tag", line, snippet, expected, actual)

        if key in seen:
            return

        seen.add(key)
        issues.append(Issue(
            "Missing B Tag",
            "error",
            line,
            message,
            snippet=snippet,
            expected=expected,
            actual=actual,
        ))

    # h1-h3 headings are expected to contain explicit <b>/<strong> in this converter output.
    # h4-h6 are skipped because real clean files may use them without inner <b>.
    for heading in soup.find_all(["h1", "h2", "h3"]):
        text = heading.get_text(" ", strip=True)
        if not text:
            continue

        if heading.find(["b", "strong"]) is None:
            add_issue(
                heading,
                f"<{heading.name}> heading text is missing the required <b>/<strong> wrapper.",
                f"<{heading.name}><b>{text}</b></{heading.name}>",
                str(heading)[:200],
            )

    return issues

def check_tag_attributes_and_styles(soup: BeautifulSoup):
    issues = []
    seen = set()

    def add_issue(category, tag, message, expected="", actual=""):
        line = getattr(tag, "sourceline", None)
        snippet = str(tag)[:350]

        key = (category, line, snippet, expected, actual)

        if key in seen:
            return

        seen.add(key)

        issues.append(Issue(
            category,
            "error",
            line,
            message,
            snippet=snippet,
            expected=expected,
            actual=actual,
        ))

    # Check <li data-list-text="">
    for li in soup.find_all("li"):
        text = li.get_text(" ", strip=True)

        if not text:
            continue

        marker = (li.get("data-list-text") or "").strip()

        if marker != EXPECTED_BULLET_MARKER:
            add_issue(
                "Tag Attribute Mismatch",
                li,
                "List item data-list-text attribute differs from the expected bullet marker.",
                expected=f'data-list-text="{EXPECTED_BULLET_MARKER}"',
                actual=f'data-list-text="{marker}"',
            )

    # Check <p> styles inside list items
    for li in soup.find_all("li"):
        for p in li.find_all("p", recursive=True):
            text = p.get_text(" ", strip=True)

            if not text:
                continue

            style = parse_inline_style(p.get("style", ""))

            expected_styles = {
                "padding-left": "23pt",
                "text-indent": "-10pt",
                "line-height": "110%",
                "text-align": "left",
            }

            for prop, expected_value in expected_styles.items():
                actual_value = style.get(prop)

                if actual_value != expected_value:
                    add_issue(
                        "Style Attribute Mismatch",
                        p,
                        f'List paragraph style "{prop}" differs from expected value.',
                        expected=f"{prop}: {expected_value}",
                        actual=f"{prop}: {actual_value if actual_value is not None else 'missing'}",
                    )

            if "padding-right" in style:
                add_issue(
                    "Style Attribute Mismatch",
                    p,
                    "List paragraph uses padding-right, but expected padding-left.",
                    expected="padding-left: 23pt",
                    actual=f"padding-right: {style.get('padding-right')}",
                )

    return issues
    
def is_hyphen_token_text(text: str) -> bool:
    return (text or "").strip() in HYPHEN_TOKENS


def merge_spaced_hyphen_tokens(tokens):
    """
    Converts:
      long - term
      half - gallon

    into:
      long-term
      half-gallon

    This avoids false Changed Text errors when PDF extraction adds spaces
    around hyphens but HTML has normal hyphenated words.
    """

    def is_word_token(text):
        return bool(re.fullmatch(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?", text or ""))

    def is_hyphen_token(text):
        return (text or "").strip() in HYPHEN_TOKENS

    merged = []
    i = 0

    while i < len(tokens):
        if (
            i + 2 < len(tokens)
            and is_word_token(tokens[i].text)
            and is_hyphen_token(tokens[i + 1].text)
            and is_word_token(tokens[i + 2].text)
        ):
            combined_text = f"{tokens[i].text}-{tokens[i + 2].text}"

            merged.append(TextToken(
                text=combined_text,
                norm=norm_token(combined_text),
                line=tokens[i].line,
                tag=tokens[i].tag,
                bold=tokens[i].bold or tokens[i + 2].bold,
                italic=tokens[i].italic or tokens[i + 2].italic,
                heading_level=tokens[i].heading_level or tokens[i + 2].heading_level,
                in_allowed_block=(
                    tokens[i].in_allowed_block
                    and tokens[i + 2].in_allowed_block
                ),
            ))

            i += 3
            continue

        merged.append(tokens[i])
        i += 1

    return merged

# ── Strict text comparison ───────────────────────────────────────────────────

def _qa_hyphen_cmp(text: str) -> str:
    """Normalize only hyphen spacing noise for final issue filtering."""
    text = str(text or "").lower()
    text = (
        text.replace("‐", "-")
            .replace("‒", "-")
            .replace("–", "-")
            .replace("—", "-")
            .replace("−", "-")
    )
    text = re.sub(r"\s*-\s*", "-", text)
    text = WS.sub(" ", text).strip()
    return text


def _is_hyphen_spacing_noise(expected: str, actual: str) -> bool:
    if not expected or not actual:
        return False

    e = _qa_hyphen_cmp(expected)
    a = _qa_hyphen_cmp(actual)

    return e == a and e != str(expected or "").lower().strip() and "-" in e


def _add_issue(issues, seen, issue: Issue):
    # Global guard for PDF extraction / converter hyphen spacing noise.
    # Examples: high - time vs high-time, long - term vs long-term, X - rays vs X-rays.
    if (
        _is_hyphen_spacing_noise(issue.expected, issue.actual)
        or is_hyphen_spacing_only_difference(issue.expected, issue.actual)
    ):
        return

    key = (
        issue.category,
        issue.line,
        issue.message,
        issue.expected,
        issue.actual,
    )

    if key not in seen:
        seen.add(key)
        issues.append(issue)
        
def extract_pdf_title(pdf_path: str) -> str:
    """
    Gets the first real non-footer PDF line.
    For this document type, that is usually the document title.
    """
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            lines = page.extract_text_lines() or []

            for line in lines:
                text = strip_boilerplate_text(line.get("text", ""))

                if not text:
                    continue

                return WS.sub(" ", text).strip()

    return ""

def is_hyphen_spacing_only_difference(expected: str, actual: str) -> bool:
    if not expected or not actual:
        return False

    return canonical_hyphen_text(expected) == canonical_hyphen_text(actual)

def check_strict_text_mapping(pdf_path: str, soup: BeautifulSoup):
    pdf_tokens = merge_spaced_hyphen_tokens(extract_pdf_tokens(pdf_path))
    html_tokens = merge_spaced_hyphen_tokens(extract_html_tokens(soup))

    pdf_norms = [t.norm for t in pdf_tokens]
    html_norms = [t.norm for t in html_tokens]

    matcher = difflib.SequenceMatcher(
        None,
        pdf_norms,
        html_norms,
        autojunk=False,
    )

    issues = []
    seen = set()
    semantic_seen = set()

    def add_semantic_issue_once(category, severity, html_token, message, expected, actual):
        tag = html_token.tag
        line = html_token.line
        tag_id = id(tag) if tag else None

        key = (
            category,
            line,
            tag_id,
            expected,
            actual,
        )

        if key in semantic_seen:
            return

        semantic_seen.add(key)

        if tag:
            snippet = str(tag)[:300]
            actual_value = actual or tag.name
        else:
            snippet = html_token.text
            actual_value = actual or html_token.text

        _add_issue(
            issues,
            seen,
            Issue(
                category,
                severity,
                line,
                message,
                snippet=snippet,
                expected=expected,
                actual=actual_value,
            ),
        )

    for op, i1, i2, j1, j2 in matcher.get_opcodes():

        if op == "equal":
            for offset in range(i2 - i1):
                p = pdf_tokens[i1 + offset]
                h = html_tokens[j1 + offset]

                # Same normalized token, but different case.
                # Example: Body vs boDy
                if (
                    p.text != h.text
                    and p.text.lower() == h.text.lower()
                    and any(ch.isalpha() for ch in p.text)
                ):
                    _add_issue(
                        issues,
                        seen,
                        Issue(
                            "Capitalization Mismatch",
                            "error",
                            h.line,
                            f'Expected capitalization "{p.text}" but HTML shows "{h.text}".',
                            snippet=(
                                f"PDF context: {context(pdf_tokens, i1 + offset)}\n"
                                f"HTML context: {context(html_tokens, j1 + offset)}"
                            ),
                            expected=p.text,
                            actual=h.text,
                        ),
                    )

                # Missing bold/strong.
                # Do not require <strong>/<b> for headings because h1-h6 are naturally bold.
                if p.bold and not p.heading_level and not h.bold:
                    add_semantic_issue_once(
                        "Missing Strong/Bold Tag",
                        "warning",
                        h,
                        "PDF text is bold, but the matching HTML text is not inside <strong>/<b> or bold CSS.",
                        "strong/b or font-weight:bold",
                        h.tag.name if h.tag else h.text,
                    )

                # Missing heading tag.
                if p.heading_level and not h.heading_level:
                    add_semantic_issue_once(
                        "Missing Heading Tag",
                        "warning",
                        h,
                        f"PDF heading text should be inside an h{p.heading_level} heading tag.",
                        f"h{p.heading_level}",
                        h.tag.name if h.tag else h.text,
                    )

                # Heading level mismatch.
                if p.heading_level and h.heading_level and p.heading_level != h.heading_level:
                    add_semantic_issue_once(
                        "Heading Level Mismatch",
                        "warning",
                        h,
                        f"PDF heading level is h{p.heading_level}, but HTML uses h{h.heading_level}.",
                        f"h{p.heading_level}",
                        f"h{h.heading_level}",
                    )

                # Text outside expected semantic document blocks.
                # Do not duplicate a missing-heading error with a generic paragraph/list warning.
                if not h.in_allowed_block and not p.heading_level:
                    add_semantic_issue_once(
                        "Missing Paragraph/List Tag",
                        "warning",
                        h,
                        "Visible text is not inside an expected document tag such as p, li, h1-h6, td/th, or figcaption.",
                        "p/li/h1-h6/td/th/figcaption",
                        h.tag.name if h.tag else h.text,
                    )

            continue

        expected = " ".join(t.text for t in pdf_tokens[i1:i2]).strip()
        actual = " ".join(t.text for t in html_tokens[j1:j2]).strip()

        line = html_tokens[j1].line if j1 < len(html_tokens) else None

        if not expected and not actual:
            continue

        # Ignore converter/PDF extraction differences around hyphen spacing.
        # Example:
        #   PDF:  mini - stroke
        #   HTML: mini-stroke
        if _is_hyphen_spacing_noise(expected, actual) or is_hyphen_spacing_only_difference(expected, actual):
            continue

        if op == "replace":
            category = "Changed Text"

            pdf_part = pdf_tokens[i1:i2]
            html_part = html_tokens[j1:j2]

            if pdf_part and html_part:
                if (
                    all(is_punctuation(t.text) for t in pdf_part)
                    or all(is_punctuation(t.text) for t in html_part)
                ):
                    category = "Punctuation Mismatch"

            _add_issue(
                issues,
                seen,
                Issue(
                    category,
                    "error",
                    line,
                    f'Expected "{expected}" but HTML shows "{actual}".',
                    snippet=(
                        f"PDF context: {context(pdf_tokens, i1)}\n"
                        f"HTML context: {context(html_tokens, j1)}"
                    ),
                    expected=expected,
                    actual=actual,
                ),
            )

        elif op == "delete":
            category = "Missing Text"

            if all(is_punctuation(t.text) for t in pdf_tokens[i1:i2]):
                category = "Missing Punctuation"

            _add_issue(
                issues,
                seen,
                Issue(
                    category,
                    "error",
                    line,
                    f'PDF text is missing from HTML: "{expected}".',
                    snippet=f"PDF context: {context(pdf_tokens, i1)}",
                    expected=expected,
                    actual="",
                ),
            )

        elif op == "insert":
            category = "Extra Text"

            if all(is_punctuation(t.text) for t in html_tokens[j1:j2]):
                category = "Extra Punctuation"

            _add_issue(
                issues,
                seen,
                Issue(
                    category,
                    "error",
                    line,
                    f'HTML contains extra text not found in PDF: "{actual}".',
                    snippet=f"HTML context: {context(html_tokens, j1)}",
                    expected="",
                    actual=actual,
                ),
            )

    return issues
    

def canonical_hyphen_text(text: str) -> str:
    """
    Makes these equivalent:
      long - term
      long- term
      long -term
      long-term
      long-term
    """
    text = norm_text(text)

    # Convert all hyphen-like unicode chars to normal hyphen
    text = re.sub(f"[{re.escape(HYPHEN_CHARS_FOR_QA)}]", "-", text)

    # Remove spaces around hyphen
    text = re.sub(r"\s*-\s*", "-", text)

    # Normal whitespace cleanup
    text = WS.sub(" ", text)

    return text.strip().lower()


def is_hyphen_spacing_only_difference(expected: str, actual: str) -> bool:
    if not expected or not actual:
        return False

    return canonical_hyphen_text(expected) == canonical_hyphen_text(actual)

def normalize_hyphen_spacing(text):
    text = str(text or "")

    # Normalize dash types to normal hyphen
    text = text.replace("‐", "-").replace("-", "-").replace("–", "-").replace("—", "-")

    # Convert spaced hyphen forms into compact hyphen
    # high - time -> high-time
    # high- time -> high-time
    # high -time -> high-time
    text = re.sub(r"(?<=\w)\s*-\s*(?=\w)", "-", text)

    # Normalize remaining whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text.lower()

# ── Other checks ─────────────────────────────────────────────────────────────

def check_filenames(pdf_path, html_path):
    pb = os.path.splitext(os.path.basename(pdf_path))[0]
    hb = os.path.splitext(os.path.basename(html_path))[0]

    if pb != hb:
        return [
            Issue(
                "Filename Mismatch",
                "error",
                None,
                f'PDF is "{os.path.basename(pdf_path)}" but HTML is "{os.path.basename(html_path)}". Basenames should usually match.',
                expected=pb,
                actual=hb,
            )
        ]

    return []


def check_garbled(soup: BeautifulSoup):
    issues = []

    for node in soup.find_all(string=True):
        if not is_visible_text_node(node):
            continue

        text = str(node)

        if MOJIBAKE.search(text):
            line = getattr(node.parent, "sourceline", None)
            issues.append(
                Issue(
                    "Garbled / Encoding Error",
                    "error",
                    line,
                    "Text contains mojibake characters indicating an encoding problem.",
                    snippet=text.strip()[:160],
                    expected="Readable Unicode text",
                    actual=text.strip()[:80],
                )
            )

    return issues


def check_placeholders(soup: BeautifulSoup):
    issues = []

    for node in soup.find_all(string=True):
        if not is_visible_text_node(node):
            continue

        text = str(node)
        m = PLACEHOLDER.search(text)

        if m:
            line = getattr(node.parent, "sourceline", None)
            issues.append(
                Issue(
                    "Leftover Placeholder",
                    "error",
                    line,
                    f'Placeholder text found: "{m.group(0)}".',
                    snippet=text.strip()[:160],
                    expected="Final content",
                    actual=m.group(0),
                )
            )

    return issues


def check_links(soup: BeautifulSoup, html_path: str):
    base = os.path.dirname(os.path.abspath(html_path))
    issues = []

    for a in soup.find_all("a"):
        href = a.get("href", "")

        if not href or href.startswith(("http://", "https://", "mailto:", "#", "javascript:")):
            continue

        resolved = os.path.normpath(os.path.join(base, href))

        if not os.path.exists(resolved):
            line = getattr(a, "sourceline", None)
            issues.append(
                Issue(
                    "Broken Link",
                    "error",
                    line,
                    f'Link target not found: "{href}".',
                    expected="Existing local link target",
                    actual=href,
                )
            )

    return issues

def check_inline_style_rules(soup: BeautifulSoup):
    issues = []
    seen = set()

    def add_style_issue(tag, message):
        line = getattr(tag, "sourceline", None)
        snippet = str(tag)[:250]

        key = (
            "Style Attribute Mismatch",
            line,
            snippet,
            "text-align: left",
            "text-align: right",
        )

        if key in seen:
            return

        seen.add(key)

        issues.append(Issue(
            "Style Attribute Mismatch",
            "error",
            line,
            message,
            snippet=snippet,
            expected="text-align: left",
            actual="text-align: right",
        ))

    # Rule 1: list item text should not be right-aligned
    for li in soup.find_all("li"):
        for tag in li.find_all(["p", "span", "div"], recursive=True):
            text = tag.get_text(" ", strip=True)
            if not text:
                continue

            actual_align = get_css_value(tag, "text-align")

            if actual_align == "right":
                add_style_issue(
                    tag,
                    "List item text is right-aligned, but it should be left-aligned."
                )

    # Rule 2: normal paragraphs should not be right-aligned
    for tag in soup.find_all("p"):
        text = tag.get_text(" ", strip=True)

        if not text:
            continue

        # IMPORTANT:
        # If this <p> is inside <li>, Rule 1 already handled it.
        # Do not report it again as a normal paragraph.
        if tag.find_parent("li"):
            continue

        if tag.find("img") and not text:
            continue

        if is_boilerplate_line(text):
            continue

        actual_align = get_css_value(tag, "text-align")

        if actual_align == "right":
            add_style_issue(
                tag,
                "Paragraph text is right-aligned, but expected document body text alignment is left."
            )

    return issues
   
def check_list_markers(soup: BeautifulSoup):
    issues = []
    seen = set()

    for ul in soup.find_all("ul"):
        ul_style = parse_inline_style(ul.get("style", ""))
        ul_list_style = ul_style.get("list-style-type", "")

        for li in ul.find_all("li", recursive=False):
            line = getattr(li, "sourceline", None)
            text = li.get_text(" ", strip=True)

            if not text:
                continue

            marker = (li.get("data-list-text") or "").strip()
            li_style = parse_inline_style(li.get("style", ""))
            li_list_style = li_style.get("list-style-type", "")

            # Case 1: bullet marker changed
            # Example: data-list-text="°" instead of data-list-text="•"
            if marker and marker != EXPECTED_BULLET_MARKER:
                key = (line, marker, text[:80])

                if key not in seen:
                    seen.add(key)

                    issues.append(Issue(
                        "Bullet Marker Mismatch",
                        "error",
                        line,
                        "List item bullet marker differs from the expected PDF bullet.",
                        snippet=str(li)[:300],
                        expected=EXPECTED_BULLET_MARKER,
                        actual=marker,
                    ))

            # Case 2: bullet marker removed/hidden
            combined_style = (
                (ul.get("style", "") or "")
                + ";"
                + (li.get("style", "") or "")
            ).replace(" ", "").lower()

            bullet_removed = (
                ul_list_style == "none"
                or li_list_style == "none"
                or "list-style:none" in combined_style
                or "list-style-type:none" in combined_style
            )

            if bullet_removed:
                key = (line, "missing-bullet", text[:80])

                if key not in seen:
                    seen.add(key)

                    issues.append(Issue(
                        "Missing Bullet Marker",
                        "error",
                        line,
                        "List item bullet marker appears to be removed or hidden.",
                        snippet=str(li)[:300],
                        expected=EXPECTED_BULLET_MARKER,
                        actual="missing / hidden bullet",
                    ))

    return issues
    

def check_ul_direct_paragraphs(soup: BeautifulSoup):
    """Catch bullet/list text placed directly inside <ul> instead of inside <li>."""
    issues = []
    seen = set()

    for ul in soup.find_all("ul"):
        for child in ul.find_all("p", recursive=False):
            text = child.get_text(" ", strip=True)
            if not text:
                continue
            line = getattr(child, "sourceline", None)
            key = (line, text[:120])
            if key in seen:
                continue
            seen.add(key)
            issues.append(Issue(
                "Missing List Item Tag",
                "error",
                line,
                "List text appears directly inside <ul>; it should be wrapped in <li data-list-text=\"•\">.",
                snippet=str(child)[:300],
                expected='<li data-list-text="•"><p>...</p></li>',
                actual='<ul><p>...</p></ul>',
            ))

    return issues

# ── Orchestrator ─────────────────────────────────────────────────────────────

def run_checks(pdf_path: str, html_path: str, progress_cb=None):
    """
    Returns:
      {
        "language": str,
        "issues": list[Issue]
      }
    """
    def prog(pct, label):
        if progress_cb:
            progress_cb(pct, label)

    prog(5, "Extracting PDF text and parsing HTML…")

    soup = load_html(html_path)
    pdf_text = extract_pdf_text(pdf_path)
    html_imgs = extract_html_images(soup, html_path)

    try:
        src_imgs = extract_pdf_images(pdf_path)
    except Exception:
        src_imgs = []

    language = detect_language(pdf_text)

    issues = []

    prog(35, "Checking title and HTML tag structure…")
    issues += check_filenames(pdf_path, html_path)
    issues += check_title(pdf_path, soup)
    issues += check_raw_html_tags(html_path)

    # One source of truth for list, bullet, and style rules
    issues += check_tag_attributes_and_styles(soup)

    issues += check_required_b_tags_by_company_spec(soup)
    issues += check_missing_b_tags_strict(soup)

    prog(45, "Running strict PDF-to-HTML text mapping…")
    issues += check_strict_text_mapping(pdf_path, soup)

    prog(72, "Checking images…")
    issues += check_images(src_imgs, html_imgs)
    
    IGNORE_ISSUE_CATEGORIES = {
    "Image Display Size Mismatch",
    "Image Aspect Ratio Mismatch",
    "Image File Aspect Ratio Mismatch",
    }

    issues = [
    issue for issue in issues
    if issue.category not in IGNORE_ISSUE_CATEGORIES
    ]

    prog(90, "Checking encoding, placeholders, and links…")
    issues += check_garbled(soup)
    issues += check_placeholders(soup)
    issues += check_links(soup, html_path)

    prog(100, "Done.")

    return {
        "language": language,
        "issues": issues,
    }
   
def parse_inline_style(style: str) -> dict:
    """
    Converts:
      'padding-left: 23pt;text-align: right;'
    into:
      {'padding-left': '23pt', 'text-align': 'right'}
    """
    result = {}

    for part in (style or "").split(";"):
        if ":" not in part:
            continue

        key, value = part.split(":", 1)
        result[key.strip().lower()] = value.strip().lower()

    return result


def get_css_value(tag, prop: str) -> str:
    if not tag:
        return ""

    style = parse_inline_style(tag.get("style", ""))
    return style.get(prop.lower(), "")