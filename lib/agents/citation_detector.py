from enum import Enum
from pydantic import BaseModel, Field
from lib.models import Agent

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage


class CitationType(str, Enum):
    BIBLIOGRAPHY = "bibliography"
    URL = "url"
    FOOTNOTE = "footnote"
    OTHER = "other"


class Citation(BaseModel):
    text: str = Field(
        description="The text of the citation or footnote mark, e.g., [1] or (Doe, et al., 2025), a url, etc. The bibliography/footnote itself is not a citation."
    )
    type: CitationType = Field(
        description="The type of the citation. This should be a value from the CitationType enum."
    )
    format: str = Field(
        description="The format of the citation or footnote mark, e.g., [number] or (Name, et al., Year), url, etc."
    )
    needs_bibliography: bool = Field(
        description="A boolean value indicating whether the citation refers to a bibliography entry or footnote in the document so it expected to have an associated bibliography entry or footnote"
    )
    associated_bibliography: str = Field(
        description="If the document includes a bibliography entry related to this citation, this will be an exact copy of that bibliography entry (do not include the entry number if there is one, just the full context of the bibliography entry), otherwise it will be an empty string."
    )
    index_of_associated_bibliography: int = Field(
        description="The index of the bibliography entry that this citation refers to, if any. Indices start at 1. If the citation does not refer to a bibliography entry, this should be -1."
    )
    rationale: str = Field(
        description="A very brief rationale for why you think this text is a citation"
    )


class CitationResponse(BaseModel):
    citations: list[Citation] = Field(
        description="A list of citations found in the chunk of text"
    )
    rationale: str = Field(
        description="Very brief rationale for why you think the chunk of text includes these citations, if any"
    )


# Create the prompt template and explicitly set input_variables  
_citation_detector_prompt = ChatPromptTemplate.from_template(
    """
## Task
You are a citation detector. You are given a chunk of text and you need to extract any citations made in that chunk of text.
You will be given a full document and a chunk of text from that document.
You need to return a list of citations made in that chunk of text.
If there are no citations made in the chunk, return an empty list.
For each citation, you need to return the following information:
- The text of the citation/footnote mark
- The type of the citation/footnote mark. This should be a value from the CitationType enum.
- The format of the citation/footnote mark, e.g., [number] or (Name, et al., Year), url, etc.
- A boolean value indicating whether the citation refers to a bibliography entry or footnote in the document so it expected to have an associated bibliography entry or footnote. For example, URLs often do not refer to a bibliography entry so this should be False, but something like (Doe, et al., 2025) does refer to a bibliography entry so this should be True.
- If the document includes a bibliography entry related to this citation, this will be an exact copy of that bibliography entry, otherwise it will be an empty string. Bibliography entries are usually included in a dedicated References section at the end of the full document.
- Your very brief rationale for why you think this is a citation/footnote mark

## The full document that the chunk is a part of
```
{full_document}
```

## The list of bibliography entries (if any) extracted from the bibliography section of the full document
The indexes in this list should be used when returning index_of_associated_bibliography.
```
{bibliography}
```

## The chunk of text to extract citations from
```
{chunk}
```
"""
)
# Explicitly set the input variables to ensure they're recognized
_citation_detector_prompt.input_variables = ["full_document", "bibliography", "chunk"]

citation_detector_agent = Agent(
    name="Citation Detector",
    description="Detect citations in a chunk of text",
    model="openai:gpt-5",
    prompt=_citation_detector_prompt,
    mandatory_tools=[],
    output_schema=CitationResponse,
)
