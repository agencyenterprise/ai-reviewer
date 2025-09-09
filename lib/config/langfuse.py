from langfuse import Langfuse
from langfuse.langchain import CallbackHandler
from lib.config.env import config

langfuse = Langfuse(
    secret_key=config.LANGFUSE_SECRET_KEY,
    public_key=config.LANGFUSE_PUBLIC_KEY,
    host=config.LANGFUSE_HOST,
)

langfuse_handler = CallbackHandler()
