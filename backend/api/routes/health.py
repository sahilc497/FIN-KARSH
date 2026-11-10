import os
import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database.connection import get_db
from backend.database.models import Stock, PriceHistory, MLModelRecord, NewsArticle
from backend.config import settings

router = APIRouter(prefix="/health", tags=["Health & System"])

@router.get("/")
def system_health_status(db: Session = Depends(get_db)):
    stock_count = db.query(Stock).count()
    price_count = db.query(PriceHistory).count()
    news_count = db.query(NewsArticle).count()
    model_count = db.query(MLModelRecord).count()

    latest_price = db.query(PriceHistory).order_by(PriceHistory.date.desc()).first()

    return {
        "status": "healthy",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "market_data_status": "Simulated / Cached Real Feed (15-min delayed when live)",
        "last_market_session": latest_price.date.strftime("%Y-%m-%d") if latest_price else "No data",
        "counts": {
            "stocks": stock_count,
            "price_records": price_count,
            "news_articles": news_count,
            "trained_models": model_count,
        },
        "environment": {
            "project_name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "finbert_device": settings.FINBERT_DEVICE,
            "finbert_offline": settings.FINBERT_OFFLINE,
            "database_url": settings.DATABASE_URL.split("///")[-1],
        }
    }

