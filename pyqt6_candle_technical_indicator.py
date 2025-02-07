import sys
import numpy as np
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget,
    QHBoxLayout, QSlider, QDockWidget, QColorDialog, QLabel, QFormLayout,
    QLineEdit, QCheckBox
)
from PyQt6.QtCharts import QChart, QChartView, QCandlestickSeries, QCandlestickSet, QDateTimeAxis, QValueAxis, \
    QLineSeries
from PyQt6.QtCore import Qt, QDateTime, QTimer, QPointF
from PyQt6.QtGui import QColor, QPainter, QPen


class CustomCandlestickSeries(QCandlestickSeries):
    def __init__(self):
        super().__init__()
        self.wick_pen = QPen(QColor("#FFFFFF"))
        self.body_width = 0.6

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

        painter.restore()


class CandlestickChartWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Stock Chart with Technical Indicators")
        self.setGeometry(100, 100, 1200, 800)
        self.dark_mode = False

        # Chart configuration
        self.max_visible_points = 30
        self.current_start_time = None
        self.df = self.generate_random_ohlc(self.max_visible_points)  # Initialize random data

        self.series = CustomCandlestickSeries()
        self.series.setIncreasingColor(QColor("#4CAF50"))
        self.series.setDecreasingColor(QColor("#F44336"))

        self.chart = QChart()
        self.chart.addSeries(self.series)
        self.chart.setTitle("Real-Time Stock Prices")
        self.chart.legend().setVisible(False)
        self.chart.setAnimationOptions(QChart.AnimationOption.NoAnimation)

        self.axis_x = QDateTimeAxis()
        self.axis_x.setFormat("HH:mm:ss")
        self.axis_y = QValueAxis()
        self.configure_axes()

        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Initialize UI elements
        self.init_ui()
        self.init_indicators()
        self.init_dock_widgets()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_chart)
        self.timer.start(500)
        self.initialize_chart_data()
        self.apply_theme()

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
        """Initialize the main UI components."""
        self.toggle_theme_button = QPushButton("Toggle Theme")
        self.toggle_theme_button.clicked.connect(self.toggle_theme)
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.toggle_pause)
        self.scroll_bar = QSlider(Qt.Orientation.Horizontal)
        self.scroll_bar.setRange(0, self.max_visible_points)
        self.scroll_bar.valueChanged.connect(self.scroll_chart)

        layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.toggle_theme_button)
        button_layout.addWidget(self.pause_button)
        layout.addLayout(button_layout)
        layout.addWidget(self.chart_view)
        layout.addWidget(self.scroll_bar)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def init_indicators(self):
        """Initialize indicator series."""
        self.ema_series = QLineSeries()
        self.rsi_series = QLineSeries()
        self.supertrend_series = QLineSeries()
        self.atr_upper_series = QLineSeries()
        self.atr_lower_series = QLineSeries()

        # Configure RSI axis
        self.axis_rsi = QValueAxis()
        self.axis_rsi.setTitleText("RSI")
        self.axis_rsi.setRange(0, 100)
        self.axis_rsi.setVisible(False)
        self.chart.addAxis(self.axis_rsi, Qt.AlignmentFlag.AlignRight)

    def init_dock_widgets(self):
        """Initialize dock widgets for settings and indicators."""
        # Color settings dock
        self.color_dock = QDockWidget("Appearance Settings", self)
        self.color_form = QWidget()
        self.color_layout = QFormLayout()

        # Bullish/Bearish color pickers
        self.init_color_pickers()

        # Indicators dock
        self.indicators_dock = QDockWidget("Technical Indicators", self)
        self.indicators_form = QWidget()
        self.indicators_layout = QVBoxLayout()

        self.ema_checkbox = QCheckBox("EMA (14)")
        self.rsi_checkbox = QCheckBox("RSI (14)")
        self.supertrend_checkbox = QCheckBox("Supertrend (10,3)")
        self.atr_bands_checkbox = QCheckBox("ATR Bands (20,2)")

        self.indicators_layout.addWidget(self.ema_checkbox)
        self.indicators_layout.addWidget(self.rsi_checkbox)
        self.indicators_layout.addWidget(self.supertrend_checkbox)
        self.indicators_layout.addWidget(self.atr_bands_checkbox)

        self.indicators_form.setLayout(self.indicators_layout)
        self.indicators_dock.setWidget(self.indicators_form)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.indicators_dock)

        # Connect checkboxes
        self.ema_checkbox.stateChanged.connect(self.toggle_ema)
        self.rsi_checkbox.stateChanged.connect(self.toggle_rsi)
        self.supertrend_checkbox.stateChanged.connect(self.toggle_supertrend)
        self.atr_bands_checkbox.stateChanged.connect(self.toggle_atr_bands)

    def init_color_pickers(self):
        """Initialize color pickers for bullish and bearish candles."""
        # Bullish color
        self.bullish_color_input = QLineEdit("#4CAF50")
        self.bullish_color_input.setReadOnly(True)
        self.bullish_color_button = QPushButton("Pick Bullish Color")
        self.bullish_color_button.clicked.connect(self.pick_bullish_color)

        # Bearish color
        self.bearish_color_input = QLineEdit("#F44336")
        self.bearish_color_input.setReadOnly(True)
        self.bearish_color_button = QPushButton("Pick Bearish Color")
        self.bearish_color_button.clicked.connect(self.pick_bearish_color)

        self.color_layout.addRow(QLabel("Bullish Color:"), self.bullish_color_input)
        self.color_layout.addRow(self.bullish_color_button)
        self.color_layout.addRow(QLabel("Bearish Color:"), self.bearish_color_input)
        self.color_layout.addRow(self.bearish_color_button)
        self.color_form.setLayout(self.color_layout)
        self.color_dock.setWidget(self.color_form)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.color_dock)

    def configure_axes(self):
        """Configure the X and Y axes for the chart."""
        self.axis_x.setTitleText("Time")
        self.chart.addAxis(self.axis_x, Qt.AlignmentFlag.AlignBottom)
        self.series.attachAxis(self.axis_x)
        self.axis_y.setTitleText("Price")
        self.chart.addAxis(self.axis_y, Qt.AlignmentFlag.AlignLeft)
        self.series.attachAxis(self.axis_y)

    def initialize_chart_data(self):
        """Initialize the chart with initial data."""
        for _, row in self.df.iterrows():
            self.add_candle(row)
        self.update_axis_ranges(initial=True)

    def add_candle(self, row):
        """Add a candlestick to the chart."""
        candle = QCandlestickSet(
            row['open'], row['high'], row['low'], row['close']
        )
        candle.setTimestamp(row['time'].toMSecsSinceEpoch())
        self.series.append(candle)

    def update_chart(self):
        """Update the chart with new data."""
        if self.timer.isActive():
            new_row = self.generate_new_candle()
            self.df = pd.concat([self.df, new_row], ignore_index=True)
            self.add_candle(new_row.iloc[0])

            if len(self.series) > self.max_visible_points:
                self.series.remove(self.series.sets()[0])

            self.update_axis_ranges()

    def generate_new_candle(self):
        """Generate a new candlestick."""
        last = self.df.iloc[-1]
        new_time = last['time'].addSecs(1)
        price_change = np.random.normal(0, 0.5)

        return pd.DataFrame([{
            'time': new_time,
            'open': last['close'],
            'high': last['close'] + abs(price_change) + np.random.uniform(0, 0.5),
            'low': last['close'] - abs(price_change) - np.random.uniform(0, 0.5),
            'close': last['close'] + price_change
        }])

    def update_axis_ranges(self, initial=False):
        """Update the axis ranges based on visible data."""
        min_time = self.df['time'].iloc[-self.max_visible_points].toMSecsSinceEpoch()
        max_time = self.df['time'].iloc[-1].toMSecsSinceEpoch()
        visible_df = self.df.iloc[-self.max_visible_points:]
        buffer = 0.05 * (visible_df['high'].max() - visible_df['low'].min())
        y_min = visible_df['low'].min() - buffer
        y_max = visible_df['high'].max() + buffer

        self.axis_x.setRange(
            QDateTime.fromMSecsSinceEpoch(min_time),
            QDateTime.fromMSecsSinceEpoch(max_time)
        )
        self.axis_y.setRange(y_min, y_max)

    def toggle_theme(self):
        """Toggle between dark and light themes."""
        self.dark_mode = not self.dark_mode
        self.apply_theme()

    def apply_theme(self):
        """Apply the current theme (dark or light)."""
        if self.dark_mode:
            # Dark theme settings
            self.chart.setBackgroundBrush(QColor("#121212"))
            self.chart.setTitleBrush(QColor("#FFFFFF"))
            self.axis_x.setLabelsBrush(QColor("#FFFFFF"))
            self.axis_y.setLabelsBrush(QColor("#FFFFFF"))
            self.series.setWickColor(QColor("#FFFFFF"))
        else:
            # Light theme settings
            self.chart.setBackgroundBrush(QColor("#FFFFFF"))
            self.chart.setTitleBrush(QColor("#000000"))
            self.axis_x.setLabelsBrush(QColor("#000000"))
            self.axis_y.setLabelsBrush(QColor("#000000"))
            self.series.setWickColor(QColor("#000000"))

        self.chart_view.repaint()

    def toggle_pause(self):
        """Pause or resume the chart updates."""
        if self.timer.isActive():
            self.timer.stop()
            self.pause_button.setText("Play")
        else:
            self.timer.start(500)
            self.pause_button.setText("Pause")

    def scroll_chart(self, value):
        """Scroll the chart to view historical data."""
        if not self.timer.isActive():
            end_index = value
            start_index = max(0, end_index - self.max_visible_points)
            visible_df = self.df.iloc[start_index:end_index]

            min_time = visible_df['time'].iloc[0].toMSecsSinceEpoch()
            max_time = visible_df['time'].iloc[-1].toMSecsSinceEpoch()
            buffer = 0.05 * (visible_df['high'].max() - visible_df['low'].min())
            y_min = visible_df['low'].min() - buffer
            y_max = visible_df['high'].max() + buffer

            self.axis_x.setRange(
                QDateTime.fromMSecsSinceEpoch(min_time),
                QDateTime.fromMSecsSinceEpoch(max_time)
            )
            self.axis_y.setRange(y_min, y_max)

    def pick_bullish_color(self):
        """Pick a color for bullish candles."""
        color = QColorDialog.getColor()
        if color.isValid():
            self.series.setIncreasingColor(color)
            self.bullish_color_input.setText(color.name())
            self.chart_view.repaint()

    def pick_bearish_color(self):
        """Pick a color for bearish candles."""
        color = QColorDialog.getColor()
        if color.isValid():
            self.series.setDecreasingColor(color)
            self.bearish_color_input.setText(color.name())
            self.chart_view.repaint()

    def toggle_ema(self, state):
        """Toggle the EMA indicator on or off."""
        if state == Qt.CheckState.Checked.value:
            self.ema_series.setName("EMA 14")
            self.ema_series.setColor(QColor(0, 0, 255))  # Blue
            self.chart.addSeries(self.ema_series)
            self.ema_series.attachAxis(self.axis_x)
            self.ema_series.attachAxis(self.axis_y)
            self.calculate_ema()
        else:
            self.chart.removeSeries(self.ema_series)

    def toggle_rsi(self, state):
        """Toggle the RSI indicator on or off."""
        if state == Qt.CheckState.Checked.value:
            self.rsi_series.setName("RSI 14")
            self.rsi_series.setColor(QColor(128, 0, 128))  # Purple
            self.chart.addSeries(self.rsi_series)
            self.rsi_series.attachAxis(self.axis_x)
            self.rsi_series.attachAxis(self.axis_rsi)
            self.axis_rsi.setVisible(True)
            self.calculate_rsi()
        else:
            self.chart.removeSeries(self.rsi_series)
            self.axis_rsi.setVisible(False)

    def toggle_supertrend(self, state):
        """Toggle the Supertrend indicator on or off."""
        if state == Qt.CheckState.Checked.value:
            self.supertrend_series.setName("Supertrend")
            self.supertrend_series.setColor(QColor(255, 165, 0))  # Orange
            self.chart.addSeries(self.supertrend_series)
            self.supertrend_series.attachAxis(self.axis_x)
            self.supertrend_series.attachAxis(self.axis_y)
            self.calculate_supertrend()
        else:
            self.chart.removeSeries(self.supertrend_series)

    def toggle_atr_bands(self, state):
        """Toggle the ATR Bands indicator on or off."""
        if state == Qt.CheckState.Checked.value:
            for series in [self.atr_upper_series, self.atr_lower_series]:
                series.setColor(QColor(0, 255, 0) if series == self.atr_upper_series else QColor(255, 0, 0))
                series.setName("ATR Upper" if series == self.atr_upper_series else "ATR Lower")
                self.chart.addSeries(series)
                series.attachAxis(self.axis_x)
                series.attachAxis(self.axis_y)
            self.calculate_atr_bands()
        else:
            for series in [self.atr_upper_series, self.atr_lower_series]:
                self.chart.removeSeries(series)

    def calculate_ema(self, period=14):
        """Calculate the Exponential Moving Average (EMA)."""
        self.df['EMA'] = self.df['close'].ewm(span=period, adjust=False).mean()
        self.ema_series.clear()
        for _, row in self.df.iterrows():
            self.ema_series.append(row['time'].toMSecsSinceEpoch(), row['EMA'])

    def calculate_rsi(self, period=14):
        """Calculate the Relative Strength Index (RSI)."""
        delta = self.df['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
        rs = avg_gain / avg_loss
        self.df['RSI'] = 100 - (100 / (1 + rs))
        self.rsi_series.clear()
        for _, row in self.df.iterrows():
            if not np.isnan(row['RSI']):
                self.rsi_series.append(row['time'].toMSecsSinceEpoch(), row['RSI'])

    def calculate_supertrend(self, period=10, multiplier=0.66):
        """Calculate the Supertrend indicator."""
        # ATR calculation
        high_low = self.df['high'] - self.df['low']
        high_close = np.abs(self.df['high'] - self.df['close'].shift())
        low_close = np.abs(self.df['low'] - self.df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.ewm(alpha=1 / period, adjust=False).mean()

        # Supertrend calculation
        hl2 = (self.df['high'] + self.df['low']) / 2
        self.df['upper_band'] = hl2 + multiplier * atr
        self.df['lower_band'] = hl2 - multiplier * atr

        # Determine supertrend values
        supertrend = []
        for i in range(len(self.df)):
            if i < period:
                supertrend.append(np.nan)
                continue
            if self.df['close'].iloc[i] > self.df['upper_band'].iloc[i - 1]:
                supertrend.append(self.df['lower_band'].iloc[i])
            elif self.df['close'].iloc[i] < self.df['lower_band'].iloc[i - 1]:
                supertrend.append(self.df['upper_band'].iloc[i])
            else:
                supertrend.append(supertrend[-1])

        self.df['supertrend'] = supertrend
        self.supertrend_series.clear()
        for _, row in self.df.iterrows():
            if not np.isnan(row['supertrend']):
                self.supertrend_series.append(row['time'].toMSecsSinceEpoch(), row['supertrend'])

    def calculate_atr_bands(self, period=20, multiplier=2):
        """Calculate the ATR Bands."""
        # SMA and ATR calculation
        self.df['SMA'] = self.df['close'].rolling(period).mean()
        tr = pd.concat([
            self.df['high'] - self.df['low'],
            abs(self.df['high'] - self.df['close'].shift()),
            abs(self.df['low'] - self.df['close'].shift())
        ], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()

        # Calculate bands
        self.df['ATR_Upper'] = self.df['SMA'] + multiplier * atr
        self.df['ATR_Lower'] = self.df['SMA'] - multiplier * atr

        # Update series
        for series, col in zip([self.atr_upper_series, self.atr_lower_series],
                               ['ATR_Upper', 'ATR_Lower']):
            series.clear()
            for _, row in self.df.iterrows():
                if not np.isnan(row[col]):
                    series.append(row['time'].toMSecsSinceEpoch(), row[col])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("fusion")
    window = CandlestickChartWindow()
    window.show()
    sys.exit(app.exec())
