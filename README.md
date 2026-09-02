<div align="center">

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
</p>

</div>

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

<table>
<tr>
<td width="25%" align="center">

Input

PDF + HTML

</td>
<td width="25%" align="center">

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

</td>
</tr>
</table>

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
