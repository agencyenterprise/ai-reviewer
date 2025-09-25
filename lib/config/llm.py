from lib.config.env import config


def get_model(model_name: str) -> str:
    if config.AZURE_OPENAI_API_KEY and config.AZURE_OPENAI_ENDPOINT:
        return f"azure_openai:{model_name}"
    else:
        return f"openai:{model_name}"


models = {
    "gpt-5": get_model("gpt-5"),
    "gpt-5-mini": get_model("gpt-5-mini"),
    "gpt-4.1": get_model("gpt-4.1"),
}
