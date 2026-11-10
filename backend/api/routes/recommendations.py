from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.database.connection import get_db
from backend.database.models import Stock, WatchlistItem
from backend.ml.prediction import PredictionService

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

class WatchlistAddRequest(BaseModel):
    symbol: str
    target_price: Optional[float] = None
    notes: Optional[str] = None

@router.get("/")
def get_all_recommendations(
    horizon_days: int = Query(default=5),
    db: Session = Depends(get_db)
):
    """Returns multi-factor ranking and analytical signals across all tracked stocks."""
    stocks = db.query(Stock).filter(Stock.symbol != "^NSEI").all()
    pred_service = PredictionService(db)
    recommendations = []

    for stock in stocks:
        try:
            rec = pred_service.get_latest_recommendation(stock.symbol, horizon_days=horizon_days)
            recommendations.append(rec)
        except Exception as e:
            continue

    recommendations.sort(key=lambda x: x["composite_score"], reverse=True)
    return recommendations

@router.get("/{symbol}")
def get_stock_recommendation(
    symbol: str,
    horizon_days: int = Query(default=5),
    db: Session = Depends(get_db)
):
    from backend.collectors.stock_universe import StockUniverseManager
    manager = StockUniverseManager(db)
    # Ensure stock is onboarded if in universe
    stock = db.query(Stock).filter(Stock.symbol == symbol).first()
    if not stock and any(item["symbol"] == symbol for item in manager.catalog.values()):
        manager.ensure_stock_onboarded(symbol)

    pred_service = PredictionService(db)
    try:
        return pred_service.get_latest_recommendation(symbol, horizon_days=horizon_days)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/watchlist/all")
def get_watchlist(db: Session = Depends(get_db)):
    items = db.query(WatchlistItem).all()
    pred_service = PredictionService(db)
    result = []
    for item in items:
        try:
            rec = pred_service.get_latest_recommendation(item.symbol)
            result.append({
                "watchlist_id": item.id,
                "target_price": item.target_price,
                "notes": item.notes,
                "added_at": item.added_at.isoformat(),
                **rec
            })
        except Exception:
            continue
    return result

@router.post("/watchlist/add")
def add_to_watchlist(req: WatchlistAddRequest, db: Session = Depends(get_db)):
    stock = db.query(Stock).filter(Stock.symbol == req.symbol).first()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {req.symbol} not found")

    existing = db.query(WatchlistItem).filter(WatchlistItem.symbol == req.symbol).first()
    if existing:
        existing.target_price = req.target_price
        existing.notes = req.notes
        db.commit()
        return {"status": "updated", "symbol": req.symbol}

    item = WatchlistItem(
        symbol=req.symbol,
        target_price=req.target_price,
        notes=req.notes
    )
    db.add(item)
    db.commit()
    return {"status": "added", "symbol": req.symbol}

@router.delete("/watchlist/{symbol}")
def remove_from_watchlist(symbol: str, db: Session = Depends(get_db)):
    item = db.query(WatchlistItem).filter(WatchlistItem.symbol == symbol).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not in watchlist")
    db.delete(item)
    db.commit()
    return {"status": "removed", "symbol": symbol}

