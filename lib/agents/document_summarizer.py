from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from lib.config.llm import models
from lib.models.agent import Agent


class DocumentSummary(BaseModel):
    title: str = Field(description="The title of the document")
    authors: str = Field(
        description="The authors of the document (if available, otherwise empty string)"
    )
    publication_date: str = Field(
        description="The publication date of the document, or 'Unknown' if not available"
    )
    abstract: str = Field(
        description="The abstract of the document, or 'Unknown' if not available"
    )
    summary: str = Field(
        description="A brief summary of the document in less than 2000 words. Make sure to include the main takeaways of the document."
    )


class DocumentSummarizerResponse(BaseModel):
    summary: DocumentSummary = Field(description="The summary of the document")


document_summarizer_agent = Agent(
    name="Document Summarizer",
    description="Read and summarize a supporting document",
    model=models["gpt-5-mini"],
    temperature=0.0,
    prompt=ChatPromptTemplate.from_template(
        """
# Task
You are a document summarizer. You are given a document and you need to summarize it.

Read the following document and summarize it in less than 2000 words. Make sure to include the main takeaways of the document. 

Also extract:
- The title, 
- Authors (if available),
- Publication date (if available), and
- Abstract (if available).

## The document to summarize
```
{document}
```
"""
    ),
    tools=[],
    mandatory_tools=[],
    output_schema=DocumentSummarizerResponse,
)
