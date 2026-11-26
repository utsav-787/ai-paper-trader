# AI Trading Assistant — Paper Trading MVP

This is a beginner-friendly **simulation prototype**. It does not place real orders and is not connected to live market data, NSE, a broker, or an AI prediction API.

## Run it

1. Install Python 3.10 or newer from https://www.python.org/downloads/
2. Extract this ZIP.
3. Open a terminal / Command Prompt in the extracted `ai_paper_trader` folder.
4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Start the app:

   ```bash
   streamlit run app.py
   ```

6. Your browser should open the dashboard. If it does not, visit http://localhost:8501

## What is included

- Demo market charts for NIFTY 50, BANK NIFTY and selected stocks
- Transparent moving-average BUY / SELL / HOLD signals
- Virtual buy and sell orders
- Virtual ₹1,00,000 starting balance
- Open-position and P/L tracking
- Daily loss guard for disabling new virtual buys
- Simple illustrative backtest

## Important limitations

- All prices are generated demo data, not live prices.
- The signal engine is a simple technical rule, not an AI model and not a proven profitable strategy.
- The backtest uses generated data and excludes fees, taxes, slippage and market impact.
- Account state is stored locally in `paper_trader_data/account.json`.
- No broker credentials or API keys are required or supported in this version.

## Before any real-money version

A future version would need a reputable live data provider, a properly validated strategy, realistic backtesting, paper trading over a meaningful period, secure broker API integration, strong risk controls, and review of applicable SEBI / exchange / broker requirements. Do not treat this prototype as a source of income.
