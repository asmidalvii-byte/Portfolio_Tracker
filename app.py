import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, date

# -- Strategy logic

def moving_average_crossover(df, short=20, long=50):
    df = df.copy()
    df["short_ma"] = df["Close"].rolling(short).mean()
    df["long_ma"] = df["Close"].rolling(long).mean()
    df["signal"] = 0
    df.loc[df["short_ma"] > df["long_ma"], "signal"] = 1
    df.loc[df["short_ma"] < df["long_ma"], "signal"] = -1
    df["position"] = df["signal"].diff()
    return df

def rsi_strategy(df, period=14, oversold=30, overbought=70):
    df = df.copy()
    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    df["rsi"] = 100 - (100 / (1 + rs))
    df["signal"] = 0
    df.loc[df["rsi"] < oversold, "signal"] = 1
    df.loc[df["rsi"] > overbought, "signal"] = -1
    df["position"] = df["signal"].diff()
    return df

def run_backtest(df, initial_capital=10000):
    capital = initial_capital
    shares = 0
    trades = []
    portfolio_values = []
    buy_price = 0
    in_position = False

    for i, row in df.iterrows():
        price = row["Close"]
        sig = row["signal"]

        if sig == 1 and not in_position and capital >= price:
            shares = capital / price
            buy_price = price
            capital = 0
            in_position = True
            trades.append({
                "Date": i,
                "Action": "BUY",
                "Price": round(price, 2),
                "Shares": round(shares, 4),
                "Value": round(shares * price, 2),
                "P&L": "—",
                "P&L %": "—"
            })

        elif sig == -1 and in_position and shares > 0:
            capital = shares * price
            pnl = (price - buy_price) * shares
            pnl_pct = ((price - buy_price) / buy_price) * 100
            trades.append({
                "Date": i,
                "Action": "SELL",
                "Price": round(price, 2),
                "Shares": round(shares, 4),
                "Value": round(capital, 2),
                "P&L": round(pnl, 2),
                "P&L %": round(pnl_pct, 2)
            })
            shares = 0
            in_position = False

        portfolio_value = capital + shares * price
        portfolio_values.append({"Date": i, "Value": portfolio_value})

    final_value = capital + shares * df["Close"].iloc[-1]
    return trades, portfolio_values, final_value

def calc_metrics(portfolio_values, initial_capital, trades):
    df_pv = pd.DataFrame(portfolio_values).set_index("Date")
    total_return = ((df_pv["Value"].iloc[-1] - initial_capital) / initial_capital) * 100
    daily_returns = df_pv["Value"].pct_change().dropna()
    sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252) if daily_returns.std() != 0 else 0
    rolling_max = df_pv["Value"].cummax()
    drawdown = (df_pv["Value"] - rolling_max) / rolling_max * 100
    max_drawdown = drawdown.min()
    sell_trades = [t for t in trades if t["Action"] == "SELL"]
    wins = [t for t in sell_trades if t.get("P&L", 0) > 0]
    win_rate = (len(wins) / len(sell_trades) * 100) if sell_trades else 0
    return {
        "Total Return %": round(total_return, 2),
        "Sharpe Ratio": round(sharpe, 2),
        "Max Drawdown %": round(max_drawdown, 2),
        "Win Rate %": round(win_rate, 2),
        "Total Trades": len(sell_trades)
    }

# -- App
st.set_page_config(page_title="Backtesting Engine", layout="wide")
st.title("Backtesting Engine")

# Sidebar controls
with st.sidebar:
    st.header("Settings")
    ticker = st.text_input("Ticker", value="AAPL")
    start_date = st.date_input("Start date", value=date(2020, 1, 1))
    end_date = st.date_input("End date", value=date.today())
    initial_capital = st.number_input("Initial capital (USD)", value=10000, min_value=100, step=100)
    strategy = st.selectbox("Strategy", ["Moving Average Crossover", "RSI Oversold/Overbought"])

    if strategy == "Moving Average Crossover":
        short_ma = st.slider("Short MA period", 5, 50, 20)
        long_ma = st.slider("Long MA period", 20, 200, 50)
    else:
        rsi_period = st.slider("RSI period", 7, 30, 14)
        oversold = st.slider("Oversold threshold", 20, 40, 30)
        overbought = st.slider("Overbought threshold", 60, 80, 70)

    run = st.button("Run backtest")

if run:
    with st.spinner("Fetching data and running backtest..."):
        raw = yf.Ticker(ticker).history(start=start_date, end=end_date)

        if raw.empty:
            st.error("No data found. Check the ticker and date range.")
        else:
            if strategy == "Moving Average Crossover":
                df = moving_average_crossover(raw, short_ma, long_ma)
            else:
                df = rsi_strategy(raw, rsi_period, oversold, overbought)

            trades, portfolio_values, final_value = run_backtest(df, initial_capital)
            metrics = calc_metrics(portfolio_values, initial_capital, trades)

            # Metrics
            st.subheader("Performance")
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Total Return", f"{metrics['Total Return %']}%")
            m2.metric("Sharpe Ratio", metrics["Sharpe Ratio"])
            m3.metric("Max Drawdown", f"{metrics['Max Drawdown %']}%")
            m4.metric("Win Rate", f"{metrics['Win Rate %']}%")
            m5.metric("Total Trades", metrics["Total Trades"])

            st.divider()

            # Portfolio value chart
            st.subheader("Portfolio value over time")
            df_pv = pd.DataFrame(portfolio_values)
            df_bh = pd.DataFrame({
                "Date": df.index,
                "Value": initial_capital * (df["Close"] / df["Close"].iloc[0])
            })

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_pv["Date"], y=df_pv["Value"],
                mode="lines", name="Strategy",
                line=dict(color="#1a9e6e", width=2)
            ))
            fig.add_trace(go.Scatter(
                x=df_bh["Date"], y=df_bh["Value"],
                mode="lines", name="Buy and hold",
                line=dict(color="#888", width=1.5, dash="dash")
            ))
            fig.update_layout(
                paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
                font=dict(color="white"),
                xaxis=dict(showgrid=False, color="white"),
                yaxis=dict(showgrid=True, gridcolor="#222", color="white"),
                legend=dict(font=dict(color="white")),
                margin=dict(t=20, b=20, l=20, r=20)
            )
            st.plotly_chart(fig, use_container_width=True)

            st.divider()

            # Price chart with buy/sell signals
            st.subheader("Price chart with signals")
            buy_signals = [t for t in trades if t["Action"] == "BUY"]
            sell_signals = [t for t in trades if t["Action"] == "SELL"]

            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=df.index, y=df["Close"],
                mode="lines", name="Price",
                line=dict(color="#4a9eda", width=1.5)
            ))
            if buy_signals:
                fig2.add_trace(go.Scatter(
                    x=[t["Date"] for t in buy_signals],
                    y=[t["Price"] for t in buy_signals],
                    mode="markers", name="Buy",
                    marker=dict(color="#1a9e6e", size=10, symbol="triangle-up")
                ))
            if sell_signals:
                fig2.add_trace(go.Scatter(
                    x=[t["Date"] for t in sell_signals],
                    y=[t["Price"] for t in sell_signals],
                    mode="markers", name="Sell",
                    marker=dict(color="#d84b2a", size=10, symbol="triangle-down")
                ))
            fig2.update_layout(
                paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
                font=dict(color="white"),
                xaxis=dict(showgrid=False, color="white"),
                yaxis=dict(showgrid=True, gridcolor="#222", color="white"),
                legend=dict(font=dict(color="white")),
                margin=dict(t=20, b=20, l=20, r=20)
            )
            st.plotly_chart(fig2, use_container_width=True)

            st.divider()

            # Trade log
            st.subheader("Trade log")
            if trades:
                df_trades = pd.DataFrame(trades).fillna("—")
                st.dataframe(df_trades, use_container_width=True)
            else:
                st.info("No trades were triggered with these settings.")