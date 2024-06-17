import pyupbit
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Function to get RSI
def get_rsi(df, period=14):
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    avg_gain = gain.ewm(com=(period - 1), min_periods=period).mean()
    avg_loss = loss.ewm(com=(period - 1), min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Simulate trading with transaction fees
def simulate_trading(data, initial_balance, trade_amount_ratio=0.1, rsi_buy=25, rsi_sell=60, fee=0.001):
    balance = initial_balance
    holdings = 0

    for i in range(len(data)):
        if i < 14:  # Ensure enough data for RSI calculation
            continue

        rsi = get_rsi(data[:i+1]).iloc[-1]
        price = data['close'].iloc[i]
        trade_amount = balance * trade_amount_ratio

        if rsi < rsi_buy and balance >= trade_amount:
            # Buy
            amount = trade_amount / price
            balance -= trade_amount * (1 + fee)
            holdings += amount

        elif rsi > rsi_sell and holdings > 0:
            # Sell
            balance += holdings * price * (1 - fee)
            holdings = 0

    # Final sell at the end of the period
    if holdings > 0:
        final_price = data['close'].iloc[-1]
        balance += holdings * final_price * (1 - fee)
        holdings = 0

    return balance

# Load historical data for simulation
def get_historical_data(ticker, interval="minute10", start_date="2022-06-16", end_date="2024-06-16"):
    data = pd.DataFrame()
    date_range = pd.date_range(start=start_date, end=end_date, freq="D")
    
    for date in date_range:
        df = pyupbit.get_ohlcv(ticker, interval=interval, to=date.strftime("%Y-%m-%d"))
        data = pd.concat([df, data])

    data = data.sort_index()
    data = data.loc[~data.index.duplicated(keep='first')]
    return data

# Function to perform the simulation with sequential periods
def perform_simulations(data, num_simulations=30, period_days=30):
    results = []
    start_idx = 0
    balance = 1000000  # Initial balance for the first simulation

    for i in range(num_simulations):
        # Select a start date for the simulation period
        start_date = data.index[start_idx]
        end_date = start_date + timedelta(days=period_days)
        start_idx += period_days

        # Ensure we do not go out of bounds
        if end_date > data.index[-1]:
            break

        # Filter data for the selected period
        period_data = data[(data.index >= start_date) & (data.index <= end_date)]

        # Run the trading simulation
        final_balance = simulate_trading(period_data, balance)
        profit_loss = final_balance - balance
        profit_loss_ratio = (profit_loss / balance) * 100
        results.append((profit_loss_ratio, final_balance))

        print(f"Simulation {i+1}: Start Date: {start_date}, End Date: {end_date}, Profit/Loss Ratio: {profit_loss_ratio:.2f}%, Final Balance: {final_balance:.2f} KRW")

        # Use the final balance of the current simulation as the starting balance for the next simulation
        balance = final_balance

    return results

ticker = "KRW-BTC"  # Bitcoin in KRW
data = get_historical_data(ticker)

# Run the simulations
num_simulations = 30
results = perform_simulations(data, num_simulations=num_simulations)

# Print all results
for i, (profit_loss_ratio, final_balance) in enumerate(results):
    print(f"Simulation {i+1}: Profit/Loss Ratio: {profit_loss_ratio:.2f}%, Final Balance: {final_balance:.2f} KRW")

# Calculate and print the final amount after all simulations
total_final_balance = results[-1][1] if results else 1000000
print(f"Total Final Balance after {num_simulations} simulations: {total_final_balance:.2f} KRW")
