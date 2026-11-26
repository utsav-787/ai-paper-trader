import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from pathlib import Path

st.set_page_config(page_title="AI Paper Trader", page_icon="📈", layout="wide")

DATA_DIR = Path("paper_trader_data")
DATA_DIR.mkdir(exist_ok=True)
STATE_FILE = DATA_DIR / "account.json"

ASSETS = {
    "NIFTY 50": 24500.0,
    "BANK NIFTY": 52000.0,
    "RELIANCE": 1450.0,
    "TCS": 3200.0,
    "INFY": 1550.0,
    "HDFCBANK": 1750.0,
}

def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"cash": 100000.0, "starting_cash": 100000.0, "positions": {}, "trades": [], "daily_loss_limit": 2000.0}

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))

def make_demo_prices(symbol, base, periods=180):
    # Reproducible illustrative data. Not live market prices.
    seed = sum(ord(c) for c in symbol)
    rng = np.random.default_rng(seed)
    returns = rng.normal(0.00025, 0.012, periods)
    prices = base * np.exp(np.cumsum(returns))
    dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=periods, freq="B")
    return pd.DataFrame({"Date": dates, "Close": prices})

def strategy(df):
    out = df.copy()
    out["SMA20"] = out["Close"].rolling(20).mean()
    out["SMA50"] = out["Close"].rolling(50).mean()
    out["Signal"] = "HOLD"
    out.loc[(out["SMA20"] > out["SMA50"]) & (out["Close"] > out["SMA20"]), "Signal"] = "BUY"
    out.loc[(out["SMA20"] < out["SMA50"]) & (out["Close"] < out["SMA20"]), "Signal"] = "SELL"
    return out

def money(x):
    return f"₹{x:,.2f}"

state = load_state()

st.title("📈 AI Trading Assistant — Paper Trading")
st.caption("Version 1 • Simulation only • No real orders • Demo prices are illustrative, not live market data.")

with st.sidebar:
    st.header("Settings")
    symbol = st.selectbox("Market / stock", list(ASSETS.keys()))
    base = ASSETS[symbol]
    quantity = st.number_input("Order quantity", min_value=1, max_value=10000, value=1, step=1)
    daily_limit = st.number_input("Maximum daily loss (₹)", min_value=100.0, max_value=100000.0, value=float(state.get("daily_loss_limit", 2000)), step=100.0)
    state["daily_loss_limit"] = daily_limit
    st.divider()
    st.warning("This app uses generated demo prices. It is not connected to NSE, a broker, or a real AI prediction service.")
    if st.button("Reset paper account", type="secondary"):
        state = {"cash": 100000.0, "starting_cash": 100000.0, "positions": {}, "trades": [], "daily_loss_limit": daily_limit}
        save_state(state)
        st.rerun()

prices = make_demo_prices(symbol, base)
analysed = strategy(prices)
last = analysed.iloc[-1]
price = float(last["Close"])
signal = str(last["Signal"])

# Mark-to-market portfolio
market_value = 0.0
for sym, pos in state["positions"].items():
    current = float(make_demo_prices(sym, ASSETS[sym]).iloc[-1]["Close"])
    market_value += current * pos["qty"]
equity = float(state["cash"]) + market_value
unrealized = sum(
    (float(make_demo_prices(sym, ASSETS[sym]).iloc[-1]["Close"]) - pos["avg_price"]) * pos["qty"]
    for sym, pos in state["positions"].items()
)

today = datetime.now().date().isoformat()
today_pnl = sum(t["pnl"] for t in state["trades"] if t.get("date") == today)
loss_locked = today_pnl <= -state["daily_loss_limit"]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Paper account equity", money(equity))
c2.metric("Available cash", money(state["cash"]))
c3.metric("Open positions value", money(market_value))
c4.metric("Unrealized P/L", money(unrealized), delta=money(unrealized))

st.subheader(f"{symbol} — market snapshot")
left, right = st.columns([2, 1])
with left:
    st.line_chart(analysed.set_index("Date")[["Close", "SMA20", "SMA50"]], height=330)
with right:
    st.metric("Latest demo price", money(price))
    st.metric("Strategy signal", signal)
    st.write("**Signal explanation**")
    st.write("BUY: 20-day average is above 50-day average and price is above the 20-day average.")
    st.write("SELL: 20-day average is below 50-day average and price is below the 20-day average.")
    st.write("Otherwise: HOLD.")
    st.caption("This is a basic moving-average rule, not a validated AI forecast.")

st.subheader("Paper trading")
st.write(f"Selected quantity: **{quantity}** • Estimated order value: **{money(price * quantity)}**")
buy_col, sell_col = st.columns(2)

with buy_col:
    if st.button("Buy (virtual)", use_container_width=True, disabled=loss_locked):
        cost = price * quantity
        if cost > state["cash"]:
            st.error("Not enough virtual cash.")
        else:
            old = state["positions"].get(symbol, {"qty": 0, "avg_price": 0.0})
            new_qty = old["qty"] + quantity
            avg = ((old["qty"] * old["avg_price"]) + cost) / new_qty
            state["positions"][symbol] = {"qty": new_qty, "avg_price": avg}
            state["cash"] -= cost
            state["trades"].append({"date": today, "time": datetime.now().strftime("%H:%M:%S"), "symbol": symbol, "side": "BUY", "qty": quantity, "price": price, "pnl": 0.0})
            save_state(state)
            st.success("Virtual buy order recorded.")
            st.rerun()

with sell_col:
    held = state["positions"].get(symbol, {}).get("qty", 0)
    if st.button("Sell (virtual)", use_container_width=True, disabled=(held < quantity)):
        pos = state["positions"][symbol]
        proceeds = price * quantity
        pnl = (price - pos["avg_price"]) * quantity
        state["cash"] += proceeds
        pos["qty"] -= quantity
        if pos["qty"] == 0:
            del state["positions"][symbol]
        state["trades"].append({"date": today, "time": datetime.now().strftime("%H:%M:%S"), "symbol": symbol, "side": "SELL", "qty": quantity, "price": price, "pnl": pnl})
        save_state(state)
        st.success(f"Virtual sell recorded. Realized P/L: {money(pnl)}")
        st.rerun()

if loss_locked:
    st.error("Daily loss limit reached. New virtual buys are disabled for today.")

st.subheader("Open positions")
if state["positions"]:
    rows = []
    for sym, pos in state["positions"].items():
        px = float(make_demo_prices(sym, ASSETS[sym]).iloc[-1]["Close"])
        rows.append({"Symbol": sym, "Quantity": pos["qty"], "Average price": pos["avg_price"], "Demo price": px, "Unrealized P/L": (px-pos["avg_price"])*pos["qty"]})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
else:
    st.info("No open positions. Use Buy (virtual) to try a simulated trade.")

st.subheader("Trade history")
if state["trades"]:
    st.dataframe(pd.DataFrame(state["trades"]).iloc[::-1], use_container_width=True, hide_index=True)
else:
    st.info("No trades yet.")

st.subheader("Simple historical strategy check")
bt = analysed.dropna().copy()
bt["Position"] = (bt["Signal"] == "BUY").astype(int)
bt["Market return"] = bt["Close"].pct_change().fillna(0)
bt["Strategy return"] = bt["Position"].shift(1).fillna(0) * bt["Market return"]
growth = (1 + bt["Strategy return"]).cumprod()
market_growth = (1 + bt["Market return"]).cumprod()
b1, b2, b3 = st.columns(3)
b1.metric("Illustrative strategy return", f"{(growth.iloc[-1]-1)*100:.2f}%")
b2.metric("Buy-and-hold return", f"{(market_growth.iloc[-1]-1)*100:.2f}%")
b3.metric("Trading days tested", f"{len(bt)}")
st.line_chart(pd.DataFrame({"Strategy": growth.values, "Buy & hold": market_growth.values}, index=bt["Date"]), height=240)
st.caption("Backtest is illustrative, uses generated data, and excludes brokerage, taxes, slippage and market impact. Past simulated results do not predict future returns.")

st.divider()
st.caption("Educational prototype only. Not investment advice. Never connect real funds until data, strategy, risk controls, broker integration and regulatory requirements have been independently reviewed.")
