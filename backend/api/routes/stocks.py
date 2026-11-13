from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.database.models import Stock, PriceHistory
from backend.features.technical_indicators import TechnicalIndicators
import pandas as pd

router = APIRouter(prefix="/stocks", tags=["Stocks"])

@router.get("/")
def list_stocks(
    db: Session = Depends(get_db),
    sector: Optional[str] = None
):
    query = db.query(Stock)
    if sector:
        query = query.filter(Stock.sector == sector)
    stocks = query.all()
    return [{
        "id": s.id,
        "symbol": s.symbol,
        "name": s.name,
        "sector": s.sector,
        "industry": s.industry,
        "exchange": s.exchange,
        "currency": s.currency,
        "market_cap": s.market_cap,
        "pe_ratio": s.pe_ratio,
        "pb_ratio": s.pb_ratio,
        "eps": s.eps,
        "dividend_yield": s.dividend_yield,
        "roe": s.roe,
        "debt_to_equity": s.debt_to_equity,
    } for s in stocks]

@router.get("/search")
def search_stock_universe(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Searches dynamically across NIFTY 50, Next 50, 100, 200, 500 and broader NSE equities."""
    from backend.collectors.stock_universe import StockUniverseManager
    manager = StockUniverseManager(db)
    return manager.search(q, limit=limit)

@router.post("/onboard/{symbol}")
def onboard_equity(symbol: str, db: Session = Depends(get_db)):
    """Dynamically onboards and ingests 3yr OHLCV data for any searched NSE ticker."""
    from backend.collectors.stock_universe import StockUniverseManager
    manager = StockUniverseManager(db)
    stock = manager.ensure_stock_onboarded(symbol)
    return {
        "status": "success",
        "symbol": stock.symbol,
        "name": stock.name,
        "sector": stock.sector,
        "exchange": stock.exchange,
    }

@router.get("/{symbol}")
def get_stock_detail(symbol: str, db: Session = Depends(get_db)):
    stock = db.query(Stock).filter(Stock.symbol == symbol).first()
    if not stock:
        from backend.collectors.stock_universe import StockUniverseManager
        manager = StockUniverseManager(db)
        # Check if symbol is in expanded universe
        if any(item["symbol"] == symbol for item in manager.catalog.values()):
            stock = manager.ensure_stock_onboarded(symbol)
        else:
            raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")

    latest_price = (
        db.query(PriceHistory)
        .filter(PriceHistory.stock_id == stock.id)
        .order_by(PriceHistory.date.desc())
        .first()
    )

    return {
        "symbol": stock.symbol,
        "name": stock.name,
        "sector": stock.sector,
        "industry": stock.industry,
        "market_cap": stock.market_cap,
        "pe_ratio": stock.pe_ratio,
        "pb_ratio": stock.pb_ratio,
        "eps": stock.eps,
        "dividend_yield": stock.dividend_yield,
        "roe": stock.roe,
        "debt_to_equity": stock.debt_to_equity,
        "current_price": latest_price.close if latest_price else None,
        "last_updated": latest_price.date.isoformat() if latest_price else None,
        "returns_1d": latest_price.returns_1d if latest_price else 0.0,
        "volatility_20d": latest_price.volatility_20d if latest_price else 0.015,
    }

@router.post("/sync-live")
def sync_live_prices(db: Session = Depends(get_db)):
    """Fetches latest prices from Yahoo Finance if online, or ensures calibrated realistic prices matching Groww/NSE."""
    from backend.collectors.yahoo_finance import YahooFinanceCollector
    yf_collector = YahooFinanceCollector(db)
    stocks = yf_collector.sync_supported_stocks()
    synced = []
    for s in stocks:
        try:
            df = yf_collector.fetch_historical_ohlcv(s.symbol)
            yf_collector.save_ohlcv_to_db(s.symbol, df, overwrite=True)
            lp = db.query(PriceHistory).filter(PriceHistory.stock_id == s.id).order_by(PriceHistory.date.desc()).first()
            synced.append({"symbol": s.symbol, "latest_price": lp.close if lp else None})
        except Exception:
            continue
    return {"status": "success", "synced_stocks": len(synced), "quotes": synced}


@router.get("/{symbol}/ohlcv")
def get_historical_ohlcv(
    symbol: str,
    limit: int = Query(default=180, ge=10, le=1000),
    db: Session = Depends(get_db)
):
    stock = db.query(Stock).filter(Stock.symbol == symbol).first()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")

    prices = (
        db.query(PriceHistory)
        .filter(PriceHistory.stock_id == stock.id)
        .order_by(PriceHistory.date.desc())
        .limit(limit)
        .all()
    )
    # Reverse to chronological order
    prices = list(reversed(prices))

    return [{
        "date": p.date.strftime("%Y-%m-%d"),
        "open": p.open,
        "high": p.high,
        "low": p.low,
        "close": p.close,
        "adj_close": p.adj_close,
        "volume": p.volume,
        "returns_1d": round(float(p.returns_1d or 0.0) * 100.0, 2),
    } for p in prices]

