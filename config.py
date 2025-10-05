from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./knowledge_graph.db"
    
    # File Upload
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # LLM Configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "tinyllama"  # Options: tinyllama, phi, llama3.2
    OLLAMA_TIMEOUT: int = 120  # seconds
    USE_OLLAMA: bool = True  # Set to False to always use fallback extraction
    
    # OpenAI Configuration (Alternative to Ollama)
    USE_OPENAI: bool = False  # Set to True to use OpenAI instead
    OPENAI_API_KEY: Optional[str] = None
    
    # Alternative: OpenAI API
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    
    # App Configuration
    APP_NAME: str = "Knowledge Graph Builder"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()