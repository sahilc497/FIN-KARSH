import pytest
from backend.database.connection import SessionLocal
from backend.backtesting.engine import BacktestingEngine

def test_backtesting_simulation():
    db = SessionLocal()
    try:
        engine = BacktestingEngine(db)
        res = engine.run_backtest(
            symbol="RELIANCE.NS",
            initial_capital=100000.0,
            horizon_days=5,
            strategy_type="threshold_filtered"
        )
        assert res["final_equity"] > 0
        assert "equity_curve" in res
        assert len(res["equity_curve"]) > 0
        assert "sharpe_ratio" in res
        assert "win_rate_pct" in res
    finally:
        db.close()

