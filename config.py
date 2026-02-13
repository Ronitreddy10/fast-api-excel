"""
Database configuration settings.
Fill in your actual SQL Server credentials here.
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file"""
    
    # Database connection settings
    DB_SERVER: str = os.getenv("DB_SERVER", "your_server_here")
    DB_NAME: str = os.getenv("DB_NAME", "CCTPROD11.0_Analytics")
    DB_USER: str = os.getenv("DB_USER", "your_username_here")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "your_password_here")
    
    # Optional: If using Windows Authentication, set this to True
    USE_WINDOWS_AUTH: bool = os.getenv("USE_WINDOWS_AUTH", "false").lower() == "true"
    
    # Query safety limits (set to 0 for unlimited)
    MAX_ROWS: int = int(os.getenv("MAX_ROWS", "0"))  # 0 = no limit
    QUERY_TIMEOUT: int = int(os.getenv("QUERY_TIMEOUT", "300"))  # 5 minutes for large queries
    
    @property
    def connection_string(self) -> str:
        """Generate ODBC connection string for SQL Server"""
        if self.USE_WINDOWS_AUTH:
            return (
                f"DRIVER={{ODBC Driver 18 for SQL Server}};"
                f"SERVER={self.DB_SERVER};"
                f"DATABASE={self.DB_NAME};"
                f"Trusted_Connection=yes;"
                f"ApplicationIntent=ReadOnly;"
                f"TrustServerCertificate=yes;"
            )
        else:
            return (
                f"DRIVER={{ODBC Driver 18 for SQL Server}};"
                f"SERVER={self.DB_SERVER};"
                f"DATABASE={self.DB_NAME};"
                f"UID={self.DB_USER};"
                f"PWD={self.DB_PASSWORD};"
                f"ApplicationIntent=ReadOnly;"
                f"TrustServerCertificate=yes;"
            )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
