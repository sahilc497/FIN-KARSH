import logging
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from backend.database.models import Stock, PriceHistory

logger = logging.getLogger(__name__)

class PortfolioSimulator:
    """
    Multi-asset hypothetical portfolio simulator computing historical metrics,
    covariance matrices, diversification indices, and Monte Carlo scenario projections
    (1-day, 5-day, 10-day, 30-day horizons) with Expected, Optimistic, and Pessimistic paths.
    """

    def __init__(self, db: Session):
        self.db = db

    def simulate(
        self,
        capital: float = 100000.0,
        allocations: Optional[List[Dict[str, Any]]] = None,
        horizon_days: int = 30
    ) -> Dict[str, Any]:
        """
        Simulates portfolio risk, diversification, and Monte Carlo forward scenarios.
        allocations format: [{'symbol': 'RELIANCE.NS', 'weight': 0.4}, {'symbol': 'TCS.NS', 'weight': 0.6}]
        """
        if not allocations:
            allocations = [
                {"symbol": "RELIANCE.NS", "weight": 0.35},
                {"symbol": "TCS.NS", "weight": 0.35},
                {"symbol": "HDFCBANK.NS", "weight": 0.30},
            ]

        # Normalize weights
        total_weight = sum(item["weight"] for item in allocations)
        for item in allocations:
            item["weight"] = item["weight"] / total_weight

        symbols = [item["symbol"] for item in allocations]
        weights = np.array([item["weight"] for item in allocations])

        # Fetch price histories
        price_series = {}
        sectors = {}
        for sym in symbols:
            stock = self.db.query(Stock).filter(Stock.symbol == sym).first()
            if not stock:
                continue
            sectors[sym] = stock.sector or "Diversified"
            recs = (
                self.db.query(PriceHistory.date, PriceHistory.close)
                .filter(PriceHistory.stock_id == stock.id)
                .order_by(PriceHistory.date.asc())
                .all()
            )
            if recs:
                df = pd.DataFrame(recs, columns=["date", "close"])
                df["return_1d"] = df["close"].pct_change()
                price_series[sym] = df.set_index("date")["return_1d"].dropna()

        if not price_series:
            raise ValueError("No price history found for specified stocks.")

        # Combined returns dataframe
        returns_df = pd.DataFrame(price_series).dropna()
        if returns_df.empty:
            raise ValueError("Insufficient overlapping price dates.")

        # Align weights with available symbols in returns_df
        active_symbols = list(returns_df.columns)
        active_weights = np.array([item["weight"] for item in allocations if item["symbol"] in active_symbols])
        active_weights = active_weights / np.sum(active_weights)

        # Historical Portfolio Metrics
        daily_portfolio_returns = returns_df.dot(active_weights)
        mean_daily_return = float(daily_portfolio_returns.mean())
        daily_volatility = float(daily_portfolio_returns.std())

        annualized_return = ((1.0 + mean_daily_return) ** 252 - 1.0) * 100.0
        annualized_volatility = daily_volatility * np.sqrt(252) * 100.0

        daily_rf = (1.0 + 0.05) ** (1.0 / 252.0) - 1.0
        excess = daily_portfolio_returns - daily_rf
        sharpe = float(excess.mean() / (daily_volatility + 1e-9) * np.sqrt(252))

        # Max Drawdown
        cum_ret = (1.0 + daily_portfolio_returns).cumprod()
        running_max = np.maximum.accumulate(cum_ret)
        drawdowns = (cum_ret - running_max) / running_max
        max_drawdown = float(drawdowns.min()) * 100.0

        # Diversification Index (Herfindahl-Hirschman Index: Lower is more diversified)
        hhi = float(np.sum(active_weights ** 2))
        diversification_score = round(float((1.0 - hhi) * 100.0), 1)  # 0 to 100

        # Sector Breakdown
        sector_alloc = {}
        for sym, w in zip(active_symbols, active_weights):
            sec = sectors.get(sym, "Other")
            sector_alloc[sec] = sector_alloc.get(sec, 0.0) + w
        sector_breakdown = [{"sector": k, "weight": round(v * 100.0, 1)} for k, v in sector_alloc.items()]

        # Monte Carlo Scenario Simulation over horizon_days
        num_simulations = 500
        rng = np.random.RandomState(42)
        
        simulated_paths = np.zeros((num_simulations, horizon_days + 1))
        simulated_paths[:, 0] = capital

        for t in range(1, horizon_days + 1):
            random_shocks = rng.normal(mean_daily_return, daily_volatility, size=num_simulations)
            simulated_paths[:, t] = simulated_paths[:, t - 1] * (1.0 + random_shocks)

        # Percentile paths
        expected_path = np.mean(simulated_paths, axis=0)
        optimistic_path = np.percentile(simulated_paths, 95, axis=0)  # 95th percentile
        pessimistic_path = np.percentile(simulated_paths, 5, axis=0)   # 5th percentile

        scenario_chart = [{
            "day": d,
            "expected": round(float(expected_path[d]), 2),
            "optimistic": round(float(optimistic_path[d]), 2),
            "pessimistic": round(float(pessimistic_path[d]), 2),
        } for d in range(horizon_days + 1)]

        return {
            "initial_capital": capital,
            "horizon_days": horizon_days,
            "annualized_return_pct": round(annualized_return, 2),
            "annualized_volatility_pct": round(annualized_volatility, 2),
            "sharpe_ratio": round(sharpe, 2),
            "max_drawdown_pct": round(max_drawdown, 2),
            "diversification_score": diversification_score,
            "allocations": [{
                "symbol": sym,
                "weight_pct": round(float(w) * 100.0, 1),
                "allocated_amount": round(float(w) * capital, 2),
                "sector": sectors.get(sym, "General"),
            } for sym, w in zip(active_symbols, active_weights)],
            "sector_breakdown": sector_breakdown,
            "scenario_projections": scenario_chart,
            "projected_outcomes": {
                "expected_final": round(float(expected_path[-1]), 2),
                "optimistic_final": round(float(optimistic_path[-1]), 2),
                "pessimistic_final": round(float(pessimistic_path[-1]), 2),
            }
        }

