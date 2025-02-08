"""
bottle==0.13.2
cffi==1.17.1
clr_loader==0.2.7.post0
lightweight-charts==2.1
numpy==2.0.2
packaging==24.2
pandas==2.2.3
plotly==5.24.1
proxy-tools==0.1.0
pycparser==2.22
PyQt6==6.7.1
PyQt6-Charts==6.7.0
PyQt6-Charts-Qt6==6.7.3
PyQt6-Qt6==6.7.3
PyQt6-WebEngine==6.7.0
PyQt6-WebEngine-Qt6==6.7.3
PyQt6-WebEngineSubwheel-Qt6==6.7.3
PyQt6_sip==13.10.0
pyqtgraph==0.13.7
python-dateutil==2.9.0.post0
pythonnet==3.0.5
pytz==2025.1
pywebview==5.4
six==1.17.0
tenacity==9.0.0
typing_extensions==4.12.2
tzdata==2025.1

"""

import sys
import numpy as np
import pandas as pd
from PyQt6.QtCore import QUrl, QObject, QTimer, pyqtSignal, pyqtSlot, QDateTime, Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout,
    QWidget, QToolButton, QFrame, QHBoxLayout, QTabWidget
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel

# Define HTML content as a string
HTML_CONTENT = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Financial OHLC Dashboard</title>
    <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
        }
        #chart {
            width: 100%;
            height: 80vh;
        }
    </style>
</head>
<body>
    <h1>Real-Time OHLC Financial Data</h1>
    <div id="chart"></div>

    <script>
        let chartData = [];

        // Initialize WebChannel
        document.addEventListener("DOMContentLoaded", function() {
            new QWebChannel(qt.webChannelTransport, function(channel) {
                window.backend = channel.objects.backend;

                // Listen for new OHLC data
                backend.newCandle.connect(function(candle) {
                    const newCandle = JSON.parse(candle);
                    chartData.push(newCandle);

                    // Update the chart
                    updateChart(chartData);
                });
            });
        });

        // Function to update the Plotly chart
        function updateChart(data) {
            const times = data.map(d => d.time);
            const opens = data.map(d => d.open);
            const highs = data.map(d => d.high);
            const lows = data.map(d => d.low);
            const closes = data.map(d => d.close);

            const trace = {
                x: times,
                close: closes,
                high: highs,
                low: lows,
                open: opens,
                type: 'candlestick',
                name: 'OHLC',
                increasing: {line: {color: 'green'}},
                decreasing: {line: {color: 'red'}}
            };

            const layout = {
                title: 'Real-Time OHLC Data',
                xaxis: { title: 'Time' },
                yaxis: { title: 'Price' }
            };

            Plotly.newPlot('chart', [trace], layout);
        }
    </script>
</body>
</html>
"""

class Backend(QObject):
    """Backend class to generate and send OHLC data to the web page."""
    newCandle = pyqtSignal(str)  # Signal to send new OHLC data to JavaScript

    def __init__(self):
        super().__init__()
        self.df = self.generate_random_ohlc(10)  # Initialize with 10 random candles
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_candle)
        self.timer.start(1000)  # Update every 1 second

    def generate_random_ohlc(self, n):
        """Generate initial random OHLC data."""
        base_time = QDateTime.currentDateTime().addSecs(-n)
        return pd.DataFrame({
            'time': [base_time.addSecs(i).toString("yyyy-MM-dd HH:mm:ss") for i in range(n)],
            'open': np.random.normal(100, 5, n).cumsum(),
            'high': np.random.normal(105, 3, n).cumsum(),
            'low': np.random.normal(95, 3, n).cumsum(),
            'close': np.random.normal(100, 4, n).cumsum()
        })

    def generate_new_candle(self):
        """Generate a new OHLC candle based on the last candle."""
        last = self.df.iloc[-1]
        new_time = QDateTime.fromString(last['time'], "yyyy-MM-dd HH:mm:ss").addSecs(1).toString("yyyy-MM-dd HH:mm:ss")
        price_change = np.random.normal(0, 0.5)

        return pd.DataFrame([{
            'time': new_time,
            'open': last['close'],
            'high': last['close'] + abs(price_change) + np.random.uniform(0, 0.5),
            'low': last['close'] - abs(price_change) - np.random.uniform(0, 0.5),
            'close': last['close'] + price_change
        }])

    @pyqtSlot()
    def update_candle(self):
        """Generate a new candle and send it to the frontend."""
        new_candle = self.generate_new_candle()
        self.df = pd.concat([self.df, new_candle], ignore_index=True)
        self.newCandle.emit(new_candle.to_json(orient='records')[1:-1])  # Send JSON string

    def start_generation(self):
        self.timer.start(1000)

    def stop_generation(self):
        self.timer.stop()

class WebDashboard(QMainWindow):
    """Main window that hosts the HTML dashboard inside a QWebEngineView."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Financial OHLC Dashboard")
        self.resize(1200, 800)

        # Create web view and web channel
        self.view = QWebEngineView()
        self.channel = QWebChannel()
        self.backend = Backend()

        # Register backend object in QWebChannel
        self.channel.registerObject("backend", self.backend)
        self.view.page().setWebChannel(self.channel)

        # Load the HTML content into QWebEngineView
        self.view.setHtml(HTML_CONTENT)

        # Create a widget for the right collapsible pane
        self.right_pane = QWidget()
        self.right_pane.setFixedWidth(self.width() // 4)  # Set width to 25% of total width
        right_layout = QVBoxLayout()

        # Add a QTabWidget to the right pane
        self.tab_widget = QTabWidget()
        control_tab = QWidget()
        control_layout = QVBoxLayout()

        # Add a button to start/stop data generation
        self.toggle_button = QPushButton("Stop Generation")
        self.toggle_button.clicked.connect(self.toggle_generation)
        control_layout.addWidget(self.toggle_button)

        control_tab.setLayout(control_layout)
        self.tab_widget.addTab(control_tab, "Control")
        right_layout.addWidget(self.tab_widget)

        self.right_pane.setLayout(right_layout)

        # Add Toggle Button for Collapsing Right Pane
        self.params_toggle = QToolButton()
        self.params_toggle.setArrowType(Qt.ArrowType.RightArrow)
        self.params_toggle.setCheckable(True)
        self.params_toggle.setChecked(True)
        self.params_toggle.clicked.connect(self.toggle_parameters)

        # Main layout
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.view)
        main_layout.addWidget(self.params_toggle)
        main_layout.addWidget(self.right_pane)

        # Create a frame to hold everything
        self.main_frame = QFrame()
        self.main_frame.setLayout(main_layout)
        self.setCentralWidget(self.main_frame)

    def toggle_parameters(self):
        """Toggles the right panel visibility."""
        is_visible = self.right_pane.isVisible()
        self.right_pane.setVisible(not is_visible)

        # Update the arrow direction
        if is_visible:
            self.params_toggle.setArrowType(Qt.ArrowType.LeftArrow)
        else:
            self.params_toggle.setArrowType(Qt.ArrowType.RightArrow)

    def toggle_generation(self):
        """Start/Stop data generation."""
        if self.backend.timer.isActive():
            self.backend.stop_generation()
            self.toggle_button.setText("Start Generation")
        else:
            self.backend.start_generation()
            self.toggle_button.setText("Stop Generation")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWin = WebDashboard()
    mainWin.show()
    sys.exit(app.exec())
