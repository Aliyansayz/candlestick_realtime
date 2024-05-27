import tkinter as tk
from PIL import Image, ImageTk
import plotly.graph_objs as go
import plotly.io as pio
import io
import threading
import random
import time

# Initial candlestick data
candlestick_data = {
    'x': [str(i) for i in range(1, 11)],
    'open': [random.uniform(100, 150) for _ in range(10)],
    'close': [random.uniform(100, 150) for _ in range(10)],
    'high': [max(random.uniform(100, 150), random.uniform(150, 200)) for _ in range(10)],
    'low': [min(random.uniform(100, 150), random.uniform(50, 100)) for _ in range(10)]
}

def create_candlestick_plot(data):
    """Generate candlestick plot with given data."""
    candlestick = go.Candlestick(
        x=data['x'],
        open=data['open'],
        high=data['high'],
        low=data['low'],
        close=data['close'],
        name='Candlestick Plot'
    )

    layout = go.Layout(
        title='Real-time Candlestick Plot',
        xaxis=dict(title='Date'),
        yaxis=dict(title='Price')
    )

    fig = go.Figure(data=[candlestick], layout=layout)
    return fig

def update_candlestick_chart():
    """Update the candlestick chart every 5 seconds."""
    global candlestick_data
    while True:
        # Generate new random data for the latest candlestick
        new_open = random.uniform(100, 150)
        new_close = random.uniform(100, 150)
        new_high = max(new_open, new_close, random.uniform(150, 200))
        new_low = min(new_open, new_close, random.uniform(50, 100))

        # Update the latest candlestick data
        candlestick_data['open'].append(new_open)
        candlestick_data['close'].append(new_close)
        candlestick_data['high'].append(new_high)
        candlestick_data['low'].append(new_low)
        candlestick_data['x'].append(str(len(candlestick_data['x']) + 1))

        fig = create_candlestick_plot(candlestick_data)
        img_bytes = pio.to_image(fig, format='png')
        image = Image.open(io.BytesIO(img_bytes))
        photo = ImageTk.PhotoImage(image)

        # Update the label with the new image
        label.config(image=photo)
        label.image = photo

        time.sleep(5)

# Create the Tkinter window
root = tk.Tk()
root.title("Real-time Candlestick Plot in Tkinter")

# Initialize with a starting chart
initial_fig = create_candlestick_plot(candlestick_data)
img_bytes = pio.to_image(initial_fig, format='png')
image = Image.open(io.BytesIO(img_bytes))
photo = ImageTk.PhotoImage(image)

label = tk.Label(root, image=photo)
label.pack()

# Start the update thread
thread = threading.Thread(target=update_candlestick_chart, daemon=True)
thread.start()

# Run the Tkinter main loop
root.mainloop()
