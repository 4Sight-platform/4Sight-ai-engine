"""
API Configuration Settings
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""
    
    API_V1_STR: str = "/api/v1"
    
    # Use simple strings for CORS origins to avoid Pydantic validation issues
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://localhost:8001",
        "https://localhost:3000",
        "https://localhost:5173",
        "https://localhost:8000",
        "https://localhost:8001",
    ]
    
    
    PROJECT_NAME: str = "4Sight AI Engine"
    
    model_config = SettingsConfigDict(case_sensitive=True)


settings = Settings()
