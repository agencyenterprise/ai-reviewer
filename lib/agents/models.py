from pydantic import BaseModel, Field
from typing import Optional


class ChunkWithIndex(BaseModel):
    content: str
    chunk_index: int
    paragraph_index: int
    headings: Optional[list[str]] = Field(
        default=None,
        description="The headings associated with the chunk, in order of hierarchy",
    )
    start_line: int = Field(ge=1, description="1-indexed starting line in markdown")
    end_line: int = Field(ge=1, description="1-indexed ending line in markdown")

