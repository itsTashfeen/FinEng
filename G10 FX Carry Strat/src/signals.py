"""
signal construction module
regime filter - only run when avg abs rate differential exceeds threshold
this avoids flatting in ZIRP env

STRAT:
highest carry 1-3 -> long +1
neutral carry 4-6 -> neutral 0
lowest carry 7-9 -> short -1
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional

from pandas.plotting import lag_plot


def comput_raw_signals(carry: pd.DataFrame) -> pd.DataFrame:
    carry_monthly = carry.resample('ME').last() # resample to month end to avoid daily ranking noise

    ranks = carry_monthly.rank(axis=1, ascending=False, method ="first")
    raw_signals_monthly = pd.DataFrame(0.0,
                                        index = carry_monthly.index,
                                        columns = carry_monthly.columns)
    
    raw_signals_monthly[ranks <= 3] = 1.0
    raw_signals_monthly[ranks > 6] = -1.0

    daily_index = carry.index # forward fill back to daily frequency
    raw_signals = raw_signals_monthly.reindex(daily_index, method='ffill')

    return raw_signals


def apply_signal_lag(raw_signals: pd.DataFrame, lag_days: int = 1) -> pd.DataFrame:
    signals = raw_signals.shift(lag_days) # :) preventing that bias baby
    return signals


def compute_regime_filter(carry: pd.DataFrame, lag_days: int, regime_min_differential_pct: float,) -> pd.Series:

    threshold_decimal = regime_min_differential_pct / 100.0

    active_mag = carry.abs()
    top3 = active_mag.apply(lambda row: row.nlargest(3).mean(), axis=1)
    bot3 = active_mag.apply(lambda row: row.nsmallest(3).mean(), axis=1)
    avg_active_carry = (top3 + bot3) / 2
    regime_ok = (avg_active_carry >= threshold_decimal).shift(lag_days)
    return regime_ok


def compute_signals(carry: pd.DataFrame, lag_days: int = 1, regime_min_differential_pct: Optional[float] = 1.0,) -> pd.DataFrame:

    raw_signals = compute_raw_signals(carry)
    signals = apply_signal_lag(raw_signals, lag_days=lag_days)
    if regime_min_differential_pct is not None:
        regime_ok = compute_regime_filter(
            carry, lag_days=lag_days, regime_min_differential_pct=regime_min_differential_pct
        )
        signals = signals.where(regime_ok, 0.0)
    return signals


def get_signal_summary(signals: pd.DataFrame) -> pd.DataFrame:
    summary = pd.DataFrame({
        'Long_Count': (signals == 1).sum(),
        'Neutral_Count': (signals == 0).sum(),
        'Short_Count': (signals == -1).sum(),
        'Long_Pct': (signals == 1).sum() / len(signals) * 100,
        'Neutral_Pct': (signals == 0).sum() / len(signals) * 100,
        'Short_Pct': (signals == -1).sum() / len(signals) * 100,
    })
    
    return summary


if __name__ == "__main__": # test usage

    from data_loader import load_processed_data
    
    print("Loading processed data...")
    fx_returns, carry, _ = load_processed_data()
    
    print("Computing signals...")
    signals = compute_signals(carry, lag_days=1)
    
    print(f"Signals shape: {signals.shape}")
    print(f"Date range: {signals.index.min()} to {signals.index.max()}")
    
    print("\nSignal summary:")
    summary = get_signal_summary(signals)
    print(summary)
