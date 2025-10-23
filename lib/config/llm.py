from openai import BaseModel
from lib.config.env import config


class LLMModel(BaseModel):
    name: str
    provider: str

    def model(self) -> str:
        return f"{self.provider}:{self.name}"

    def __str__(self) -> str:
        return self.model()


def get_model(model_name: str) -> LLMModel:
    if config.AZURE_OPENAI_API_KEY and config.AZURE_OPENAI_ENDPOINT:
        return LLMModel(provider="azure_openai", name=model_name)
    else:
        return LLMModel(provider="openai", name=model_name)


models = {
    "gpt-5": get_model("gpt-5"),
    "gpt-5-mini": get_model("gpt-5-mini"),
    "gpt-4.1": get_model("gpt-4.1"),
    "o4-mini-deep-research": get_model("o4-mini-deep-research"),
}
