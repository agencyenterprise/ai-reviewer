from langfuse import Langfuse
from langfuse.langchain import CallbackHandler
from lib.config.env import config

langfuse = Langfuse(
    secret_key=config.LANGFUSE_SECRET_KEY,
    public_key=config.LANGFUSE_PUBLIC_KEY,
    host=config.LANGFUSE_HOST,
    timeout=120,  # Extended timeout to 120 seconds for large payloads
    flush_at=100,  # Batch up to 100 traces before sending
    flush_interval=10,  # Send batches every 10 seconds
)

langfuse_handler = CallbackHandler()
