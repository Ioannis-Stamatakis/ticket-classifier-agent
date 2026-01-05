"""Application configuration management."""
import os
from dataclasses import dataclass
from urllib.parse import quote_plus
from dotenv import load_dotenv


@dataclass
class Settings:
    """Application settings loaded from environment variables."""
    gemini_api_key: str
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from environment variables."""
        load_dotenv()

        # Validate required environment variables
        required_vars = [
            "GEMINI_API_KEY",
            "DB_HOST",
            "DB_PORT",
            "DB_NAME",
            "DB_USER",
            "DB_PASSWORD"
        ]

        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

        return cls(
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            db_host=os.getenv("DB_HOST"),
            db_port=int(os.getenv("DB_PORT", "5432")),
            db_name=os.getenv("DB_NAME"),
            db_user=os.getenv("DB_USER"),
            db_password=os.getenv("DB_PASSWORD")
        )

    @property
    def database_dsn(self) -> str:
        """Build PostgreSQL connection DSN with properly encoded credentials."""
        # URL-encode the username and password to handle special characters
        user = quote_plus(self.db_user)
        password = quote_plus(self.db_password)
        return f"postgresql://{user}:{password}@{self.db_host}:{self.db_port}/{self.db_name}"
