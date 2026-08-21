"""Build a ZIP that can be uploaded directly to static.app."""

from __future__ import annotations

import shutil
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "src" / "python_calculator"
OUTPUT_ROOT = ROOT / ".artifacts"
SITE_DIR = OUTPUT_ROOT / "calm-calculator"
ZIP_PATH = OUTPUT_ROOT / "calm-calculator-static.zip"


def build() -> Path:
    """Create the static site directory and upload-ready archive."""
    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)
    SITE_DIR.mkdir(parents=True)

    template = (PACKAGE / "templates" / "index.html").read_text(encoding="utf-8")
    template = template.replace(
        "{{ url_for('static', filename='calculator.css') }}",
        "./calculator.css",
    ).replace(
        "{{ url_for('static', filename='calculator.js') }}",
        "./calculator.js",
    )
    (SITE_DIR / "index.html").write_text(template, encoding="utf-8")

    for filename in ("calculator.css", "calculator.js"):
        shutil.copy2(PACKAGE / "static" / filename, SITE_DIR / filename)

    OUTPUT_ROOT.mkdir(exist_ok=True)
    with ZipFile(ZIP_PATH, "w", compression=ZIP_DEFLATED) as archive:
        for path in sorted(SITE_DIR.iterdir()):
            archive.write(path, path.name)

    return ZIP_PATH


if __name__ == "__main__":
    archive = build()
    print(f"Built {archive.relative_to(ROOT)}")
