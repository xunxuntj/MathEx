from pathlib import Path
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "REILAY_REPORT_DRAFT.md"
OUT = ROOT / "output" / "pdf" / "Reilay-避障游戏-研究方案与研究结果-三问阶段版.pdf"
OUT.parent.mkdir(parents=True, exist_ok=True)


pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
styles = getSampleStyleSheet()
body = ParagraphStyle(
    "CNBody",
    fontName="STSong-Light",
    fontSize=10.2,
    leading=16,
    textColor=colors.HexColor("#243247"),
    spaceAfter=6,
)
h1 = ParagraphStyle(
    "CNH1",
    parent=body,
    fontSize=17,
    leading=23,
    textColor=colors.HexColor("#123A63"),
    spaceBefore=12,
    spaceAfter=8,
    keepWithNext=True,
)
h2 = ParagraphStyle(
    "CNH2",
    parent=body,
    fontSize=13.5,
    leading=19,
    textColor=colors.HexColor("#176B87"),
    spaceBefore=10,
    spaceAfter=6,
    keepWithNext=True,
)
h3 = ParagraphStyle(
    "CNH3",
    parent=body,
    fontSize=11.5,
    leading=17,
    textColor=colors.HexColor("#9A5B13"),
    spaceBefore=7,
    spaceAfter=4,
    keepWithNext=True,
)
title = ParagraphStyle(
    "CNTitle",
    parent=body,
    fontSize=23,
    leading=31,
    alignment=TA_CENTER,
    textColor=colors.HexColor("#123A63"),
    spaceAfter=12,
)
subtitle = ParagraphStyle(
    "CNSub",
    parent=body,
    fontSize=13.5,
    leading=21,
    alignment=TA_CENTER,
    textColor=colors.HexColor("#52677F"),
    spaceAfter=16,
)
note = ParagraphStyle(
    "CNNote",
    parent=body,
    fontSize=9.2,
    leading=14,
    leftIndent=8,
    rightIndent=8,
    backColor=colors.HexColor("#EEF5F8"),
    borderPadding=7,
    spaceAfter=8,
)
bullet = ParagraphStyle("CNBullet", parent=body, leftIndent=15, firstLineIndent=-8, spaceAfter=3)
code = ParagraphStyle(
    "CNCode",
    parent=body,
    fontName="Courier",
    fontSize=8.2,
    leading=11,
    textColor=colors.HexColor("#2F3A45"),
    backColor=colors.HexColor("#F2F5F7"),
    leftIndent=6,
    rightIndent=6,
    borderPadding=4,
    spaceAfter=4,
)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def inline(s):
    s = esc(s)
    s = re.sub(r"`([^`]+)`", r'<font name="Courier" color="#34495E">\1</font>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
    return s


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("STSong-Light", 8.5)
    canvas.setFillColor(colors.HexColor("#6A7685"))
    canvas.drawString(20 * mm, 12 * mm, "第五届上海市中学数学学术展评活动｜长期题一｜Reilay 三问阶段版")
    canvas.drawRightString(190 * mm, 12 * mm, f"第 {doc.page} 页")
    canvas.restoreState()


def add_table(story, rows):
    data = [[Paragraph(inline(c), body) for c in row] for row in rows]
    if not data:
        return
    n = len(data[0])
    widths = [(170 * mm) / n] * n
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "STSong-Light"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.2),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DDECF2")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#123A63")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#AFC2CE")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.extend([table, Spacer(1, 3 * mm)])


def main():
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    story = []
    in_code = False
    code_lines = []
    first_h1 = True
    i = 0

    while i < len(lines):
        raw = lines[i]
        line = raw.strip()

        if line.startswith("```"):
            if in_code:
                if code_lines:
                    story.append(Paragraph(esc("<br/>".join(code_lines)), code))
                code_lines = []
                in_code = False
            else:
                in_code = True
            i += 1
            continue

        if in_code:
            code_lines.append(raw)
            i += 1
            continue

        if not line:
            story.append(Spacer(1, 2.2 * mm))
            i += 1
            continue

        if line.startswith("| "):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", c or "-") for c in cells):
                    rows.append(cells)
                i += 1
            add_table(story, rows)
            continue

        if line.startswith("# "):
            text = line[2:]
            if first_h1:
                story.extend(
                    [
                        Spacer(1, 16 * mm),
                        Paragraph(inline(text), title),
                        Paragraph("研究方案与研究结果（三问阶段版）", subtitle),
                        Spacer(1, 8 * mm),
                        Paragraph("参赛学校：上海市娄山中学", subtitle),
                        Paragraph("队伍名称：娄山最优解", subtitle),
                        Spacer(1, 4 * mm),
                        Paragraph("说明：本版整合 Reilay 采样搜索、算法优化过程与第三问旋转障碍物数值候选。", note),
                        PageBreak(),
                    ]
                )
                first_h1 = False
            else:
                story.append(Paragraph(inline(text), h1))
        elif line.startswith("## "):
            story.append(Paragraph(inline(line[3:]), h2))
        elif line.startswith("### "):
            story.append(Paragraph(inline(line[4:]), h3))
        elif line.startswith("> "):
            story.append(Paragraph(inline(line[2:]), note))
        elif re.match(r"^[-*] ", line):
            story.append(Paragraph("• " + inline(line[2:]), bullet))
        elif re.match(r"^\d+\. ", line):
            story.append(Paragraph(inline(line), bullet))
        else:
            story.append(Paragraph(inline(line), body))
        i += 1

    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=20 * mm,
        title="Reilay 避障游戏研究方案与研究结果",
        author="参赛团队",
    )
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(OUT)


if __name__ == "__main__":
    main()
