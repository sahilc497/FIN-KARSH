from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.database.connection import get_db
from backend.portfolio.simulator import PortfolioSimulator

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])

class AllocationItem(BaseModel):
    symbol: str
    weight: float = Field(..., ge=0.01, le=1.0)

class PortfolioSimRequest(BaseModel):
    capital: float = Field(default=100000.0, ge=1000.0)
    allocations: List[AllocationItem]
    horizon_days: int = Field(default=30, ge=1, le=252)

@router.post("/simulate")
def simulate_portfolio(req: PortfolioSimRequest, db: Session = Depends(get_db)):
    simulator = PortfolioSimulator(db)
    alloc_dicts = [{"symbol": a.symbol, "weight": a.weight} for a in req.allocations]
    try:
        results = simulator.simulate(
            capital=req.capital,
            allocations=alloc_dicts,
            horizon_days=req.horizon_days,
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

