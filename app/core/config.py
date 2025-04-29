from typing import List

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API information
    PROJECT_NAME: str = "OED Data API"
    DESCRIPTION: str = "API for accessing enzyme kinetic data from the OED database"
    VERSION: str = "0.1.0"
    
    # CORS configuration
    CORS_ORIGINS: List[str] = ["*"]
    
    # Database configuration
    OED_DB_USER: str
    OED_DB_PASSWORD: str
    OED_DB_HOST: str
    OED_DB_PORT: str = "5432"
    OED_DB_NAME: str = "oed_data"
    
    # Database connection string
    @property
    def DATABASE_URL(self) -> str:
        """Get database connection URL."""
        return f"postgresql+asyncpg://{self.OED_DB_USER}:{self.OED_DB_PASSWORD}@{self.OED_DB_HOST}:{self.OED_DB_PORT}/{self.OED_DB_NAME}"
    
    # Use model_config instead of class Config
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
    )


# Create settings instance
settings = Settings()