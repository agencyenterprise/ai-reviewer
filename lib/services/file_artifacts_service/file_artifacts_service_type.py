from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, List, Sequence

from lib.models.file import FileRole

if TYPE_CHECKING:
    from lib.workflows.chunk_utils import AnalyzedChunk
    from lib.models.bibliography_item import BibliographyItem
    from lib.models.footnote_item import FootnoteItem
    from lib.services.file import FileDocument
    from lib.workflows.document_summarization.state import FileSummary
    from lib.workflows.reference_extraction.state import ExtractedReference


# Virtual-filesystem mount directory for each file role in the deep-agent
# backend. Files of a mounted role are placed at ``/<dir>/<file_id>.md``. The
# main file is always mounted at ``/main.md`` and is not listed here.
DEEPAGENT_ROLE_MOUNT_DIRS: dict[FileRole, str] = {
    FileRole.SUPPORT: "supporting",
    FileRole.REVIEWER_MEMO: "reviewer-memos",
}


class FileArtifactsServiceType(ABC):
    @abstractmethod
    async def get_file_document(self, file_id: str) -> "FileDocument": ...

    @abstractmethod
    async def get_main_file(self) -> "FileDocument": ...

    @abstractmethod
    async def get_project_files(
        self, roles: list[FileRole]
    ) -> list["FileDocument"]: ...

    @abstractmethod
    async def get_file_summary(self, file_id: str) -> "FileSummary": ...

    @abstractmethod
    async def get_extracted_references(self) -> list["ExtractedReference"]: ...

    @abstractmethod
    async def get_references(self) -> list["BibliographyItem"]: ...

    @abstractmethod
    async def get_chunks(self) -> list["AnalyzedChunk"]: ...

    @abstractmethod
    async def get_footnotes(self) -> list["FootnoteItem"]: ...

    @abstractmethod
    async def get_deepagent_backend_files(
        self,
        roles: Sequence[FileRole] = (FileRole.SUPPORT,),
        include_skills: bool = True,
    ) -> dict[str, Any]: ...

    def get_paragraph_chunks(
        self, chunks: List["AnalyzedChunk"], paragraph_index: int
    ) -> List["AnalyzedChunk"]:
        """Get all the chunks for a given paragraph index."""

        return [chunk for chunk in chunks if chunk.paragraph_index == paragraph_index]

    def get_paragraph_text(
        self, chunks: List["AnalyzedChunk"], paragraph_index: int
    ) -> str:
        """Get the full paragraph text for a given paragraph index."""

        paragraph_chunks = [
            chunk for chunk in chunks if chunk.paragraph_index == paragraph_index
        ]
        return "\n".join([chunk.content for chunk in paragraph_chunks])
