import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Defaults
    DEFAULT_CITY_DOCS: int = 200
    DEFAULT_REDDIT_PAGES: int = 5
    DEFAULT_REDDIT_COMMENTS: int = 50
    
    class Config:
        env_file = ".env"

settings = Settings()
