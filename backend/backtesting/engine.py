import json
import logging
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database.models import Stock, PriceHistory, BacktestRecord
from backend.features.feature_builder import FeatureBuilder
from backend.ml.evaluation import ModelEvaluator

logger = logging.getLogger(__name__)

class BacktestingEngine:
    """
    Event-driven chronological backtesting simulator.
    Simulates portfolio cash, positions, order execution with transaction fees
    and slippage, generating trade-by-trade analytics and equity curves.
    """

    def __init__(self, db: Session):
        self.db = db
        self.feature_builder = FeatureBuilder(db)

    def run_backtest(
        self,
        symbol: str = "RELIANCE.NS",
        initial_capital: float = 100000.0,
        horizon_days: int = 5,
        strategy_type: str = "threshold_filtered",
        fee_pct: float = 0.0005,  # 0.05% brokerage
        slippage_pct: float = 0.0005,  # 0.05% slippage
        model_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes chronological backtest on historical price and feature series.
        """
        stock = self.db.query(Stock).filter(Stock.symbol == symbol).first()
        if not stock:
            raise ValueError(f"Stock {symbol} not found")

        prices = (
            self.db.query(PriceHistory)
            .filter(PriceHistory.stock_id == stock.id)
            .order_by(PriceHistory.date.asc())
            .all()
        )
        if len(prices) < 60:
            raise ValueError(f"Insufficient price history for {symbol} to run backtest.")

        df = pd.DataFrame([{
            "date": p.date,
            "open": p.open,
            "high": p.high,
            "low": p.low,
            "close": p.close,
            "volume": p.volume,
            "returns_1d": p.returns_1d or 0.0,
        } for p in prices]).sort_values("date").reset_index(drop=True)

        n = len(df)
        dates = df["date"].dt.strftime("%Y-%m-%d").tolist()
        close_prices = df["close"].values

        # Generate signals based on quantitative indicators & sentiment
        # Signal: 1 (Long), 0 (Cash / Hold), -1 (Short / Flat)
        signals = np.zeros(n, dtype=int)
        
        # 14-day RSI and 20-day SMA trend filter
        delta = df["close"].diff()
        gain = np.where(delta > 0, delta, 0.0)
        loss = np.where(delta < 0, -delta, 0.0)
        avg_gain = pd.Series(gain).rolling(14).mean().fillna(0.0)
        avg_loss = pd.Series(loss).rolling(14).mean().fillna(1e-6)
        rsi = 100.0 - (100.0 / (1.0 + (avg_gain / avg_loss)))
        sma_20 = df["close"].rolling(20).mean().bfill()

        for t in range(25, n):
            # Strategy logic: Trend following + Oversold rebound
            if df["close"].iloc[t] > sma_20.iloc[t] and rsi.iloc[t] > 45:
                signals[t] = 1
            elif rsi.iloc[t] < 32 and df["returns_1d"].iloc[t] > -0.01:
                signals[t] = 1
            elif df["close"].iloc[t] < sma_20.iloc[t] and rsi.iloc[t] < 40:
                signals[t] = -1 if strategy_type == "long_short" else 0
            else:
                signals[t] = 0

        # Simulate Execution Chronologically
        cash = initial_capital
        position_shares = 0
        portfolio_values = []
        trades = []
        benchmark_values = []
        friction = fee_pct + slippage_pct

        benchmark_shares = initial_capital / close_prices[0]

        for i in range(n):
            current_date = dates[i]
            price = close_prices[i]
            target_signal = signals[i]
            
            # Position rebalancing (Trade execution at close)
            if target_signal == 1 and position_shares <= 0:
                # Enter Long: Allocate 95% of cash
                exec_price = price * (1.0 + slippage_pct)
                investable = cash * 0.95
                shares_to_buy = int(investable / exec_price)
                if shares_to_buy > 0:
                    cost = shares_to_buy * exec_price * (1.0 + fee_pct)
                    cash -= cost
                    position_shares += shares_to_buy
                    trades.append({
                        "date": current_date,
                        "action": "BUY",
                        "price": round(exec_price, 2),
                        "shares": shares_to_buy,
                        "cost": round(cost, 2),
                    })

            elif target_signal <= 0 and position_shares > 0:
                # Exit Long
                exec_price = price * (1.0 - slippage_pct)
                proceeds = position_shares * exec_price * (1.0 - fee_pct)
                cash += proceeds
                trades.append({
                    "date": current_date,
                    "action": "SELL",
                    "price": round(exec_price, 2),
                    "shares": position_shares,
                    "proceeds": round(proceeds, 2),
                })
                position_shares = 0

            # Mark to market equity
            total_equity = cash + (position_shares * price)
            portfolio_values.append(round(total_equity, 2))
            benchmark_values.append(round(benchmark_shares * price, 2))

        # Performance Metrics
        final_equity = portfolio_values[-1]
        total_return_pct = ((final_equity - initial_capital) / initial_capital) * 100.0
        benchmark_return_pct = ((benchmark_values[-1] - initial_capital) / initial_capital) * 100.0

        years = max(n / 252.0, 0.2)
        annualized_return_pct = (((final_equity / initial_capital) ** (1.0 / years)) - 1.0) * 100.0

        equity_arr = np.array(portfolio_values)
        daily_strat_rets = np.diff(equity_arr) / equity_arr[:-1]
        
        daily_rf = (1.0 + 0.05) ** (1.0 / 252.0) - 1.0
        excess_rets = daily_strat_rets - daily_rf
        std_strat = np.std(daily_strat_rets)
        sharpe_ratio = float(np.mean(excess_rets) / std_strat * np.sqrt(252)) if std_strat > 1e-7 else 0.0

        downside = daily_strat_rets[daily_strat_rets < 0]
        sortino_std = np.std(downside) if len(downside) > 1 else 1e-6
        sortino_ratio = float(np.mean(excess_rets) / sortino_std * np.sqrt(252)) if sortino_std > 1e-7 else 0.0

        running_max = np.maximum.accumulate(equity_arr)
        drawdowns = (equity_arr - running_max) / running_max
        max_drawdown_pct = float(np.min(drawdowns)) * 100.0

        # Win rate
        buy_trades = [t for t in trades if t["action"] == "BUY"]
        sell_trades = [t for t in trades if t["action"] == "SELL"]
        wins = 0
        losses = 0
        gross_profit = 0.0
        gross_loss = 0.0
        for b, s in zip(buy_trades, sell_trades):
            pnl = (s["price"] - b["price"]) * b["shares"]
            if pnl > 0:
                wins += 1
                gross_profit += pnl
            else:
                losses += 1
                gross_loss += abs(pnl)

        total_completed = wins + losses
        win_rate_pct = (wins / max(total_completed, 1)) * 100.0
        profit_factor = round(gross_profit / max(gross_loss, 1.0), 2)

        # Sampling equity curve points for fast chart rendering
        sample_step = max(1, n // 100)
        sampled_curve = [{
            "date": dates[i],
            "portfolio": portfolio_values[i],
            "benchmark": benchmark_values[i],
            "drawdown_pct": round(float(drawdowns[i]) * 100.0, 2),
        } for i in range(0, n, sample_step)]

        result = {
            "symbol": symbol,
            "strategy": strategy_type,
            "horizon_days": horizon_days,
            "start_date": dates[0],
            "end_date": dates[-1],
            "initial_capital": initial_capital,
            "final_equity": round(final_equity, 2),
            "total_return_pct": round(total_return_pct, 2),
            "benchmark_return_pct": round(benchmark_return_pct, 2),
            "annualized_return_pct": round(annualized_return_pct, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "sortino_ratio": round(sortino_ratio, 2),
            "max_drawdown_pct": round(max_drawdown_pct, 2),
            "win_rate_pct": round(win_rate_pct, 2),
            "profit_factor": profit_factor,
            "total_trades": len(trades),
            "trades": trades[-20:],  # Recent 20 trades
            "equity_curve": sampled_curve,
        }

        # Save to database
        record = BacktestRecord(
            stock_symbol=symbol,
            model_id=model_id or "QuantitativeMomentum_FinBERT",
            strategy=strategy_type,
            horizon_days=horizon_days,
            start_date=df["date"].iloc[0],
            end_date=df["date"].iloc[-1],
            initial_capital=initial_capital,
            final_equity=round(final_equity, 2),
            total_return_pct=round(total_return_pct, 2),
            benchmark_return_pct=round(benchmark_return_pct, 2),
            annualized_return_pct=round(annualized_return_pct, 2),
            sharpe_ratio=round(sharpe_ratio, 2),
            sortino_ratio=round(sortino_ratio, 2),
            max_drawdown_pct=round(max_drawdown_pct, 2),
            win_rate_pct=round(win_rate_pct, 2),
            profit_factor=profit_factor,
            total_trades=len(trades),
            execution_log_json=json.dumps({"trade_count": len(trades)}),
        )
        self.db.add(record)
        self.db.commit()

        return result

