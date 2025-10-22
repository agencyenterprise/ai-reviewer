from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.config import RunnableConfig
from pydantic import BaseModel, Field

from lib.config.llm import models
from lib.models.agent import DEFAULT_LLM_TIMEOUT, AgentProtocol


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


_document_summarizer_agent_prompt = ChatPromptTemplate.from_template(
    """
# Task
You are a document summarizer. You are given a document and you need to summarize it.

Read the following document and summarize it in less than 2000 words. Make sure to include the main takeaways of the document.

Also extract:
- The title of the document. Suggest a title if the document does not have one.
- Authors (if available)
- Publication date (if available)
- Abstract (if available)

## The document to summarize
```
{document}
```
"""
)


class DocumentSummarizerAgent(AgentProtocol):
    name = "Document Summarizer"
    description = "Read and summarize a supporting document"

    def __init__(self):
        self.llm = init_chat_model(
            models["gpt-5-mini"],
            temperature=0.0,
            timeout=DEFAULT_LLM_TIMEOUT,
        ).with_structured_output(DocumentSummarizerResponse)

    async def ainvoke(
        self,
        prompt_kwargs: dict,
        config: RunnableConfig = None,
    ) -> DocumentSummarizerResponse:
        messages = _document_summarizer_agent_prompt.format_messages(**prompt_kwargs)
        return await self.llm.ainvoke(messages, config=config)


document_summarizer_agent = DocumentSummarizerAgent()
