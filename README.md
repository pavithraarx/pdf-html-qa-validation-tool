<div align="center">

# PDF to HTML QA Validation Tool

### Automated QA validation for converted HTML documents against original PDF sources

<p>
  <img src="https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Backend-Flask-111827?style=for-the-badge&logo=flask&logoColor=white" alt="Flask">
  <img src="https://img.shields.io/badge/Reports-Excel-217346?style=for-the-badge&logo=microsoftexcel&logoColor=white" alt="Excel">
  <img src="https://img.shields.io/badge/Validation-Rule--Based-7C3AED?style=for-the-badge" alt="Rule Based">
</p>

<p>
  <b>Token-level comparison · HTML structure validation · Image checks · Severity-based Excel reporting</b>
</p>

</div>

---

## Overview

The PDF to HTML QA Validation Tool is a Flask-based web application built to verify whether converted HTML files accurately preserve the content and structure of their original PDF documents.

PDF-to-HTML conversion can introduce small but serious issues such as changed words, missing text, broken images, incorrect titles, lost heading tags, missing bold labels, bullet/list mismatches, and formatting inconsistencies.

This project automates that review process by comparing each PDF and HTML pair, detecting conversion issues, classifying them by severity, and generating readable Excel reports.

---

## What This Tool Checks

<table>
<tr>
<td width="50%">

### Content Accuracy

- Changed text
- Missing text
- Extra text
- Punctuation mismatch
- Capitalization mismatch
- Title mismatch

</td>
<td width="50%">

### HTML Quality

- Missing heading tags
- Missing bold or strong tags
- List and bullet issues
- Broken image references
- Missing images
- Style and structure mismatches

</td>
</tr>
</table>

---

## At a Glance

<table>
<tr>
<th>Input</th>
<th>Processing</th>
<th>Output</th>
</tr>
<tr>
<td>PDF ZIP</td>
<td>PDF text extraction</td>
<td>Overall Summary</td>
</tr>
<tr>
<td>HTML ZIP</td>
<td>HTML parsing</td>
<td>File Based Summary</td>
</tr>
<tr>
<td>HTML image assets</td>
<td>Token and structure comparison</td>
<td>Individual File Errors</td>
</tr>
</table>

---

## System Workflow

<table>
<tr>
<td align="center"><b>01</b><br>Upload Files</td>
<td align="center">➡️</td>
<td align="center"><b>02</b><br>Extract Content</td>
<td align="center">➡️</td>
<td align="center"><b>03</b><br>Pair Files</td>
</tr>
<tr>
<td align="center"><b>04</b><br>Run QA Engine</td>
<td align="center">➡️</td>
<td align="center"><b>05</b><br>Classify Errors</td>
<td align="center">➡️</td>
<td align="center"><b>06</b><br>Generate Excel Report</td>
</tr>
</table>

---

## Tech Stack

<table>
<tr>
<th>Layer</th>
<th>Tool / Library</th>
<th>Role</th>
</tr>
<tr>
<td>Frontend</td>
<td>HTML, CSS, JavaScript</td>
<td>Upload UI, dashboard, progress tracking, report actions</td>
</tr>
<tr>
<td>Backend</td>
<td>Python Flask</td>
<td>API routes, file handling, QA job management, downloads</td>
</tr>
<tr>
<td>PDF Extraction</td>
<td>pdfplumber</td>
<td>Extract PDF text, words, layout information, and images</td>
</tr>
<tr>
<td>HTML Parsing</td>
<td>BeautifulSoup</td>
<td>Read visible HTML text and inspect tags</td>
</tr>
<tr>
<td>Tokenization</td>
<td>Python re</td>
<td>Split text into words, numbers, punctuation, and hyphenated terms</td>
</tr>
<tr>
<td>Text Matching</td>
<td>difflib.SequenceMatcher</td>
<td>Align and compare PDF tokens with HTML tokens</td>
</tr>
<tr>
<td>Image Validation</td>
<td>Pillow, NumPy, ImageHash</td>
<td>Check image existence and visual similarity</td>
</tr>
<tr>
<td>Excel Reporting</td>
<td>openpyxl</td>
<td>Create structured Excel reports</td>
</tr>
</table>

---

## Core Logic

### Token-Level Text Comparison

Token-level comparison is the main validation method used in this project.

Instead of comparing full paragraphs directly, the system breaks PDF and HTML text into smaller units called tokens. A token can be a word, number, punctuation mark, or hyphenated word.

Once both files are tokenized, the PDF token list is compared with the HTML token list. This helps detect exactly where a word was changed, removed, added, or punctuated differently.

<table>
<tr>
<th>PDF Text</th>
<th>HTML Text</th>
<th>Detected Issue</th>
</tr>
<tr>
<td>The doctor may insert <b>small</b> tubes.</td>
<td>The doctor may insert <b>large</b> tubes.</td>
<td>Changed Text</td>
</tr>
</table>

<table>
<tr>
<th>PDF Token</th>
<th>HTML Token</th>
<th>Result</th>
</tr>
<tr>
<td>The</td>
<td>The</td>
<td>Match</td>
</tr>
<tr>
<td>doctor</td>
<td>doctor</td>
<td>Match</td>
</tr>
<tr>
<td>small</td>
<td>large</td>
<td>Changed Text</td>
</tr>
<tr>
<td>tubes</td>
<td>tubes</td>
<td>Match</td>
</tr>
</table>

This helps catch small but important content changes that may affect meaning.

---

## Severity Model

<table>
<tr>
<th>Severity</th>
<th>Meaning</th>
<th>Examples</th>
</tr>
<tr>
<td><b>Critical</b></td>
<td>Content or correctness issue that can affect meaning or usability</td>
<td>Changed text, missing text, broken image, title mismatch</td>
</tr>
<tr>
<td><b>Major</b></td>
<td>Structure or conversion quality issue</td>
<td>Missing heading tag, missing bold tag, list mismatch</td>
</tr>
<tr>
<td><b>Minor</b></td>
<td>Low-risk formatting or cosmetic issue</td>
<td>Small style inconsistency</td>
</tr>
<tr>
<td><b>Passed</b></td>
<td>No issue found</td>
<td>PDF and HTML match successfully</td>
</tr>
</table>

---

## Excel Report Design

The generated batch report is organized into three readable sheets.

<table>
<tr>
<th>Sheet</th>
<th>Purpose</th>
</tr>
<tr>
<td><b>Overall Summary</b></td>
<td>Batch-level totals, passed/failed files, severity counts, category breakdown, and color key</td>
</tr>
<tr>
<td><b>File Based Summary</b></td>
<td>One row per PDF-HTML pair with status, file severity, error counts, language, and details link</td>
</tr>
<tr>
<td><b>Individual File Errors</b></td>
<td>Detailed file-wise errors with expected value, actual value, description, and context</td>
</tr>
</table>

---

## API Endpoints

<table>
<tr>
<th>Endpoint</th>
<th>Method</th>
<th>Description</th>
</tr>
<tr>
<td>/</td>
<td>GET</td>
<td>Serves the frontend interface</td>
</tr>
<tr>
<td>/upload</td>
<td>POST</td>
<td>Uploads PDF and HTML ZIP files and prepares file pairs</td>
</tr>
<tr>
<td>/run</td>
<td>POST</td>
<td>Starts QA validation for one file pair</td>
</tr>
<tr>
<td>/status/&lt;job_id&gt;</td>
<td>GET</td>
<td>Returns live progress and validation result</td>
</tr>
<tr>
<td>/download/&lt;job_id&gt;</td>
<td>GET</td>
<td>Downloads an individual file report</td>
</tr>
<tr>
<td>/download-batch/&lt;batch_id&gt;</td>
<td>GET</td>
<td>Downloads the full batch Excel report</td>
</tr>
</table>

---

## Project Structure

<table>
<tr>
<th>Path</th>
<th>Description</th>
</tr>
<tr>
<td>server.py</td>
<td>Flask backend, API routes, file upload, job handling, and batch report generation</td>
</tr>
<tr>
<td>qa_engine.py</td>
<td>Core validation engine for text, tags, images, and severity classification</td>
</tr>
<tr>
<td>report.py</td>
<td>Individual file Excel report generation</td>
</tr>
<tr>
<td>static/index.html</td>
<td>Frontend dashboard</td>
</tr>
<tr>
<td>reports/</td>
<td>Generated per-file reports</td>
</tr>
<tr>
<td>audits/</td>
<td>Generated batch reports and audit outputs</td>
</tr>
<tr>
<td>requirements.txt</td>
<td>Python dependency list</td>
</tr>
</table>

---

## Installation

<table>
<tr>
<th>Step</th>
<th>Command</th>
</tr>
<tr>
<td>Clone repository</td>
<td>git clone https://github.com/pavithraarx/pdf-html-qa-validation-tool.git</td>
</tr>
<tr>
<td>Open folder</td>
<td>cd pdf-html-qa-validation-tool</td>
</tr>
<tr>
<td>Create virtual environment</td>
<td>python -m venv venv</td>
</tr>
<tr>
<td>Activate environment on Windows</td>
<td>venv\Scripts\activate</td>
</tr>
<tr>
<td>Install dependencies</td>
<td>pip install -r requirements.txt</td>
</tr>
<tr>
<td>Run application</td>
<td>python server.py</td>
</tr>
</table>

Open the application in your browser at:

<p align="center">
<b>http://127.0.0.1:5000</b>
</p>

---

## Usage

<table>
<tr>
<th>Step</th>
<th>Action</th>
</tr>
<tr>
<td>1</td>
<td>Upload the PDF ZIP file</td>
</tr>
<tr>
<td>2</td>
<td>Upload the HTML ZIP file</td>
</tr>
<tr>
<td>3</td>
<td>Prepare PDF and HTML file pairs</td>
</tr>
<tr>
<td>4</td>
<td>Run QA validation</td>
</tr>
<tr>
<td>5</td>
<td>View results in the browser dashboard</td>
</tr>
<tr>
<td>6</td>
<td>Download the Excel report</td>
</tr>
</table>

---

## Library and License Policy

This project uses open-source Python libraries with permissive licenses such as MIT, BSD, and PSF-style licenses.

<table>
<tr>
<th>Library</th>
<th>Purpose</th>
</tr>
<tr>
<td>Flask</td>
<td>Backend web framework</td>
</tr>
<tr>
<td>pdfplumber</td>
<td>PDF text and layout extraction</td>
</tr>
<tr>
<td>BeautifulSoup</td>
<td>HTML parsing</td>
</tr>
<tr>
<td>Pillow</td>
<td>Image processing</td>
</tr>
<tr>
<td>NumPy</td>
<td>Image and numeric processing</td>
</tr>
<tr>
<td>ImageHash</td>
<td>Perceptual image comparison</td>
</tr>
<tr>
<td>openpyxl</td>
<td>Excel report generation</td>
</tr>
</table>

---

## Limitations

- The system is rule-based and does not use semantic AI understanding.
- PDF extraction quality depends on the structure and encoding of the source PDF.
- Very complex layouts may require additional validation rules.
- Some visual formatting issues may still need manual review.
- Heavily transformed images may not always match perfectly.
- Highly inconsistent filenames may require manual pairing review.

---

## Future Enhancements

<table>
<tr>
<td>User authentication</td>
<td>Database-backed QA history</td>
</tr>
<tr>
<td>Role-based review workflow</td>
<td>PDF preview with highlighted errors</td>
</tr>
<tr>
<td>Improved visual layout comparison</td>
<td>Better table validation</td>
</tr>
<tr>
<td>CI/CD QA automation</td>
<td>PDF summary export</td>
</tr>
</table>

---

## Summary

The PDF to HTML QA Validation Tool provides an automated, explainable, and structured way to validate converted HTML files against original PDFs.

It compares content token by token, validates HTML structure, checks images, classifies errors by severity, and generates clear Excel reports for reviewers.

<div align="center">

<b>Built to reduce manual QA effort and catch critical PDF-to-HTML conversion errors faster.</b>

</div>