from abc import abstractmethod
from typing import Any
from openai import AsyncOpenAI, OpenAI
from pydantic import BaseModel


class LLMClient(BaseModel):
    provider: str
    model: str

    tools: list[dict]
    background: bool = False  # Is background model?
    output_schema: Any

    @abstractmethod
    async def ainvoke(self, input: str) -> str:
        pass


class OpenAIWrapper(LLMClient):
    provider: str = "openai"
    client: Any | None = None
    status: str | None = None
    resp: Any | None = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = None

    async def ainvoke(self, input: str) -> str:
        from openai import AsyncOpenAI
        from time import sleep

        client = AsyncOpenAI()

        input_dict = [
            message.model_dump(include={"content", "type", "role"}) for message in input
        ]
        for message in input_dict:
            if message.get("type"):
                message["role"] = message["type"]
                del message["type"]
            if message.get("role") == "human":
                message["role"] = "user"

        if not self.output_schema or self.output_schema is str:
            self.resp = await client.responses.create(
                model=self.model,
                input=input_dict,
                background=self.background,
                tools=self.tools,
            )
        else:
            self.resp = await client.responses.parse(
                model=self.model,
                input=input_dict,
                background=self.background,
                tools=self.tools,
                # text_format=self.output_schema,
            )

        if not self.background:
            return self.resp.output_text
        else:
            while self.resp.status in {"queued", "in_progress"}:
                self.status = self.resp.status
                print(f"Call id: {self.resp.id} => Current status: {self.resp.status}")
                sleep(2)
                self.resp = await client.responses.retrieve(self.resp.id)

                print(
                    f"Final status: {self.resp.status}\nOutput:\n{self.resp.output_text}"
                )
            self.status = self.resp.status
            return self.resp.output_text
