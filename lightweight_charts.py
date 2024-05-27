import tkinter as tk
from lightweight_charts import Chart
import pandas as pd
import numpy as np
import threading
import time
from datetime import timedelta


def generate_random_ohlc(n):
    # Generating random OHLC data
    open_price = np.random.rand(n) * 100 + 100
    close_price = np.random.rand(n) * 100 + 100
    high_price = np.maximum(open_price, close_price) + np.random.rand(n) * 10
    low_price = np.minimum(open_price, close_price) - np.random.rand(n) * 10
    volume = np.random.randint(100, 1000, size=n)
    time = pd.date_range(start='2024-05-27', periods=n, freq='D')

    # Creating a dataframe
    df = pd.DataFrame({
        'time': time,
        'open': open_price,
        'high': high_price,
        'low': low_price,
        'close': close_price,
        'volume': volume
    })

    # Reordering columns
    df = df[['time', 'open', 'high', 'low', 'close', 'volume']]

    return df


def update_chart(chart, df):
    while True:
        # Generate new OHLC data for the next day
        last_row = df.iloc[-1]
        new_time = last_row['time'] + timedelta(days=1)
        new_open = last_row['close']
        new_close = new_open + (np.random.rand() - 0.5) * 10
        new_high = max(new_open, new_close) + np.random.rand() * 5
        new_low = min(new_open, new_close) - np.random.rand() * 5
        new_volume = np.random.randint(100, 1000)

        new_ohlc = pd.DataFrame({
            'time': [new_time],
            'open': [new_open],
            'high': [new_high],
            'low': [new_low],
            'close': [new_close],
            'volume': [new_volume]
        })

        # Concatenate the new OHLC record to the DataFrame
        df = pd.concat([df, new_ohlc], ignore_index=True)

        # Update the chart with the new record
        chart.update(df.iloc[-1,:])

        # Sleep for 5 seconds before updating again
        time.sleep(0.1)


def start_chart():
    chart = Chart()

    # Generating initial random OHLC data
    df = generate_random_ohlc(np.random.randint(20, 31))

    # Setting the data on the chart
    chart.set(df)

    # Start the chart in a non-blocking way
    chart.show(block=False)

    # Start the update thread
    thread = threading.Thread(target=update_chart, args=(chart, df), daemon=True)
    thread.start()


def main():
    # Create the Tkinter window
    root = tk.Tk()
    root.title("Real-time Candlestick Plot in Tkinter")

    # Start the chart
    start_chart()

    # Run the Tkinter main loop
    root.mainloop()


if __name__ == '__main__':
    main()
