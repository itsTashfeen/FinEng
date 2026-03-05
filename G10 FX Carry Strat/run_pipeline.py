import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent / 'src'))

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

print("=" * 70)
print("G10 FX Carry Strategy - Full Pipeline Execution")
print("=" * 70)

print("\n[Step 1/5] Data Ingestion & Cleaning...")
from data_loader import (
    load_fx_data, load_interest_rates, compute_carry_per_pair,
    align_data, save_processed_data
)

fx_returns = load_fx_data(start_date='2002-04-01')
print(f"  [OK] Loaded FX returns: {fx_returns.shape}")

ir_rates = load_interest_rates(start_date='2002-04-01')
print(f"  [OK] Loaded interest rates: {ir_rates.shape}")

carry = compute_carry_per_pair(fx_returns, ir_rates)
print(f"  [OK] Computed carry: {carry.shape}")

fx_returns, ir_rates, carry = align_data(fx_returns, ir_rates, carry)
print(f"  [OK] Aligned data: {len(fx_returns)} trading days")

save_processed_data(fx_returns, carry)
print("  [OK] Saved processed data")

print("\n[Step 2/5] Signal Construction...")
from signals import compute_signals, compute_raw_signals, apply_signal_lag

signals = compute_signals(carry, lag_days=1)
raw_signals_lagged = apply_signal_lag(compute_raw_signals(carry), lag_days=1)
signal_change_days = (raw_signals_lagged.diff().abs().sum(axis=1) > 0).sum()
print(f"Days with signal change: {signal_change_days} out of {len(raw_signals_lagged)}")
print(f"  [OK] Computed signals: {signals.shape}")

print("\n[Step 3/5] Volatility Targeting & Weight Construction...")
from portfolio import construct_portfolio

weights, vol, leverage, transaction_costs = construct_portfolio(
    signals, fx_returns, target_vol=0.10, max_leverage=2.0,
    signals_for_tc=raw_signals_lagged
)
print(f"  [OK] Constructed portfolio: {weights.shape}")
print(f"  [OK] Average leverage: {leverage.mean():.2f}x")
print(f"  [OK] Max leverage: {leverage.max():.2f}x")

save_processed_data(fx_returns, carry, weights)
print("  [OK] Saved portfolio weights")

print("\n[Step 4/5] Backtest Engine & Performance Metrics...")
from backtest import run_backtest, compute_drawdown, load_benchmark_data
from metrics import compute_all_metrics

benchmark_returns = load_benchmark_data('SPY', start_date='2002-04-01')
results = run_backtest(fx_returns, weights, transaction_costs, benchmark_returns)
print(f"  [OK] Backtest complete: {results.shape}")

print("\nGross vs Net annual returns (%):")
gross_annual = results['gross_return'].resample('YE').sum() * 100
net_annual = results['net_return'].resample('YE').sum() * 100
tc_drag = gross_annual - net_annual
print(pd.DataFrame({'Gross': gross_annual, 'Net': net_annual, 'TC_Drag': tc_drag}).round(2))
print(f"  Mean annual TC drag: {tc_drag.mean():.2f}%")

benchmark_for_metrics = results['benchmark_return'] if 'benchmark_return' in results.columns else None
metrics = compute_all_metrics(
    results['net_return'],
    benchmark_returns=benchmark_for_metrics,
    risk_free_rate=0.0
)
print("  [OK] Computed all performance metrics")

print("\n[Step 5/5] Generate Charts & Outputs...")
from plots import (
    plot_equity_curve, plot_drawdown, plot_rolling_sharpe,
    plot_signal_heatmap, plot_portfolio_leverage, plot_correlation_heatmap,
    plot_monthly_returns_heatmap, plot_return_distribution
)

benchmark_cum = results['cumulative_benchmark'] if 'cumulative_benchmark' in results.columns else None
plot_equity_curve(results['cumulative_net'], benchmark_cumulative=benchmark_cum, 
                 title='Equity Curve: G10 FX Carry Strategy vs. SPY', log_scale=True)
print("  [OK] Equity curve saved")

drawdown = compute_drawdown(results['net_return'])
highlight_periods = [
    (pd.Timestamp('2008-09-01'), pd.Timestamp('2008-12-31'), '2008 Crisis'),
    (pd.Timestamp('2020-03-01'), pd.Timestamp('2020-04-30'), 'COVID-19')
]
plot_drawdown(drawdown, title='Drawdown Chart', highlight_periods=highlight_periods)
print("  [OK] Drawdown chart saved")

plot_rolling_sharpe(results['net_return'], window=252, title='Rolling 252-Day Sharpe Ratio')
print("  [OK] Rolling Sharpe chart saved")

plot_signal_heatmap(signals, title='Signal Heatmap: Long/Neutral/Short Over Time')
print("  [OK] Signal heatmap saved")

plot_portfolio_leverage(leverage, title='Portfolio Leverage Over Time')
print("  [OK] Portfolio leverage chart saved")

plot_monthly_returns_heatmap(results['net_return'], title='Monthly Returns Heatmap')
print("  [OK] Monthly returns heatmap saved")

plot_return_distribution(results['net_return'], title='Return Distribution')
print("  [OK] Return distribution saved")

if 'benchmark_return' in results.columns and results['benchmark_return'].notna().any():
    corr_val = results['net_return'].corr(results['benchmark_return'])
    corr_matrix = pd.DataFrame({
        'Strategy': [1.0, corr_val],
        'SPY': [corr_val, 1.0]
    }, index=['Strategy', 'SPY'])
    plot_correlation_heatmap(corr_matrix, title='Correlation Matrix: Strategy vs. SPY')
    print("  [OK] Correlation heatmap saved")

summary_data = {
    'Metric': [
        'Total Return (April 1, 2002-February 27, 2026)',
        'Annualized Return',
        'Annualized Volatility',
        'Sharpe Ratio',
        'Sortino Ratio',
        'Calmar Ratio',
        'Max Drawdown',
        'Max DD Duration',
        'VaR (95%, daily)',
        'CVaR (95%, daily)',
        'Skewness',
        'Kurtosis',
        'Hit Rate',
    ],
    'Strategy': [
        f"{metrics.get('Total_Return', 0):.2f}%",
        f"{metrics.get('Annualized_Return', 0):.2f}%",
        f"{metrics.get('Annualized_Volatility', 0):.2f}%",
        f"{metrics.get('Sharpe_Ratio', 0):.2f}",
        f"{metrics.get('Sortino_Ratio', 0):.2f}",
        f"{metrics.get('Calmar_Ratio', 0):.2f}",
        f"{metrics.get('Max_Drawdown', 0):.2f}%",
        f"{metrics.get('Max_DD_Duration', 0)} days",
        f"{metrics.get('VaR_95pct', 0):.2f}%",
        f"{metrics.get('CVaR_95pct', 0):.2f}%",
        f"{metrics.get('Skewness', 0):.2f}",
        f"{metrics.get('Kurtosis', 0):.2f}",
        f"{metrics.get('Hit_Rate', 0):.2f}%",
    ]
}

if benchmark_for_metrics is not None:
    summary_data['Benchmark (SPY)'] = [
        f"{metrics.get('Benchmark_Total_Return', 0):.2f}%",
        f"{metrics.get('Benchmark_Annualized_Return', 0):.2f}%",
        f"{metrics.get('Benchmark_Annualized_Volatility', 0):.2f}%",
        f"{metrics.get('Benchmark_Sharpe_Ratio', 0):.2f}",
        '—',
        '—',
        f"{metrics.get('Benchmark_Max_Drawdown', 0):.2f}%",
        f"{metrics.get('Benchmark_Max_DD_Duration', 0)} days",
        '—',
        '—',
        '—',
        '—',
        f"{metrics.get('Benchmark_Hit_Rate', 0):.2f}%",
    ]

summary_df = pd.DataFrame(summary_data)
summary_df.to_csv('output/performance_table.csv', index=False)
print("  [OK] Performance table saved")

print("\n" + "=" * 70)
print("PERFORMANCE SUMMARY")
print("=" * 70)
for key, value in sorted(metrics.items()):
    if isinstance(value, float) and not np.isnan(value):
        print(f"{key:35s}: {value:12.4f}")

print("\n" + "=" * 70)
print("Pipeline execution complete!")
print("All outputs saved to output/ directory")
print("=" * 70)
