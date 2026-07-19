# PDF to HTML QA Validation Tool

A Flask-based rule-driven QA tool that validates converted HTML documents against their original PDF files and generates structured Excel reports.

## Overview

This project checks whether a converted HTML file correctly matches its original PDF source. It detects text mismatches, punctuation issues, missing headings, missing bold tags, image problems, title mismatches, and structural conversion errors.

The system is designed to reduce manual QA effort and provide clear Excel reports for reviewers.

## Features

- PDF ZIP and HTML ZIP upload
- Automatic PDF and HTML file pairing
- Token-level text comparison
- Missing, extra, and changed text detection
- Punctuation and capitalization mismatch detection
- Heading and bold tag validation
- Image validation
- Severity classification
- Excel report generation

## Tech Stack

| Area | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python Flask |
| PDF Extraction | pdfplumber |
| HTML Parsing | BeautifulSoup |
| Tokenization | Python re |
| Text Comparison | difflib.SequenceMatcher |
| Image Processing | Pillow, NumPy, ImageHash |
| Reports | openpyxl |

## How It Works

1. User uploads a PDF ZIP and an HTML ZIP.
2. Flask backend extracts PDFs, HTML files, and images.
3. PDF and HTML files are paired by filename.
4. PDF text is extracted using pdfplumber.
5. HTML text and tags are parsed using BeautifulSoup.
6. Text is tokenized into words, numbers, punctuation, and hyphenated terms.
7. PDF tokens and HTML tokens are compared using difflib.SequenceMatcher.
8. Errors are classified as Critical, Major, or Minor.
9. Excel reports are generated using openpyxl.

## Excel Report

The batch Excel report contains three sheets:

| Sheet | Purpose |
|---|---|
| Overall Summary | Shows total files, passed files, failed files, and severity counts |
| File Based Summary | Shows one row per file with status and error counts |
| Individual File Errors | Shows detailed errors grouped by file |

## API Endpoints

| Endpoint | Purpose |
|---|---|
| / | Serves the frontend |
| /upload | Uploads and prepares PDF/HTML pairs |
| /run | Starts QA validation |
| /status/<job_id> | Shows live progress |
| /download/<job_id> | Downloads individual report |
| /download-batch/<batch_id> | Downloads batch report |

## Running the Project

Install dependencies:

pip install -r requirements.txt

Run the server:

python server.py

Open:

http://127.0.0.1:5000

## Project Structure

| File / Folder | Purpose |
|---|---|
| server.py | Flask backend and API routes |
| qa_engine.py | Core validation engine |
| report.py | Excel report generation |
| static/index.html | Frontend interface |
| reports/ | Generated per-file reports |
| audits/ | Generated batch reports |
| requirements.txt | Python dependencies |

## Summary

This tool provides an automated and explainable way to validate HTML files converted from PDFs. It compares content token by token, checks HTML structure and images, classifies issues by severity, and generates readable Excel reports.