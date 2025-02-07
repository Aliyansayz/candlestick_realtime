import sys
import numpy as np
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget,
    QHBoxLayout, QSlider, QDockWidget, QColorDialog, QLabel, QFormLayout,
    QLineEdit, QCheckBox
)
from PyQt6.QtCharts import QChart, QChartView, QCandlestickSeries, QCandlestickSet, QDateTimeAxis, QValueAxis, QLineSeries
from PyQt6.QtCore import Qt, QDateTime, QTimer, QPointF
from PyQt6.QtGui import QColor, QPainter, QPen

class CustomCandlestickSeries(QCandlestickSeries):
    def __init__(self):
        super().__init__()
        self.wick_pen = QPen(QColor("#FFFFFF"))
        self.body_width = 0.6  # Initial body width

    def setWickColor(self, color):
        self.wick_pen.setColor(color)

    def draw(self, painter):
        painter.save()
        painter.setPen(self.wick_pen)
        plot_area = self.chart().plotArea()
        x_axis = self.chart().axes(Qt.Orientation.Horizontal)[0]
        y_axis = self.chart().axes(Qt.Orientation.Vertical)[0]

        for candlestick in self.sets():
            o = candlestick.open()
            h = candlestick.high()
            l = candlestick.low()
            c = candlestick.close()
            ts = candlestick.timestamp()

            x = x_axis.mapValueToPosition(ts)
            y_h = y_axis.mapValueToPosition(h)
            y_l = y_axis.mapValueToPosition(l)
            y_o = y_axis.mapValueToPosition(max(o, c))
            y_c = y_axis.mapValueToPosition(min(o, c))

            time_range = x_axis.max() - x_axis.min()
            candle_width = plot_area.width() / (time_range / self.body_width)

            painter.drawLine(QPointF(x, y_h), QPointF(x, y_l))
            body_color = self.increasingColor() if c >= o else self.decreasingColor()
            painter.fillRect(x - candle_width / 2, y_c,
                             candle_width, y_o - y_c, body_color)

        painter.restool()

class CandlestickChartWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Advanced Stock Chart")
        self.setGeometry(100, 100, 1200, 800)
        self.dark_mode = False
        self.zoom_factor = 0.05  # Initial zoom buffer (5%)

        # Chart configuration
        self.max_visible_points = 30
        self.df = self.generate_random_ohlc(self.max_visible_points)

        self.series = CustomCandlestickSeries()
        self.series.setIncreasingColor(QColor("#4CAF50"))
        self.series.setDecreasingColor(QColor("#F44336"))

        self.chart = QChart()
        self.chart.addSeries(self.series)
        self.chart.setTitle("Real-Time Stock Prices")
        self.chart.legend().setVisible(False)

        self.axis_x = QDateTimeAxis()
        self.axis_x.setFormat("HH:mm:ss")
        self.axis_y = QValueAxis()
        self.configure_axes()

        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.chart_view.setRubberBand(QChartView.RubberBand.HorizontalRubberBand)

        self.init_ui()
        self.init_indicators()
        self.init_dock_widgets()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_chart)
        self.timer.start(500)
        self.initialize_chart_data()
        self.apply_theme()

    # ... [Keep all existing methods from previous implementation] ...

    def generate_random_ohlc(self, n):
        """Generate random OHLC data for initializing the chart."""
        base_time = QDateTime.currentDateTime().addSecs(-n)
        return pd.DataFrame({
            'time': [base_time.addSecs(i) for i in range(n)],
            'open': np.random.normal(100, 5, n).cumsum(),
            'high': np.random.normal(105, 3, n).cumsum(),
            'low': np.random.normal(95, 3, n).cumsum(),
            'close': np.random.normal(100, 4, n).cumsum()
        })

  

    def init_ui(self):
        """Initialize the main UI components with new controls."""
        self.toggle_theme_button = QPushButton("Toggle Theme")
        self.toggle_theme_button.clicked.connect(self.toggle_theme)
        
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.toggle_pause)
        
        # New control buttons
        self.squeeze_in_btn = QPushButton("Squeeze In")
        self.squeeze_in_btn.clicked.connect(self.squeeze_in)
        
        self.squeeze_out_btn = QPushButton("Squeeze Out")
        self.squeeze_out_btn.clicked.connect(self.squeeze_out)
        
        self.zoom_in_btn = QPushButton("Zoom In")
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        
        self.zoom_out_btn = QPushButton("Zoom Out")
        self.zoom_out_btn.clicked.connect(self.zoom_out)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.toggle_theme_button)
        button_layout.addWidget(self.pause_button)
        button_layout.addWidget(self.squeeze_in_btn)
        button_layout.addWidget(self.squeeze_out_btn)
        button_layout.addWidget(self.zoom_in_btn)
        button_layout.addWidget(self.zoom_out_btn)

        layout = QVBoxLayout()
        layout.addLayout(button_layout)
        layout.addWidget(self.chart_view)
        layout.addWidget(self.scroll_bar)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def squeeze_in(self):
        """Increase candle width for better visibility"""
        self.series.body_width = min(1.0, self.series.body_width + 0.1)
        self.chart_view.repaint()

    def squeeze_out(self):
        """Decrease candle width to see more data points"""
        self.series.body_width = max(0.2, self.series.body_width - 0.1)
        self.chart_view.repaint()

    def zoom_in(self):
        """Zoom in vertically (reduce price range)"""
        self.zoom_factor = max(0.01, self.zoom_factor * 0.8)
        self.update_axis_ranges()

    def zoom_out(self):
        """Zoom out vertically (increase price range)"""
        self.zoom_factor = min(0.5, self.zoom_factor * 1.2)
        self.update_axis_ranges()

    def update_axis_ranges(self, initial=False):
        """Update axis ranges with current zoom factor"""
        min_time = self.df['time'].iloc[-self.max_visible_points].toMSecsSinceEpoch()
        max_time = self.df['time'].iloc[-1].toMSecsSinceEpoch()
        visible_df = self.df.iloc[-self.max_visible_points:]
        
        # Use zoom factor for vertical range calculation
        buffer = self.zoom_factor * (visible_df['high'].max() - visible_df['low'].min())
        y_min = visible_df['low'].min() - buffer
        y_max = visible_df['high'].max() + buffer

        self.axis_x.setRange(
            QDateTime.fromMSecsSinceEpoch(min_time),
            QDateTime.fromMSecsSinceEpoch(max_time)
        )
        self.axis_y.setRange(y_min, y_max)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("fusion")
    window = CandlestickChartWindow()
    window.show()
    sys.exit(app.exec())
