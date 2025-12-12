from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    # Application
    PROJECT_NAME: str = "Talent Connect API"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production-please"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///backend/talent_connect.db"
    
    # AI APIs
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    
    # File Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:6173",
        "http://127.0.0.1:6173",
        "http://localhost:6174",
        "http://127.0.0.1:6174",
        "http://localhost:6175",
        "http://127.0.0.1:6175",
    ]
    
    # Demo Accounts
    ENABLE_DEMO_ACCOUNTS: bool = True
    
    model_config = ConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


settings = Settings()
