import os
from pathlib import Path
from typing import List, Any
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "SENTIMENT-APLHA"
    VERSION: str = "2.0.0"
    API_PREFIX: str = "/api"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Directory paths
    ROOT_DIR: Path = Path(__file__).resolve().parent.parent
    BACKEND_DIR: Path = ROOT_DIR / "backend"
    MODELS_DIR: Path = ROOT_DIR / "models" / "trained"
    DATASETS_DIR: Path = ROOT_DIR / "datasets"
    
    # Database (SQLite by default, seamlessly switchable to PostgreSQL)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", f"sqlite:///{ROOT_DIR / 'sentiment_alpha.db'}"
    )
    
    # FinBERT Settings
    FINBERT_MODEL_NAME: str = "ProsusAI/finbert"
    FINBERT_DEVICE: str = os.getenv("FINBERT_DEVICE", "cpu")
    FINBERT_BATCH_SIZE: int = int(os.getenv("FINBERT_BATCH_SIZE", "16"))
    FINBERT_MAX_LENGTH: int = int(os.getenv("FINBERT_MAX_LENGTH", "256"))
    FINBERT_OFFLINE: bool = os.getenv("FINBERT_OFFLINE", "False").lower() in ("true", "1")
    LIGHTWEIGHT_MODE: bool = os.getenv("LIGHTWEIGHT_MODE", "False").lower() in ("true", "1")
    
    # Gemini API Settings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    
    # Reddit PRAW Settings
    REDDIT_CLIENT_ID: str = os.getenv("REDDIT_CLIENT_ID", "")
    REDDIT_CLIENT_SECRET: str = os.getenv("REDDIT_CLIENT_SECRET", "")
    REDDIT_USER_AGENT: str = os.getenv("REDDIT_USER_AGENT", "SentimentAlpha/2.0")
    
    # Ingestion & Feeds
    NEWS_REQUEST_TIMEOUT: int = int(os.getenv("NEWS_REQUEST_TIMEOUT", "15"))
    MAX_ARTICLES_PER_FEED: int = int(os.getenv("MAX_ARTICLES_PER_FEED", "50"))
    
    # ML & Backtesting Defaults
    DEFAULT_HORIZONS: Any = [1, 5, 10]  # 1-day, 5-day, 10-day forward predictions
    NEUTRAL_RETURN_THRESHOLD: float = 0.003  # +/- 0.3% returns classified as neutral
    TRANSACTION_FEE_PCT: float = 0.0005  # 0.05% brokerage / fees
    SLIPPAGE_PCT: float = 0.0005  # 0.05% slippage
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ]

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()

# Ensure directories exist
settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)
(settings.DATASETS_DIR / "raw").mkdir(parents=True, exist_ok=True)
(settings.DATASETS_DIR / "processed").mkdir(parents=True, exist_ok=True)
