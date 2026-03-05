
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime

sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9
plt.rcParams['legend.fontsize'] = 9

OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def plot_equity_curve(strategy_cumulative: pd.Series,
                     benchmark_cumulative: Optional[pd.Series] = None,
                     title: str = "Equity Curve",
                     log_scale: bool = True,
                     save_path: Optional[Path] = None) -> None:

    fig, ax = plt.subplots(figsize=(14, 7))
    
    strategy_normalized = strategy_cumulative * 100
    ax.plot(strategy_normalized.index, strategy_normalized.values, 
            label='Strategy (Net)', linewidth=2, color='#2E86AB')
    
    if benchmark_cumulative is not None:
        benchmark_normalized = benchmark_cumulative * 100
        ax.plot(benchmark_normalized.index, benchmark_normalized.values,
                label='Benchmark (SPY)', linewidth=2, color='#A23B72', linestyle='--')
    
    ax.set_xlabel('Date', fontweight='bold')
    ax.set_ylabel('Cumulative Return (Index = 100)', fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    
    if log_scale:
        ax.set_yscale('log')
    
    plt.tight_layout()
    
    if save_path is None:
        save_path = OUTPUT_DIR / "equity_curve.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()


def plot_drawdown(drawdown: pd.Series,
                 title: str = "Drawdown Chart",
                 highlight_periods: Optional[list] = None,
                 save_path: Optional[Path] = None) -> None:

    fig, ax = plt.subplots(figsize=(14, 7))
    
    ax.fill_between(drawdown.index, drawdown.values * 100, 0,
                    color='#E63946', alpha=0.6, label='Drawdown')
    ax.plot(drawdown.index, drawdown.values * 100,
            color='#E63946', linewidth=1.5)
    
    if highlight_periods:
        for start_date, end_date, label in highlight_periods:
            ax.axvspan(start_date, end_date, alpha=0.2, color='gray', label=label)
    
    ax.set_xlabel('Date', fontweight='bold')
    ax.set_ylabel('Drawdown (%)', fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    ax.set_ylim(bottom=drawdown.min() * 100 * 1.1)
    
    plt.tight_layout()
    
    if save_path is None:
        save_path = OUTPUT_DIR / "drawdown_chart.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()


def plot_rolling_sharpe(returns: pd.Series,
                        window: int = 252,
                        title: str = "Rolling 252-Day Sharpe Ratio",
                        save_path: Optional[Path] = None) -> None:

    from metrics import sharpe_ratio
    
    rolling_sharpe = []
    for i in range(window, len(returns)):
        window_returns = returns.iloc[i-window:i]
        sharpe = sharpe_ratio(window_returns, risk_free_rate=0.0)
        rolling_sharpe.append(sharpe)
    
    rolling_sharpe_series = pd.Series(rolling_sharpe, index=returns.index[window:])
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    ax.plot(rolling_sharpe_series.index, rolling_sharpe_series.values,
            linewidth=2, color='#06A77D')
    ax.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
    ax.axhline(y=1, color='green', linestyle='--', linewidth=1, alpha=0.5, label='Sharpe = 1')
    
    ax.set_xlabel('Date', fontweight='bold')
    ax.set_ylabel('Rolling Sharpe Ratio', fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path is None:
        save_path = OUTPUT_DIR / "rolling_sharpe.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()


def plot_signal_heatmap(signals: pd.DataFrame,
                       title: str = "Signal Heatmap",
                       save_path: Optional[Path] = None) -> None:

    fig, ax = plt.subplots(figsize=(16, 8))
    
    signals_monthly = signals.resample('ME').last()
    
    sns.heatmap(signals_monthly.T, cmap='RdYlGn', center=0,
                cbar_kws={'label': 'Signal (Long/Neutral/Short)'},
                ax=ax, vmin=-1, vmax=1)
    
    ax.set_xlabel('Date', fontweight='bold')
    ax.set_ylabel('Currency Pair', fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    
    if save_path is None:
        save_path = OUTPUT_DIR / "signal_heatmap.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()


def plot_portfolio_leverage(leverage: pd.Series,
                           title: str = "Portfolio Leverage Over Time",
                           save_path: Optional[Path] = None) -> None:

    fig, ax = plt.subplots(figsize=(14, 6))
    
    ax.plot(leverage.index, leverage.values, linewidth=2, color='#F77F00')
    ax.axhline(y=1.0, color='black', linestyle='--', linewidth=1, alpha=0.5, label='1x Leverage')
    ax.axhline(y=2.0, color='red', linestyle='--', linewidth=1, alpha=0.5, label='Max Leverage (2x)')
    
    ax.set_xlabel('Date', fontweight='bold')
    ax.set_ylabel('Leverage Multiplier', fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    ax.set_ylim(bottom=0, top=leverage.max() * 1.1)
    
    plt.tight_layout()
    
    if save_path is None:
        save_path = OUTPUT_DIR / "portfolio_leverage.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()


def plot_correlation_heatmap(correlation_matrix: pd.DataFrame,
                            title: str = "Correlation Matrix",
                            save_path: Optional[Path] = None) -> None:

    fig, ax = plt.subplots(figsize=(10, 8))
    
    sns.heatmap(correlation_matrix, annot=True, fmt='.2f', cmap='coolwarm',
                center=0, vmin=-1, vmax=1, square=True,
                cbar_kws={'label': 'Correlation'},
                ax=ax)
    
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    
    if save_path is None:
        save_path = OUTPUT_DIR / "correlation_heatmap.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()


def plot_monthly_returns_heatmap(returns: pd.Series,
                                title: str = "Monthly Returns Heatmap",
                                save_path: Optional[Path] = None) -> None:

    monthly_returns = returns.resample('ME').apply(lambda x: np.exp(x.sum()) - 1) * 100
    
    monthly_returns.index = pd.to_datetime(monthly_returns.index)
    monthly_returns_df = pd.DataFrame({
        'Year': monthly_returns.index.year,
        'Month': monthly_returns.index.month,
        'Return': monthly_returns.values
    })
    
    pivot = monthly_returns_df.pivot(index='Year', columns='Month', values='Return')
    
    fig, ax = plt.subplots(figsize=(14, 10))
    
    sns.heatmap(pivot, annot=True, fmt='.1f', cmap='RdYlGn', center=0,
                cbar_kws={'label': 'Monthly Return (%)'},
                ax=ax, linewidths=0.5)
    
    ax.set_xlabel('Month', fontweight='bold')
    ax.set_ylabel('Year', fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    ax.set_xticklabels(month_labels)
    
    plt.tight_layout()
    
    if save_path is None:
        save_path = OUTPUT_DIR / "monthly_returns_heatmap.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()


def plot_return_distribution(returns: pd.Series,
                            title: str = "Return Distribution",
                            save_path: Optional[Path] = None) -> None:

    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.hist(returns.values * 100, bins=50, density=True, alpha=0.7,
            color='#2E86AB', edgecolor='black', label='Strategy Returns')
    
    mu = returns.mean() * 100
    sigma = returns.std() * 100
    x = np.linspace(returns.min() * 100, returns.max() * 100, 100)
    normal_pdf = (1 / (sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mu) / sigma) ** 2)
    ax.plot(x, normal_pdf, 'r-', linewidth=2, label=f'Normal (μ={mu:.2f}%, σ={sigma:.2f}%)')
    
    ax.set_xlabel('Daily Return (%)', fontweight='bold')
    ax.set_ylabel('Density', fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    
    stats_text = f'Mean: {mu:.2f}%\nStd: {sigma:.2f}%\nSkew: {returns.skew():.2f}\nKurtosis: {returns.kurtosis():.2f}'
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    
    if save_path is None:
        save_path = OUTPUT_DIR / "return_distribution.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()


if __name__ == "__main__":
    print("Plotting functions ready. Import and use in notebooks.")
