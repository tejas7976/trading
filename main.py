from __future__ import annotations

from config import BacktestConfig
from data_fetcher import fetch_data
from indicators import add_indicators
from metrics import compute_metrics
from strategy import Backtester
from visualizer import plot_results


def run_backtest(cfg: BacktestConfig):
    source_used = cfg.data_source
    try:
        df = fetch_data(
            symbol=cfg.symbol,
            timeframe=cfg.timeframe,
            start_date=cfg.start_date,
            end_date=cfg.end_date,
            source=cfg.data_source,
        )
    except Exception as exc:
        if cfg.data_source == "synthetic":
            raise
        print(f"Data fetch failed for source='{cfg.data_source}': {exc}")
        print("Falling back to synthetic data for offline/backtest validation.")
        source_used = "synthetic"
        df = fetch_data(
            symbol=cfg.symbol,
            timeframe=cfg.timeframe,
            start_date=cfg.start_date,
            end_date=cfg.end_date,
            source=source_used,
        )
    df = add_indicators(df, cfg)

    backtester = Backtester(df, cfg)
    trades, equity_curve = backtester.run()

    stats = compute_metrics(trades, equity_curve, cfg.initial_balance)
    plot_results(
        df,
        trades,
        equity_curve,
        stats,
        output_file=f"{cfg.symbol}_{cfg.timeframe}_backtest.png",
        rsi_long_threshold=cfg.rsi_long_threshold,
        rsi_short_threshold=cfg.rsi_short_threshold,
        adx_threshold=cfg.adx_threshold,
    )

    print("Backtest complete")
    print(f"Symbol: {cfg.symbol}  Timeframe: {cfg.timeframe}  Source: {source_used}")
    print(f"Trades: {stats['total_trades']}")
    print(f"Win Rate: {stats['win_rate']:.2f}%")
    print(f"Final Balance: {stats['final_balance']:.2f}")
    print(f"Return: {stats['total_return_pct']:.2f}%")
    print(f"Max Drawdown: {stats['max_drawdown_pct']:.2f}%")
    print(f"Profit Factor: {stats['profit_factor']:.2f}")

    if not trades.empty:
        print("\nRecent Trades:")
        print(trades.tail(10).to_string(index=False))

    return trades, equity_curve, stats


if __name__ == "__main__":
    config = BacktestConfig()
    run_backtest(config)
