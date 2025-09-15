from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

from lib.models.agent import Agent


class ReferenceMatch(BaseModel):
    reference_text: str = Field(
        description="The text of the reference in the list of references that matches the supporting document"
    )
    reference_index: int = Field(
        description="The index (starting from 0) of the reference in the list of references that matches the supporting document"
    )
    rationale: str = Field(
        description="A brief rationale for why you think the reference matches the supporting document"
    )


reference_matcher_agent = Agent(
    name="Reference Matcher",
    description="Match references to supporting documents",
    model="openai:gpt-5",
    prompt=ChatPromptTemplate.from_template(
        """
# Task
You will be given a list of references and the beginning of the text of a document that may be the original text of one of the references.
Your job is to match one of the references to the supporting document.
If there's no matching reference, return None.
If there's a matching reference, return the reference text and the index of the reference in the list of references and a brief rationale for why you think the reference matches the supporting document.

## The list of references
```
{references}
```

## The beginning of the text of the supporting document
```
{supporting_document}
```
        """
    ),
    mandatory_tools=[],
    output_schema=ReferenceMatch,
)
