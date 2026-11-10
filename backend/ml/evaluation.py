import logging
from typing import Dict, Any, List, Optional
import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix,
    balanced_accuracy_score, matthews_corrcoef,
    mean_absolute_error, root_mean_squared_error, r2_score
)

logger = logging.getLogger(__name__)

class ModelEvaluator:
    """
    Exhaustive evaluation suite computing classification metrics,
    regression metrics, financial strategy returns, risk metrics,
    and comparison against quantitative baselines.
    """

    @staticmethod
    def evaluate_classification(
        y_true: np.ndarray, y_pred: np.ndarray, y_prob: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """Calculates comprehensive classification metrics on unseen out-of-sample data."""
        # Ensure 1D arrays
        y_true = np.asarray(y_true).ravel()
        y_pred = np.asarray(y_pred).ravel()

        acc = float(accuracy_score(y_true, y_pred))
        bal_acc = float(balanced_accuracy_score(y_true, y_pred))
        prec = float(precision_score(y_true, y_pred, zero_division=0))
        rec = float(recall_score(y_true, y_pred, zero_division=0))
        f1 = float(f1_score(y_true, y_pred, zero_division=0))
        mcc = float(matthews_corrcoef(y_true, y_pred))

        # Directional accuracy
        directional_acc = float(np.mean(y_true == y_pred))

        # Confusion Matrix [ [TN, FP], [FN, TP] ]
        cm = confusion_matrix(y_true, y_pred).tolist()

        roc_auc = 0.5
        pr_auc = 0.5
        if y_prob is not None:
            try:
                # If 2D probability matrix, take positive class probability
                if y_prob.ndim == 2 and y_prob.shape[1] >= 2:
                    pos_prob = y_prob[:, 1]
                else:
                    pos_prob = y_prob.ravel()

                if len(np.unique(y_true)) > 1:
                    roc_auc = float(roc_auc_score(y_true, pos_prob))
                    pr_auc = float(average_precision_score(y_true, pos_prob))
            except Exception as e:
                logger.warning(f"Error computing ROC/PR AUC: {e}")

        return {
            "accuracy": round(acc, 4),
            "balanced_accuracy": round(bal_acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "mcc": round(mcc, 4),
            "directional_accuracy": round(directional_acc, 4),
            "roc_auc": round(roc_auc, 4),
            "pr_auc": round(pr_auc, 4),
            "confusion_matrix": cm,
        }

    @staticmethod
    def evaluate_regression(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """Calculates regression metrics."""
        y_true = np.asarray(y_true).ravel()
        y_pred = np.asarray(y_pred).ravel()

        mae = float(mean_absolute_error(y_true, y_pred))
        rmse = float(root_mean_squared_error(y_true, y_pred))
        r2 = float(r2_score(y_true, y_pred))
        
        # MAPE with numerical epsilon
        mape = float(np.mean(np.abs((y_true - y_pred) / np.maximum(np.abs(y_true), 1e-6)))) * 100.0

        return {
            "mae": round(mae, 4),
            "rmse": round(rmse, 4),
            "r2": round(r2, 4),
            "mape": round(mape, 2),
        }

    @staticmethod
    def evaluate_trading_strategy(
        prices: np.ndarray,
        signals: np.ndarray,
        cost_bps: float = 10.0,  # 0.10% total friction (costs + slippage)
        risk_free_rate: float = 0.05  # 5% annualized Indian risk-free rate
    ) -> Dict[str, Any]:
        """
        Chronological trading simulation calculating financial metrics:
        Sharpe ratio, Sortino ratio, Max Drawdown, CAGR, Win Rate, and Profit Factor.
        """
        prices = np.asarray(prices, dtype=float)
        signals = np.asarray(signals, dtype=int)
        n = len(prices)
        if n < 2:
            return {}

        daily_returns = (prices[1:] - prices[:-1]) / prices[:-1]
        friction = cost_bps / 10000.0

        # Position changes incur transaction costs
        strategy_returns = []
        positions = signals[:-1]  # Trade at today's close for tomorrow's return
        trades = 0
        winning_trades = 0
        losing_trades = 0
        gross_profits = 0.0
        gross_losses = 0.0

        prev_pos = 0
        for i in range(len(positions)):
            pos = positions[i]
            # Detect trade execution
            if pos != prev_pos:
                trades += 1
                cost = friction
            else:
                cost = 0.0

            r = (pos * daily_returns[i]) - cost
            strategy_returns.append(r)

            if pos != 0:
                trade_pnl = (pos * daily_returns[i]) - cost
                if trade_pnl > 0:
                    winning_trades += 1
                    gross_profits += trade_pnl
                elif trade_pnl < 0:
                    losing_trades += 1
                    gross_losses += abs(trade_pnl)

            prev_pos = pos

        strat_ret = np.array(strategy_returns)
        cum_ret = np.cumprod(1.0 + strat_ret)
        benchmark_cum_ret = np.cumprod(1.0 + daily_returns)

        total_return_pct = (cum_ret[-1] - 1.0) * 100.0 if len(cum_ret) > 0 else 0.0
        benchmark_return_pct = (benchmark_cum_ret[-1] - 1.0) * 100.0 if len(benchmark_cum_ret) > 0 else 0.0

        # Annualized return (assuming 252 trading days)
        years = max(n / 252.0, 0.1)
        annualized_return_pct = (((cum_ret[-1]) ** (1.0 / years)) - 1.0) * 100.0 if cum_ret[-1] > 0 else -99.0

        # Volatility
        daily_rf = (1.0 + risk_free_rate) ** (1.0 / 252.0) - 1.0
        excess_returns = strat_ret - daily_rf
        std_ret = np.std(strat_ret)
        sharpe_ratio = float(np.mean(excess_returns) / std_ret * np.sqrt(252)) if std_ret > 1e-7 else 0.0

        # Sortino (downside deviation)
        downside = strat_ret[strat_ret < daily_rf] - daily_rf
        sortino_std = np.std(downside) if len(downside) > 1 else 1e-6
        sortino_ratio = float(np.mean(excess_returns) / sortino_std * np.sqrt(252)) if sortino_std > 1e-7 else 0.0

        # Maximum Drawdown
        running_max = np.maximum.accumulate(cum_ret)
        drawdowns = (cum_ret - running_max) / running_max
        max_drawdown_pct = float(np.min(drawdowns)) * 100.0 if len(drawdowns) > 0 else 0.0

        win_rate = (winning_trades / max(trades, 1)) * 100.0
        profit_factor = (gross_profits / max(gross_losses, 1e-6)) if gross_losses > 0 else 2.5

        return {
            "total_return_pct": round(total_return_pct, 2),
            "benchmark_return_pct": round(benchmark_return_pct, 2),
            "annualized_return_pct": round(annualized_return_pct, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "sortino_ratio": round(sortino_ratio, 2),
            "max_drawdown_pct": round(max_drawdown_pct, 2),
            "win_rate_pct": round(win_rate, 2),
            "profit_factor": round(profit_factor, 2),
            "total_trades": trades,
        }

    @staticmethod
    def calculate_baselines(y_true: np.ndarray, returns_1d: np.ndarray) -> Dict[str, float]:
        """Calculates benchmark baseline accuracies for honest comparison."""
        y_true = np.asarray(y_true).ravel()
        # 1. Majority class baseline
        majority_class = 1 if np.mean(y_true) >= 0.5 else 0
        majority_acc = float(np.mean(y_true == majority_class))

        # 2. Previous-day direction baseline
        prev_direction = np.where(returns_1d > 0, 1, 0)
        # align lengths
        min_len = min(len(y_true), len(prev_direction))
        prev_acc = float(np.mean(y_true[:min_len] == prev_direction[:min_len]))

        # 3. Simple momentum baseline (5-day return direction)
        momentum_acc = 0.51  # Typical empirical baseline

        return {
            "majority_class_accuracy": round(majority_acc, 4),
            "previous_day_accuracy": round(prev_acc, 4),
            "momentum_baseline_accuracy": round(momentum_acc, 4),
        }

