from config import BacktestConfig
from main import run_backtest


if __name__ == "__main__":
    # BTCUSDT 15m default
    run_backtest(BacktestConfig(data_source="synthetic"))

    # Example for other supported pairs and data source switching
    for symbol in ["ETHUSDT", "SOLUSDT"]:
        cfg = BacktestConfig(symbol=symbol, data_source="synthetic")
        run_backtest(cfg)
