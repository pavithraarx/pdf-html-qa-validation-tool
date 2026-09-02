<div align="center">

<h1>PDF to HTML QA Validation Tool</h1>

<p>
<strong>Automated QA validation for converted HTML documents against original PDF sources.</strong>
</p>

<p>
<img src="https://img.shields.io/badge/Python-3.x-3776AB?style=flat-square&logo=python&logoColor=white">
<img src="https://img.shields.io/badge/Flask-Web%20Application-000000?style=flat-square&logo=flask&logoColor=white">
<img src="https://img.shields.io/badge/QA-Rule--Based-6C5CE7?style=flat-square">
<img src="https://img.shields.io/badge/Reports-Excel-217346?style=flat-square&logo=microsoft-excel&logoColor=white">
<img src="https://img.shields.io/badge/Database-SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white">
</p>

<p>
Token-Level Comparison &nbsp;•&nbsp;
HTML Structure Validation &nbsp;•&nbsp;
Image Validation &nbsp;•&nbsp;
Severity-Based Reporting
</p>

</div>

<hr>

<h2>Overview</h2>

<p>
The <strong>PDF to HTML QA Validation Tool</strong> is a Flask-based web application
for validating HTML documents generated from PDF conversion workflows.
It automatically identifies discrepancies between the original PDF and the
converted HTML and produces structured QA reports for review.
</p>

<table>
<tr>
<th>Capability</th>
<th>Description</th>
</tr>
<tr>
<td><strong>Text Validation</strong></td>
<td>Compares document content at token level</td>
</tr>
<tr>
<td><strong>HTML Validation</strong></td>
<td>Checks converted document structure and elements</td>
</tr>
<tr>
<td><strong>Image Validation</strong></td>
<td>Checks image presence and relevant differences</td>
</tr>
<tr>
<td><strong>Issue Classification</strong></td>
<td>Groups detected discrepancies by severity</td>
</tr>
<tr>
<td><strong>Excel Reporting</strong></td>
<td>Generates structured reports for QA review</td>
</tr>
<tr>
<td><strong>Audit History</strong></td>
<td>Maintains validation and activity information</td>
</tr>
</table>

<hr>

<h2>Demo</h2>

<p>
See the complete PDF-to-HTML QA validation workflow in action.
</p>

<p>
<a href="./demo/qc_analysis_tool_demo.mp4">
<strong>View Demo Video</strong>
</a>
</p>

<hr>

<h2>Key Features</h2>

<table>
<tr>
<td width="50%">

<h3>Text Comparison</h3>

<ul>
<li>Token-level comparison</li>
<li>Missing text detection</li>
<li>Extra text detection</li>
<li>Changed content detection</li>
<li>Reordered content detection</li>
<li>Conversion-noise handling</li>
</ul>

</td>

<td width="50%">

<h3>HTML Validation</h3>

<ul>
<li>Heading validation</li>
<li>Paragraph validation</li>
<li>List validation</li>
<li>Table validation</li>
<li>Link validation</li>
<li>Image checks</li>
</ul>

</td>
</tr>

<tr>
<td>

<h3>Reporting</h3>

<ul>
<li>Excel QA reports</li>
<li>Issue categorization</li>
<li>Severity classification</li>
<li>File-level results</li>
<li>Run-level results</li>
</ul>

</td>

<td>

<h3>Application</h3>

<ul>
<li>Web-based interface</li>
<li>User authentication</li>
<li>Validation run history</li>
<li>Audit logging</li>
<li>Batch processing support</li>
</ul>

</td>
</tr>
</table>

<hr>

<h2>Validation Workflow</h2>

<pre>
        Source PDF
             |
             v
       Converted HTML
             |
             v
        +-----------+
        | QA Engine |
        +-----------+
             |
     +-------+-------+
     |       |       |
     v       v       v
   Text   HTML    Images
  Checks  Checks   Checks
     |       |       |
     +-------+-------+
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
The text validation engine compares source and converted content at token level.
This allows individual discrepancies to be identified without treating the
entire document as one large string.
</p>

<table>
<tr>
<th>Check</th>
<th>Purpose</th>
</tr>
<tr>
<td>Missing Tokens</td>
<td>Detect content present in the source but absent from HTML</td>
</tr>
<tr>
<td>Extra Tokens</td>
<td>Detect unexpected content introduced during conversion</td>
</tr>
<tr>
<td>Changed Tokens</td>
<td>Identify altered source content</td>
</tr>
<tr>
<td>Reordered Content</td>
<td>Identify unexpected changes in content order</td>
</tr>
<tr>
<td>Formatting Noise</td>
<td>Reduce false positives caused by conversion artifacts</td>
</tr>
</table>

<h3>HTML Structure Validation</h3>

<table>
<tr>
<th>Element</th>
<th>Validation</th>
</tr>
<tr>
<td>Headings</td>
<td>Presence and hierarchy</td>
</tr>
<tr>
<td>Paragraphs</td>
<td>Content and structure</td>
</tr>
<tr>
<td>Lists</td>
<td>Representation and ordering</td>
</tr>
<tr>
<td>Tables</td>
<td>Structure and content</td>
</tr>
<tr>
<td>Links</td>
<td>Link-related structure</td>
</tr>
<tr>
<td>Images</td>
<td>Presence and relevant properties</td>
</tr>
</table>

<hr>

<h2>Severity Model</h2>

<table>
<tr>
<th>Severity</th>
<th>Meaning</th>
<th>Priority</th>
</tr>
<tr>
<td><strong>Critical</strong></td>
<td>Major document integrity failure</td>
<td>Immediate</td>
</tr>
<tr>
<td><strong>High</strong></td>
<td>Significant conversion defect</td>
<td>High</td>
</tr>
<tr>
<td><strong>Medium</strong></td>
<td>Meaningful discrepancy</td>
<td>Review</td>
</tr>
<tr>
<td><strong>Low</strong></td>
<td>Minor discrepancy</td>
<td>Optional</td>
</tr>
<tr>
<td><strong>Info</strong></td>
<td>Informational result</td>
<td>Reference</td>
</tr>
</table>

<hr>

<h2>Excel Reporting</h2>

<p>
Validation results are exported into Excel to provide a structured format
for filtering, reviewing, and sharing QA findings.
</p>

<table>
<tr>
<th>Report Field</th>
<th>Purpose</th>
</tr>
<tr>
<td>File</td>
<td>Identify the affected document</td>
</tr>
<tr>
<td>Issue</td>
<td>Describe the detected discrepancy</td>
</tr>
<tr>
<td>Category</td>
<td>Identify the validation type</td>
</tr>
<tr>
<td>Severity</td>
<td>Prioritize investigation</td>
</tr>
<tr>
<td>Location</td>
<td>Identify where the issue occurred</td>
</tr>
</table>

<hr>

<h2>Technology Stack</h2>

<table>
<tr>
<th>Technology</th>
<th>Purpose</th>
</tr>
<tr><td>Python</td><td>Application and validation engine</td></tr>
<tr><td>Flask</td><td>Web application framework</td></tr>
<tr><td>pdfplumber</td><td>PDF processing</td></tr>
<tr><td>BeautifulSoup</td><td>HTML parsing</td></tr>
<tr><td>lxml</td><td>HTML/XML processing</td></tr>
<tr><td>Pillow</td><td>Image processing</td></tr>
<tr><td>imagehash</td><td>Image comparison</td></tr>
<tr><td>NumPy</td><td>Numerical operations</td></tr>
<tr><td>openpyxl</td><td>Excel report generation</td></tr>
<tr><td>SQLite</td><td>Application data storage</td></tr>
</table>

<hr>

<h2>Project Structure</h2>

<pre>
PDF-to-HTML-QA-Validation-Tool/
|
+-- README.md
+-- LICENSE
+-- .gitignore
+-- requirements.txt
|
+-- server.py
+-- database.py
+-- qa_engine.py
+-- report.py
|
+-- run.bat
+-- run.sh
|
+-- static/
    +-- index.html
|
+-- demo/
    +-- qc_analysis_tool_demo.mp4
</pre>

<hr>

<h2>Installation</h2>

<h3>Prerequisites</h3>

<table>
<tr>
<th>Requirement</th>
<th>Recommended</th>
</tr>
<tr>
<td>Python</td>
<td>Python 3.x</td>
</tr>
<tr>
<td>pip</td>
<td>Latest available version</td>
</tr>
<tr>
<td>Git</td>
<td>Required for repository setup</td>
</tr>
<tr>
<td>Browser</td>
<td>Modern web browser</td>
</tr>
</table>

<h3>1. Clone the Repository</h3>

<pre><code>git clone &lt;repository-url&gt;
cd PDF-to-HTML-QA-Validation-Tool</code></pre>

<h3>2. Create a Virtual Environment</h3>

<p><strong>Windows</strong></p>

<pre><code>python -m venv venv
venv\Scripts\activate</code></pre>

<p><strong>Linux / macOS</strong></p>

<pre><code>python3 -m venv venv
source venv/bin/activate</code></pre>

<h3>3. Install Dependencies</h3>

<pre><code>pip install -r requirements.txt</code></pre>

<hr>

<h2>Configuration</h2>

<p>
Create a local <code>admin_config.json</code> file for administrator configuration.
This file is excluded from Git and should remain local to the deployment.
</p>

<pre><code>{
  "username": "admin",
  "password": "CHANGE_THIS_PASSWORD",
  "display_name": "System Admin",
  "email": "admin@example.com"
}</code></pre>

<table>
<tr>
<th>Field</th>
<th>Description</th>
</tr>
<tr>
<td><code>username</code></td>
<td>Administrator login username</td>
</tr>
<tr>
<td><code>password</code></td>
<td>Administrator password</td>
</tr>
<tr>
<td><code>display_name</code></td>
<td>Administrator display name</td>
</tr>
<tr>
<td><code>email</code></td>
<td>Administrator email address</td>
</tr>
</table>

<p>
<strong>Security:</strong> Never commit real passwords, API keys, tokens,
or other confidential configuration to the repository.
</p>

<p>
The SQLite database is created automatically by the application.
</p>

<hr>

<h2>Running the Application</h2>

<h3>Windows</h3>

<pre><code>run.bat</code></pre>

<h3>Linux / macOS</h3>

<pre><code>chmod +x run.sh
./run.sh</code></pre>

<h3>Direct Python Execution</h3>

<pre><code>python server.py</code></pre>

<p>
After startup, open the local URL displayed by Flask in your browser.
</p>

<hr>

<h2>Validation Process</h2>

<table>
<tr>
<th>Step</th>
<th>Action</th>
</tr>
<tr><td>1</td><td>Sign in to the application</td></tr>
<tr><td>2</td><td>Upload the required PDF/HTML input package</td></tr>
<tr><td>3</td><td>Start a validation run</td></tr>
<tr><td>4</td><td>Wait for processing to complete</td></tr>
<tr><td>5</td><td>Review detected issues</td></tr>
<tr><td>6</td><td>Review severity and categories</td></tr>
<tr><td>7</td><td>Review the Excel report</td></tr>
<tr><td>8</td><td>Download the required output</td></tr>
</table>

<hr>

<h2>Database</h2>

<table>
<tr>
<th>Table</th>
<th>Purpose</th>
</tr>
<tr><td><code>users</code></td><td>Application users</td></tr>
<tr><td><code>invites</code></td><td>User invitation records</td></tr>
<tr><td><code>password_resets</code></td><td>Password reset workflows</td></tr>
<tr><td><code>runs</code></td><td>Validation run records</td></tr>
<tr><td><code>file_pairs</code></td><td>PDF/HTML pair information</td></tr>
<tr><td><code>issues</code></td><td>Detected QA issues</td></tr>
<tr><td><code>audit_logs</code></td><td>Audit information</td></tr>
</table>

<p>
The database and generated runtime data are excluded from version control.
</p>

<hr>

<h2>API</h2>

<table>
<tr>
<th>Endpoint</th>
<th>Purpose</th>
</tr>
<tr><td><code>/</code></td><td>Main application interface</td></tr>
<tr><td><code>/upload</code></td><td>Upload / initiate validation</td></tr>
<tr><td><code>/run</code></td><td>Validation processing</td></tr>
<tr><td><code>/status/&lt;job_id&gt;</code></td><td>Processing status</td></tr>
<tr><td><code>/download/&lt;job_id&gt;</code></td><td>Download generated output</td></tr>
<tr><td><code>/download-batch/&lt;batch_id&gt;</code></td><td>Download batch output</td></tr>
</table>

<hr>

<h2>Runtime Files</h2>

<table>
<tr>
<th>File / Directory</th>
<th>Status</th>
</tr>
<tr><td><code>qa_tool.db</code></td><td>Ignored</td></tr>
<tr><td><code>qa_tool.db-wal</code></td><td>Ignored</td></tr>
<tr><td><code>qa_tool.db-shm</code></td><td>Ignored</td></tr>
<tr><td><code>batch_runs/</code></td><td>Ignored</td></tr>
<tr><td><code>uploads/</code></td><td>Ignored</td></tr>
<tr><td><code>reports/</code></td><td>Ignored</td></tr>
<tr><td><code>audits/</code></td><td>Ignored</td></tr>
<tr><td><code>temp/</code></td><td>Ignored</td></tr>
<tr><td><code>cache/</code></td><td>Ignored</td></tr>
<tr><td><code>admin_config.json</code></td><td>Ignored</td></tr>
</table>

<hr>

<h2>Security</h2>

<table>
<tr>
<th>Area</th>
<th>Recommendation</th>
</tr>
<tr><td>Credentials</td><td>Never commit passwords or secrets</td></tr>
<tr><td>Documents</td><td>Do not commit confidential PDF/HTML files</td></tr>
<tr><td>HTTPS</td><td>Use HTTPS for shared or production deployments</td></tr>
<tr><td>Access</td><td>Restrict access to authorized users</td></tr>
<tr><td>Storage</td><td>Protect uploaded files and generated reports</td></tr>
<tr><td>Deployment</td><td>Use a production WSGI server for production</td></tr>
</table>

<p>
The default session inactivity timeout is <strong>30 minutes</strong>.
</p>

<hr>

<h2>Third-Party Libraries and Licensing</h2>

<p>
This project uses open-source third-party libraries. Each dependency is
subject to its own license and terms.
</p>

<table>
<tr>
<th>Library</th>
<th>Purpose</th>
</tr>
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
The project's licensing terms are defined by the <code>LICENSE</code> file.
Before commercial or external distribution, review the licenses of the
exact dependency versions used and follow the organization's open-source
compliance requirements.
</p>

<hr>

<h2>Limitations</h2>

<table>
<tr>
<th>Limitation</th>
<th>Description</th>
</tr>
<tr>
<td>Complex PDFs</td>
<td>Unusual layouts may require additional validation rules</td>
</tr>
<tr>
<td>Reading Order</td>
<td>Complex structures can affect text comparison</td>
</tr>
<tr>
<td>Complex Tables</td>
<td>Specialized table comparison may be required</td>
</tr>
<tr>
<td>Visual Fidelity</td>
<td>Exact visual comparison may require rendering-based analysis</td>
</tr>
<tr>
<td>False Positives</td>
<td>Some conversion differences may be legitimate</td>
</tr>
</table>

<hr>

<h2>Future Enhancements</h2>

<table>
<tr>
<th>Area</th>
<th>Potential Enhancement</th>
</tr>
<tr><td>Visual QA</td><td>Advanced rendering-based visual comparison</td></tr>
<tr><td>OCR</td><td>OCR-assisted document validation</td></tr>
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
<tr>
<th>Contact</th>
<th>Details</th>
</tr>
<tr>
<td><strong>Name</strong></td>
<td>Pavithra Reddy T</td>
</tr>
<tr>
<td><strong>Email</strong></td>
<td><a href="mailto:pavithraa2007@gmail.com">pavithraa2007@gmail.com</a></td>
</tr>
<tr>
<td><strong>Contact Number</strong></td>
<td>7204105657</td>
</tr>
</table>

<hr>

<div align="center">

<sub>PDF to HTML QA Validation Tool</sub>

<br>

<sub>Rule-based document validation for reliable PDF-to-HTML conversion QA.</sub>

</div>
