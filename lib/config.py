from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    OPENAI_API_KEY: str


config = Config(
    OPENAI_API_KEY=os.getenv("OPENAI_API_KEY"),
)

print(config)
