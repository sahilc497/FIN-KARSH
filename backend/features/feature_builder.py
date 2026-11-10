import logging
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from backend.database.models import Stock, PriceHistory, DailySentiment
from backend.features.technical_indicators import TechnicalIndicators
from backend.config import settings

logger = logging.getLogger(__name__)

class FeatureBuilder:
    """
    Constructs leak-free feature matrices combining technical indicators,
    price/volume dynamics, fundamental metrics, FinBERT sentiment signals,
    and market benchmark context.
    """

    def __init__(self, db: Session):
        self.db = db

    def build_dataset_for_stock(
        self, symbol: str, horizon_days: int = 5
    ) -> Tuple[pd.DataFrame, pd.Series, pd.Series, List[str]]:
        """
        Builds feature matrix X and targets y_class, y_reg for a stock.
        Returns (X, y_class, y_reg, feature_names).
        """
        stock = self.db.query(Stock).filter(Stock.symbol == symbol).first()
        if not stock:
            raise ValueError(f"Stock {symbol} not found in database.")

        # Load price history
        prices = (
            self.db.query(PriceHistory)
            .filter(PriceHistory.stock_id == stock.id)
            .order_by(PriceHistory.date.asc())
            .all()
        )
        if len(prices) < 60:
            raise ValueError(f"Insufficient historical prices for {symbol} ({len(prices)} rows, minimum 60 required)")

        df = pd.DataFrame([{
            "date": p.date,
            "open": p.open,
            "high": p.high,
            "low": p.low,
            "close": p.close,
            "adj_close": p.adj_close,
            "volume": p.volume,
        } for p in prices]).sort_values("date").reset_index(drop=True)

        # 1. Technical Indicators
        df["rsi_14"] = TechnicalIndicators.calculate_rsi(df["close"], period=14)
        
        macd_df = TechnicalIndicators.calculate_macd(df["close"])
        df["macd"] = macd_df["macd"]
        df["macd_signal"] = macd_df["macd_signal"]
        df["macd_hist"] = macd_df["macd_hist"]

        df["ema_9"] = TechnicalIndicators.calculate_ema(df["close"], span=9)
        df["ema_20"] = TechnicalIndicators.calculate_ema(df["close"], span=20)
        df["ema_50"] = TechnicalIndicators.calculate_ema(df["close"], span=50)
        df["ema_200"] = TechnicalIndicators.calculate_ema(df["close"], span=200)

        df["sma_20"] = TechnicalIndicators.calculate_sma(df["close"], window=20)
        df["sma_50"] = TechnicalIndicators.calculate_sma(df["close"], window=50)
        df["sma_200"] = TechnicalIndicators.calculate_sma(df["close"], window=200)

        # Distances to Moving Averages (stationary features)
        df["dist_ema_20"] = (df["close"] - df["ema_20"]) / np.maximum(df["ema_20"], 1e-9)
        df["dist_sma_50"] = (df["close"] - df["sma_50"]) / np.maximum(df["sma_50"], 1e-9)
        df["dist_sma_200"] = (df["close"] - df["sma_200"]) / np.maximum(df["sma_200"], 1e-9)

        bb_df = TechnicalIndicators.calculate_bollinger_bands(df["close"])
        df["bb_bandwidth"] = bb_df["bb_bandwidth"]
        df["bb_percent_b"] = bb_df["bb_percent_b"]

        df["atr_14"] = TechnicalIndicators.calculate_atr(df["high"], df["low"], df["close"], period=14)
        df["norm_atr"] = df["atr_14"] / np.maximum(df["close"], 1e-9)

        adx_df = TechnicalIndicators.calculate_adx(df["high"], df["low"], df["close"])
        df["adx"] = adx_df["adx"]
        df["plus_di"] = adx_df["plus_di"]
        df["minus_di"] = adx_df["minus_di"]

        stoch_df = TechnicalIndicators.calculate_stochastic(df["high"], df["low"], df["close"])
        df["stoch_k"] = stoch_df["stoch_k"]
        df["stoch_d"] = stoch_df["stoch_d"]

        df["obv"] = TechnicalIndicators.calculate_obv(df["close"], df["volume"])
        df["obv_slope_5"] = (df["obv"] - df["obv"].shift(5)) / np.maximum(df["obv"].shift(5).abs(), 1.0)

        df["vwap_20"] = TechnicalIndicators.calculate_vwap(df["high"], df["low"], df["close"], df["volume"])
        df["dist_vwap"] = (df["close"] - df["vwap_20"]) / np.maximum(df["vwap_20"], 1e-9)

        # 2. Price and Volume Features
        df["return_1d"] = df["close"].pct_change().fillna(0.0)
        df["log_return_1d"] = np.log(df["close"] / df["close"].shift(1)).fillna(0.0)
        df["return_5d"] = df["close"].pct_change(periods=5).fillna(0.0)
        df["return_10d"] = df["close"].pct_change(periods=10).fillna(0.0)
        df["return_20d"] = df["close"].pct_change(periods=20).fillna(0.0)

        df["volatility_10d"] = df["return_1d"].rolling(10).std().fillna(0.01)
        df["volatility_20d"] = df["return_1d"].rolling(20).std().fillna(0.015)
        df["volatility_50d"] = df["return_1d"].rolling(50).std().fillna(0.02)

        df["vol_sma_20"] = df["volume"].rolling(20).mean()
        df["volume_ratio_20"] = df["volume"] / np.maximum(df["vol_sma_20"], 1.0)
        df["volume_change_1d"] = df["volume"].pct_change().fillna(0.0).clip(-2.0, 5.0)

        df["price_gap"] = (df["open"] - df["close"].shift(1)) / np.maximum(df["close"].shift(1), 1e-9)
        df["high_20d_ratio"] = df["close"] / np.maximum(df["high"].rolling(20).max(), 1e-9)
        df["low_20d_ratio"] = df["close"] / np.maximum(df["low"].rolling(20).min(), 1e-9)

        # 3. Fundamental Features (point-in-time)
        df["pe_ratio"] = float(stock.pe_ratio or 20.0)
        df["pb_ratio"] = float(stock.pb_ratio or 3.0)
        df["eps"] = float(stock.eps or 50.0)
        df["dividend_yield"] = float(stock.dividend_yield or 1.0)
        df["roe"] = float(stock.roe or 15.0)
        df["debt_to_equity"] = float(stock.debt_to_equity or 0.5)

        # 4. Sentiment Features
        sent_records = (
            self.db.query(DailySentiment)
            .filter(DailySentiment.stock_id == stock.id)
            .all()
        )
        if sent_records:
            sent_df = pd.DataFrame([{
                "date": s.date,
                "news_sentiment": s.news_sentiment,
                "reddit_sentiment": s.reddit_sentiment,
                "combined_sentiment": s.combined_sentiment,
                "sentiment_momentum": s.sentiment_momentum,
                "sentiment_volatility": s.sentiment_volatility,
                "article_count": s.article_count,
                "discussion_volume": s.discussion_volume,
            } for s in sent_records])
            df = pd.merge(df, sent_df, on="date", how="left")
        else:
            df["news_sentiment"] = 0.0
            df["reddit_sentiment"] = 0.0
            df["combined_sentiment"] = 0.0
            df["sentiment_momentum"] = 0.0
            df["sentiment_volatility"] = 0.0
            df["article_count"] = 0
            df["discussion_volume"] = 0

        # Fill missing sentiment forward and zero remaining
        sentiment_cols = [
            "news_sentiment", "reddit_sentiment", "combined_sentiment",
            "sentiment_momentum", "sentiment_volatility", "article_count", "discussion_volume"
        ]
        df[sentiment_cols] = df[sentiment_cols].ffill().fillna(0.0)

        # 5. Market Benchmark Context (NIFTY 50)
        nifty = self.db.query(Stock).filter(Stock.symbol == "^NSEI").first()
        if nifty and nifty.id != stock.id:
            nifty_prices = (
                self.db.query(PriceHistory.date, PriceHistory.returns_1d)
                .filter(PriceHistory.stock_id == nifty.id)
                .all()
            )
            if nifty_prices:
                nifty_df = pd.DataFrame(nifty_prices, columns=["date", "nifty_return_1d"])
                df = pd.merge(df, nifty_df, on="date", how="left")
                df["nifty_return_1d"] = df["nifty_return_1d"].ffill().fillna(0.0)
                df["relative_return_1d"] = df["return_1d"] - df["nifty_return_1d"]
            else:
                df["nifty_return_1d"] = 0.0
                df["relative_return_1d"] = df["return_1d"]
        else:
            df["nifty_return_1d"] = 0.0
            df["relative_return_1d"] = df["return_1d"]

        # 6. Targets (Calculated strictly into the future to eliminate data leakage)
        # Forward Return over horizon_days:
        df["target_forward_return"] = (df["close"].shift(-horizon_days) - df["close"]) / df["close"]
        
        # Classification Target:
        # 1: Bullish (> +neutral_threshold)
        # 0: Bearish (< -neutral_threshold)
        # -1 / filtered: Neutral
        thresh = settings.NEUTRAL_RETURN_THRESHOLD
        df["target_direction"] = np.where(
            df["target_forward_return"] > thresh, 1,
            np.where(df["target_forward_return"] < -thresh, 0, 2)  # 2 represents neutral
        )

        # Drop the last horizon_days rows where future returns are unknown
        df_clean = df.iloc[:-horizon_days].copy()
        
        # Drop warm-up rows (e.g. 50 days for moving averages)
        df_clean = df_clean.iloc[50:].reset_index(drop=True)

        feature_cols = [
            "rsi_14", "macd", "macd_signal", "macd_hist",
            "dist_ema_20", "dist_sma_50", "dist_sma_200",
            "bb_bandwidth", "bb_percent_b", "norm_atr",
            "adx", "plus_di", "minus_di", "stoch_k", "stoch_d",
            "obv_slope_5", "dist_vwap",
            "return_1d", "return_5d", "return_10d", "return_20d",
            "volatility_10d", "volatility_20d", "volatility_50d",
            "volume_ratio_20", "volume_change_1d", "price_gap",
            "high_20d_ratio", "low_20d_ratio",
            "pe_ratio", "pb_ratio", "eps", "dividend_yield", "roe", "debt_to_equity",
            "combined_sentiment", "sentiment_momentum", "sentiment_volatility",
            "article_count", "discussion_volume",
            "nifty_return_1d", "relative_return_1d"
        ]

        # Handle any possible NaN or Inf values in feature columns
        df_clean[feature_cols] = df_clean[feature_cols].replace([np.inf, -np.inf], np.nan).ffill().bfill().fillna(0.0)

        X = df_clean[feature_cols].copy()
        y_class = df_clean["target_direction"].copy()
        y_reg = df_clean["target_forward_return"].copy()

        return X, y_class, y_reg, feature_cols

