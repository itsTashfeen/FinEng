import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
try:
    import empyrical as ep
    EMPYRICAL_AVAILABLE = True
except ImportError:
    EMPYRICAL_AVAILABLE = False
    print("Warning: empyrical not available. Using manual implementations.")


def annualized_return(returns: pd.Series, periods_per_year: int = 252) -> float:
    if EMPYRICAL_AVAILABLE:
        simple_returns = np.exp(returns) - 1
        return ep.annual_return(simple_returns, period='daily')
    else:
        mean_return = returns.mean()
        ann_return = np.exp(mean_return * periods_per_year) - 1
        return ann_return


def annualized_volatility(returns: pd.Series, periods_per_year: int = 252) -> float:

    if EMPYRICAL_AVAILABLE:
        simple_returns = np.exp(returns) - 1
        return ep.annual_volatility(simple_returns, period='daily')
    else:
        ann_vol = returns.std() * np.sqrt(periods_per_year)
        return ann_vol


def sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.0, periods_per_year: int = 252) -> float:
    
    if EMPYRICAL_AVAILABLE:
        simple_returns = np.exp(returns) - 1
        return ep.sharpe_ratio(simple_returns, risk_free=risk_free_rate, period='daily')
    
    else:
        ann_return = annualized_return(returns, periods_per_year)
        ann_vol = annualized_volatility(returns, periods_per_year)
        if ann_vol == 0:
            return np.nan
        sharpe = (ann_return - risk_free_rate) / ann_vol
        return sharpe


def sortino_ratio(returns: pd.Series, risk_free_rate: float = 0.0, periods_per_year: int = 252) -> float:
    
    if EMPYRICAL_AVAILABLE:
        simple_returns = np.exp(returns) - 1
        return ep.sortino_ratio(simple_returns, risk_free=risk_free_rate, period='daily')
    
    else:
        ann_return = annualized_return(returns, periods_per_year)
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0:
            return np.nan
        downside_vol = downside_returns.std() * np.sqrt(periods_per_year)
        if downside_vol == 0:
            return np.nan
        sortino = (ann_return - risk_free_rate) / downside_vol
        return sortino


def max_drawdown(returns: pd.Series) -> float:
    
    if EMPYRICAL_AVAILABLE:
        simple_returns = np.exp(returns) - 1
        return ep.max_drawdown(simple_returns)
    
    else:
        cum = np.exp(returns.cumsum())
        rolling_max = cum.cummax()
        drawdown = (cum - rolling_max) / rolling_max
        mdd = drawdown.min()
        return mdd


def calmar_ratio(returns: pd.Series, periods_per_year: int = 252) -> float:

    if EMPYRICAL_AVAILABLE:
        simple_returns = np.exp(returns) - 1
        return ep.calmar_ratio(simple_returns, period='daily')
    else:
        ann_return = annualized_return(returns, periods_per_year)
        mdd = abs(max_drawdown(returns))
        if mdd == 0:
            return np.nan
        calmar = ann_return / mdd
        return calmar


def var_cvar(returns: pd.Series, confidence: float = 0.95) -> Tuple[float, float]:
    var = returns.quantile(1 - confidence)
    cvar = returns[returns <= var].mean()
    return var, cvar


def skewness(returns: pd.Series) -> float:
    return returns.skew()


def kurtosis(returns: pd.Series) -> float:
    return returns.kurtosis()


def hit_rate(returns: pd.Series) -> float:
    return (returns > 0).sum() / len(returns) * 100


def profit_factor(returns: pd.Series) -> float:
    gains = returns[returns > 0].sum()
    losses = abs(returns[returns < 0].sum())
    if losses == 0:
        return np.nan
    return gains / losses


def average_win_loss(returns: pd.Series) -> Tuple[float, float]:

    wins = returns[returns > 0]
    losses = returns[returns < 0]
    
    avg_win = wins.mean() if len(wins) > 0 else 0.0
    avg_loss = losses.mean() if len(losses) > 0 else 0.0
    
    return avg_win, avg_loss


def information_ratio(strategy_returns: pd.Series, benchmark_returns: pd.Series, periods_per_year: int = 252) -> float:

    common_dates = strategy_returns.index.intersection(benchmark_returns.index)
    strategy_aligned = strategy_returns.loc[common_dates]
    benchmark_aligned = benchmark_returns.loc[common_dates]
    
    excess_returns = strategy_aligned - benchmark_aligned
    ann_excess = annualized_return(excess_returns, periods_per_year)
    tracking_error = annualized_volatility(excess_returns, periods_per_year)
    
    if tracking_error == 0:
        return np.nan
    
    ir = ann_excess / tracking_error
    return ir


def correlation_to_benchmark(strategy_returns: pd.Series, benchmark_returns: pd.Series) -> float:

    common_dates = strategy_returns.index.intersection(benchmark_returns.index)
    strategy_aligned = strategy_returns.loc[common_dates]
    benchmark_aligned = benchmark_returns.loc[common_dates]
    
    corr = strategy_aligned.corr(benchmark_aligned)
    return corr


def max_drawdown_duration(returns: pd.Series) -> int:

    cum = np.exp(returns.cumsum())
    rolling_max = cum.cummax()
    drawdown = (cum - rolling_max) / rolling_max
    
    in_drawdown = drawdown < 0 # finding drawdown peridos
    drawdown_periods = []
    current_period_start = None
    
    for i, is_dd in enumerate(in_drawdown):
        if is_dd and current_period_start is None:
            current_period_start = i
        elif not is_dd and current_period_start is not None:
            drawdown_periods.append(i - current_period_start)
            current_period_start = None
    
    if current_period_start is not None:
        drawdown_periods.append(len(in_drawdown) - current_period_start)
    
    if len(drawdown_periods) == 0:
        return 0
    
    max_dd_duration = max(drawdown_periods)
    return max_dd_duration


def compute_all_metrics(strategy_returns: pd.Series, 
                       benchmark_returns: Optional[pd.Series] = None,
                       risk_free_rate: float = 0.0,
                       periods_per_year: int = 252) -> Dict[str, float]:

    metrics = {}
    
    metrics['Total_Return'] = (np.exp(strategy_returns.sum()) - 1) * 100
    metrics['Annualized_Return'] = annualized_return(strategy_returns, periods_per_year) * 100
    metrics['Annualized_Volatility'] = annualized_volatility(strategy_returns, periods_per_year) * 100
    
    metrics['Sharpe_Ratio'] = sharpe_ratio(strategy_returns, risk_free_rate, periods_per_year)
    metrics['Sortino_Ratio'] = sortino_ratio(strategy_returns, risk_free_rate, periods_per_year)
    metrics['Calmar_Ratio'] = calmar_ratio(strategy_returns, periods_per_year)
    
    metrics['Max_Drawdown'] = max_drawdown(strategy_returns) * 100
    metrics['Max_DD_Duration'] = max_drawdown_duration(strategy_returns)
    
    var, cvar = var_cvar(strategy_returns, confidence=0.95)
    metrics['VaR_95pct'] = var * 100
    metrics['CVaR_95pct'] = cvar * 100
    
    metrics['Skewness'] = skewness(strategy_returns)
    metrics['Kurtosis'] = kurtosis(strategy_returns)
    
    metrics['Hit_Rate'] = hit_rate(strategy_returns)
    metrics['Profit_Factor'] = profit_factor(strategy_returns)
    avg_win, avg_loss = average_win_loss(strategy_returns)
    metrics['Avg_Win'] = avg_win * 100
    metrics['Avg_Loss'] = avg_loss * 100
    
    if benchmark_returns is not None:
        metrics['Information_Ratio'] = information_ratio(strategy_returns, benchmark_returns, periods_per_year)
        metrics['Correlation_to_Benchmark'] = correlation_to_benchmark(strategy_returns, benchmark_returns)
        
        metrics['Benchmark_Total_Return'] = (np.exp(benchmark_returns.sum()) - 1) * 100
        metrics['Benchmark_Annualized_Return'] = annualized_return(benchmark_returns, periods_per_year) * 100
        metrics['Benchmark_Annualized_Volatility'] = annualized_volatility(benchmark_returns, periods_per_year) * 100
        metrics['Benchmark_Sharpe_Ratio'] = sharpe_ratio(benchmark_returns, risk_free_rate, periods_per_year)
        metrics['Benchmark_Max_Drawdown'] = max_drawdown(benchmark_returns) * 100
        metrics['Benchmark_Max_DD_Duration'] = max_drawdown_duration(benchmark_returns)
        metrics['Benchmark_Hit_Rate'] = hit_rate(benchmark_returns)
    
    return metrics


if __name__ == "__main__": #test usage
    from data_loader import load_processed_data
    from signals import compute_signals
    from portfolio import construct_portfolio
    from backtest import run_backtest
    
    print("Loading data and running backtest...")
    fx_returns, carry, _ = load_processed_data()
    signals = compute_signals(carry, lag_days=1)
    weights, vol, leverage, tc = construct_portfolio(signals, fx_returns)
    results = run_backtest(fx_returns, weights, tc)
    
    print("Computing metrics...")
    metrics = compute_all_metrics(results['net_return'])
    
    print("\nPerformance Metrics:")
    for key, value in metrics.items():
        print(f"{key}: {value:.4f}")
