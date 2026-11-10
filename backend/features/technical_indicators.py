import numpy as np
import pandas as pd

class TechnicalIndicators:
    """
    Vectorized technical indicators computed purely using NumPy & Pandas
    to guarantee numerical precision, fast execution, and zero dependency issues.
    """

    @staticmethod
    def calculate_sma(series: pd.Series, window: int) -> pd.Series:
        return series.rolling(window=window, min_periods=window).mean()

    @staticmethod
    def calculate_ema(series: pd.Series, span: int) -> pd.Series:
        return series.ewm(span=span, adjust=False).mean()

    @staticmethod
    def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff()
        gain = np.where(delta > 0, delta, 0.0)
        loss = np.where(delta < 0, -delta, 0.0)

        gain_series = pd.Series(gain, index=series.index)
        loss_series = pd.Series(loss, index=series.index)

        avg_gain = gain_series.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
        avg_loss = loss_series.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

        rs = avg_gain / np.maximum(avg_loss, 1e-9)
        rsi = 100.0 - (100.0 / (1.0 + rs))
        return rsi.fillna(50.0)

    @staticmethod
    def calculate_macd(
        series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> pd.DataFrame:
        ema_fast = series.ewm(span=fast, adjust=False).mean()
        ema_slow = series.ewm(span=slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=signal, adjust=False).mean()
        macd_hist = macd - macd_signal
        return pd.DataFrame({
            "macd": macd,
            "macd_signal": macd_signal,
            "macd_hist": macd_hist
        }, index=series.index)

    @staticmethod
    def calculate_bollinger_bands(
        series: pd.Series, window: int = 20, num_std: float = 2.0
    ) -> pd.DataFrame:
        sma = series.rolling(window=window, min_periods=window).mean()
        std = series.rolling(window=window, min_periods=window).std()
        upper = sma + (std * num_std)
        lower = sma - (std * num_std)
        bandwidth = (upper - lower) / np.maximum(sma, 1e-9)
        percent_b = (series - lower) / np.maximum(upper - lower, 1e-9)
        return pd.DataFrame({
            "bb_middle": sma,
            "bb_upper": upper,
            "bb_lower": lower,
            "bb_bandwidth": bandwidth,
            "bb_percent_b": percent_b.clip(0.0, 1.0)
        }, index=series.index)

    @staticmethod
    def calculate_atr(
        high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
    ) -> pd.Series:
        prev_close = close.shift(1)
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
        return atr.bfill().fillna(0.0)

    @staticmethod
    def calculate_adx(
        high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
    ) -> pd.DataFrame:
        up_move = high - high.shift(1)
        down_move = low.shift(1) - low

        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

        atr = TechnicalIndicators.calculate_atr(high, low, close, period=period)
        plus_di = 100.0 * (pd.Series(plus_dm, index=high.index).ewm(alpha=1.0 / period, adjust=False).mean() / np.maximum(atr, 1e-9))
        minus_di = 100.0 * (pd.Series(minus_dm, index=high.index).ewm(alpha=1.0 / period, adjust=False).mean() / np.maximum(atr, 1e-9))

        dx = 100.0 * ((plus_di - minus_di).abs() / np.maximum(plus_di + minus_di, 1e-9))
        adx = dx.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

        return pd.DataFrame({
            "adx": adx.fillna(25.0),
            "plus_di": plus_di.fillna(25.0),
            "minus_di": minus_di.fillna(25.0)
        }, index=high.index)

    @staticmethod
    def calculate_stochastic(
        high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3
    ) -> pd.DataFrame:
        lowest_low = low.rolling(window=k_period, min_periods=k_period).min()
        highest_high = high.rolling(window=k_period, min_periods=k_period).max()
        fast_k = 100.0 * ((close - lowest_low) / np.maximum(highest_high - lowest_low, 1e-9))
        slow_d = fast_k.rolling(window=d_period, min_periods=d_period).mean()
        return pd.DataFrame({
            "stoch_k": fast_k.fillna(50.0).clip(0.0, 100.0),
            "stoch_d": slow_d.fillna(50.0).clip(0.0, 100.0)
        }, index=close.index)

    @staticmethod
    def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        direction = np.sign(close.diff().fillna(0.0))
        obv = (direction * volume).cumsum()
        return obv

    @staticmethod
    def calculate_vwap(
        high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, window: int = 20
    ) -> pd.Series:
        typical_price = (high + low + close) / 3.0
        pv = typical_price * volume
        vwap = pv.rolling(window=window).sum() / np.maximum(volume.rolling(window=window).sum(), 1e-9)
        return vwap.bfill().fillna(close)

