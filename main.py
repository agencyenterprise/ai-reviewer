from lib.config.env import config
from lib.config.langfuse import langfuse_handler
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage


def main():
    print("Hello from rand-ai-reviewer!")
    print(config)

    model = init_chat_model("gpt-4o-mini", model_provider="openai")
    messages = [
        SystemMessage(content="Translate the following from English into Portuguese"),
        HumanMessage(content="hello world!"),
    ]

    response = model.invoke(messages, config={"callbacks": [langfuse_handler]})
    print(response)


if __name__ == "__main__":
    main()
