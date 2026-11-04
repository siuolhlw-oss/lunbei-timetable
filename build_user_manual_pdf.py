#!/usr/bin/env python3
"""Build a PDF user manual from the project's Markdown tutorial."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


IMAGE_RE = re.compile(r"!\[(?P<alt>[^\]]*)\]\((?P<path>[^)]+)\)")
INLINE_CODE_RE = re.compile(r"`([^`]+)`")
PAGE_WIDTH, PAGE_HEIGHT = A4
FONT_NAME = "MSung-Light"
EMBEDDED_FONT_CANDIDATES = (
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/NISC18030.ttf",
    "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build PDF user manual from Markdown.")
    parser.add_argument("--project-root", default=".", help="Project root directory.")
    parser.add_argument("--source", default="user-manual.md", help="Markdown source path.")
    parser.add_argument("--output", default="崙背國中課表使用說明.pdf", help="PDF output path.")
    return parser.parse_args()


def register_fonts() -> str:
    for path in EMBEDDED_FONT_CANDIDATES:
        font_path = Path(path)
        if not font_path.exists():
            continue
        try:
            pdfmetrics.registerFont(TTFont("ManualSans", str(font_path)))
            return "ManualSans"
        except Exception:
            continue

    for name in ("MSung-Light", "STSong-Light"):
        try:
            pdfmetrics.registerFont(UnicodeCIDFont(name))
            return name
        except Exception:
            continue
    return "Helvetica"


def make_styles(font_name: str) -> dict[str, ParagraphStyle]:
    return {
        "title": ParagraphStyle(
            "ManualTitle",
            fontName=font_name,
            fontSize=24,
            leading=31,
            textColor=colors.HexColor("#1F4E79"),
            alignment=TA_CENTER,
            spaceAfter=6,
            wordWrap="CJK",
        ),
        "subtitle": ParagraphStyle(
            "ManualSubtitle",
            fontName=font_name,
            fontSize=13,
            leading=18,
            textColor=colors.HexColor("#475569"),
            alignment=TA_CENTER,
            spaceAfter=10,
            wordWrap="CJK",
        ),
        "cover_note": ParagraphStyle(
            "ManualCoverNote",
            fontName=font_name,
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#64748B"),
            alignment=TA_CENTER,
            wordWrap="CJK",
        ),
        "h1": ParagraphStyle(
            "ManualHeading1",
            fontName=font_name,
            fontSize=18,
            leading=24,
            textColor=colors.HexColor("#1F4E79"),
            spaceBefore=14,
            spaceAfter=8,
            wordWrap="CJK",
        ),
        "h2": ParagraphStyle(
            "ManualHeading2",
            fontName=font_name,
            fontSize=15,
            leading=20,
            textColor=colors.HexColor("#2B579A"),
            spaceBefore=12,
            spaceAfter=6,
            wordWrap="CJK",
        ),
        "body": ParagraphStyle(
            "ManualBody",
            fontName=font_name,
            fontSize=11,
            leading=16,
            textColor=colors.HexColor("#111827"),
            spaceAfter=6,
            wordWrap="CJK",
        ),
        "bullet": ParagraphStyle(
            "ManualBullet",
            fontName=font_name,
            fontSize=11,
            leading=16,
            textColor=colors.HexColor("#111827"),
            leftIndent=16,
            bulletIndent=4,
            spaceAfter=5,
            wordWrap="CJK",
        ),
        "button_heading": ParagraphStyle(
            "ManualButtonHeading",
            fontName=font_name,
            fontSize=11,
            leading=16,
            textColor=colors.HexColor("#1F4E79"),
            spaceBefore=4,
            spaceAfter=5,
            wordWrap="CJK",
        ),
        "caption": ParagraphStyle(
            "ManualCaption",
            fontName=font_name,
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#64748B"),
            alignment=TA_CENTER,
            spaceAfter=10,
            wordWrap="CJK",
        ),
        "table": ParagraphStyle(
            "ManualTable",
            fontName=font_name,
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#111827"),
            wordWrap="CJK",
        ),
    }


def inline_markup(text: str) -> str:
    last = 0
    parts: list[str] = []
    for match in INLINE_CODE_RE.finditer(text):
        if match.start() > last:
            parts.append(escape(text[last:match.start()]))
        parts.append(
            '<font name="' + FONT_NAME + '" color="#313B49">'
            + escape(match.group(1))
            + "</font>"
        )
        last = match.end()
    if last < len(text):
        parts.append(escape(text[last:]))
    return "".join(parts)


def resolve_image(project_root: Path, source_dir: Path, image_path: str) -> Path | None:
    candidates = [(source_dir / image_path).resolve(), (project_root / image_path).resolve()]
    for path in candidates:
        if path.exists():
            return path
    return None


def add_cover(story: list, styles: dict[str, ParagraphStyle]) -> None:
    styles['title'].textColor = colors.black
    styles['title'].spaceAfter = 14
    story.append(Paragraph('崙背國中課表使用說明', styles['title']))


def add_image(
    story: list,
    styles: dict[str, ParagraphStyle],
    project_root: Path,
    source_dir: Path,
    image_path: str,
    alt: str,
) -> None:
    path = resolve_image(project_root, source_dir, image_path)
    if path is None:
        story.append(Paragraph("找不到截圖：" + escape(image_path), styles["body"]))
        return

    with PILImage.open(path) as img:
        width_px, height_px = img.size
    max_width = 5.85 * inch
    max_height = 7.05 * inch
    scale = min(max_width / width_px, max_height / height_px)
    width = width_px * scale
    height = height_px * scale

    flowables = [Image(str(path), width=width, height=height, hAlign="CENTER")]
    if alt:
        flowables.append(Paragraph(inline_markup(alt), styles["caption"]))
    story.append(KeepTogether(flowables))


def add_button_table(story: list, styles: dict[str, ParagraphStyle], bullets: list[str]) -> None:
    if not bullets:
        return

    data = [
        [Paragraph("按鈕", styles["table"]), Paragraph("功能", styles["table"])],
    ]
    for item in bullets:
        label, sep, desc = item.partition("：")
        data.append([
            Paragraph(inline_markup(label.replace("`", "").strip()), styles["table"]),
            Paragraph(inline_markup(desc.strip() if sep else item), styles["table"]),
        ])

    table = Table(data, colWidths=[1.45 * inch, 4.65 * inch], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF5")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.1 * inch))


def add_paragraph(story: list, styles: dict[str, ParagraphStyle], lines: list[str]) -> None:
    text = " ".join(line.strip() for line in lines if line.strip())
    if text:
        story.append(Paragraph(inline_markup(text), styles["body"]))


def add_bullets(story: list, styles: dict[str, ParagraphStyle], bullets: list[str], in_button_functions: bool) -> None:
    if not bullets:
        return
    if in_button_functions:
        add_button_table(story, styles, bullets)
        return
    for item in bullets:
        story.append(Paragraph(inline_markup(item), styles["bullet"], bulletText="-"))


def footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont(FONT_NAME, 9)
    canvas.setFillColor(colors.HexColor("#64748B"))
    canvas.drawString(doc.leftMargin, 0.42 * inch, "崙背國中課表使用說明")
    canvas.drawRightString(PAGE_WIDTH - doc.rightMargin, 0.42 * inch, str(doc.page))
    canvas.restoreState()


def build_pdf(project_root: Path, source: Path, output: Path) -> None:
    global FONT_NAME
    FONT_NAME = register_fonts()
    styles = make_styles(FONT_NAME)
    story: list = []
    add_cover(story, styles)

    lines = source.read_text(encoding="utf-8").splitlines()
    paragraph_lines: list[str] = []
    bullets: list[str] = []
    in_button_functions = False

    def flush_paragraph() -> None:
        nonlocal paragraph_lines
        add_paragraph(story, styles, paragraph_lines)
        paragraph_lines = []

    def flush_bullets() -> None:
        nonlocal bullets, in_button_functions
        if not bullets:
            return
        add_bullets(story, styles, bullets, in_button_functions)
        bullets = []
        in_button_functions = False

    for raw in lines:
        line = raw.rstrip()
        if not line:
            flush_paragraph()
            flush_bullets()
            continue

        image = IMAGE_RE.match(line.strip())
        if image:
            flush_paragraph()
            flush_bullets()
            add_image(story, styles, project_root, source.parent, image.group("path"), image.group("alt"))
            continue

        if line.startswith("# "):
            flush_paragraph()
            flush_bullets()
            continue

        if line.startswith("## "):
            flush_paragraph()
            flush_bullets()
            story.append(Paragraph(inline_markup(line[3:].strip()), styles["h1"]))
            continue

        if line.startswith("### "):
            flush_paragraph()
            flush_bullets()
            story.append(Paragraph(inline_markup(line[4:].strip()), styles["h2"]))
            continue

        if line.strip() == "按鈕功能：":
            flush_paragraph()
            flush_bullets()
            story.append(Paragraph("按鈕功能", styles["button_heading"]))
            in_button_functions = True
            continue

        if line.startswith("- "):
            flush_paragraph()
            bullets.append(line[2:].strip())
            continue

        paragraph_lines.append(line)

    flush_paragraph()
    flush_bullets()

    output.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        topMargin=0.65 * inch,
        bottomMargin=0.60 * inch,
        leftMargin=0.82 * inch,
        rightMargin=0.82 * inch,
        title="崙背國中課表使用說明",
        author="崙背國中課表",
    )
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


def main() -> None:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    source = (project_root / args.source).resolve()
    output = (project_root / args.output).resolve()
    build_pdf(project_root, source, output)
    print(output)


if __name__ == "__main__":
    main()
