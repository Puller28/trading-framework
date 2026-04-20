# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
from datetime import datetime
from freqtrade.strategy import IStrategy
from freqtrade.persistence import Trade
from pandas import DataFrame


class Strategy04(IStrategy):
    """
    BCH Pivot Point Mean Reversion
    --------------------------------
    Pivot = (rolling_48_high + rolling_48_low + prev_close) / 3
    Entry long  : close < pivot  → price below mean, expect bounce up
    Entry short : close > pivot  → price above mean, expect fade down  (requires futures config)
    Exit        : price crosses back through pivot (mean achieved)
    Stop loss   : 1%
    Max hold    : 60 candles (5 hours) — force-exits via custom_exit
    """

    INTERFACE_VERSION = 3

    timeframe = "5m"

    stoploss = -0.01
    minimal_roi = {"0": 99}

    can_short = False

    _PAIR = "BCH/USDT"
    _PIVOT_PERIOD = 48
    _MAX_CANDLES = 60

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        rolling_high = dataframe["high"].rolling(self._PIVOT_PERIOD).max()
        rolling_low = dataframe["low"].rolling(self._PIVOT_PERIOD).min()
        prev_close = dataframe["close"].shift(1)

        dataframe["pivot"] = (rolling_high + rolling_low + prev_close) / 3
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        valid = dataframe["pivot"].notna() & (dataframe["pivot"] > 0) & (dataframe["volume"] > 0)

        dataframe.loc[valid & (dataframe["close"] < dataframe["pivot"]), "enter_long"] = 1
        dataframe.loc[valid & (dataframe["close"] > dataframe["pivot"]), "enter_short"] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["close"] >= dataframe["pivot"]) & (dataframe["volume"] > 0),
            "exit_long",
        ] = 1
        dataframe.loc[
            (dataframe["close"] <= dataframe["pivot"]) & (dataframe["volume"] > 0),
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
            return "max_hold_60_candles"
        return None
