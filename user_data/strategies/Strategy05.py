# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
from datetime import datetime
from freqtrade.strategy import IStrategy
from freqtrade.persistence import Trade
from pandas import DataFrame
import pandas as pd


class Strategy05(IStrategy):
    """
    Keltner Channel Flipped — Mean Reversion
    ------------------------------------------
    Middle  : EMA(20) of close
    ATR     : EMA-smoothed true range, period=10  (k = 2/11, same as original)
    Upper   : EMA20 + 1.5 × ATR
    Lower   : EMA20 − 1.5 × ATR

    Entry long  : close < lower band  → fade the breakdown, expect snap-back to mid
    Entry short : close > upper band  → fade the breakout, expect snap-back to mid  (requires futures config)
    Exit        : price returns to EMA20 (mid band)
    Stop loss   : 1.5%
    Max hold    : 120 candles (10 hours) — force-exits via custom_exit

    Pair: apply to any liquid USDT pair in pair_whitelist.
    """

    INTERFACE_VERSION = 3

    timeframe = "5m"

    stoploss = -0.015
    minimal_roi = {"0": 99}

    can_short = False

    _KC_PERIOD_EMA = 20
    _KC_PERIOD_ATR = 10
    _KC_MULTIPLIER = 1.5
    _MAX_CANDLES = 120

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # --- Middle band: EMA(20) ---
        dataframe["kc_mid"] = (
            dataframe["close"].ewm(span=self._KC_PERIOD_EMA, adjust=False).mean()
        )

        # --- True Range ---
        prev_close = dataframe["close"].shift(1)
        tr = pd.concat(
            [
                dataframe["high"] - dataframe["low"],
                (dataframe["high"] - prev_close).abs(),
                (dataframe["low"] - prev_close).abs(),
            ],
            axis=1,
        ).max(axis=1)

        # EMA-smooth TR with k=2/(10+1) — matches the original atr() exactly
        dataframe["kc_atr"] = tr.ewm(span=self._KC_PERIOD_ATR, adjust=False).mean()

        # --- Bands ---
        dataframe["kc_upper"] = dataframe["kc_mid"] + self._KC_MULTIPLIER * dataframe["kc_atr"]
        dataframe["kc_lower"] = dataframe["kc_mid"] - self._KC_MULTIPLIER * dataframe["kc_atr"]

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        valid = (
            dataframe["kc_mid"].notna()
            & dataframe["kc_atr"].notna()
            & (dataframe["volume"] > 0)
        )

        # Fade the breakdown: close broke below lower band
        dataframe.loc[
            valid & (dataframe["close"] < dataframe["kc_lower"]),
            "enter_long",
        ] = 1

        # Fade the breakout: close broke above upper band
        dataframe.loc[
            valid & (dataframe["close"] > dataframe["kc_upper"]),
            "enter_short",
        ] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Mean reversion achieved: price returned to the middle band
        dataframe.loc[
            (dataframe["close"] >= dataframe["kc_mid"]) & (dataframe["volume"] > 0),
            "exit_long",
        ] = 1
        dataframe.loc[
            (dataframe["close"] <= dataframe["kc_mid"]) & (dataframe["volume"] > 0),
            "exit_short",
        ] = 1
        return dataframe

    def custom_exit(
        self,
        pair: str,
        trade: Trade,
        current_time: datetime,
        current_rate: float,
        current_profit: float,
        **kwargs,
    ):
        elapsed_candles = (current_time - trade.open_date_utc).total_seconds() / (5 * 60)
        if elapsed_candles >= self._MAX_CANDLES:
            return "max_hold_120_candles"
        return None
