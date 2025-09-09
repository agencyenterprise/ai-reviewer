from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    OPENAI_API_KEY: str

    LANGFUSE_SECRET_KEY: str
    LANGFUSE_PUBLIC_KEY: str
    LANGFUSE_HOST: str


config = Config(
    OPENAI_API_KEY=os.getenv("OPENAI_API_KEY"),
    LANGFUSE_HOST=os.getenv("LANGFUSE_HOST"),
    LANGFUSE_SECRET_KEY=os.getenv("LANGFUSE_SECRET_KEY"),
    LANGFUSE_PUBLIC_KEY=os.getenv("LANGFUSE_PUBLIC_KEY"),
)
