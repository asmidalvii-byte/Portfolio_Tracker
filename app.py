import streamlit as st
import yfinance as yf
import pandas as pd
import sqlalchemy as db
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# -- Database setup
engine = db.create_engine("sqlite:///portfolio.db")

def init_db():
    with engine.connect() as conn:
        conn.execute(db.text("""
            CREATE TABLE IF NOT EXISTS holdings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                shares REAL NOT NULL,
                buy_price REAL NOT NULL,
                date_added TEXT NOT NULL
            )
        """))
        conn.commit()

# -- Data functions
def get_holdings():
    with engine.connect() as conn:
        result = conn.execute(db.text("SELECT * FROM holdings"))
        return pd.DataFrame(result.fetchall(), columns=result.keys())

def add_holding(ticker, shares, buy_price):
    with engine.connect() as conn:
        conn.execute(db.text("""
            INSERT INTO holdings (ticker, shares, buy_price, date_added)
            VALUES (:ticker, :shares, :buy_price, :date)
        """), {"ticker": ticker.upper(), "shares": shares, "buy_price": buy_price, "date": datetime.today().strftime("%Y-%m-%d")})
        conn.commit()

def delete_holding(holding_id):
    with engine.connect() as conn:
        conn.execute(db.text("DELETE FROM holdings WHERE id = :id"), {"id": holding_id})
        conn.commit()

def get_live_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        return round(stock.fast_info["last_price"], 2)
    except:
        return None

def get_price_history(ticker, period="3mo"):
    try:
        df = yf.Ticker(ticker).history(period=period)
        return df["Close"]
    except:
        return None

# -- App
init_db()

st.set_page_config(page_title="Portfolio Tracker", layout="wide")
st.title("Portfolio Tracker")

# Add new position
with st.expander("Add new position", expanded=False):
    col1, col2, col3 = st.columns(3)
    with col1:
        ticker = st.text_input("Ticker (e.g. AAPL)")
    with col2:
        shares = st.number_input("Shares", min_value=0.01, step=0.01)
    with col3:
        buy_price = st.number_input("Buy price (USD)", min_value=0.01, step=0.01)
    if st.button("Add to portfolio"):
        if ticker and shares and buy_price:
            add_holding(ticker, shares, buy_price)
            st.success(f"Added {shares} shares of {ticker.upper()} at ${buy_price}")
            st.rerun()
        else:
            st.warning("Fill in all fields first.")

# Load holdings
holdings = get_holdings()

if holdings.empty:
    st.info("No positions yet — add your first stock above.")
else:
    rows = []
    values = []
    tickers_list = []

    for _, row in holdings.iterrows():
        live = get_live_price(row["ticker"])
        if live:
            pnl = (live - row["buy_price"]) * row["shares"]
            pnl_pct = ((live - row["buy_price"]) / row["buy_price"]) * 100
            value = live * row["shares"]
            values.append(value)
            tickers_list.append(row["ticker"])
            rows.append({
                "ID": row["id"],
                "Ticker": row["ticker"],
                "Shares": row["shares"],
                "Buy Price": f"${row['buy_price']:.2f}",
                "Live Price": f"${live:.2f}",
                "Value": f"${value:.2f}",
                "P&L": f"${pnl:.2f}",
                "P&L %": f"{pnl_pct:.2f}%",
                "Added": row["date_added"]
            })

    df = pd.DataFrame(rows)
    total_value = sum(float(r["Value"].replace("$", "")) for r in rows)
    total_pnl = sum(float(r["P&L"].replace("$", "")) for r in rows)
    total_cost = sum(h["shares"] * h["buy_price"] for _, h in holdings.iterrows())

    # Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Portfolio Value", f"${total_value:,.2f}")
    m2.metric("Total P&L", f"${total_pnl:,.2f}", delta=f"{(total_pnl / total_cost * 100):.2f}%")
    m3.metric("Positions", len(rows))
    m4.metric("Cost Basis", f"${total_cost:,.2f}")

    st.divider()

    # Charts
    chart_col1, chart_col2 = st.columns(2)

    # Allocation pie chart
    with chart_col1:
        st.subheader("Allocation")
        fig_pie = px.pie(
            names=tickers_list,
            values=values,
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.Teal
        )
        fig_pie.update_layout(
            paper_bgcolor="#0e1117",
            plot_bgcolor="#0e1117",
            font=dict(color="white"),
            legend=dict(font=dict(color="white")),
            margin=dict(t=20, b=20, l=20, r=20)
        )
        fig_pie.update_traces(textfont_color="white")
        st.plotly_chart(fig_pie, use_container_width=True)

    # Price history chart
    with chart_col2:
        st.subheader("Price history")
        selected = st.selectbox("Select stock", options=tickers_list)
        period = st.radio("Period", ["1mo", "3mo", "6mo", "1y"], horizontal=True, index=1)
        hist = get_price_history(selected, period)
        if hist is not None and not hist.empty:
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(
                x=hist.index,
                y=hist.values,
                mode="lines",
                line=dict(color="#1a9e6e", width=2),
                fill="tozeroy",
                fillcolor="rgba(26,158,110,0.1)",
                name=selected
            ))
            fig_line.update_layout(
                paper_bgcolor="#0e1117",
                plot_bgcolor="#0e1117",
                font=dict(color="white"),
                xaxis=dict(showgrid=False, color="white"),
                yaxis=dict(showgrid=True, gridcolor="#222", color="white"),
                margin=dict(t=20, b=20, l=20, r=20),
                showlegend=False
            )
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.warning("Could not load price history.")

    st.divider()

    # Holdings table
    st.subheader("Holdings")
    st.dataframe(df.drop(columns=["ID"]), use_container_width=True)

    st.divider()

    # Remove position
    st.subheader("Remove a position")
    del_id = st.selectbox("Select position to remove", options=holdings["id"].tolist(),
                           format_func=lambda x: holdings[holdings["id"] == x]["ticker"].values[0])
    if st.button("Remove"):
        delete_holding(del_id)
        st.success("Position removed.")
        st.rerun()