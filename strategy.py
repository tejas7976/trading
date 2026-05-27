from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd


@dataclass
class Position:
    side: str
    entry_time: pd.Timestamp
    entry_price: float
    stop_loss: float
    risk_per_unit: float
    qty: float
    tp1: float
    tp2: float
    tp1_hit: bool = False
    tp2_hit: bool = False
    trailing_active: bool = False


class Backtester:
    def __init__(self, df: pd.DataFrame, cfg):
        self.df = df.copy()
        self.cfg = cfg
        self.balance = float(cfg.initial_balance)
        self.position: Optional[Position] = None
        self.trades = []
        self.equity_curve = []

    def _is_long_signal(self, i: int) -> bool:
        row, prev = self.df.iloc[i], self.df.iloc[i - 1]
        crossed = prev["ema_fast"] <= prev["ema_slow"] and row["ema_fast"] > row["ema_slow"]
        return (
            row["close"] > row["ema_trend"]
            and crossed
            and row["rsi"] > self.cfg.rsi_long_threshold
            and row["adx"] > self.cfg.adx_threshold
        )

    def _is_short_signal(self, i: int) -> bool:
        row, prev = self.df.iloc[i], self.df.iloc[i - 1]
        crossed = prev["ema_fast"] >= prev["ema_slow"] and row["ema_fast"] < row["ema_slow"]
        return (
            row["close"] < row["ema_trend"]
            and crossed
            and row["rsi"] < self.cfg.rsi_short_threshold
            and row["adx"] > self.cfg.adx_threshold
        )

    def _open_position(self, i: int, side: str) -> None:
        row = self.df.iloc[i]
        entry = float(row["close"])
        atr_val = float(row["atr"])
        risk_distance = self.cfg.atr_sl_multiplier * atr_val
        if risk_distance <= 0:
            return

        if side == "long":
            sl = entry - risk_distance
            tp1 = entry + self.cfg.tp1_rr * risk_distance
            tp2 = entry + self.cfg.tp2_rr * risk_distance
        else:
            sl = entry + risk_distance
            tp1 = entry - self.cfg.tp1_rr * risk_distance
            tp2 = entry - self.cfg.tp2_rr * risk_distance

        risk_amount = self.balance * self.cfg.risk_per_trade
        qty = (risk_amount / risk_distance) * self.cfg.leverage
        if qty <= 0:
            return

        self.position = Position(
            side=side,
            entry_time=self.df.index[i],
            entry_price=entry,
            stop_loss=sl,
            risk_per_unit=risk_distance,
            qty=qty,
            tp1=tp1,
            tp2=tp2,
        )

    def _close_position(self, i: int, reason: str, exit_price: float) -> None:
        pos = self.position
        if pos is None:
            return

        if pos.side == "long":
            gross_pnl = (exit_price - pos.entry_price) * pos.qty
        else:
            gross_pnl = (pos.entry_price - exit_price) * pos.qty
        fees = (pos.entry_price + exit_price) * pos.qty * self.cfg.fee_rate
        pnl = gross_pnl - fees
        self.balance += pnl

        self.trades.append(
            {
                "entry_time": pos.entry_time,
                "exit_time": self.df.index[i],
                "side": pos.side,
                "entry": pos.entry_price,
                "exit": exit_price,
                "qty": pos.qty,
                "pnl": pnl,
                "reason": reason,
                "tp1_hit": pos.tp1_hit,
                "tp2_hit": pos.tp2_hit,
            }
        )
        self.position = None

    def _manage_position(self, i: int) -> None:
        pos = self.position
        if pos is None:
            return

        row = self.df.iloc[i]
        prev = self.df.iloc[i - 1]
        high, low = float(row["high"]), float(row["low"])

        if pos.side == "long":
            if not pos.tp1_hit and high >= pos.tp1:
                pos.tp1_hit = True
                pos.stop_loss = pos.entry_price
            if not pos.tp2_hit and high >= pos.tp2:
                pos.tp2_hit = True
                pos.trailing_active = True
            if pos.trailing_active:
                pos.stop_loss = max(pos.stop_loss, float(prev["low"]))
            if low <= pos.stop_loss:
                self._close_position(i, "stop_loss", pos.stop_loss)

        else:
            if not pos.tp1_hit and low <= pos.tp1:
                pos.tp1_hit = True
                pos.stop_loss = pos.entry_price
            if not pos.tp2_hit and low <= pos.tp2:
                pos.tp2_hit = True
                pos.trailing_active = True
            if pos.trailing_active:
                pos.stop_loss = min(pos.stop_loss, float(prev["high"]))
            if high >= pos.stop_loss:
                self._close_position(i, "stop_loss", pos.stop_loss)

    def run(self) -> tuple[pd.DataFrame, pd.Series]:
        # Use a larger warmup window so long-period EMA/ADX/ATR values are more stable.
        warmup = 2 * max(self.cfg.ema_trend, self.cfg.atr_period, self.cfg.adx_period, self.cfg.rsi_period)
        # +1 ensures crossover checks can safely reference the previous bar.
        start = warmup + 1

        for i in range(start, len(self.df)):
            if self.position is not None:
                self._manage_position(i)

            if self.position is None:
                if self._is_long_signal(i):
                    self._open_position(i, "long")
                elif self._is_short_signal(i):
                    self._open_position(i, "short")

            self.equity_curve.append({"timestamp": self.df.index[i], "equity": self.balance})

        if self.position is not None:
            last_price = float(self.df.iloc[-1]["close"])
            self._close_position(len(self.df) - 1, "end_of_data", last_price)
            self.equity_curve.append({"timestamp": self.df.index[-1], "equity": self.balance})

        trades_df = pd.DataFrame(self.trades)
        equity_df = pd.DataFrame(self.equity_curve)
        equity_series = (
            equity_df.set_index("timestamp")["equity"]
            if not equity_df.empty
            else pd.Series([self.balance], index=[self.df.index[-1]], name="equity")
        )
        return trades_df, equity_series
