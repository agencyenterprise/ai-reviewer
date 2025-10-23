from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from lib.config.llm_models import gpt_5_model
from lib.models.agent import DEFAULT_LLM_TIMEOUT, AgentProtocol


class Claim(BaseModel):
    text: str = Field(
        description="The relevant part of the text within the chunk of text that implies the claims"
    )
    claim: str = Field(description="The claim made in the text")
    rationale: str = Field(
        description="The rationale for why you think the chunk of text implies this claim"
    )


class ClaimResponse(BaseModel):
    claims: list[Claim] = Field(
        description="A list of claims made in the chunk of text"
    )
    rationale: str = Field(
        description="Overall rationale for why you think the chunk of text implies these claims"
    )


_claim_extractor_prompt = ChatPromptTemplate.from_template(
    """
## Task
You are a claim extractor. You are given a chunk of text and you need to extract any claims made in that chunk of text.
You will be given a full document and a chunk of text from that document.
You need to return a list of claims made in that chunk of text.
If there are no claims made in the chunk, return an empty list.
For each claim, you need to return the following information:
- The claim
- Your rationale for why you think the chunk of text implies this claim

{domain_context}

{audience_context}

## The full document that the chunk is a part of
```
{full_document}
```

## The paragraph of the original document that contains the chunk of text that we want to analyze
```
{paragraph}
```

## The chunk of text to extract claims from
```
{chunk}
```
"""
)


class ClaimExtractorAgent(AgentProtocol):
    name = "Claim Extractor"
    description = "Extract claims from a chunk of text"

    def __init__(self):
        self.llm = init_chat_model(
            gpt_5_model.model_name,
            temperature=0.2,
            timeout=DEFAULT_LLM_TIMEOUT,
        ).with_structured_output(ClaimResponse)

    async def ainvoke(
        self,
        prompt_kwargs: dict,
        config: RunnableConfig = None,
    ) -> ClaimResponse:
        messages = _claim_extractor_prompt.format_messages(**prompt_kwargs)
        return await self.llm.ainvoke(messages, config=config)


claim_extractor_agent = ClaimExtractorAgent()
