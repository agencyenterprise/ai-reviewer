"""Unit tests for reading display sizes out of a DOCX."""

import io

from docx import Document
from docx.shared import Inches
from PIL import Image
from xxhash import xxh128

from lib.services.docx.image_display_sizes import read_docx_image_display_sizes


def _png_bytes(color: str) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (300, 100), color).save(buf, format="PNG")
    return buf.getvalue()


def test_reads_display_size_in_css_pixels(tmp_path):
    png = _png_bytes("magenta")
    doc = Document()
    doc.add_picture(io.BytesIO(png), width=Inches(2), height=Inches(1))
    path = str(tmp_path / "doc.docx")
    doc.save(path)

    sizes = read_docx_image_display_sizes(path)

    assert sizes.take(xxh128(png).hexdigest()) == (192, 96)  # 96 px per inch


def test_same_image_twice_yields_sizes_in_document_order(tmp_path):
    png = _png_bytes("navy")
    doc = Document()
    doc.add_picture(io.BytesIO(png), width=Inches(2), height=Inches(1))
    doc.add_picture(io.BytesIO(png), width=Inches(1), height=Inches(1))
    path = str(tmp_path / "doc.docx")
    doc.save(path)

    sizes = read_docx_image_display_sizes(path)
    content_hash = xxh128(png).hexdigest()

    assert sizes.take(content_hash) == (192, 96)
    assert sizes.take(content_hash) == (96, 96)
    assert sizes.take(content_hash) is None


def test_unreadable_docx_returns_empty_sizes(tmp_path):
    path = str(tmp_path / "not-a-docx.docx")
    with open(path, "wb") as f:
        f.write(b"garbage")

    sizes = read_docx_image_display_sizes(path)

    assert sizes.take("anything") is None

def test_reads_size_of_anchored_floating_image(tmp_path):
    """Floating images (wp:anchor) are not in `document.inline_shapes`; sizes
    must come from walking the drawing XML — a cover-page logo regression."""
    from docx import Document
    from docx.oxml import parse_xml
    from docx.oxml.ns import nsdecls

    png = _png_bytes("magenta")
    path = str(tmp_path / "img.png")
    with open(path, "wb") as f:
        f.write(png)

    doc = Document()
    embed_id, _ = doc.part.get_or_add_image(path)
    drawing = (
        f'<w:p {nsdecls("w", "wp", "a", "r", "pic")}><w:r><w:drawing>'
        "<wp:anchor>"
        '<wp:extent cx="580644" cy="580644"/>'
        '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        '<pic:pic><pic:nvPicPr><pic:cNvPr id="0" name="logo"/><pic:cNvPicPr/></pic:nvPicPr>'
        f'<pic:blipFill><a:blip r:embed="{embed_id}"/></pic:blipFill><pic:spPr/></pic:pic>'
        "</a:graphicData></a:graphic>"
        "</wp:anchor></w:drawing></w:r></w:p>"
    )
    doc.element.body.get_or_add_sectPr().addprevious(parse_xml(drawing))
    docx_path = str(tmp_path / "doc.docx")
    doc.save(docx_path)

    sizes = read_docx_image_display_sizes(docx_path)

    assert sizes.take(xxh128(png).hexdigest()) == (61, 61)
