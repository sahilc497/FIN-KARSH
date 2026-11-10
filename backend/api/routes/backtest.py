from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.database.connection import get_db
from backend.database.models import BacktestRecord
from backend.backtesting.engine import BacktestingEngine

router = APIRouter(prefix="/backtest", tags=["Backtesting"])

class BacktestRunRequest(BaseModel):
    symbol: str = "RELIANCE.NS"
    initial_capital: float = 100000.0
    horizon_days: int = 5
    strategy: str = "threshold_filtered"
    fee_pct: float = 0.0005
    slippage_pct: float = 0.0005

@router.post("/run")
def execute_backtest(req: BacktestRunRequest, db: Session = Depends(get_db)):
    engine = BacktestingEngine(db)
    try:
        results = engine.run_backtest(
            symbol=req.symbol,
            initial_capital=req.initial_capital,
            horizon_days=req.horizon_days,
            strategy_type=req.strategy,
            fee_pct=req.fee_pct,
            slippage_pct=req.slippage_pct,
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/history")
def get_backtest_history(
    symbol: Optional[str] = None,
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    query = db.query(BacktestRecord).order_by(BacktestRecord.created_at.desc())
    if symbol:
        query = query.filter(BacktestRecord.stock_symbol == symbol)
    records = query.limit(limit).all()

    return [{
        "id": r.id,
        "symbol": r.stock_symbol,
        "strategy": r.strategy,
        "initial_capital": r.initial_capital,
        "final_equity": r.final_equity,
        "total_return_pct": r.total_return_pct,
        "benchmark_return_pct": r.benchmark_return_pct,
        "sharpe_ratio": r.sharpe_ratio,
        "sortino_ratio": r.sortino_ratio,
        "max_drawdown_pct": r.max_drawdown_pct,
        "win_rate_pct": r.win_rate_pct,
        "total_trades": r.total_trades,
        "created_at": r.created_at.isoformat(),
    } for r in records]

