# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
from datetime import datetime
from freqtrade.strategy import IStrategy
from freqtrade.persistence import Trade
from pandas import DataFrame
import numpy as np


def _compute_streak(opens: np.ndarray, closes: np.ndarray) -> np.ndarray:
    """
    Returns a signed consecutive-candle streak array.
    Negative = consecutive reds, positive = consecutive greens.
    A doji (open == close) resets the streak to 0.
    """
    streak = np.zeros(len(closes), dtype=np.int32)
    for i in range(1, len(closes)):
        if closes[i] < opens[i]:      # red candle
            streak[i] = streak[i - 1] - 1 if streak[i - 1] < 0 else -1
        elif closes[i] > opens[i]:    # green candle
            streak[i] = streak[i - 1] + 1 if streak[i - 1] > 0 else 1
        # doji: streak stays 0
    return streak


class Strategy01(IStrategy):
    """
    XRP 5-Red-Candle Reversal
    --------------------------
    Timeframe : 5-minute candles
    Entry long : 5+ consecutive red candles  → expect mean-reversion bounce
    Entry short: 5+ consecutive green candles → expect fade  (requires futures config)
    Stop loss  : 1%
    Max hold   : 120 candles (10 hours) — force-exits via custom_exit
    """

    INTERFACE_VERSION = 3

    timeframe = "5m"

    # tight 1 % stop; ROI set astronomically high so custom_exit controls the close
    stoploss = -0.01
    minimal_roi = {"0": 99}

    # Short signals are populated but only fire when the exchange config supports it.
    # To enable: set trading_mode=futures + margin_mode=isolated in config.json.
    can_short = False

    # keep the pair in sync with the pair whitelist in config.json
    _PAIR = "XRP/USDT"
    _MAX_CANDLES = 120
    _STREAK_THRESHOLD = 5

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        streak = _compute_streak(
            dataframe["open"].to_numpy(),
            dataframe["close"].to_numpy(),
        )
        dataframe["streak"] = streak
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Long: 5+ consecutive reds on the *previous* closed candle
        dataframe.loc[
            (dataframe["streak"] <= -self._STREAK_THRESHOLD)
            & (dataframe["volume"] > 0),
            "enter_long",
        ] = 1

        # Short: 5+ consecutive greens (active only when can_short=True)
        dataframe.loc[
            (dataframe["streak"] >= self._STREAK_THRESHOLD)
            & (dataframe["volume"] > 0),
            "enter_short",
        ] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Streak flipping to positive closes the long; negative closes the short.
        dataframe.loc[
            (dataframe["streak"] > 0) & (dataframe["volume"] > 0),
            "exit_long",
        ] = 1
        dataframe.loc[
            (dataframe["streak"] < 0) & (dataframe["volume"] > 0),
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
