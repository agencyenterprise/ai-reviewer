"""OOXML namespaces and small helpers for reading WordprocessingML.

Shared by the modules that read the markup directly. Writing it is
``docx-editor``'s job, so the element builders that used to live here are gone.

The names match the prefixes used in the XML itself, which keeps call sites
readable when they mirror the markup's structure.
"""

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
# Word 2010 and 2012 extensions: paragraph ids, and comment threads and their
# resolved state, which review markup reads.
W14 = "http://schemas.microsoft.com/office/word/2010/wordml"
W15 = "http://schemas.microsoft.com/office/word/2012/wordml"
PKG = "http://schemas.microsoft.com/office/2006/xmlPackage"


def qn(tag: str, namespace: str = W) -> str:
    """Qualified name for an element or attribute, e.g. ``qn("comment")``."""

    return f"{{{namespace}}}{tag}"


def w(tag: str) -> str:
    """Qualified name in the main WordprocessingML namespace."""

    return qn(tag, W)
