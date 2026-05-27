from __future__ import annotations

import numpy as np
import pandas as pd


def _safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0


def compute_metrics(trades: pd.DataFrame, equity_curve: pd.Series, initial_balance: float) -> dict:
    if trades.empty:
        final_balance = float(equity_curve.iloc[-1]) if len(equity_curve) else initial_balance
        return {
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": 0.0,
            "initial_balance": initial_balance,
            "final_balance": final_balance,
            "total_return_pct": _safe_div(final_balance - initial_balance, initial_balance) * 100,
            "profit_factor": 0.0,
            "max_drawdown_pct": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "expectancy": 0.0,
        }

    wins = trades[trades["pnl"] > 0]
    losses = trades[trades["pnl"] <= 0]

    gross_profit = float(wins["pnl"].sum())
    gross_loss = abs(float(losses["pnl"].sum()))

    running_max = equity_curve.cummax()
    dd = (equity_curve - running_max) / running_max.replace(0, np.nan)

    final_balance = float(equity_curve.iloc[-1])

    return {
        "total_trades": int(len(trades)),
        "wins": int(len(wins)),
        "losses": int(len(losses)),
        "win_rate": _safe_div(len(wins), len(trades)) * 100,
        "initial_balance": initial_balance,
        "final_balance": final_balance,
        "total_return_pct": _safe_div(final_balance - initial_balance, initial_balance) * 100,
        "profit_factor": _safe_div(gross_profit, gross_loss),
        "max_drawdown_pct": float(dd.min() * 100 if len(dd) else 0),
        "avg_win": float(wins["pnl"].mean() if len(wins) else 0),
        "avg_loss": float(losses["pnl"].mean() if len(losses) else 0),
        "expectancy": float(trades["pnl"].mean()),
    }
