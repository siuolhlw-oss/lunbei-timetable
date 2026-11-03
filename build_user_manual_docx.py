#!/usr/bin/env python3
"""Build a Word user manual from the project's Markdown tutorial."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION_START
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


IMAGE_RE = re.compile(r"!\[(?P<alt>[^\]]*)\]\((?P<path>[^)]+)\)")
INLINE_CODE_RE = re.compile(r"`([^`]+)`")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build DOCX user manual from Markdown.")
    parser.add_argument("--project-root", default=".", help="Project root directory.")
    parser.add_argument("--source", default="user-manual.md", help="Markdown source path.")
    parser.add_argument("--output", default="崙背國中課表使用說明.docx", help="DOCX output path.")
    return parser.parse_args()


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_width(cell, width_inches: float) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_w = tc_pr.find(qn("w:tcW"))
    if tc_w is None:
        tc_w = OxmlElement("w:tcW")
        tc_pr.append(tc_w)
    tc_w.set(qn("w:w"), str(int(width_inches * 1440)))
    tc_w.set(qn("w:type"), "dxa")


def set_cell_margins(table, top=90, start=120, bottom=90, end=120) -> None:
    tbl_pr = table._tbl.tblPr
    tbl_cell_mar = tbl_pr.find(qn("w:tblCellMar"))
    if tbl_cell_mar is None:
        tbl_cell_mar = OxmlElement("w:tblCellMar")
        tbl_pr.append(tbl_cell_mar)
    for name, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tbl_cell_mar.find(qn(f"w:{name}"))
        if node is None:
            node = OxmlElement(f"w:{name}")
            tbl_cell_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def add_page_number(paragraph) -> None:
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = paragraph.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_end)


def add_inline_runs(paragraph, text: str, bold: bool = False) -> None:
    last = 0
    for match in INLINE_CODE_RE.finditer(text):
        if match.start() > last:
            paragraph.add_run(text[last:match.start()]).bold = bold
        run = paragraph.add_run(match.group(1))
        run.bold = True
        run.font.name = "Consolas"
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor(49, 59, 73)
        last = match.end()
    if last < len(text):
        paragraph.add_run(text[last:]).bold = bold


def setup_styles(doc: Document) -> None:
    section = doc.sections[0]
    section.top_margin = Inches(0.82)
    section.bottom_margin = Inches(0.72)
    section.left_margin = Inches(0.82)
    section.right_margin = Inches(0.82)

    normal = doc.styles["Normal"]
    normal.font.name = "Arial Unicode MS"
    normal.font.size = Pt(11)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.15

    for style_name, size, color, before, after in [
        ("Heading 1", 18, "1F4E79", 14, 8),
        ("Heading 2", 15, "2B579A", 12, 6),
        ("Heading 3", 12, "34495E", 10, 4),
    ]:
        style = doc.styles[style_name]
        style.font.name = "Arial Unicode MS"
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor.from_string(color)
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)

    footer = section.footer.paragraphs[0]
    footer.text = "崙背國中課表使用說明 | "
    footer.runs[0].font.size = Pt(9)
    footer.runs[0].font.color.rgb = RGBColor(100, 116, 139)
    add_page_number(footer)


def add_cover(doc: Document) -> None:
    title = doc.add_paragraph('崙背國中課表使用說明', style='Title')
    title.paragraph_format.space_after = Pt(12)
    for run in title.runs:
        run.font.name = 'Arial Unicode MS'
        run.font.size = Pt(22)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0, 0, 0)


def add_image(doc: Document, project_root: Path, source_dir: Path, image_path: str, alt: str) -> None:
    path = (source_dir / image_path).resolve()
    if not path.exists():
        path = (project_root / image_path).resolve()
    if not path.exists():
        paragraph = doc.add_paragraph(style="Intense Quote")
        paragraph.add_run(f"找不到截圖：{image_path}").bold = True
        return

    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    run.add_picture(str(path), width=Inches(5.85))

    if alt:
        caption = doc.add_paragraph()
        caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
        caption.paragraph_format.space_after = Pt(10)
        cap_run = caption.add_run(alt)
        cap_run.font.size = Pt(9)
        cap_run.font.color.rgb = RGBColor(100, 116, 139)


def add_button_table(doc: Document, bullets: list[str]) -> None:
    if not bullets:
        return
    table = doc.add_table(rows=1, cols=2)
    table.style = "Table Grid"
    set_cell_margins(table)
    hdr = table.rows[0].cells
    hdr[0].text = "按鈕"
    hdr[1].text = "功能"
    for cell in hdr:
        set_cell_shading(cell, "E8EEF5")
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.bold = True
    set_cell_width(hdr[0], 1.45)
    set_cell_width(hdr[1], 4.65)

    for item in bullets:
        label, sep, desc = item.partition("：")
        row = table.add_row().cells
        row[0].text = label.replace("`", "").strip()
        row[1].text = desc.strip() if sep else item
        set_cell_width(row[0], 1.45)
        set_cell_width(row[1], 4.65)
    doc.add_paragraph()


def flush_paragraph(doc: Document, lines: list[str]) -> None:
    if not lines:
        return
    paragraph = doc.add_paragraph()
    add_inline_runs(paragraph, " ".join(line.strip() for line in lines if line.strip()))


def build_docx(project_root: Path, source: Path, output: Path) -> None:
    doc = Document()
    setup_styles(doc)
    add_cover(doc)

    lines = source.read_text(encoding="utf-8").splitlines()
    paragraph_lines: list[str] = []
    bullets: list[str] = []
    in_button_functions = False

    def flush_bullets() -> None:
        nonlocal bullets, in_button_functions
        if not bullets:
            return
        if in_button_functions:
            add_button_table(doc, bullets)
        else:
            for item in bullets:
                paragraph = doc.add_paragraph(style="List Bullet")
                add_inline_runs(paragraph, item)
        bullets = []
        in_button_functions = False

    for raw in lines:
        line = raw.rstrip()
        if not line:
            flush_paragraph(doc, paragraph_lines)
            paragraph_lines = []
            flush_bullets()
            continue

        image = IMAGE_RE.match(line.strip())
        if image:
            flush_paragraph(doc, paragraph_lines)
            paragraph_lines = []
            flush_bullets()
            add_image(doc, project_root, source.parent, image.group("path"), image.group("alt"))
            continue

        if line.startswith("# "):
            flush_paragraph(doc, paragraph_lines)
            paragraph_lines = []
            flush_bullets()
            # Cover already carries the H1 title.
            continue
        if line.startswith("## "):
            flush_paragraph(doc, paragraph_lines)
            paragraph_lines = []
            flush_bullets()
            doc.add_heading(line[3:].strip(), level=1)
            continue
        if line.startswith("### "):
            flush_paragraph(doc, paragraph_lines)
            paragraph_lines = []
            flush_bullets()
            doc.add_heading(line[4:].strip(), level=2)
            continue

        if line.strip() == "按鈕功能：":
            flush_paragraph(doc, paragraph_lines)
            paragraph_lines = []
            flush_bullets()
            heading = doc.add_paragraph()
            run = heading.add_run("按鈕功能")
            run.bold = True
            run.font.color.rgb = RGBColor(31, 78, 121)
            in_button_functions = True
            continue

        if line.startswith("- "):
            flush_paragraph(doc, paragraph_lines)
            paragraph_lines = []
            bullets.append(line[2:].strip())
            continue

        paragraph_lines.append(line)

    flush_paragraph(doc, paragraph_lines)
    flush_bullets()

    output.parent.mkdir(parents=True, exist_ok=True)
    for style in doc.styles:
        if style.type == 1:
            style.font.name = 'Arial Unicode MS'
            rpr = style.element.get_or_add_rPr()
            fonts = rpr.find(qn('w:rFonts'))
            if fonts is None:
                fonts = OxmlElement('w:rFonts'); rpr.append(fonts)
            fonts.set(qn('w:eastAsia'), 'Arial Unicode MS')
    for root in [doc.styles.element, doc.element]:
        for border in list(root.iter(qn('w:pBdr'))):
            border.getparent().remove(border)
    for paragraph in doc.paragraphs:
        for run in paragraph.runs:
            run.font.name = 'Arial Unicode MS'
            run._element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'), 'Arial Unicode MS')
    doc.save(output)


def main() -> None:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    source = (project_root / args.source).resolve()
    output = (project_root / args.output).resolve()
    build_docx(project_root, source, output)
    print(output)


if __name__ == "__main__":
    main()
