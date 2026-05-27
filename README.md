# Crypto Futures Strategy Backtester

This repository contains a complete backtesting framework for the professional crypto futures strategy described in the strategy guide.

## Strategy Logic

- Trend filter: EMA 200
- Entry confirmation: EMA 9/21 crossover + RSI + ADX
- Long: `close > EMA200`, `EMA9 > EMA21` crossover, `RSI > 55`, `ADX > 20`
- Short: `close < EMA200`, `EMA9 < EMA21` crossover, `RSI < 45`, `ADX > 20`
- Initial stop-loss: `1.5 x ATR`
- Risk per trade: `2%` of account balance
- TP1: `1:2 RR`, move SL to breakeven
- TP2: `1:3 RR`, activate trailing stop
- Trailing stop: previous **closed** candle low (long) / high (short)

## Files

- `/tmp/workspace/tejas7976/trading/config.py` - strategy and runtime configuration
- `/tmp/workspace/tejas7976/trading/data_fetcher.py` - Binance futures (ccxt), yfinance, synthetic data fetchers
- `/tmp/workspace/tejas7976/trading/indicators.py` - EMA, RSI, ADX, ATR calculations
- `/tmp/workspace/tejas7976/trading/strategy.py` - backtester engine and trade management
- `/tmp/workspace/tejas7976/trading/metrics.py` - performance statistics
- `/tmp/workspace/tejas7976/trading/visualizer.py` - trade and equity visualization
- `/tmp/workspace/tejas7976/trading/main.py` - main entry point
- `/tmp/workspace/tejas7976/trading/example_usage.py` - multi-symbol usage example

## Installation

```bash
cd /tmp/workspace/tejas7976/trading
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Configuration

Edit `BacktestConfig` in `config.py` to tune parameters:

- symbol (`BTCUSDT`, `ETHUSDT`, `SOLUSDT`)
- timeframe (`15m` recommended)
- indicator thresholds
- risk settings and leverage
- data source (`binance`, `yfinance`, `synthetic`)

## Notes

- Binance futures data requires internet access and the `ccxt` package.
- The `synthetic` source is included for offline validation and example execution.
