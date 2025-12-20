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
    
    # Google Gemini API (for keyword generation)
    GEMINI_API_KEY: str = "YOUR_GEMINI_API_KEY"
    
    # Google OAuth Settings (Add actual values in .env or environment variables)
    GOOGLE_CLIENT_ID: str = "YOUR_GOOGLE_CLIENT_ID"
    GOOGLE_CLIENT_SECRET: str = "YOUR_GOOGLE_CLIENT_SECRET"
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/oauth/callback"
    
    # Encryption key for token storage (Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    ENCRYPTION_KEY: str = "YOUR_FERNET_ENCRYPTION_KEY"
    
    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env")


settings = Settings()

