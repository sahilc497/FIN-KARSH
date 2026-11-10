# SENTIMENT-APLHA Datasets & Ingestion Architecture

This directory houses raw and processed financial market datasets, news records, and Reddit discussions.

## Directory Structure
- `datasets/raw/`: Raw JSON/CSV dumps of historical OHLCV quotes from Yahoo Finance, RSS XML feed items from Moneycontrol, and Reddit API submissions.
- `datasets/processed/`: Normalized feature matrices with lagged technical indicators, stationary return features, and FinBERT sentiment aggregations.

## Data Schema
1. **Prices (OHLCV)**: Date, Open, High, Low, Close, Adj Close, Volume, 1d Return, 20d Volatility.
2. **FinBERT News Records**: Headline, Source, URL, Timestamp, P(Positive), P(Negative), P(Neutral), Sentiment Score ($P(pos) - P(neg)$).
3. **Multi-Factor Feature Matrix**: 42 stationary indicators including RSI(14), MACD, EMA(9/20/50/200), SMA(20/50/200), Bollinger Bands, ATR(14), ADX(14), Stochastic, OBV, VWAP, P/E, ROE, 5-day sentiment momentum, and relative benchmark return vs NIFTY 50.

