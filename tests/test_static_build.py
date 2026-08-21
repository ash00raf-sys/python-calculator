import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / ".artifacts" / "calm-calculator-static.zip"


def test_static_app_archive_is_upload_ready():
    subprocess.run(
        [sys.executable, "scripts/build_static.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    with ZipFile(ARCHIVE) as archive:
        assert set(archive.namelist()) == {
            "index.html",
            "calculator.css",
            "calculator.js",
        }
        index = archive.read("index.html").decode()
        javascript = archive.read("calculator.js").decode()

    assert "{{" not in index
    assert 'href="./calculator.css"' in index
    assert 'src="./calculator.js"' in index
    assert 'fetch("/api/calculate"' not in javascript
    assert "calculateLocally" in javascript
