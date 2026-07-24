"""Audit submission reports for editorial residue and render every PDF page."""
from pathlib import Path
import sys
from datetime import datetime

import pypdfium2 as pdfium
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
REPORTS = [
    ROOT / "题一-避障游戏备赛包/output/pdf/长期题一-避障游戏-研究方案与研究结果.pdf",
    ROOT / "题二-备赛包/06-研究方案与研究结果.pdf",
]
if len(sys.argv) > 1:
    REPORTS[0] = Path(sys.argv[1]).resolve()
SOURCES = [
    ROOT / "题一-避障游戏备赛包/12-题一研究方案与研究结果初稿.md",
    ROOT / "题二-备赛包/06-研究方案与研究结果.md",
]
BANNED = (
    "送审",
    "最终版本",
    "最终送审版",
    "送审口径",
    "内部提示",
    "tools/",
    ".mjs",
    ".json",
    ".py",
    "工作区根目录",
    "老师提供的 7 页参考资料",
)
REQUIRED = {
    REPORTS[0]: ("1 <= M(2) <= 9", "M(n) <= 24n", "47张转向卡", "53张加速卡", "174.5136米", "0.014577777米"),
    REPORTS[1]: ("F=K_{1,4}", "E(n,1)=7", "57", "78–84", "E_c(n,1)=n", "计算复核说明"),
}
EXHIBIT = ROOT / "双题交互展示/index.html"
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
        for term in REQUIRED.get(report, ()):
            if term not in text:
                failures.append(f"{report.relative_to(ROOT)}: 缺少关键结论 {term}")
        document = pdfium.PdfDocument(report)
        target = RENDER_DIR / report.stem
        target.mkdir()
        for number, page in enumerate(document, 1):
            page.render(scale=1.6).to_pil().save(target / f"page-{number:02d}.png")
        print(f"RENDERED {report.name}: {len(document)} pages")

    exhibit = EXHIBIT.read_text(encoding="utf-8")
    failures += check_text(str(EXHIBIT.relative_to(ROOT)), exhibit)
    for term in ("M(n)≤24n", "47张转向卡", "53张加速卡", "174.5136米", "E(n,1)=7", "57–84"):
        if term not in exhibit:
            failures.append(f"{EXHIBIT.relative_to(ROOT)}: 缺少关键结论 {term}")

    if failures:
        raise SystemExit("EDITORIAL_RESIDUE\n" + "\n".join(failures))
    print("EDITORIAL_AUDIT_OK")


if __name__ == "__main__":
    main()
