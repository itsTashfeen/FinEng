"""
data load module to:
loads and clean FX spot data and interest rate data from CSV files.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Tuple


DATA_RAW_FX = Path(__file__).parent.parent / "data" / "raw" / "fx_spot"
DATA_RAW_IR = Path(__file__).parent.parent / "data" / "raw" / "interest_rates"
DATA_PROCESSED = Path(__file__).parent.parent / "data" / "processed"

FX_PAIRS = {
    "EURUSD": "EURUSD_daily.csv",
    "USDJPY": "USDJPY_daily.csv",
    "GBPUSD": "GBPUSD_daily.csv",
    "AUDUSD": "AUDUSD_daily.csv",
    "NZDUSD": "NZDUSD_daily.csv",
    "USDCAD": "USDCAD_daily.csv",
    "USDCHF": "USDCHF_daily.csv",
    "USDNOK": "USDNOK_daily.csv",
    "USDSEK": "USDSEK_daily.csv",
}

USD_BASE_PAIRS = ["USDCAD", "USDCHF", "USDNOK", "USDSEK", "USDJPY"]

IR_CURRENCIES = {
    "USD": "DTB3.csv",
    "EUR": "IR3TIB01EZM156N.csv",
    "JPY": "IR3TIB01JPM156N.csv",
    "GBP": "IR3TIB01GBM156N.csv",
    "AUD": "IR3TIB01AUM156N.csv",
    "NZD": "IR3TIB01NZM156N.csv",
    "CAD": "IR3TIB01CAM156N.csv",
    "CHF": "IR3TIB01CHM156N.csv",
    "NOK": "IR3TIB01NOM156N.csv",
    "SEK": "IR3TIB01SEM156N.csv",
}


def load_fx_data(start_date: str = "2002-04-01", end_date: str = None) -> pd.DataFrame:
    """
    retruns are daily log returns
    USD-base pairs sign is flipped as that would correctly represent the long foreign return
    """
    fx_data = {}
    
    for pair, filename in FX_PAIRS.items():
        filepath = DATA_RAW_FX / filename
        
        if not filepath.exists():
            raise FileNotFoundError(f"FX data file not found: {filepath}")
        

        df = pd.read_csv(filepath, skipfooter=1, engine='python') # barchart adds a footer so i skipped it
        
        
        date_col = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()][0] # parse date column as barchart uses "Time"
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce') # using coerce to easily drop naT values
        df = df.dropna(subset=[date_col])
        df.set_index(date_col, inplace=True)
        df.sort_index(inplace=True)
        
        close_col = [col for col in df.columns if 'close' in col.lower() or 'latest' in col.lower()][0]
        prices = df[close_col].astype(float)
        log_returns = np.log(prices / prices.shift(1))
        

        if pair in USD_BASE_PAIRS:
            log_returns = -log_returns
        
        fx_data[pair] = log_returns
    
    fx_returns = pd.DataFrame(fx_data)
    
    if start_date:
        fx_returns = fx_returns[fx_returns.index >= start_date]
    if end_date:
        fx_returns = fx_returns[fx_returns.index <= end_date]
    
    fx_returns = fx_returns.dropna(how='all')
    
    return fx_returns


def load_interest_rates(start_date: str = "2002-04-01", end_date: str = None) -> pd.DataFrame:

    ir_data = {}
    
    for currency, filename in IR_CURRENCIES.items():
        filepath = DATA_RAW_IR / filename
        
        if not filepath.exists():
            raise FileNotFoundError(f"Interest rate file not found: {filepath}")
        
        df = pd.read_csv(filepath)
        
        date_col = [col for col in df.columns if 'date' in col.lower()][0]
        value_col = [col for col in df.columns if col != date_col][0]
        
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=[date_col])
        df.set_index(date_col, inplace=True)
        df.sort_index(inplace=True)
        
        
        rates = pd.to_numeric(df[value_col], errors='coerce') / 100.0 
        """again using coerce to drop NaT's. Rate values from FRED are in percentages"""
        
        daily_index = pd.date_range(start=rates.index.min(), end=rates.index.max(), freq='D')
        rates_daily = rates.reindex(daily_index, method='ffill')
        ir_data[currency] = rates_daily
    
    ir_rates = pd.DataFrame(ir_data)

    if start_date:
        ir_rates = ir_rates[ir_rates.index >= start_date]
    if end_date:
        ir_rates = ir_rates[ir_rates.index <= end_date]
    
    ir_rates = ir_rates.dropna(how='all')
    
    return ir_rates


def compute_carry_per_pair(fx_returns: pd.DataFrame, ir_rates: pd.DataFrame) -> pd.DataFrame:

    common_dates = fx_returns.index.intersection(ir_rates.index) # alligning dates for carry calculation

    fx_returns = fx_returns.loc[common_dates]
    ir_rates = ir_rates.loc[common_dates]
    
    carry_data = {}
    
    pair_to_foreign_currency = {
        "EURUSD": "EUR",
        "USDJPY": "JPY",
        "GBPUSD": "GBP",
        "AUDUSD": "AUD",
        "NZDUSD": "NZD",
        "USDCAD": "CAD",
        "USDCHF": "CHF",
        "USDNOK": "NOK",
        "USDSEK": "SEK",
    }
    
    for pair, foreign_curr in pair_to_foreign_currency.items():
        foreign_rate = ir_rates[foreign_curr]
        usd_rate = ir_rates['USD']
        carry_data[pair] = foreign_rate - usd_rate
    
    carry = pd.DataFrame(carry_data, index=common_dates)
    
    return carry


def align_data(fx_returns: pd.DataFrame, ir_rates: pd.DataFrame, carry: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:

    common_dates = fx_returns.index.intersection(ir_rates.index).intersection(carry.index)
    
    fx_returns_aligned = fx_returns.loc[common_dates]
    ir_rates_aligned = ir_rates.loc[common_dates]
    carry_aligned = carry.loc[common_dates]
    
    return fx_returns_aligned, ir_rates_aligned, carry_aligned


def save_processed_data(fx_returns: pd.DataFrame, carry: pd.DataFrame, portfolio_weights: pd.DataFrame = None):

    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    
    fx_returns.to_parquet(DATA_PROCESSED / "fx_returns.parquet")
    carry.to_parquet(DATA_PROCESSED / "carry_signals.parquet")
    if portfolio_weights is not None:
        portfolio_weights.to_parquet(DATA_PROCESSED / "portfolio_weights.parquet")


def load_processed_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:

    fx_returns = pd.read_parquet(DATA_PROCESSED / "fx_returns.parquet")
    carry = pd.read_parquet(DATA_PROCESSED / "carry_signals.parquet")
    
    portfolio_weights_path = DATA_PROCESSED / "portfolio_weights.parquet"
    portfolio_weights = None
    if portfolio_weights_path.exists():
        portfolio_weights = pd.read_parquet(portfolio_weights_path)
    
    return fx_returns, carry, portfolio_weights


if __name__ == "__main__": # for testing
    
    print("Loading FX data...")
    fx_returns = load_fx_data()
    print(f"FX returns shape: {fx_returns.shape}")
    print(f"Date range: {fx_returns.index.min()} to {fx_returns.index.max()}")
    
    print("\nLoading interest rate data...")
    ir_rates = load_interest_rates()
    print(f"Interest rates shape: {ir_rates.shape}")
    print(f"Date range: {ir_rates.index.min()} to {ir_rates.index.max()}")
    
    print("\nComputing carry per pair...")
    carry = compute_carry_per_pair(fx_returns, ir_rates)
    print(f"Carry shape: {carry.shape}")
    
    print("\nAligning data...")
    fx_returns, ir_rates, carry = align_data(fx_returns, ir_rates, carry)
    print(f"Aligned date range: {fx_returns.index.min()} to {fx_returns.index.max()}")
    
    print("\nSaving processed data...")
    save_processed_data(fx_returns, carry)
    print("Done!")
