import os
from pathlib import Path
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings

ROOT_DIR = Path(__file__).resolve().parents[3]

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI File Chatbot"
    API_V1_STR: str = "/api/v1"
    
    GROQ_API_KEY: str = Field(..., env="GROQ_API_KEY")
    
    # File processing settings
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", 10))
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", 1000))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", 200))
    
    class Config:
        env_file = str(ROOT_DIR / ".env")

    @model_validator(mode="after")
    def validate_groq_key(cls, values):
        groq_key = values.GROQ_API_KEY
        invalid_values = {"", "your_groq_api_key_here", "REPLACE_WITH_YOUR_GROQ_KEY"}
        if groq_key in invalid_values:
            raise ValueError(
                "GROQ_API_KEY must be set to a valid Groq API key in the repository root .env file."
            )
        return values

settings = Settings()
