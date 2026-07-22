"""Audit submission reports for editorial residue and render every PDF page."""
from pathlib import Path
import sys
from datetime import datetime

import pypdfium2 as pdfium
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
REPORTS = [
    ROOT / "题一-避障游戏备赛包/output/pdf/长期题一-避障游戏-研究方案与研究结果-最终版.pdf",
    ROOT / "题二-备赛包/06-研究方案与研究结果.pdf",
]
if len(sys.argv) > 1:
    REPORTS[0] = Path(sys.argv[1]).resolve()
SOURCES = [
    ROOT / "题一-避障游戏备赛包/12-题一研究方案与研究结果初稿.md",
    ROOT / "题二-备赛包/06-研究方案与研究结果.md",
]
BANNED = ("送审", "最终版本", "最终送审版", "送审口径", "内部提示")
RENDER_DIR = ROOT / "tmp/report-audit" / datetime.now().strftime("%Y%m%d-%H%M%S-%f")


def check_text(label: str, text: str) -> list[str]:
    return [f"{label}: {term}" for term in BANNED if term in text]


def main() -> None:
    failures = []
    for source in SOURCES:
        failures += check_text(str(source.relative_to(ROOT)), source.read_text(encoding="utf-8"))

    RENDER_DIR.mkdir(parents=True)

    for report in REPORTS:
        text = "\n".join(page.extract_text() or "" for page in PdfReader(report).pages)
        failures += check_text(str(report.relative_to(ROOT)), text)
        document = pdfium.PdfDocument(report)
        target = RENDER_DIR / report.stem
        target.mkdir()
        for number, page in enumerate(document, 1):
            page.render(scale=1.6).to_pil().save(target / f"page-{number:02d}.png")
        print(f"RENDERED {report.name}: {len(document)} pages")

    if failures:
        raise SystemExit("EDITORIAL_RESIDUE\n" + "\n".join(failures))
    print("EDITORIAL_AUDIT_OK")


if __name__ == "__main__":
    main()
