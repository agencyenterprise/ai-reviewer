"""A tracked change inside a Word text box is reported once."""

import zipfile
from pathlib import Path

from lib.services.docx.review_markup import read_docx_review_markup

_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_MC = "http://schemas.openxmlformats.org/markup-compatibility/2006"
_WPS = "http://schemas.microsoft.com/office/word/2010/wordprocessingShape"

_BOX = (
    '<w:p><w:ins w:id="1" w:author="Rev" w:date="2026-01-01T00:00:00Z">'
    "<w:r><w:t>added in the box</w:t></w:r></w:ins></w:p>"
)

_DOCUMENT = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{_W}" xmlns:mc="{_MC}" xmlns:wps="{_WPS}">
<w:body>
<w:p><w:r><w:t>Body text. </w:t></w:r>
<w:r><mc:AlternateContent>
<mc:Choice Requires="wps"><w:drawing><wps:txbx><w:txbxContent>{_BOX}</w:txbxContent></wps:txbx></w:drawing></mc:Choice>
<mc:Fallback><w:pict><w:txbxContent>{_BOX}</w:txbxContent></w:pict></mc:Fallback>
</mc:AlternateContent></w:r></w:p>
</w:body>
</w:document>"""


def test_a_change_in_a_text_box_is_reported_once(tmp_path: Path) -> None:
    path = tmp_path / "boxed.docx"
    with zipfile.ZipFile(path, "w") as package:
        package.writestr("word/document.xml", _DOCUMENT)

    markup = read_docx_review_markup(str(path))

    assert [c.inserted for c in markup.tracked_changes] == ["added in the box"]
