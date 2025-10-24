# Polymarket BTC Binary Option Pricer

A probabilistic arbitrage bot for Polymarket binary options trading, focusing on BTC price movements over 15-minute intervals.

## Project Overview

This project implements a systematic approach to identifying and exploiting pricing inefficiencies in Polymarket's BTC binary options. The strategy is built around accurate probability modeling rather than execution speed, with rigorous backtesting and risk management.

I am very skeptical of how this will turn out as it will be my first time putting a trading system together. Nevertheless, I'm willing to devote the time as one learns through experience.

## Project Structure

```
polymarket-btc-pricer/
├── src/                          # Main source code
│   ├── data/                     # Data acquisition and storage
│   ├── models/                   # ML models and prediction engines
│   ├── trading/                  # Trading logic and execution
│   ├── risk/                     # Risk management modules
│   ├── monitoring/               # Monitoring and alerting
│   ├── utils/                    # Utility functions
│   └── config/                   
├── notebooks/                    # Jupyter notebooks for analysis
├── tests/                        # Test suites
├── config/                       # Configuration files
├── data/                         # Data storage (local)
├── logs/                         # Application logs
├── docs/                         # Documentation
└── scripts/                      # Utility scripts
```

## Phase Implementation - Refer to roadmap.

- **Phase 0**: Feasibility Study & Strategy Validation
- **Phase 1**: Research, Modeling, and Backtesting
- **Phase 2**: Live Forward-Testing & Infrastructure
- **Phase 3**: Live Deployment & Risk Management
- **Phase 4**: Optimization & Scaling

## Getting Started

1. Install dependencies: `pip install -r requirements.txt`
2. Configure environment variables: `cp .env.example .env`
3. Run Phase 0 feasibility study: `python scripts/phase0_feasibility.py`

## License

Private project - All rights reserved.
