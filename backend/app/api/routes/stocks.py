from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.engine import get_db
from app.database.repositories import StockRepository, PriceRepository, FactorRepository
from app.database.schemas import StockResponse, PriceHistoryResponse, SentimentFactorResponse
from app.services.price_data import MarketDataService
from app.services.factor_builder import SentimentFactorBuilder

router = APIRouter(prefix="/stocks", tags=["Stocks & Market Data"])

@router.get("", response_model=List[StockResponse])
def list_stocks(active_only: bool = True, db: Session = Depends(get_db)):
    repo = StockRepository(db)
    return repo.get_all(active_only=active_only)

@router.get("/{symbol}", response_model=StockResponse)
def get_stock(symbol: str, db: Session = Depends(get_db)):
    repo = StockRepository(db)
    stock = repo.get_by_symbol(symbol)
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock '{symbol}' not found")
    return stock

@router.get("/{symbol}/prices", response_model=List[PriceHistoryResponse])
def get_stock_prices(
    symbol: str,
    limit: int = Query(180, ge=1, le=1000),
    sync_if_empty: bool = Query(True),
    db: Session = Depends(get_db),
):
    repo = StockRepository(db)
    stock = repo.get_by_symbol(symbol)
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock '{symbol}' not found")

    price_repo = PriceRepository(db)
    prices = price_repo.get_by_stock(stock.id, limit=limit)

    # Sync automatically if empty and requested
    if not prices and sync_if_empty:
        service = MarketDataService(db)
        service.fetch_and_calculate_indicators(stock.symbol)
        prices = price_repo.get_by_stock(stock.id, limit=limit)

    return prices

@router.get("/{symbol}/factors", response_model=List[SentimentFactorResponse])
def get_stock_sentiment_factors(
    symbol: str,
    limit: int = Query(180, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    repo = StockRepository(db)
    stock = repo.get_by_symbol(symbol)
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock '{symbol}' not found")

    factor_repo = FactorRepository(db)
    factors = factor_repo.get_by_stock(stock.id, limit=limit)
    return factors
