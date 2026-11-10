import pytest
import numpy as np
import pandas as pd
from backend.features.technical_indicators import TechnicalIndicators

def test_rsi_bounds():
    prices = pd.Series([100.0 + i + (i % 3) * 2 for i in range(50)])
    rsi = TechnicalIndicators.calculate_rsi(prices, period=14)
    assert len(rsi) == len(prices)
    assert (rsi >= 0.0).all() and (rsi <= 100.0).all()

def test_macd_calculation():
    prices = pd.Series([100.0 * (1.01 ** i) for i in range(60)])
    macd_df = TechnicalIndicators.calculate_macd(prices)
    assert "macd" in macd_df.columns
    assert "macd_signal" in macd_df.columns
    assert "macd_hist" in macd_df.columns
    assert not macd_df["macd"].isna().all()

def test_bollinger_bands():
    prices = pd.Series([50.0 + np.sin(i / 5.0) * 5.0 for i in range(50)])
    bb = TechnicalIndicators.calculate_bollinger_bands(prices, window=20)
    assert (bb["bb_upper"].dropna() >= bb["bb_middle"].dropna()).all()
    assert (bb["bb_middle"].dropna() >= bb["bb_lower"].dropna()).all()
