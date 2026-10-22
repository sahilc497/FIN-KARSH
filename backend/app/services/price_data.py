import datetime
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
import yfinance as yf
from sqlalchemy.orm import Session
from app.core.logging import logger
from app.database.repositories import StockRepository, PriceRepository

class MarketDataService:
    def __init__(self, db: Session):
        self.db = db
        self.stock_repo = StockRepository(db)
        self.price_repo = PriceRepository(db)

    def fetch_and_calculate_indicators(self, symbol: str, period: str = "1y") -> List[Dict[str, Any]]:
        """
        Retrieves historical prices via yfinance for the Indian ticker,
        calculates technical indicators, and saves them to SQLite.
        """
        stock = self.stock_repo.get_by_symbol(symbol)
        if not stock:
            logger.warning(f"Stock symbol {symbol} not found in database.")
            return []

        ticker = stock.ticker  # e.g., 'RELIANCE.NS'
        logger.info(f"Downloading historical market data for {ticker} (period={period})...")

        try:
            df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
            if df.empty:
                logger.warning(f"No price data returned from yfinance for {ticker}.")
                return []

            # Handle multi-level columns if present in newer yfinance versions
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            df = df.reset_index()
            # Standardize date column
            date_col = "Date" if "Date" in df.columns else df.columns[0]
            df["Date"] = pd.to_datetime(df[date_col]).dt.tz_localize(None)
            df = df.sort_values("Date").drop_duplicates("Date")

            # Calculate technical indicators strictly using past data
            close = df["Close"]

            # 1. Daily return
            df["returns_1d"] = close.pct_change()

            # 2. Momentum: 5-day, 20-day, 60-day
            df["momentum_5d"] = close.pct_change(5)
            df["momentum_20d"] = close.pct_change(20)
            df["momentum_60d"] = close.pct_change(60)

            # 3. Moving averages: 20-day and 50-day
            df["ma_20"] = close.rolling(window=20).mean()
            df["ma_50"] = close.rolling(window=50).mean()

            # 4. RSI (14 periods)
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / (loss.replace(0, np.nan))
            df["rsi_14"] = 100 - (100 / (1 + rs))

            # 5. MACD (12 EMA - 26 EMA) and 9 EMA Signal
            ema_12 = close.ewm(span=12, adjust=False).mean()
            ema_26 = close.ewm(span=26, adjust=False).mean()
            df["macd"] = ema_12 - ema_26
            df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()

            # 6. Volatility (20-session rolling std of daily returns)
            df["volatility_20d"] = df["returns_1d"].rolling(window=20).std()

            # 7. Volume ratio (current volume vs 20-day moving average volume)
            vol = df["Volume"]
            vol_ma_20 = vol.rolling(window=20).mean()
            df["volume_ratio"] = vol / (vol_ma_20.replace(0, np.nan))

            # Clean and package records
            records: List[Dict[str, Any]] = []
            for _, row in df.iterrows():
                # Replace nan with None
                rec = {
                    "date": row["Date"].to_pydatetime(),
                    "open": float(row["Open"]) if pd.notna(row["Open"]) else 0.0,
                    "high": float(row["High"]) if pd.notna(row["High"]) else 0.0,
                    "low": float(row["Low"]) if pd.notna(row["Low"]) else 0.0,
                    "close": float(row["Close"]) if pd.notna(row["Close"]) else 0.0,
                    "volume": float(row["Volume"]) if pd.notna(row["Volume"]) else 0.0,
                    "returns_1d": float(row["returns_1d"]) if pd.notna(row["returns_1d"]) else None,
                    "momentum_5d": float(row["momentum_5d"]) if pd.notna(row["momentum_5d"]) else None,
                    "momentum_20d": float(row["momentum_20d"]) if pd.notna(row["momentum_20d"]) else None,
                    "momentum_60d": float(row["momentum_60d"]) if pd.notna(row["momentum_60d"]) else None,
                    "ma_20": float(row["ma_20"]) if pd.notna(row["ma_20"]) else None,
                    "ma_50": float(row["ma_50"]) if pd.notna(row["ma_50"]) else None,
                    "rsi_14": float(row["rsi_14"]) if pd.notna(row["rsi_14"]) else None,
                    "macd": float(row["macd"]) if pd.notna(row["macd"]) else None,
                    "macd_signal": float(row["macd_signal"]) if pd.notna(row["macd_signal"]) else None,
                    "volatility_20d": float(row["volatility_20d"]) if pd.notna(row["volatility_20d"]) else None,
                    "volume_ratio": float(row["volume_ratio"]) if pd.notna(row["volume_ratio"]) else None,
                }
                records.append(rec)

            saved_count = self.price_repo.save_prices(stock.id, records)
            logger.info(f"Saved {saved_count} price rows with technical indicators for {symbol}.")
            return records

        except Exception as e:
            logger.error(f"Error fetching price data for {symbol}: {e}", exc_info=True)
            return []

    def sync_all_stocks(self, period: str = "1y") -> Dict[str, int]:
        """Syncs price data for all active stocks"""
        stocks = self.stock_repo.get_all(active_only=True)
        results = {}
        for stock in stocks:
            recs = self.fetch_and_calculate_indicators(stock.symbol, period=period)
            results[stock.symbol] = len(recs)
        return results
