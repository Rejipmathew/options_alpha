import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from alpha_vantage.timeseries import TimeSeries

# Set your Alpha Vantage API key
API_KEY = 'RWVVMG6H5Z6H8XQ9'

# Title of the app
st.title("Options Trading Dashboard")

# Sidebar for user inputs
st.sidebar.header("User Input Parameters")

# Function to get user inputs
def user_input_features():
    ticker = st.sidebar.text_input("Stock Ticker", "AAPL")
    start_date = st.sidebar.date_input("Start Date", datetime.today() - timedelta(days=365))
    end_date = st.sidebar.date_input("End Date", datetime.today())
    option_type = st.sidebar.selectbox("Option Type", ["call", "put"])
    strike_price = st.sidebar.number_input("Strike Price", value=150.0)
    expiration = st.sidebar.date_input("Expiration Date", datetime.today() + timedelta(days=30))
    return ticker.upper(), start_date, end_date, option_type, strike_price, expiration

ticker, start_date, end_date, option_type, strike_price, expiration = user_input_features()

st.header(f"Options Data for {ticker}")

# Function to fetch stock data from Alpha Vantage
def get_stock_data(ticker, start_date, end_date):
    ts = TimeSeries(key=API_KEY, output_format='pandas')
    try:
        # Fetch historical stock data (Daily)
        stock_data, meta_data = ts.get_daily(symbol=ticker, outputsize='full')
        
        # Convert index to datetime
        stock_data.index = pd.to_datetime(stock_data.index)
        
        # Filter based on user-selected dates
        stock_data = stock_data[(stock_data.index >= pd.to_datetime(start_date)) & 
                                (stock_data.index <= pd.to_datetime(end_date))]
        
        # Simple Moving Average (20 days)
        stock_data['SMA_20'] = stock_data['4. close'].rolling(window=20).mean()

        return stock_data
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

# Fetch stock data
stock_data = get_stock_data(ticker, start_date, end_date)

if stock_data is not None:
    # Get the most recent stock price
    current_price = stock_data['4. close'][-1]
    
    # Display the current stock price at the top of the dashboard
    st.subheader(f"Current Stock Price: ${current_price:.2f}")

    # Stock Price Data
    st.subheader("Stock Price Data")
    st.write(stock_data.tail())

    # Plot Adjusted Close Price
    st.subheader("Close Price Over Time")
    fig, ax = plt.subplots()
    ax.plot(stock_data.index, stock_data['4. close'], label='Close Price')
    ax.plot(stock_data.index, stock_data['SMA_20'], label='20-Day SMA')
    ax.set_xlabel("Date")
    ax.set_ylabel("Price ($)")
    ax.set_title(f"{ticker} Price Chart")
    ax.legend()
    st.pyplot(fig)

    # Option Pricing Simulation (Black-Scholes)
    from math import log, sqrt, exp
    from scipy.stats import norm

    def black_scholes(S, K, T, r, sigma, option_type='call'):
        d1 = (log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))
        d2 = d1 - sigma * sqrt(T)
        if option_type == 'call':
            price = S * norm.cdf(d1) - K * exp(-r * T) * norm.cdf(d2)
        elif option_type == 'put':
            price = K * exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        return price

    # Latest stock price
    S = stock_data['4. close'][-1]
    K = strike_price
    T = (expiration - datetime.today().date()).days / 365  # Convert datetime.today() to date
    r = 0.01  # Assume 1% risk-free rate
    sigma = stock_data['4. close'].pct_change().std() * (252 ** 0.5)  # Annualized volatility

    option_price = black_scholes(S, K, T, r, sigma, option_type)

    st.subheader("Option Pricing")
    st.write(f"**Option Type:** {option_type.capitalize()}")
    st.write(f"**Strike Price:** ${K}")
    st.write(f"**Expiration Date:** {expiration.strftime('%Y-%m-%d')}")
    st.write(f"**Current Stock Price:** ${S:.2f}")
    st.write(f"**Estimated Volatility:** {sigma:.2%}")
    st.write(f"**Option Price (Black-Scholes):** ${option_price:.2f}")

else:
    st.write("No data available.")
