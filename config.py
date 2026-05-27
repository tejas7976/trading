from dataclasses import dataclass


@dataclass
class BacktestConfig:
    symbol: str = "BTCUSDT"
    timeframe: str = "15m"
    start_date: str = "2023-01-01"
    end_date: str = "2024-01-01"
    initial_balance: float = 10_000.0

    ema_fast: int = 9
    ema_slow: int = 21
    ema_trend: int = 200
    rsi_period: int = 14
    adx_period: int = 14
    atr_period: int = 14

    rsi_long_threshold: float = 55.0
    rsi_short_threshold: float = 45.0
    adx_threshold: float = 20.0

    risk_per_trade: float = 0.02
    atr_sl_multiplier: float = 1.5
    tp1_rr: float = 2.0
    tp2_rr: float = 3.0

    leverage: float = 3.0
    fee_rate: float = 0.0004

    data_source: str = "binance"  # binance | yfinance | synthetic
