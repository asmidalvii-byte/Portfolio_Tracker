# Portfolio Tracker

A live stock portfolio tracker built with Python and Streamlit that shows how your investments are performing in real time.

## What it does

- Add stocks with purchase price and quantity
- Fetches live US stock prices via yfinance
- Calculates P&L per position and total portfolio value
- Interactive allocation pie chart showing portfolio breakdown
- Price history chart with adjustable time periods
- Persistent storage with SQLite database

## Tech stack

Python · Streamlit · Plotly · yfinance · pandas · SQLAlchemy · SQLite

## How to run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Live demo

https://portfoliotracker-d8npsnkzpyebcgddmfy3uk.streamlit.app