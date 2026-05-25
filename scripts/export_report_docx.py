#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
import tempfile
import zipfile
from copy import deepcopy
from pathlib import Path
import xml.etree.ElementTree as ET


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
XML_NS = "http://www.w3.org/XML/1998/namespace"
WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
PIC_NS = "http://schemas.openxmlformats.org/drawingml/2006/picture"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
NSMAP = {"w": W_NS, "r": R_NS}

ET.register_namespace("w", W_NS)
ET.register_namespace("r", R_NS)
ET.register_namespace("wp", WP_NS)
ET.register_namespace("a", A_NS)
ET.register_namespace("pic", PIC_NS)
ET.register_namespace("", CT_NS)


def w_tag(tag: str) -> str:
    return f"{{{W_NS}}}{tag}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export the Markdown research report to DOCX using a DOCX template for styles."
    )
    parser.add_argument(
        "--input",
        default="BAO_CAO_BREASTCARE_MINT.md",
        help="Path to the Markdown report.",
    )
    parser.add_argument(
        "--template",
        default="Đề tài nghiên cứu khoa học sử dụng CNN.docx",
        help="Path to the DOCX template used for styles/layout.",
    )
    parser.add_argument(
        "--output",
        default="BAO_CAO_BREASTCARE_MINT.docx",
        help="Output DOCX path.",
    )
    return parser.parse_args()


def load_markdown(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def parse_markdown(lines: list[str]) -> list[dict]:
    blocks: list[dict] = []
    i = 0
    in_toc = False
    in_front_matter = True
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if stripped.startswith("```"):
            fence = stripped[:3]
            language = stripped[3:].strip()
            i += 1
            code_lines: list[str] = []
            while i < len(lines) and not lines[i].strip().startswith(fence):
                code_lines.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1
            blocks.append({"type": "code", "language": language, "lines": code_lines})
            continue

        if re.match(r"^#{1,6}\s+", line):
            level = len(line) - len(line.lstrip("#"))
            text = line[level:].strip()
            blocks.append({"type": "heading", "level": level, "text": text})
            in_toc = text == "MỤC LỤC"
            i += 1
            continue

        image_match = re.match(r"^!\[(.*?)\]\((.+?)\)\s*$", stripped)
        if image_match:
            blocks.append(
                {
                    "type": "image",
                    "caption": image_match.group(1).strip(),
                    "path": image_match.group(2).strip(),
                }
            )
            i += 1
            continue

        if stripped in {"---", "***"}:
            blocks.append({"type": "rule"})
            in_toc = False
            if in_front_matter:
                in_front_matter = False
            i += 1
            continue

        if in_toc or in_front_matter:
            blocks.append({"type": "paragraph", "text": stripped})
            i += 1
            continue

        if stripped.startswith("|"):
            table_lines = [line]
            i += 1
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            blocks.append(parse_table_block(table_lines))
            continue

        if re.match(r"^[-*]\s+", stripped):
            items: list[str] = []
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i].strip()):
                items.append(re.sub(r"^[-*]\s+", "", lines[i].strip()))
                i += 1
            blocks.append({"type": "bullet_list", "items": items})
            continue

        if re.match(r"^\d+\.\s+", stripped):
            items: list[str] = []
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i].strip()):
                items.append(re.sub(r"^\d+\.\s+", "", lines[i].strip()))
                i += 1
            blocks.append({"type": "number_list", "items": items})
            continue

        para_lines = [stripped]
        i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if not nxt:
                break
            if nxt.startswith("```") or nxt.startswith("|") or nxt in {"---", "***"}:
                break
            if re.match(r"^#{1,6}\s+", lines[i]):
                break
            if re.match(r"^[-*]\s+", nxt) or re.match(r"^\d+\.\s+", nxt):
                break
            para_lines.append(nxt)
            i += 1
        blocks.append({"type": "paragraph", "text": " ".join(para_lines)})

    return blocks


def parse_table_block(lines: list[str]) -> dict:
    rows = [parse_table_row(line) for line in lines]
    alignments: list[str] | None = None
    header = rows[0] if rows else []
    body = rows[1:]

    if len(rows) >= 2 and is_separator_row(rows[1]):
        alignments = [alignment_from_separator(cell) for cell in rows[1]]
        body = rows[2:]

    return {
        "type": "table",
        "header": header,
        "rows": body,
        "alignments": alignments or ["left"] * len(header),
    }


def parse_table_row(line: str) -> list[str]:
    raw = line.strip()
    if raw.startswith("|"):
        raw = raw[1:]
    if raw.endswith("|"):
        raw = raw[:-1]
    return [cell.strip() for cell in raw.split("|")]


def is_separator_row(cells: list[str]) -> bool:
    if not cells:
        return False
    for cell in cells:
        if not re.fullmatch(r":?-{3,}:?", cell.strip()):
            return False
    return True


def alignment_from_separator(cell: str) -> str:
    c = cell.strip()
    if c.startswith(":") and c.endswith(":"):
        return "center"
    if c.endswith(":"):
        return "right"
    return "left"


def build_docx(markdown_path: Path, template_path: Path, output_path: Path) -> None:
    lines = load_markdown(markdown_path)
    blocks = parse_markdown(lines)

    with tempfile.TemporaryDirectory(prefix="bcai_docx_") as tmp:
        tmp_path = Path(tmp)
        with zipfile.ZipFile(template_path) as zf:
            zf.extractall(tmp_path)

        doc_xml_path = tmp_path / "word" / "document.xml"
        doc_tree = ET.parse(doc_xml_path)
        doc_root = doc_tree.getroot()
        body = doc_root.find("w:body", NSMAP)
        if body is None:
            raise RuntimeError("Template DOCX missing word/document.xml body")

        sect_pr = body.find("w:sectPr", NSMAP)
        sect_copy = deepcopy(sect_pr) if sect_pr is not None else None
        body.clear()

        media_manager = DocxMediaManager(package_dir=tmp_path)
        writer = OOXMLWriter(body=body, media_manager=media_manager, base_dir=markdown_path.parent)
        writer.write_blocks(blocks)

        if sect_copy is not None:
            body.append(sect_copy)

        doc_tree.write(doc_xml_path, encoding="utf-8", xml_declaration=True)
        media_manager.save()

        update_core_properties(
            tmp_path / "docProps" / "core.xml",
            title="Nghiên cứu các mô hình nhận dạng, phân loại các khối u vú ác tính",
        )

        if output_path.exists():
            output_path.unlink()
        zip_directory(tmp_path, output_path)


def update_core_properties(core_path: Path, title: str) -> None:
    try:
        tree = ET.parse(core_path)
        root = tree.getroot()
        title_el = None
        for child in root:
            if child.tag.endswith("title"):
                title_el = child
                break
        if title_el is not None:
            title_el.text = title
        tree.write(core_path, encoding="utf-8", xml_declaration=True)
    except Exception:
        return


def zip_directory(source_dir: Path, output_path: Path) -> None:
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(source_dir.rglob("*")):
            if path.is_dir():
                continue
            zf.write(path, arcname=str(path.relative_to(source_dir)))


class OOXMLWriter:
    def __init__(self, body: ET.Element, media_manager: "DocxMediaManager", base_dir: Path):
        self.body = body
        self.media_manager = media_manager
        self.base_dir = base_dir
        self.in_front_matter = True
        self.in_toc = False
        self.seen_main_content = False

    def write_blocks(self, blocks: list[dict]) -> None:
        for block in blocks:
            btype = block["type"]
            if btype == "heading":
                self.write_heading(block["level"], block["text"])
            elif btype == "paragraph":
                self.write_paragraph(block["text"])
            elif btype == "bullet_list":
                for item in block["items"]:
                    self.write_list_item(item, bullet=True)
            elif btype == "number_list":
                for idx, item in enumerate(block["items"], start=1):
                    self.write_list_item(item, bullet=False, number=idx)
            elif btype == "code":
                self.write_code_block(block["lines"])
            elif btype == "table":
                self.write_table(block["header"], block["rows"], block["alignments"])
            elif btype == "image":
                self.write_image(block["path"], block["caption"])
            elif btype == "rule":
                self.handle_rule()

    def write_heading(self, level: int, text: str) -> None:
        normalized = text.strip()

        if normalized == "MỤC LỤC":
            if len(self.body):
                self.add_page_break()
            self.in_front_matter = False
            self.in_toc = True
            self.body.append(
                make_paragraph(
                    [("MỤC LỤC", {})],
                    style="TOCHeading",
                    align="center",
                    spacing_before=120,
                    spacing_after=160,
                )
            )
            return

        self.in_toc = False
        if normalized.startswith("CHƯƠNG "):
            if self.seen_main_content:
                self.add_page_break()
            self.seen_main_content = True

        if level == 1 and self.in_front_matter:
            self.body.append(
                make_paragraph(
                    [(normalized, {"bold": True})],
                    style="Title",
                    align="center",
                    spacing_before=120,
                    spacing_after=120,
                )
            )
            return

        style = heading_style_for(level)
        self.body.append(
            make_paragraph(
                parse_inline(normalized),
                style=style,
                align="left",
            )
        )

    def write_paragraph(self, text: str) -> None:
        normalized = text.strip()
        if not normalized:
            return

        if self.in_toc:
            self.body.append(make_toc_paragraph(normalized))
            return

        align = "center" if self.in_front_matter else "left"
        style = "Normal"
        if self.in_front_matter:
            spacing_before = 0
            spacing_after = 60
        else:
            spacing_before = 0
            spacing_after = 80

        self.body.append(
            make_paragraph(
                parse_inline(normalized),
                style=style,
                align=align,
                spacing_before=spacing_before,
                spacing_after=spacing_after,
            )
        )

    def write_list_item(self, text: str, bullet: bool, number: int | None = None) -> None:
        prefix = "• " if bullet else f"{number}. "
        runs = [(prefix, {"bold": False})] + parse_inline(text.strip())
        self.body.append(
            make_paragraph(
                runs,
                style="ListParagraph",
                align="left",
                spacing_before=0,
                spacing_after=40,
                indent_left=360,
            )
        )

    def write_code_block(self, lines: list[str]) -> None:
        if not lines:
            self.body.append(
                make_paragraph(
                    [("", {"code": True})],
                    style="HTMLPreformatted",
                    align="left",
                )
            )
            return

        for line in lines:
            self.body.append(
                make_paragraph(
                    [(line, {"code": True})],
                    style="HTMLPreformatted",
                    align="left",
                    spacing_before=0,
                    spacing_after=0,
                )
            )

    def write_table(self, header: list[str], rows: list[list[str]], alignments: list[str]) -> None:
        self.body.append(make_table(header, rows, alignments))

    def write_image(self, rel_path: str, caption: str) -> None:
        image_path = (self.base_dir / rel_path).resolve()
        if not image_path.exists():
            self.body.append(
                make_paragraph(
                    [(f"[Missing image: {rel_path}]", {"italic": True})],
                    style="Quote",
                    align="center",
                )
            )
            return

        image_ref = self.media_manager.add_image(image_path)
        self.body.append(
            make_image_paragraph(
                rid=image_ref["rid"],
                filename=image_ref["filename"],
                width_emu=image_ref["width_emu"],
                height_emu=image_ref["height_emu"],
                docpr_id=image_ref["docpr_id"],
            )
        )
        if caption:
            self.body.append(
                make_paragraph(
                    [(caption, {})],
                    style="Caption",
                    align="center",
                    spacing_before=40,
                    spacing_after=120,
                )
            )

    def handle_rule(self) -> None:
        if self.in_toc:
            self.in_toc = False
        self.body.append(make_empty_paragraph())

    def add_page_break(self) -> None:
        self.body.append(make_page_break_paragraph())


def heading_style_for(level: int) -> str:
    mapping = {
        2: "Heading1",
        3: "Heading2",
        4: "Heading3",
        5: "Heading4",
        6: "Heading5",
    }
    return mapping.get(level, "Heading1")


def make_toc_paragraph(text: str) -> ET.Element:
    if text.startswith(("I.", "II.", "CHƯƠNG ")):
        style = "TOC1"
    elif re.match(r"^\d+\.\d+", text):
        style = "TOC3"
    elif re.match(r"^\d+\.", text):
        style = "TOC2"
    else:
        style = "TOC2"

    return make_paragraph(
        [(text, {})],
        style=style,
        align="left",
        spacing_before=0,
        spacing_after=0,
    )


def make_table(header: list[str], rows: list[list[str]], alignments: list[str]) -> ET.Element:
    tbl = ET.Element(w_tag("tbl"))

    tbl_pr = ET.SubElement(tbl, w_tag("tblPr"))
    tbl_style = ET.SubElement(tbl_pr, w_tag("tblStyle"))
    tbl_style.set(w_tag("val"), "TableGrid")
    tbl_w = ET.SubElement(tbl_pr, w_tag("tblW"))
    tbl_w.set(w_tag("w"), "0")
    tbl_w.set(w_tag("type"), "auto")
    tbl_look = ET.SubElement(tbl_pr, w_tag("tblLook"))
    tbl_look.set(w_tag("firstRow"), "1")
    tbl_look.set(w_tag("lastRow"), "0")
    tbl_look.set(w_tag("firstColumn"), "1")
    tbl_look.set(w_tag("lastColumn"), "0")
    tbl_look.set(w_tag("noHBand"), "0")
    tbl_look.set(w_tag("noVBand"), "1")
    tbl_look.set(w_tag("val"), "04A0")

    grid = ET.SubElement(tbl, w_tag("tblGrid"))
    col_count = len(header)
    for _ in range(col_count):
        grid_col = ET.SubElement(grid, w_tag("gridCol"))
        grid_col.set(w_tag("w"), "2400")

    tbl.append(make_table_row(header, alignments, header=True))
    for row in rows:
        padded = row + [""] * (col_count - len(row))
        tbl.append(make_table_row(padded[:col_count], alignments, header=False))

    return tbl


def make_table_row(cells: list[str], alignments: list[str], header: bool) -> ET.Element:
    tr = ET.Element(w_tag("tr"))
    for idx, text in enumerate(cells):
        tc = ET.SubElement(tr, w_tag("tc"))
        tc_pr = ET.SubElement(tc, w_tag("tcPr"))
        tc_w = ET.SubElement(tc_pr, w_tag("tcW"))
        tc_w.set(w_tag("w"), "2400")
        tc_w.set(w_tag("type"), "dxa")

        align = alignments[idx] if idx < len(alignments) else "left"
        runs = parse_inline(text)
        if header:
            runs = [(seg, {**props, "bold": True}) for seg, props in runs]
        tc.append(
            make_paragraph(
                runs,
                style="Normal",
                align=align,
                spacing_before=0,
                spacing_after=0,
            )
        )
    return tr


def make_empty_paragraph() -> ET.Element:
    return make_paragraph([("", {})], style="Normal", spacing_before=0, spacing_after=0)


def make_page_break_paragraph() -> ET.Element:
    p = ET.Element(w_tag("p"))
    r = ET.SubElement(p, w_tag("r"))
    br = ET.SubElement(r, w_tag("br"))
    br.set(w_tag("type"), "page")
    return p


def make_image_paragraph(
    *,
    rid: str,
    filename: str,
    width_emu: int,
    height_emu: int,
    docpr_id: int,
) -> ET.Element:
    p = ET.Element(w_tag("p"))
    p_pr = ET.SubElement(p, w_tag("pPr"))
    jc = ET.SubElement(p_pr, w_tag("jc"))
    jc.set(w_tag("val"), "center")

    r = ET.SubElement(p, w_tag("r"))
    drawing = ET.SubElement(r, w_tag("drawing"))

    inline = ET.SubElement(
        drawing,
        f"{{{WP_NS}}}inline",
        {
            "distT": "0",
            "distB": "0",
            "distL": "0",
            "distR": "0",
        },
    )
    ET.SubElement(
        inline,
        f"{{{WP_NS}}}extent",
        {"cx": str(width_emu), "cy": str(height_emu)},
    )
    ET.SubElement(
        inline,
        f"{{{WP_NS}}}docPr",
        {"id": str(docpr_id), "name": filename},
    )
    c_nv = ET.SubElement(inline, f"{{{WP_NS}}}cNvGraphicFramePr")
    ET.SubElement(
        c_nv,
        f"{{{A_NS}}}graphicFrameLocks",
        {"noChangeAspect": "1"},
    )

    graphic = ET.SubElement(inline, f"{{{A_NS}}}graphic")
    graphic_data = ET.SubElement(
        graphic,
        f"{{{A_NS}}}graphicData",
        {"uri": "http://schemas.openxmlformats.org/drawingml/2006/picture"},
    )
    pic = ET.SubElement(graphic_data, f"{{{PIC_NS}}}pic")
    nv_pic_pr = ET.SubElement(pic, f"{{{PIC_NS}}}nvPicPr")
    ET.SubElement(
        nv_pic_pr,
        f"{{{PIC_NS}}}cNvPr",
        {"id": "0", "name": filename},
    )
    ET.SubElement(nv_pic_pr, f"{{{PIC_NS}}}cNvPicPr")

    blip_fill = ET.SubElement(pic, f"{{{PIC_NS}}}blipFill")
    ET.SubElement(
        blip_fill,
        f"{{{A_NS}}}blip",
        {f"{{{R_NS}}}embed": rid},
    )
    stretch = ET.SubElement(blip_fill, f"{{{A_NS}}}stretch")
    ET.SubElement(stretch, f"{{{A_NS}}}fillRect")

    sp_pr = ET.SubElement(pic, f"{{{PIC_NS}}}spPr")
    xfrm = ET.SubElement(sp_pr, f"{{{A_NS}}}xfrm")
    ET.SubElement(xfrm, f"{{{A_NS}}}off", {"x": "0", "y": "0"})
    ET.SubElement(
        xfrm,
        f"{{{A_NS}}}ext",
        {"cx": str(width_emu), "cy": str(height_emu)},
    )
    prst_geom = ET.SubElement(sp_pr, f"{{{A_NS}}}prstGeom", {"prst": "rect"})
    ET.SubElement(prst_geom, f"{{{A_NS}}}avLst")
    return p


def make_paragraph(
    runs: list[tuple[str, dict]],
    *,
    style: str | None = None,
    align: str = "left",
    spacing_before: int | None = None,
    spacing_after: int | None = None,
    indent_left: int | None = None,
) -> ET.Element:
    p = ET.Element(w_tag("p"))
    p_pr = ET.SubElement(p, w_tag("pPr"))

    if style:
        p_style = ET.SubElement(p_pr, w_tag("pStyle"))
        p_style.set(w_tag("val"), style)

    if align != "left":
        jc = ET.SubElement(p_pr, w_tag("jc"))
        jc.set(w_tag("val"), align)

    if spacing_before is not None or spacing_after is not None:
        spacing = ET.SubElement(p_pr, w_tag("spacing"))
        if spacing_before is not None:
            spacing.set(w_tag("before"), str(spacing_before))
        if spacing_after is not None:
            spacing.set(w_tag("after"), str(spacing_after))

    if indent_left is not None:
        ind = ET.SubElement(p_pr, w_tag("ind"))
        ind.set(w_tag("left"), str(indent_left))

    if not runs:
        runs = [("", {})]

    for text, props in runs:
        p.append(make_run(text, props))

    return p


def make_run(text: str, props: dict) -> ET.Element:
    r = ET.Element(w_tag("r"))
    if props:
        r_pr = ET.SubElement(r, w_tag("rPr"))
        if props.get("bold"):
            ET.SubElement(r_pr, w_tag("b"))
        if props.get("italic"):
            ET.SubElement(r_pr, w_tag("i"))
        if props.get("code"):
            r_fonts = ET.SubElement(r_pr, w_tag("rFonts"))
            for attr in ("ascii", "hAnsi", "eastAsia", "cs"):
                r_fonts.set(w_tag(attr), "Courier New")
    t = ET.SubElement(r, w_tag("t"))
    t.set(f"{{{XML_NS}}}space", "preserve")
    t.text = text
    return r


INLINE_RE = re.compile(r"(\*\*.+?\*\*|`[^`]+`)")


def parse_inline(text: str) -> list[tuple[str, dict]]:
    runs: list[tuple[str, dict]] = []
    parts = INLINE_RE.split(text)
    for part in parts:
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) >= 4:
            runs.append((part[2:-2], {"bold": True}))
        elif part.startswith("`") and part.endswith("`") and len(part) >= 2:
            runs.append((part[1:-1], {"code": True}))
        else:
            runs.append((part, {}))
    return runs


class DocxMediaManager:
    def __init__(self, package_dir: Path):
        self.package_dir = package_dir
        self.media_dir = package_dir / "word" / "media"
        self.media_dir.mkdir(parents=True, exist_ok=True)
        self.rels_path = package_dir / "word" / "_rels" / "document.xml.rels"
        self.rels_tree = ET.parse(self.rels_path)
        self.rels_root = self.rels_tree.getroot()
        self.content_types_path = package_dir / "[Content_Types].xml"
        self.content_types_tree = ET.parse(self.content_types_path)
        self.content_types_root = self.content_types_tree.getroot()
        self.next_rid = self._infer_next_rid()
        self.next_docpr_id = 1000
        self.image_counter = 1
        self.image_cache: dict[Path, dict[str, object]] = {}

    def _infer_next_rid(self) -> int:
        max_id = 0
        for rel in self.rels_root.findall(f"{{{REL_NS}}}Relationship"):
            rid = rel.attrib.get("Id", "")
            match = re.fullmatch(r"rId(\d+)", rid)
            if match:
                max_id = max(max_id, int(match.group(1)))
        return max_id + 1

    def _ensure_content_type(self, suffix: str) -> None:
        defaults = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
        }
        content_type = defaults.get(suffix.lower())
        if not content_type:
            raise ValueError(f"Unsupported image type: {suffix}")

        ext = suffix.lower().lstrip(".")
        existing = {
            node.attrib.get("Extension", "").lower()
            for node in self.content_types_root.findall(f"{{{CT_NS}}}Default")
        }
        if ext in existing:
            return
        ET.SubElement(
            self.content_types_root,
            f"{{{CT_NS}}}Default",
            {"Extension": ext, "ContentType": content_type},
        )

    def add_image(self, image_path: Path) -> dict:
        image_path = image_path.resolve()
        suffix = image_path.suffix.lower()
        self._ensure_content_type(suffix)

        cached = self.image_cache.get(image_path)
        if cached is not None:
            docpr_id = self.next_docpr_id
            self.next_docpr_id += 1
            return {
                "rid": cached["rid"],
                "filename": cached["filename"],
                "width_emu": cached["width_emu"],
                "height_emu": cached["height_emu"],
                "docpr_id": docpr_id,
            }

        target_name = f"embedded_{self.image_counter:03d}{suffix}"
        self.image_counter += 1
        target_path = self.media_dir / target_name
        target_path.write_bytes(image_path.read_bytes())

        rid = f"rId{self.next_rid}"
        self.next_rid += 1
        ET.SubElement(
            self.rels_root,
            f"{{{REL_NS}}}Relationship",
            {
                "Id": rid,
                "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image",
                "Target": f"media/{target_name}",
            },
        )

        width_px, height_px = get_image_dimensions(image_path)
        width_emu, height_emu = scale_image_emu(width_px, height_px)
        docpr_id = self.next_docpr_id
        self.next_docpr_id += 1

        self.image_cache[image_path] = {
            "rid": rid,
            "filename": target_name,
            "width_emu": width_emu,
            "height_emu": height_emu,
        }

        return {
            "rid": rid,
            "filename": target_name,
            "width_emu": width_emu,
            "height_emu": height_emu,
            "docpr_id": docpr_id,
        }

    def save(self) -> None:
        self.rels_tree.write(self.rels_path, encoding="utf-8", xml_declaration=True)
        self.content_types_tree.write(
            self.content_types_path,
            encoding="utf-8",
            xml_declaration=True,
        )


def scale_image_emu(width_px: int, height_px: int) -> tuple[int, int]:
    emu_per_px = 9525
    max_width_emu = int(6.2 * 914400)
    width_emu = max(1, width_px * emu_per_px)
    height_emu = max(1, height_px * emu_per_px)

    if width_emu <= max_width_emu:
        return width_emu, height_emu

    scale = max_width_emu / width_emu
    return int(width_emu * scale), int(height_emu * scale)


def get_image_dimensions(path: Path) -> tuple[int, int]:
    suffix = path.suffix.lower()
    data = path.read_bytes()
    if suffix == ".png":
        return get_png_dimensions(data)
    if suffix in {".jpg", ".jpeg"}:
        return get_jpeg_dimensions(data)
    raise ValueError(f"Unsupported image format: {suffix}")


def get_png_dimensions(data: bytes) -> tuple[int, int]:
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Invalid PNG signature")
    width = int.from_bytes(data[16:20], "big")
    height = int.from_bytes(data[20:24], "big")
    return width, height


def get_jpeg_dimensions(data: bytes) -> tuple[int, int]:
    if data[:2] != b"\xff\xd8":
        raise ValueError("Invalid JPEG signature")
    i = 2
    while i < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        i += 2
        if marker in {0xD8, 0xD9}:
            continue
        if i + 2 > len(data):
            break
        seg_len = int.from_bytes(data[i:i + 2], "big")
        if marker in {
            0xC0, 0xC1, 0xC2, 0xC3,
            0xC5, 0xC6, 0xC7,
            0xC9, 0xCA, 0xCB,
            0xCD, 0xCE, 0xCF,
        }:
            if i + 7 > len(data):
                break
            height = int.from_bytes(data[i + 3:i + 5], "big")
            width = int.from_bytes(data[i + 5:i + 7], "big")
            return width, height
        i += seg_len
    raise ValueError("JPEG size not found")


def main() -> int:
    args = parse_args()
    input_path = Path(args.input).resolve()
    template_path = Path(args.template).resolve()
    output_path = Path(args.output).resolve()

    if not input_path.exists():
        raise SystemExit(f"Missing input Markdown file: {input_path}")
    if not template_path.exists():
        raise SystemExit(f"Missing DOCX template file: {template_path}")

    build_docx(input_path, template_path, output_path)
    print(f"Exported DOCX: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
