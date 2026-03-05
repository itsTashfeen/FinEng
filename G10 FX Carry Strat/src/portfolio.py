"""
portfolio construction module:
vol targeting and position sizing
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional


def compute_realized_volatility(fx_returns: pd.DataFrame, window: int = 63, lag_days: int = 1) -> pd.DataFrame:
    rolling_std = fx_returns.rolling(window=window).std()
    vol = rolling_std * np.sqrt(252)
    vol = vol.shift(lag_days) # avoiding the fatal mistake i made last time, similar to signals.py
    
    return vol


def compute_inverse_vol_weights(signals: pd.DataFrame, vol: pd.DataFrame) -> pd.DataFrame:
    weights = pd.DataFrame(index=signals.index, columns=signals.columns, dtype=float)
    weights[:] = 0.0
    
    for date in signals.index:
        signal_row = signals.loc[date]
        vol_row = vol.loc[date]
        
        longs = signal_row[signal_row == 1.0].index
        shorts = signal_row[signal_row == -1.0].index
        
        if len(longs) > 0: # computing inverse-vol weights
            inv_vol_longs = 1.0 / vol_row[longs]
            inv_vol_longs = inv_vol_longs.replace([np.inf, -np.inf], 0.0)
            inv_vol_longs = inv_vol_longs.fillna(0.0)
            
            sum_inv_vol_longs = inv_vol_longs.sum()
            if sum_inv_vol_longs > 0:
                weights.loc[date, longs] = inv_vol_longs / sum_inv_vol_longs
        
        if len(shorts) > 0: 
            inv_vol_shorts = 1.0 / vol_row[shorts]
            inv_vol_shorts = inv_vol_shorts.replace([np.inf, -np.inf], 0.0)
            inv_vol_shorts = inv_vol_shorts.fillna(0.0)
            
            sum_inv_vol_shorts = inv_vol_shorts.sum()
            if sum_inv_vol_shorts > 0:
                weights.loc[date, shorts] = -inv_vol_shorts / sum_inv_vol_shorts
    
    return weights


def compute_portfolio_volatility(weights: pd.DataFrame, fx_returns: pd.DataFrame, window: int = 63) -> pd.Series:

    portfolio_returns = (weights * fx_returns).sum(axis=1)
    port_vol = portfolio_returns.rolling(window=window).std() * np.sqrt(252)
    
    return port_vol


def scale_to_target_vol(weights: pd.DataFrame, fx_returns: pd.DataFrame, 
                        target_vol: float = 0.10, max_leverage: float = 2.0,
                        window: int = 63) -> Tuple[pd.DataFrame, pd.Series]:

    # computing portfolio volatility - rolling based on unscaled weights
    port_vol = compute_portfolio_volatility(weights, fx_returns, window=window)
    port_vol = port_vol.shift(1)
    
    port_vol_safe = port_vol.replace(0, np.nan)
    scalar = target_vol / port_vol_safe
    scalar = scalar.fillna(1.0)  # no scaling when vol is undefined
    
    # floor prevents the book from being crushed to zero size in high vol regimes
    scalar = scalar.clip(lower=0.5, upper=max_leverage)
    scaled_weights = weights.multiply(scalar, axis=0)
    
    return scaled_weights, scalar


def compute_transaction_costs(weights: pd.DataFrame,
                             signals: pd.DataFrame,
                             cost_per_unit: float = 0.0002,
                             signals_for_tc: Optional[pd.DataFrame] = None) -> pd.Series:


    use = signals_for_tc if signals_for_tc is not None else signals
    signal_changed = use.diff().abs().sum(axis=1) > 0
    signal_changed = signal_changed.reindex(weights.index).fillna(False)
    turnover = weights.diff().abs().sum(axis=1)
    transaction_costs = turnover * cost_per_unit * signal_changed.astype(float)
    transaction_costs.iloc[0] = 0.0
    return transaction_costs


def construct_portfolio(signals: pd.DataFrame, fx_returns: pd.DataFrame,
                       target_vol: float = 0.10, max_leverage: float = 2.0,
                       vol_window: int = 63, cost_per_unit: float = 0.0002,
                       signals_for_tc: Optional[pd.DataFrame] = None) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:

    vol = compute_realized_volatility(fx_returns, window=vol_window, lag_days=1)
    weights = compute_inverse_vol_weights(signals, vol)
    final_weights, leverage = scale_to_target_vol(
        weights, fx_returns, target_vol=target_vol, 
        max_leverage=max_leverage, window=vol_window
    )
    
    transaction_costs = compute_transaction_costs(
        final_weights, signals, cost_per_unit=cost_per_unit, signals_for_tc=signals_for_tc
    )
    
    return final_weights, vol, leverage, transaction_costs


if __name__ == "__main__": # test usage like usual
    
    from data_loader import load_processed_data
    from signals import compute_signals
    
    print("Loading processed data...")
    fx_returns, carry, _ = load_processed_data()
    
    print("Computing signals...")
    signals = compute_signals(carry, lag_days=1)
    
    print("Constructing portfolio...")
    weights, vol, leverage, tc = construct_portfolio(
        signals, fx_returns, target_vol=0.10, max_leverage=2.0
    )
    
    print(f"Weights shape: {weights.shape}")
    print(f"Average leverage: {leverage.mean():.2f}x")
    print(f"Max leverage: {leverage.max():.2f}x")
    print(f"Total transaction costs: {tc.sum():.4f}")
