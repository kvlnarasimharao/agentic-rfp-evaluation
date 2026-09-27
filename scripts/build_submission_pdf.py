"""Export the detailed Word submission as a matching PDF on Windows."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
docx = ROOT / "docs" / "Agentic_RFP_Evaluation_Submission.docx"
pdf = ROOT / "docs" / "Agentic_RFP_Evaluation_Submission.pdf"

if sys.platform != "win32":
    raise SystemExit("PDF export requires Microsoft Word on Windows.")
subprocess.run([sys.executable, str(ROOT / "scripts" / "build_submission.py")], check=True)
source_path = str(docx).replace("'", "''")
target_path = str(pdf).replace("'", "''")
script = (
    "$ErrorActionPreference = 'Stop'; "
    "$word = New-Object -ComObject Word.Application; "
    "$word.Visible = $false; "
    "try { "
    f"$document = $word.Documents.Open('{source_path}', $false, $true); "
    f"$document.ExportAsFixedFormat('{target_path}', 17); "
    "$document.Close($false); "
    "} finally { $word.Quit() }"
)
subprocess.run(["powershell.exe", "-NoProfile", "-Command", script], check=True)
print(pdf)
