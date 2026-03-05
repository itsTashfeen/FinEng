import pandas as pd
import numpy as np
from typing import Optional, Tuple


def run_backtest(fx_returns: pd.DataFrame,
                 weights: pd.DataFrame,
                 transaction_costs: pd.Series,
                 benchmark_returns: Optional[pd.Series] = None) -> pd.DataFrame:


    common_dates = fx_returns.index.intersection(weights.index).intersection(transaction_costs.index)
    if benchmark_returns is not None and len(benchmark_returns) > 0:
        common_dates = common_dates.intersection(benchmark_returns.index)
    fx_returns = fx_returns.loc[common_dates]
    weights = weights.loc[common_dates]
    transaction_costs = transaction_costs.loc[common_dates]
    

    gross_pnl = (weights * fx_returns).sum(axis=1)
    net_pnl = gross_pnl - transaction_costs

    cum_gross = np.exp(gross_pnl.cumsum())
    cum_net = np.exp(net_pnl.cumsum())
    
    results = pd.DataFrame({
        'gross_return': gross_pnl,
        'net_return': net_pnl,
        'cumulative_gross': cum_gross,
        'cumulative_net': cum_net,
    }, index=common_dates)
    
    if benchmark_returns is not None and len(benchmark_returns) > 0: # add benchmark if provided
        benchmark_aligned = benchmark_returns.loc[common_dates]
        results['benchmark_return'] = benchmark_aligned
        results['cumulative_benchmark'] = np.exp(benchmark_aligned.cumsum())
    
    return results


def load_benchmark_data(benchmark_symbol: str = "SPY", start_date: str = "2002-04-01") -> pd.Series:

    from pathlib import Path
    
    benchmark_path = Path(__file__).parent.parent / "data" / "raw" / f"{benchmark_symbol}_daily.csv"
    if not benchmark_path.exists():
        benchmark_path = Path(__file__).parent.parent / "data" / "raw" / "fx_spot" / f"{benchmark_symbol}_daily.csv"
    
    if benchmark_path.exists():
        df = pd.read_csv(benchmark_path, skipfooter=1, engine='python')
        
        date_col = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()][0]
        close_col = [col for col in df.columns if 'close' in col.lower() or 'latest' in col.lower()][0]
        
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=[date_col])
        df.set_index(date_col, inplace=True)
        df.sort_index(inplace=True)
        
        prices = pd.to_numeric(df[close_col], errors='coerce')
        log_returns = np.log(prices / prices.shift(1))
        
        if start_date:
            log_returns = log_returns[log_returns.index >= start_date]
        
        return log_returns.dropna()
    else:
        return pd.Series(dtype=float)


def compute_drawdown(returns: pd.Series) -> pd.Series:

    cum = np.exp(returns.cumsum())
    rolling_max = cum.cummax()
    drawdown = (cum - rolling_max) / rolling_max
    return drawdown


def compute_rolling_returns(returns: pd.Series, window: int = 252) -> pd.Series:

    rolling_returns = returns.rolling(window=window).sum()
    return rolling_returns


if __name__ == "__main__": # test usage

    from data_loader import load_processed_data
    from signals import compute_signals
    from portfolio import construct_portfolio
    
    print("Loading processed data...")
    fx_returns, carry, _ = load_processed_data()
    
    print("Computing signals...")
    signals = compute_signals(carry, lag_days=1)
    
    print("Constructing portfolio...")
    weights, vol, leverage, tc = construct_portfolio(signals, fx_returns)
    
    print("Running backtest...")
    results = run_backtest(fx_returns, weights, tc)
    
    print(f"Backtest results shape: {results.shape}")
    print(f"Final cumulative net: {results['cumulative_net'].iloc[-1]:.4f}")
    print(f"Total return: {(results['cumulative_net'].iloc[-1] - 1) * 100:.2f}%")
    
    drawdown = compute_drawdown(results['net_return'])
    print(f"Max drawdown: {drawdown.min() * 100:.2f}%")
