from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd


def plot_results(df: pd.DataFrame, trades: pd.DataFrame, equity_curve: pd.Series, metrics: dict, output_file: str = "backtest_results.png") -> None:
    fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True, gridspec_kw={"height_ratios": [2, 1, 1]})

    ax_price, ax_mom, ax_eq = axes

    ax_price.plot(df.index, df["close"], label="Close", linewidth=1.0)
    ax_price.plot(df.index, df["ema_fast"], label="EMA9", linewidth=1.0)
    ax_price.plot(df.index, df["ema_slow"], label="EMA21", linewidth=1.0)
    ax_price.plot(df.index, df["ema_trend"], label="EMA200", linewidth=1.2)

    if not trades.empty:
        longs = trades[trades["side"] == "long"]
        shorts = trades[trades["side"] == "short"]
        ax_price.scatter(longs["entry_time"], longs["entry"], marker="^", color="green", label="Long Entry", s=30)
        ax_price.scatter(shorts["entry_time"], shorts["entry"], marker="v", color="red", label="Short Entry", s=30)
        ax_price.scatter(trades["exit_time"], trades["exit"], marker="x", color="black", label="Exit", s=20)

    ax_price.legend(loc="upper left")
    ax_price.set_title("Price, EMAs, and Trades")
    ax_price.grid(alpha=0.3)

    ax_mom.plot(df.index, df["rsi"], label="RSI", linewidth=1.0)
    ax_mom.plot(df.index, df["adx"], label="ADX", linewidth=1.0)
    ax_mom.axhline(55, linestyle="--", linewidth=0.8)
    ax_mom.axhline(45, linestyle="--", linewidth=0.8)
    ax_mom.axhline(20, linestyle=":", linewidth=0.8)
    ax_mom.legend(loc="upper left")
    ax_mom.set_title("RSI / ADX")
    ax_mom.grid(alpha=0.3)

    ax_eq.plot(equity_curve.index, equity_curve.values, label="Equity Curve", color="purple")
    ax_eq.set_title("Equity Curve")
    ax_eq.grid(alpha=0.3)

    stats = (
        f"Trades: {metrics['total_trades']} | Win Rate: {metrics['win_rate']:.2f}% | "
        f"Return: {metrics['total_return_pct']:.2f}% | MDD: {metrics['max_drawdown_pct']:.2f}% | "
        f"PF: {metrics['profit_factor']:.2f}"
    )
    fig.suptitle(stats, fontsize=11)

    plt.tight_layout()
    plt.savefig(output_file, dpi=150)
    plt.close(fig)
