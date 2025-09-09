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

    # Database Configuration
    DATABASE_URL: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str


config = Config(
    OPENAI_API_KEY=os.getenv("OPENAI_API_KEY"),
    LANGFUSE_HOST=os.getenv("LANGFUSE_HOST"),
    LANGFUSE_SECRET_KEY=os.getenv("LANGFUSE_SECRET_KEY"),
    LANGFUSE_PUBLIC_KEY=os.getenv("LANGFUSE_PUBLIC_KEY"),
    # Database Configuration
    DATABASE_URL=os.getenv(
        "DATABASE_URL",
        "postgresql://rand_user:rand_password@localhost:5432/rand_ai_reviewer",
    ),
    POSTGRES_HOST=os.getenv("POSTGRES_HOST", "localhost"),
    POSTGRES_PORT=os.getenv("POSTGRES_PORT", "5432"),
    POSTGRES_DB=os.getenv("POSTGRES_DB", "rand_ai_reviewer"),
    POSTGRES_USER=os.getenv("POSTGRES_USER", "rand_user"),
    POSTGRES_PASSWORD=os.getenv("POSTGRES_PASSWORD", "rand_password"),
)
