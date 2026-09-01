"""Unit tests for `lib.services.docx.drawing_rasterization` — no LibreOffice.

The rendering leg (LibreOffice PDF export + pypdfium2) is covered by the
integration tests; everything here exercises the pure structure work: which
drawings are selected, how the render-source copy is built, and how rendered
images are spliced back into the document.
"""

import io
import os
import tempfile
from unittest.mock import AsyncMock, patch

import pytest
from docx import Document
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.opc.packuri import PackURI
from docx.opc.part import Part
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn
from PIL import Image

from lib.services.docx.drawing_rasterization import (
    CHART_GRAPHIC_URI,
    PICTURE_GRAPHIC_URI,
    _renderable_paragraphs,
    _replace_drawing_with_image,
    _trim_background,
    _write_render_source_docx,
    rasterize_docx_drawings,
)

MODULE = "lib.services.docx.drawing_rasterization"


# --- fixture helpers -------------------------------------------------------


def _chart_graphic_data() -> str:
    return (
        f'<a:graphicData uri="{CHART_GRAPHIC_URI}">'
        '<c:chart r:id="rId999"/>'
        "</a:graphicData>"
    )


def _picture_graphic_data(embed_id: str) -> str:
    return (
        f'<a:graphicData uri="{PICTURE_GRAPHIC_URI}">'
        "<pic:pic>"
        '<pic:nvPicPr><pic:cNvPr id="0" name="p"/><pic:cNvPicPr/></pic:nvPicPr>'
        f'<pic:blipFill><a:blip r:embed="{embed_id}"/></pic:blipFill>'
        "<pic:spPr/>"
        "</pic:pic>"
        "</a:graphicData>"
    )


def _drawing_xml(graphic_data: str, with_extent: bool = True) -> str:
    extent = '<wp:extent cx="914400" cy="457200"/>' if with_extent else ""
    return (
        "<w:drawing><wp:inline>"
        f"{extent}"
        f"<a:graphic>{graphic_data}</a:graphic>"
        "</wp:inline></w:drawing>"
    )


def _paragraph_xml(*runs: str) -> str:
    body = "".join(f"<w:r>{run}</w:r>" for run in runs)
    return f'<w:p {nsdecls("w", "wp", "a", "r", "c", "pic")}>{body}</w:p>'


def _append_paragraph(document, *runs: str) -> None:
    document.element.body.get_or_add_sectPr().addprevious(
        parse_xml(_paragraph_xml(*runs))
    )


def _add_emf_part(document) -> str:
    """Relate a fake EMF image part and return its relationship id."""
    part = Part(
        PackURI("/word/media/image99.emf"),
        "image/x-emf",
        b"\x01\x00\x00\x00EMF-bytes",
        document.part.package,
    )
    return document.part.relate_to(part, RT.IMAGE)


def _png_file(tmp_path, name: str = "img.png", color: str = "magenta") -> str:
    path = str(tmp_path / name)
    Image.new("RGB", (20, 10), color).save(path, format="PNG")
    return path


def _graphic_uri(drawing) -> str:
    return drawing.find(f".//{qn('a:graphicData')}").get("uri")


# --- selection -------------------------------------------------------------


def test_selects_lone_chart_paragraph():
    document = Document()
    document.add_paragraph("Before the chart.")
    _append_paragraph(document, _drawing_xml(_chart_graphic_data()))
    document.add_paragraph("After the chart.")

    renderable = _renderable_paragraphs(document)

    assert len(renderable) == 1
    _, drawing = renderable[0]
    assert _graphic_uri(drawing) == CHART_GRAPHIC_URI


def test_chart_sharing_a_paragraph_with_text_is_not_renderable():
    document = Document()
    _append_paragraph(
        document, "<w:t>Figure 1 caption</w:t>", _drawing_xml(_chart_graphic_data())
    )

    assert _renderable_paragraphs(document) == []


def test_two_drawings_in_one_paragraph_are_not_renderable():
    document = Document()
    _append_paragraph(
        document,
        _drawing_xml(_chart_graphic_data()),
        _drawing_xml(_chart_graphic_data()),
    )

    assert _renderable_paragraphs(document) == []


def test_chart_inside_a_table_is_not_renderable():
    document = Document()
    table_xml = (
        f'<w:tbl {nsdecls("w")}><w:tr><w:tc>'
        + _paragraph_xml(_drawing_xml(_chart_graphic_data()))
        + "</w:tc></w:tr></w:tbl>"
    )
    document.element.body.get_or_add_sectPr().addprevious(parse_xml(table_xml))

    assert _renderable_paragraphs(document) == []


def test_regular_picture_is_not_renderable(tmp_path):
    document = Document()
    with open(_png_file(tmp_path), "rb") as f:
        document.add_picture(io.BytesIO(f.read()))

    assert _renderable_paragraphs(document) == []


def test_metafile_picture_is_renderable():
    document = Document()
    embed_id = _add_emf_part(document)
    _append_paragraph(document, _drawing_xml(_picture_graphic_data(embed_id)))

    renderable = _renderable_paragraphs(document)

    assert len(renderable) == 1
    _, drawing = renderable[0]
    assert _graphic_uri(drawing) == PICTURE_GRAPHIC_URI


# --- render-source construction --------------------------------------------


def test_render_source_keeps_only_renderable_paragraphs(tmp_path):
    document = Document()
    document.add_paragraph("PARA-0")
    _append_paragraph(document, _drawing_xml(_chart_graphic_data()))
    document.add_paragraph("PARA-1")
    _append_paragraph(document, _drawing_xml(_chart_graphic_data()))
    src, dst = str(tmp_path / "src.docx"), str(tmp_path / "dst.docx")
    document.save(src)

    kept = _write_render_source_docx(src, dst)

    assert kept == 2
    rendered = Document(dst)
    body_paragraphs = [
        el for el in rendered.element.body if el.tag == qn("w:p")
    ]
    assert len(body_paragraphs) == 2
    assert "PARA" not in "\n".join(p.text for p in rendered.paragraphs)
    # Page breaks put each drawing on its own PDF page; the first needs none.
    breaks = [
        p.find(qn("w:pPr")) is not None
        and p.find(qn("w:pPr")).find(qn("w:pageBreakBefore")) is not None
        for p in body_paragraphs
    ]
    assert breaks == [False, True]
    # Page geometry survives.
    assert rendered.element.body.find(qn("w:sectPr")) is not None


def test_render_source_strips_headers_and_footers(tmp_path):
    document = Document()
    document.sections[0].header.paragraphs[0].text = "Running header"
    document.sections[0].footer.paragraphs[0].text = "Page footer"
    _append_paragraph(document, _drawing_xml(_chart_graphic_data()))
    src, dst = str(tmp_path / "src.docx"), str(tmp_path / "dst.docx")
    document.save(src)

    assert _write_render_source_docx(src, dst) == 1

    rendered = Document(dst)
    assert rendered.element.findall(f".//{qn('w:headerReference')}") == []
    assert rendered.element.findall(f".//{qn('w:footerReference')}") == []


# --- splicing rendered images back ------------------------------------------


def test_replace_drawing_swaps_chart_for_picture(tmp_path):
    document = Document()
    _append_paragraph(document, _drawing_xml(_chart_graphic_data()))
    _, drawing = _renderable_paragraphs(document)[0]

    assert _replace_drawing_with_image(document, drawing, _png_file(tmp_path))

    graphic_data = drawing.find(f".//{qn('a:graphicData')}")
    assert graphic_data.get("uri") == PICTURE_GRAPHIC_URI
    blip = graphic_data.find(f".//{qn('a:blip')}")
    embed_id = blip.get(qn("r:embed"))
    assert document.part.related_parts[embed_id].content_type == "image/png"
    # The drawing keeps the size the document declared.
    ext = graphic_data.find(f".//{qn('a:ext')}")
    assert (ext.get("cx"), ext.get("cy")) == ("914400", "457200")


def test_replace_drawing_without_extent_fails(tmp_path):
    document = Document()
    _append_paragraph(document, _drawing_xml(_chart_graphic_data(), with_extent=False))
    drawing = next(document.element.body.iter(qn("w:drawing")))

    assert not _replace_drawing_with_image(document, drawing, _png_file(tmp_path))


# --- page-render cropping ----------------------------------------------------


def test_trim_background_crops_to_content():
    page = Image.new("RGB", (200, 100), "white")
    page.paste(Image.new("RGB", (10, 10), "black"), (50, 20))

    assert _trim_background(page).size == (10, 10)


def test_trim_background_keeps_solid_image():
    page = Image.new("RGB", (30, 30), "white")

    assert _trim_background(page).size == (30, 30)


# --- orchestration -----------------------------------------------------------


@pytest.mark.asyncio
async def test_rasterize_returns_none_without_render_targets(tmp_path):
    document = Document()
    document.add_paragraph("Only text.")
    src = str(tmp_path / "doc.docx")
    document.save(src)

    with patch(f"{MODULE}._render_drawings_to_images") as render_mock:
        assert await rasterize_docx_drawings(src) is None

    render_mock.assert_not_called()


@pytest.mark.asyncio
async def test_rasterize_replaces_drawings_with_rendered_images(tmp_path):
    document = Document()
    document.add_paragraph("PARA-0")
    _append_paragraph(document, _drawing_xml(_chart_graphic_data()))
    _append_paragraph(document, _drawing_xml(_chart_graphic_data()))
    src = str(tmp_path / "doc.docx")
    document.save(src)

    render_dir = tempfile.mkdtemp()  # removed by the function under test
    renders = [
        _png_file(tmp_path, "r0.png", "magenta"),
        _png_file(tmp_path, "r1.png", "navy"),
    ]
    with patch(
        f"{MODULE}._render_drawings_to_images",
        new=AsyncMock(return_value=(render_dir, renders)),
    ):
        out = await rasterize_docx_drawings(src)

    assert out is not None
    try:
        rendered = Document(out)
        uris = [
            gd.get("uri")
            for gd in rendered.element.body.iter(qn("a:graphicData"))
        ]
        assert uris == [PICTURE_GRAPHIC_URI, PICTURE_GRAPHIC_URI]
        assert "PARA-0" in "\n".join(p.text for p in rendered.paragraphs)
        assert not os.path.exists(render_dir)
    finally:
        os.remove(out)


@pytest.mark.asyncio
async def test_rasterize_swallows_failures(tmp_path):
    broken = str(tmp_path / "not-a-docx.docx")
    with open(broken, "wb") as f:
        f.write(b"garbage")

    assert await rasterize_docx_drawings(broken) is None
