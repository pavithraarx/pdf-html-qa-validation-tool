<div align="center">

<<<<<<< Updated upstream
<h1>PDF to HTML QA Validation Tool</h1>

<p><strong>Automated QA validation for converted HTML documents against original PDF sources.</strong></p>

<p>
  <img src="https://img.shields.io/badge/Python-3.x-3776AB?style=flat-square&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/Flask-Web%20App-000000?style=flat-square&logo=flask&logoColor=white">
  <img src="https://img.shields.io/badge/QA-Rule--Based-6C5CE7?style=flat-square">
  <img src="https://img.shields.io/badge/Reports-Excel-217346?style=flat-square&logo=microsoft-excel&logoColor=white">
  <img src="https://img.shields.io/badge/Database-SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white">
</p>

<p>
  Token-Level Comparison &nbsp;•&nbsp;
  HTML Structure Validation &nbsp;•&nbsp;
  Image Checks &nbsp;•&nbsp;
  Severity-Based Reporting
=======
PDF to HTML QA Validation Tool

Automated QA validation for converted HTML documents against original PDF sources.

<p>
  <img src="https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Flask-Web%20Application-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask">
  <img src="https://img.shields.io/badge/QA-Rule--Based-6C5CE7?style=for-the-badge" alt="Rule Based QA">
  <img src="https://img.shields.io/badge/Reports-Excel-217346?style=for-the-badge&logo=microsoft-excel&logoColor=white" alt="Excel">
  <img src="https://img.shields.io/badge/Storage-SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite">
</p>

<p>
  <strong>Token-level comparison</strong> ·
  <strong>HTML structure validation</strong> ·
  <strong>Image checks</strong> ·
  <strong>Severity-based Excel reporting</strong>
>>>>>>> Stashed changes
</p>

</div>

<<<<<<< Updated upstream
<hr>

<h2>Overview</h2>

<h2>Demo</h2>

<p>
  A short demonstration of the PDF-to-HTML QA validation workflow.
</p>

<p>
  <a href="./demo/demo-video.mp4">
    <strong>View Demo Video</strong>
  </a>
</p>

<p>
The <strong>PDF to HTML QA Validation Tool</strong> is a Flask-based web application
that validates converted HTML documents against their original PDF sources.
It detects conversion discrepancies and produces structured Excel reports for QA review.
</p>

<table>
<tr>
<th>Area</th>
<th>Purpose</th>
</tr>
<tr>
<td><strong>Text</strong></td>
<td>Compare PDF and HTML content at token level</td>
</tr>
<tr>
<td><strong>Structure</strong></td>
<td>Validate HTML document structure and elements</td>
</tr>
<tr>
<td><strong>Images</strong></td>
<td>Check image presence and relevant differences</td>
</tr>
<tr>
<td><strong>Severity</strong></td>
<td>Classify detected issues by impact</td>
</tr>
<tr>
<td><strong>Reporting</strong></td>
<td>Generate Excel-based QA reports</td>
</tr>
<tr>
<td><strong>Audit</strong></td>
<td>Maintain run and issue history</td>
</tr>
</table>

<hr>

<h2>Key Features</h2>
=======
1. Overview

The PDF to HTML QA Validation Tool is a Flask-based web application for validating HTML documents produced from PDF conversion workflows.

It compares the converted HTML against the original PDF and identifies discrepancies that may affect document accuracy, structure, or visual fidelity.

The tool is designed for:

document conversion QA

automated regression testing

batch validation

structured issue reporting

internal enterprise workflows

repeatable PDF-to-HTML quality checks

The application provides a browser-based interface for uploading source files, running validation, reviewing results, and downloading generated reports.

2. What This Tool Checks

Validation Area

What Is Checked

Text

Token-level differences between PDF-derived source text and HTML content

Structure

HTML elements, headings, paragraphs, lists, tables, and structural consistency

Images

Presence and relevant image characteristics where applicable

Formatting

Conversion-related text and markup discrepancies

Severity

Issues classified according to their impact

Reports

Machine-readable Excel output for QA review

Audit History

Run and issue information stored for traceability

The validation engine is rule-based, deterministic, and intended to produce repeatable results for the same inputs.

3. At a Glance
>>>>>>> Stashed changes

<table>
<tr>
<td width="25%" align="center">

<<<<<<< Updated upstream
<h3>Text Validation</h3>

<ul>
<li>Token-level comparison</li>
<li>Missing and extra text detection</li>
<li>Changed or reordered content detection</li>
<li>Spacing and punctuation checks</li>
<li>Conversion-noise handling</li>
</ul>
=======
Input

PDF + HTML
>>>>>>> Stashed changes

</td>
<td width="25%" align="center">

<<<<<<< Updated upstream
<h3>HTML Validation</h3>

<ul>
<li>Heading validation</li>
<li>Paragraph validation</li>
<li>List validation</li>
<li>Table validation</li>
<li>Link and image checks</li>
</ul>

</td>
</tr>
<tr>
<td>

<h3>Image Validation</h3>

<ul>
<li>Image presence checks</li>
<li>Image discrepancy detection</li>
<li>Conversion-related image validation</li>
</ul>

</td>
<td>

<h3>Reporting</h3>

<ul>
<li>Excel QA reports</li>
<li>Issue categorization</li>
<li>Severity classification</li>
<li>File and run-level results</li>
</ul>
=======
Engine

Rule-Based QA

</td>
<td width="25%" align="center">

Output

Excel Reports

</td>
<td width="25%" align="center">

Storage

SQLite
>>>>>>> Stashed changes

</td>
</tr>
</table>

<<<<<<< Updated upstream
<hr>

<h2>Workflow</h2>

<pre>
PDF + Converted HTML
        |
        v
   QA Engine
        |
   +----+----+----+
   |         |    |
 Text    Structure Images
   |         |    |
   +----+----+----+
        |
        v
 Issue Detection
        |
        v
Severity Classification
        |
        v
   Excel Report
        |
        v
    QA Review
</pre>

<hr>

<h2>QA Methodology</h2>

<h3>Token-Level Text Comparison</h3>

<p>
The engine compares document content at token level to identify localized conversion
differences instead of relying only on whole-document equality.
</p>

<table>
<tr>
<th>Issue</th>
<th>Example</th>
</tr>
<tr>
<td>Missing Token</td>
<td>Source text is absent from HTML</td>
</tr>
<tr>
<td>Extra Token</td>
<td>HTML contains unexpected content</td>
</tr>
<tr>
<td>Changed Token</td>
<td>Converted text differs from source</td>
</tr>
<tr>
<td>Reordered Content</td>
<td>Content appears in an unexpected order</td>
</tr>
<tr>
<td>Formatting Noise</td>
<td>Conversion introduces non-content differences</td>
</tr>
</table>

<h3>HTML Structure Validation</h3>

<table>
<tr>
<th>Element</th>
<th>Validation</th>
</tr>
<tr><td>Headings</td><td>Presence and hierarchy</td></tr>
<tr><td>Paragraphs</td><td>Content and structure</td></tr>
<tr><td>Lists</td><td>Representation and ordering</td></tr>
<tr><td>Tables</td><td>Structure and content</td></tr>
<tr><td>Links</td><td>Link-related structure</td></tr>
<tr><td>Images</td><td>Presence and relevant properties</td></tr>
</table>

<h3>Image Validation</h3>

<p>
Image checks help identify missing, unexpected, or incorrectly converted images.
</p>

<hr>

<h2>Severity Model</h2>

<table>
<tr>
<th>Severity</th>
<th>Meaning</th>
</tr>
<tr><td><strong>Critical</strong></td><td>Major document integrity failure</td></tr>
<tr><td><strong>High</strong></td><td>Significant conversion defect</td></tr>
<tr><td><strong>Medium</strong></td><td>Meaningful discrepancy requiring review</td></tr>
<tr><td><strong>Low</strong></td><td>Minor discrepancy</td></tr>
<tr><td><strong>Info</strong></td><td>Informational validation result</td></tr>
</table>

<hr>

<h2>Excel Reports</h2>

<p>
Validation results are exported into Excel for filtering, review, and sharing.
</p>

<table>
<tr>
<th>Report Information</th>
<th>Use</th>
</tr>
<tr><td>File</td><td>Identify affected documents</td></tr>
<tr><td>Issue</td><td>Describe the detected discrepancy</td></tr>
<tr><td>Category</td><td>Identify the validation type</td></tr>
<tr><td>Severity</td><td>Prioritize investigation</td></tr>
<tr><td>Location</td><td>Help identify where the issue occurred</td></tr>
</table>

<hr>

<h2>Technology Stack</h2>

<table>
<tr>
<th>Technology</th>
<th>Purpose</th>
</tr>
<tr><td>Python</td><td>Application and QA engine</td></tr>
<tr><td>Flask</td><td>Web application</td></tr>
<tr><td>pdfplumber</td><td>PDF processing</td></tr>
<tr><td>BeautifulSoup / lxml</td><td>HTML parsing</td></tr>
<tr><td>Pillow / imagehash / NumPy</td><td>Image processing</td></tr>
<tr><td>openpyxl</td><td>Excel report generation</td></tr>
<tr><td>SQLite</td><td>Application data storage</td></tr>
<tr><td>HTML / CSS / JavaScript</td><td>Frontend</td></tr>
</table>

<hr>

<h2>Project Structure</h2>

<pre>
PDF-to-HTML-QA-Validation-Tool/
│
├── README.md
├── LICENSE
├── .gitignore
├── requirements.txt
│
├── server.py
├── database.py
├── qa_engine.py
├── report.py
│
├── run.bat
├── run.sh
│
└── static/
    └── index.html
</pre>

<hr>

<h2>Installation</h2>

<h3>Prerequisites</h3>

<table>
<tr><th>Requirement</th><th>Version</th></tr>
<tr><td>Python</td><td>3.x</td></tr>
<tr><td>pip</td><td>Latest recommended</td></tr>
<tr><td>Git</td><td>Required for repository setup</td></tr>
</table>

<h3>Clone</h3>

<pre><code>git clone &lt;repository-url&gt;
cd PDF-to-HTML-QA-Validation-Tool</code></pre>

<h3>Create Virtual Environment</h3>

<p><strong>Windows:</strong></p>

<pre><code>python -m venv venv
venv\Scripts\activate</code></pre>

<p><strong>Linux / macOS:</strong></p>

<pre><code>python3 -m venv venv
source venv/bin/activate</code></pre>

<h3>Install Dependencies</h3>

<pre><code>pip install -r requirements.txt</code></pre>

<hr>

<h2>Configuration</h2>

<p>
Create a local <code>admin_config.json</code> file for administrator configuration.
This file is intentionally excluded from Git.
</p>

<pre><code>{
  "username": "admin",
  "password": "CHANGE_THIS_PASSWORD",
  "display_name": "System Admin",
  "email": "admin@example.com"
}</code></pre>

<table>
<tr><th>Field</th><th>Description</th></tr>
<tr><td><code>username</code></td><td>Administrator login username</td></tr>
<tr><td><code>password</code></td><td>Administrator password</td></tr>
<tr><td><code>display_name</code></td><td>Administrator display name</td></tr>
<tr><td><code>email</code></td><td>Administrator email address</td></tr>
</table>

<p><strong>Security:</strong> Never commit real credentials, API keys, tokens, or production configuration.</p>

<p>
The SQLite database is created automatically by the application.
There is no need to manually create <code>qa_tool.db</code>.
</p>

<hr>

<h2>Running the Application</h2>

<h3>Windows</h3>

<pre><code>run.bat</code></pre>

<h3>Linux / macOS</h3>

<pre><code>chmod +x run.sh
./run.sh</code></pre>

<h3>Directly with Python</h3>

<pre><code>python server.py</code></pre>

<p>
After startup, open the local URL displayed by Flask in your browser.
</p>

<hr>

<h2>Validation Process</h2>

<table>
<tr><th>Step</th><th>Action</th></tr>
<tr><td>1</td><td>Sign in</td></tr>
<tr><td>2</td><td>Upload the required PDF/HTML input package</td></tr>
<tr><td>3</td><td>Start a validation run</td></tr>
<tr><td>4</td><td>Wait for processing to complete</td></tr>
<tr><td>5</td><td>Review detected issues</td></tr>
<tr><td>6</td><td>Review severity and categories</td></tr>
<tr><td>7</td><td>Review the Excel report</td></tr>
<tr><td>8</td><td>Download the required output</td></tr>
</table>

<p>
Each upload creates a new validation run rather than silently reusing an earlier result.
</p>

<hr>

<h2>Database</h2>

<table>
<tr><th>Table</th><th>Purpose</th></tr>
<tr><td><code>users</code></td><td>Application users</td></tr>
<tr><td><code>invites</code></td><td>User invitations</td></tr>
<tr><td><code>password_resets</code></td><td>Password reset workflows</td></tr>
<tr><td><code>runs</code></td><td>Validation runs</td></tr>
<tr><td><code>file_pairs</code></td><td>PDF/HTML pair information</td></tr>
<tr><td><code>issues</code></td><td>Detected QA issues</td></tr>
<tr><td><code>audit_logs</code></td><td>Audit information</td></tr>
</table>

<hr>

<h2>API</h2>

<table>
<tr><th>Endpoint</th><th>Purpose</th></tr>
<tr><td><code>/</code></td><td>Main application interface</td></tr>
<tr><td><code>/upload</code></td><td>Upload / initiate validation</td></tr>
<tr><td><code>/run</code></td><td>Validation processing</td></tr>
<tr><td><code>/status/&lt;job_id&gt;</code></td><td>Processing status</td></tr>
<tr><td><code>/download/&lt;job_id&gt;</code></td><td>Download generated output</td></tr>
<tr><td><code>/download-batch/&lt;batch_id&gt;</code></td><td>Download batch output</td></tr>
</table>

<p><em>For external integrations, verify the current route implementation in <code>server.py</code>.</em></p>

<hr>

<h2>Runtime Files</h2>

<table>
<tr><th>File / Directory</th><th>Purpose</th></tr>
<tr><td><code>qa_tool.db</code></td><td>SQLite database</td></tr>
<tr><td><code>batch_runs/</code></td><td>Validation run data</td></tr>
<tr><td><code>uploads/</code></td><td>Uploaded files where applicable</td></tr>
<tr><td><code>reports/</code></td><td>Generated reports where applicable</td></tr>
<tr><td><code>audits/</code></td><td>Audit-related runtime data</td></tr>
<tr><td><code>temp/</code></td><td>Temporary files</td></tr>
<tr><td><code>cache/</code></td><td>Cached runtime data</td></tr>
<tr><td><code>admin_config.json</code></td><td>Local administrator configuration</td></tr>
</table>

<p>
These files are excluded from version control through <code>.gitignore</code>.
</p>

<hr>

<h2>Security</h2>

<table>
<tr><th>Area</th><th>Recommendation</th></tr>
<tr><td>Credentials</td><td>Never commit passwords or secrets</td></tr>
<tr><td>Documents</td><td>Do not commit confidential PDF/HTML files</td></tr>
<tr><td>HTTPS</td><td>Use HTTPS in shared or production environments</td></tr>
<tr><td>Access</td><td>Restrict access to authorized users</td></tr>
<tr><td>Storage</td><td>Protect uploaded files and generated reports</td></tr>
<tr><td>Deployment</td><td>Use a production WSGI server rather than Flask development server</td></tr>
</table>

<p>
The default session inactivity timeout is <strong>30 minutes</strong>.
</p>

<hr>

<h2>Licensing</h2>

<p>
The project's licensing terms are defined in the <code>LICENSE</code> file.
Third-party libraries remain subject to their respective licenses and terms.
</p>

<table>
<tr><th>Dependency</th><th>Purpose</th></tr>
<tr><td>Flask</td><td>Web framework</td></tr>
<tr><td>pdfplumber</td><td>PDF processing</td></tr>
<tr><td>BeautifulSoup</td><td>HTML parsing</td></tr>
<tr><td>lxml</td><td>HTML/XML processing</td></tr>
<tr><td>Pillow</td><td>Image processing</td></tr>
<tr><td>NumPy</td><td>Numerical operations</td></tr>
<tr><td>openpyxl</td><td>Excel generation</td></tr>
<tr><td>imagehash</td><td>Image comparison</td></tr>
<tr><td>regex</td><td>Text processing</td></tr>
<tr><td>striprtf</td><td>RTF processing</td></tr>
<tr><td>python-docx</td><td>Word document processing</td></tr>
</table>

<p>
Before commercial or external distribution, review the exact dependency versions,
their licenses, and the organization's open-source compliance requirements.
</p>

<hr>

<h2>Limitations</h2>

<table>
<tr><th>Limitation</th><th>Description</th></tr>
<tr><td>Complex PDFs</td><td>Unusual layouts may require additional rules</td></tr>
<tr><td>Reading Order</td><td>Complex structures can affect text comparison</td></tr>
<tr><td>Tables</td><td>Highly complex tables may need specialized comparison</td></tr>
<tr><td>Visual Fidelity</td><td>Exact visual equivalence may require rendering-based comparison</td></tr>
<tr><td>False Positives</td><td>Some conversion differences may be legitimate</td></tr>
<tr><td>Domain Rules</td><td>Specialized documents may require additional validation rules</td></tr>
</table>

<hr>

<h2>Future Enhancements</h2>

<table>
<tr><th>Area</th><th>Planned Direction</th></tr>
<tr><td>Visual QA</td><td>Advanced rendering-based visual comparison</td></tr>
<tr><td>OCR</td><td>OCR-assisted validation</td></tr>
<tr><td>Tables</td><td>Advanced table comparison</td></tr>
<tr><td>Rules</td><td>Configurable validation rules</td></tr>
<tr><td>Reports</td><td>Configurable report templates</td></tr>
<tr><td>API</td><td>Complete API documentation</td></tr>
<tr><td>Deployment</td><td>Containerized production deployment</td></tr>
<tr><td>Analytics</td><td>QA dashboards and metrics</td></tr>
</table>

<hr>

<h2>Contact</h2>

<table>
<tr><th>Contact</th><th>Details</th></tr>
<tr><td><strong>Name</strong></td><td>Pavithra Reddy T</td></tr>
<tr><td><strong>Email</strong></td><td><a href="mailto:pavithraa2007@gmail.com">pavithraa2007@gmail.com</a></td></tr>
<tr><td><strong>Contact Number</strong></td><td>7204105657</td></tr>
</table>

<hr>

<div align="center">
<sub>PDF to HTML QA Validation Tool · Rule-based document validation for reliable PDF-to-HTML conversion QA</sub>
</div>
=======
4. System Workflow

                    ┌──────────────────────┐
                    │     Source PDF       │
                    └──────────┬───────────┘
                               │
                               │
                    ┌──────────▼───────────┐
                    │   Converted HTML      │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │     QA Engine        │
                    │                      │
                    │  Text Validation     │
                    │  Structure Checks    │
                    │  Image Checks        │
                    │  Rule Evaluation     │
                    └──────────┬───────────┘
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
          ┌──────────┐   ┌───────────┐   ┌───────────┐
          │ Issues   │   │ Severity  │   │ Audit Data│
          └────┬─────┘   └─────┬─────┘   └─────┬─────┘
               │               │               │
               └───────────────┼───────────────┘
                               ▼
                    ┌──────────────────────┐
                    │   Excel QA Report    │
                    └──────────────────────┘

5. Core QA Methodology

5.1 Token-Level Text Comparison

The text validation layer compares document content at a token level rather than relying only on whole-document string equality.

This makes it possible to detect localized conversion errors such as:

missing words

extra words

altered text

reordered content

spacing differences

punctuation discrepancies

conversion artifacts

The engine also contains normalization and noise-handling rules so that formatting artifacts do not automatically become false-positive QA issues.

5.2 HTML Structure Validation

The HTML validation layer examines the converted document structure and checks whether expected document elements are represented appropriately.

Typical validation targets include:

headings

paragraphs

lists

tables

links

images

document hierarchy

structural mismatches

5.3 Image Validation

Image-related validation checks the presence and relevant characteristics of images in the converted HTML.

This helps identify conversion failures where document images are:

missing

unexpectedly altered

incorrectly represented

inconsistent with the source document

6. Severity Model

Detected issues are categorized by severity so that QA teams can prioritize investigation.

Severity

Meaning

Typical Handling

Critical

Major document integrity failure

Immediate investigation

High

Significant conversion problem

Prioritize for correction

Medium

Meaningful discrepancy

Review during QA

Low

Minor or non-critical issue

Review if required

Info

Informational validation result

No immediate action required

Severity classification is intended to separate meaningful conversion defects from lower-impact differences.

7. Excel Report Design

Validation results are exported into Excel-oriented reports for practical QA review.

Reports are designed to make it easy to:

identify affected files

filter issues by severity

inspect issue descriptions

review validation categories

track issue locations

share results with QA or engineering teams

retain validation output for audit purposes

The report format is suitable for both manual review and downstream processing.

8. Application Architecture

Browser
   │
   ▼
Flask Application
   │
   ├── Authentication / Sessions
   │
   ├── Upload & Run Management
   │
   ├── QA Engine
   │      ├── Text comparison
   │      ├── Structure validation
   │      └── Image validation
   │
   ├── Report Generator
   │      └── Excel output
   │
   └── SQLite Database
          ├── Users
          ├── Runs
          ├── File Pairs
          ├── Issues
          ├── Invites
          └── Audit Logs

9. Tech Stack

Component

Technology

Backend

Python

Web Framework

Flask

PDF Processing

pdfplumber

HTML Parsing

BeautifulSoup / lxml

Document Processing

python-docx, striprtf

Image Processing

Pillow, imagehash, NumPy

Spreadsheet Reporting

openpyxl

Database

SQLite

Frontend

HTML / CSS / JavaScript

Authentication

Flask session-based authentication

10. Project Structure

PDF-to-HTML-QA-Validation-Tool/
│
├── README.md
├── LICENSE
├── .gitignore
├── requirements.txt
│
├── server.py
├── database.py
├── qa_engine.py
├── report.py
│
├── run.bat
├── run.sh
│
└── static/
    └── index.html

Runtime-generated files

The application may create runtime data during execution. These files and directories are intentionally excluded from version control.

Examples include:

qa_tool.db
qa_tool.db-wal
qa_tool.db-shm
batch_runs/
uploads/
reports/
audits/
temp/
cache/
admin_config.json

The exact runtime directories depend on the workflow and application configuration.

11. Installation

Prerequisites

Install:

Python 3.x

pip

Git

Verify the installation:

python --version
pip --version
git --version

Clone the Repository

git clone <repository-url>
cd PDF-to-HTML-QA-Validation-Tool

Create a Virtual Environment

Windows

python -m venv venv
venv\Scripts\activate

Linux / macOS

python3 -m venv venv
source venv/bin/activate

Install Dependencies

pip install -r requirements.txt

12. Configuration

The application supports a local admin_config.json file for initial administrator configuration.

Example:

{
  "username": "admin",
  "password": "CHANGE_THIS_PASSWORD",
  "display_name": "System Admin",
  "email": "admin@example.com"
}

Important

admin_config.json is intentionally excluded from Git.

Do not commit real administrator credentials to the repository.

For company deployment:

Clone the repository.

Create admin_config.json locally.

Set the required administrator credentials.

Start the application.

Verify administrator login.

Keep the configuration file outside source-control workflows.

The application initializes its SQLite database automatically when required. There is no need to manually create qa_tool.db.

13. Authentication and Access

The application includes authentication and role-aware access control.

The database maintains information for:

users

invitations

password reset workflows

runs

validation issues

audit logs

Sessions use an inactivity timeout. The current application default is 30 minutes of idle session time.

For production deployment, authentication should be used together with:

HTTPS

secure secret management

restricted network access

appropriate reverse-proxy configuration

controlled administrator access

14. Running the Application

Windows

The repository includes:

run.bat

Run:

run.bat

Linux / macOS

The repository includes:

run.sh

Run:

chmod +x run.sh
./run.sh

Direct Python Execution

The application can also be started directly with Python:

python server.py

Once the server starts, open the local application URL shown by Flask in your browser.

15. Validation Workflow

A typical validation cycle is:

Sign in to the application.

Upload the required PDF/HTML input package.

Start a validation run.

Wait for the QA engine to process the documents.

Review detected issues.

Inspect issue severity and category.

Review the generated report.

Download the report for QA or engineering review.

Use run/audit information for traceability.

Each upload is treated as a new validation run rather than silently reusing an earlier result.

16. Input Pairing

The validation workflow requires the tool to determine which HTML document corresponds to which source PDF.

The pairing process is important because an incorrect PDF/HTML pair can produce misleading QA results.

For batch workflows:

keep source PDFs organized

keep converted HTML files organized

use consistent file naming where possible

avoid mixing unrelated documents in the same input package

17. Database and Runtime Data

The application uses SQLite for local application data.

The database contains tables supporting:

users
invites
password_resets
runs
file_pairs
issues
audit_logs

Runtime databases are not intended to be committed to Git.

The repository .gitignore excludes SQLite database files and generated runtime artifacts to prevent accidental publication of:

user accounts

authentication data

validation history

audit information

generated reports

temporary files

18. Git and Repository Hygiene

The repository is configured to keep local runtime data out of source control.

The .gitignore covers common categories such as:

Python cache files
Virtual environments
Environment files
SQLite databases
Runtime directories
Generated reports
Logs
IDE files
Local administrator configuration

Before pushing changes, verify:

git status

To inspect the tracked repository contents:

git ls-tree -r --name-only HEAD

Never use Git to store:

real passwords

API keys

tokens

private certificates

production databases

customer documents

confidential reports

19. API Endpoints

The application exposes HTTP endpoints for its web workflow.

Core routes include functionality for:

Route

Purpose

/

Main application interface

/upload

Upload/start a validation workflow

/run

Execute or manage validation processing

/status/<job_id>

Retrieve processing status

/download/<job_id>

Download generated output

/download-batch/<batch_id>

Download batch output

The exact request and response behavior should be treated as an implementation detail of the current server.py.

For integrations, review the route implementations before building external clients against the API.

20. Company Deployment

For internal company use, a typical deployment flow is:

Company Machine / Server
        │
        ├── Python Environment
        │
        ├── Application Repository
        │
        ├── Local Configuration
        │
        └── SQLite / Runtime Storage
                 │
                 ▼
              Flask App
                 │
                 ▼
          Internal Users

Recommended production considerations

The included Flask development server is appropriate for local development and controlled testing.

For production deployment, use a proper WSGI deployment architecture and place the application behind an appropriate web server or reverse proxy.

Recommended controls include:

HTTPS

firewall/network restrictions

secure configuration management

regular backups where required

controlled file upload limits

log management

access monitoring

separation of development and production environments

21. Security Considerations

This project processes potentially sensitive documents. Deployment teams should treat uploaded PDFs, HTML files, generated reports, and validation history as potentially confidential.

Recommended practices:

never commit credentials

never commit customer documents

use HTTPS in shared environments

restrict application access to authorized users

protect runtime storage

rotate administrative credentials

back up production data according to company policy

avoid exposing the development server directly to the public internet

The repository's .gitignore is a source-control safeguard; it is not a replacement for production access controls or secure storage.

22. Library and Third-Party License Policy

This project uses third-party Python packages.

Examples include:

Flask

pdfplumber

BeautifulSoup

lxml

Pillow

NumPy

openpyxl

imagehash

regex

striprtf

python-docx

Each dependency has its own license and usage conditions.

Before distributing the application commercially or externally:

Review the license of every dependency in the exact version used.

Retain required copyright and license notices.

Check company open-source compliance requirements.

Maintain a dependency inventory.

Review newly added dependencies before adoption.

Project License

The project license is defined by the LICENSE file in the repository.

If this project is being distributed under the MIT License, the repository should contain the corresponding MIT license text and the README should be kept consistent with that choice.

If a different license is selected by the project owner or company, update this section and LICENSE together.

23. Limitations

The tool is designed as a rule-based QA system and therefore has practical limitations.

Conversion-dependent behavior

Validation quality depends on the quality of the PDF-to-HTML conversion being tested.

Complex layouts

Highly complex PDFs may contain:

unusual reading orders

layered content

non-standard tables

embedded objects

complex typography

positioning-dependent layouts

These cases may require additional rules.

Image equivalence

Image validation can identify relevant discrepancies, but exact visual equivalence may require more advanced rendering-based comparison.

False positives

Minor conversion differences can sometimes be legitimate. QA results should therefore be reviewed according to the project's acceptance criteria.

Domain-specific rules

Different document types may require additional rules or severity policies.

24. Future Enhancements

Potential future improvements include:

richer visual diffing

OCR-assisted validation

configurable validation rules

custom severity policies

improved table comparison

layout-aware comparison

configurable report templates

REST API documentation

background job processing

production-grade database support

containerized deployment

CI/CD integration

automated regression test suites

metrics and QA dashboards

25. Development

For development:

git clone <repository-url>
cd PDF-to-HTML-QA-Validation-Tool

python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
python server.py

When modifying the validation engine:

Add or update the relevant rule.

Test against representative PDF/HTML pairs.

Check for false positives.

Verify severity classification.

Verify Excel report output.

Confirm runtime files remain excluded from Git.

Review git status before committing.

26. Troubleshooting

Application starts but login does not work

Check the local administrator configuration and ensure the application has initialized its database.

Do not copy production credentials into source control.

Previous runs are missing

Runtime databases and batch-run directories are intentionally excluded from Git. A clean checkout is not expected to contain previous local validation history.

Generated files appear in Git status

Check .gitignore and verify that the files are not already tracked:

git status
git ls-files

If a file was previously tracked, adding it to .gitignore alone does not remove it from Git history. It must be removed from tracking separately.

Dependency errors

Recreate the virtual environment and install from:

pip install -r requirements.txt

Port already in use

Stop the process using the configured Flask port or change the local development configuration.

27. Summary

The PDF to HTML QA Validation Tool provides a structured way to validate converted HTML documents against their original PDF sources.

Its core workflow combines:

PDF + HTML
    ↓
Automated QA Rules
    ↓
Text / Structure / Image Validation
    ↓
Severity Classification
    ↓
Excel Reporting
    ↓
Audit and Run History

The project is intended to provide a repeatable foundation for document-conversion quality assurance while remaining simple to run locally and straightforward to integrate into larger internal workflows.

28. Contact

For questions, issues, or queries regarding this project, please contact:

<table>
<tr>
<td><strong>Name</strong></td>
<td>Pavithra Reddy T</td>
</tr>
<tr>
<td><strong>Email</strong></td>
<td><a href="mailto:pavithraa2007@gmail.com">pavithraa2007@gmail.com</a></td>
</tr>
<tr>
<td><strong>Contact</strong></td>
<td>7204105657</td>
</tr>
</table>

<div align="center">

PDF to HTML QA Validation Tool

<sub>Rule-based document validation for reliable PDF-to-HTML conversion QA.</sub>

</div>
>>>>>>> Stashed changes
