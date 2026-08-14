import os
from dotenv import load_dotenv
from pydantic import BaseModel

# Load environment variables from .env file if it exists
load_dotenv()

class Settings:
    # PostgreSQL Configuration
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "admin")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "adminpassword")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "searchops")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5433")

    # ChromaDB Configuration
    CHROMA_DB_PATH: str = os.getenv("CHROMA_DB_PATH", "./data/chroma")
    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")

    # Mock Data Paths
    MOCK_DATA_DIR: str = os.getenv("MOCK_DATA_DIR", "data/mock")

settings = Settings()
