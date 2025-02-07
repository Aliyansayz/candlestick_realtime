import sys
import numpy as np
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget,
    QHBoxLayout, QSlider, QDockWidget, QColorDialog, QLabel, QFormLayout, QLineEdit
)
from PyQt6.QtCharts import QChart, QChartView, QCandlestickSeries, QCandlestickSet, QDateTimeAxis, QValueAxis
from PyQt6.QtCore import Qt, QDateTime, QTimer, QPointF
from PyQt6.QtGui import QColor, QPainter, QPen

class CustomCandlestickSeries(QCandlestickSeries):
    def __init__(self):
        super().__init__()
        self.wick_pen = QPen(QColor("#FFFFFF"))
        self.body_width = 0.6  # Width of candlestick body (0-1)

    def setWickColor(self, color):
        self.wick_pen.setColor(color)

    def draw(self, painter):
        painter.save()
        painter.setPen(self.wick_pen)

        # Calculate candlestick geometry
        plot_area = self.chart().plotArea()
        x_axis = self.chart().axes(Qt.Orientation.Horizontal)[0]
        y_axis = self.chart().axes(Qt.Orientation.Vertical)[0]

        for candlestick in self.sets():
            # Get price values
            o = candlestick.open()
            h = candlestick.high()
            l = candlestick.low()
            c = candlestick.close()
            ts = candlestick.timestamp()

            # Convert to chart coordinates
            x = x_axis.mapValueToPosition(ts)
            y_h = y_axis.mapValueToPosition(h)
            y_l = y_axis.mapValueToPosition(l)
            y_o = y_axis.mapValueToPosition(max(o, c))
            y_c = y_axis.mapValueToPosition(min(o, c))

            # Calculate candlestick width
            time_range = x_axis.max() - x_axis.min()
            candle_width = plot_area.width() / (time_range / self.body_width)

            # Draw wicks
            painter.drawLine(QPointF(x, y_h), QPointF(x, y_l))

            # Draw body (as rectangle)
            body_color = self.increasingColor() if c >= o else self.decreasingColor()
            painter.fillRect(x - candle_width / 2, y_c,
                             candle_width, y_o - y_c, body_color)

        painter.restore()

class CandlestickChartWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Smooth Real-Time Candlestick Chart")
        self.setGeometry(100, 100, 1200, 800)

        self.dark_mode = False  # Theme state

        # Chart configuration
        self.max_visible_points = 30
        self.current_start_time = None
        self.df = self.generate_random_ohlc(self.max_visible_points)

        # Use custom series instead of QCandlestickSeries
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

        self.toggle_theme_button = QPushButton("Toggle Theme")
        self.toggle_theme_button.clicked.connect(self.toggle_theme)

        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.toggle_pause)

        # Add squeeze and zoom buttons
        self.squeeze_in_button = QPushButton("Squeeze In")
        self.squeeze_in_button.clicked.connect(self.squeeze_in)
        self.squeeze_out_button = QPushButton("Squeeze Out")
        self.squeeze_out_button.clicked.connect(self.squeeze_out)
        self.zoom_in_button = QPushButton("Zoom In")
        self.zoom_in_button.clicked.connect(self.zoom_in)
        self.zoom_out_button = QPushButton("Zoom Out")
        self.zoom_out_button.clicked.connect(self.zoom_out)

        self.scroll_bar = QSlider(Qt.Orientation.Horizontal)
        self.scroll_bar.setMinimum(0)
        self.scroll_bar.setMaximum(max(0, len(self.df) - self.max_visible_points))
        self.scroll_bar.setValue(len(self.df) - self.max_visible_points)
        self.scroll_bar.valueChanged.connect(self.scroll_chart)

        layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.toggle_theme_button)
        button_layout.addWidget(self.pause_button)
        button_layout.addWidget(self.squeeze_in_button)
        button_layout.addWidget(self.squeeze_out_button)
        button_layout.addWidget(self.zoom_in_button)
        button_layout.addWidget(self.zoom_out_button)
        layout.addLayout(button_layout)
        layout.addWidget(self.chart_view)
        layout.addWidget(self.scroll_bar)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_chart)
        self.timer.start(500)

        self.initialize_chart_data()
        self.apply_theme()

        # Create a dock widget for color settings
        self.color_dock = QDockWidget("Candlestick Colors", self)
        self.color_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        self.color_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetClosable |
                                    QDockWidget.DockWidgetFeature.DockWidgetMovable)

        self.color_form = QWidget()
        self.color_layout = QFormLayout()

        self.bullish_color_label = QLabel("Bullish Color:")
        self.bullish_color_input = QLineEdit()
        self.bullish_color_input.setReadOnly(True)
        self.bullish_color_input.setText("#4CAF50")
        self.bullish_color_button = QPushButton("Pick Color")
        self.bullish_color_button.clicked.connect(self.pick_bullish_color)

        self.bearish_color_label = QLabel("Bearish Color:")
        self.bearish_color_input = QLineEdit()
        self.bearish_color_input.setReadOnly(True)
        self.bearish_color_input.setText("#F44336")
        self.bearish_color_button = QPushButton("Pick Color")
        self.bearish_color_button.clicked.connect(self.pick_bearish_color)

        self.color_layout.addRow(self.bullish_color_label, self.bullish_color_input)
        self.color_layout.addRow(self.bullish_color_button)
        self.color_layout.addRow(self.bearish_color_label, self.bearish_color_input)
        self.color_layout.addRow(self.bearish_color_button)

        self.color_form.setLayout(self.color_layout)
        self.color_dock.setWidget(self.color_form)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.color_dock)

        # Create a toggle button for the dock widget
        self.toggle_dock_button = QPushButton("🔽")
        self.toggle_dock_button.setFixedSize(30, 30)
        self.toggle_dock_button.clicked.connect(self.toggle_dock_visibility)
        self.toggle_dock_button.setStyleSheet("QPushButton { font-size: 16px; }")

        # Add the toggle button to the main layout
        layout.addWidget(self.toggle_dock_button, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

    def configure_axes(self):
        self.axis_x.setTitleText("Time")
        self.chart.addAxis(self.axis_x, Qt.AlignmentFlag.AlignBottom)
        self.series.attachAxis(self.axis_x)

        self.axis_y.setTitleText("Price")
        self.chart.addAxis(self.axis_y, Qt.AlignmentFlag.AlignLeft)
        self.series.attachAxis(self.axis_y)

    def generate_random_ohlc(self, n):
        base_time = QDateTime.currentDateTime().addSecs(-n)
        return pd.DataFrame({
            'time': [base_time.addSecs(i) for i in range(n)],
            'open': np.random.normal(100, 5, n).cumsum(),
            'high': np.random.normal(105, 3, n).cumsum(),
            'low': np.random.normal(95, 3, n).cumsum(),
            'close': np.random.normal(100, 4, n).cumsum()
        })

    def initialize_chart_data(self):
        for _, row in self.df.iterrows():
            self.add_candle(row)
        self.update_axis_ranges(initial=True)

    def add_candle(self, row):
        candle = QCandlestickSet(
            row['open'], row['high'], row['low'], row['close']
        )
        candle.setTimestamp(row['time'].toMSecsSinceEpoch())
        self.series.append(candle)

    def update_chart(self):
        if self.timer.isActive():
            new_row = self.generate_new_candle()
            self.df = pd.concat([self.df, new_row], ignore_index=True)
            self.add_candle(new_row.iloc[0])

            # Remove oldest candle if exceeding max visible points
            if len(self.series) > self.max_visible_points:
                self.series.remove(self.series.sets()[0])

            # Update scroll bar maximum
            self.scroll_bar.setMaximum(max(0, len(self.df) - self.max_visible_points))
            self.update_axis_ranges()

    def generate_new_candle(self):
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
        if len(self.series) == 0:
            return

        min_time = self.df['time'].iloc[-self.max_visible_points].toMSecsSinceEpoch() if len(self.df) >= self.max_visible_points else self.df['time'].iloc[0].toMSecsSinceEpoch()
        max_time = self.df['time'].iloc[-1].toMSecsSinceEpoch()
        visible_df = self.df.iloc[-self.max_visible_points:] if len(self.df) >= self.max_visible_points else self.df
        buffer = 0.05 * (visible_df['high'].max() - visible_df['low'].min())
        y_min = visible_df['low'].min() - buffer
        y_max = visible_df['high'].max() + buffer

        self.axis_x.setRange(
            QDateTime.fromMSecsSinceEpoch(min_time),
            QDateTime.fromMSecsSinceEpoch(max_time)
        )
        self.axis_y.setRange(y_min, y_max)

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()

    def apply_theme(self):
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
        if self.timer.isActive():
            self.timer.stop()
            self.pause_button.setText("Play")
        else:
            self.timer.start(500)
            self.pause_button.setText("Pause")

    def scroll_chart(self, value):
        if not self.timer.isActive():
            start_index = value
            end_index = start_index + self.max_visible_points
            visible_df = self.df.iloc[start_index:end_index]

            if visible_df.empty:
                return

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
        color = QColorDialog.getColor()
        if color.isValid():
            self.series.setIncreasingColor(color)
            self.bullish_color_input.setText(color.name())
            self.chart_view.repaint()

    def pick_bearish_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.series.setDecreasingColor(color)
            self.bearish_color_input.setText(color.name())
            self.chart_view.repaint()

    def toggle_dock_visibility(self):
        if self.color_dock.isVisible():
            self.color_dock.hide()
            self.toggle_dock_button.setText("🔻")
        else:
            self.color_dock.show()
            self.toggle_dock_button.setText("🔽")

    def squeeze_in(self):
        # Decrease body width (minimum 0.1)
        self.series.body_width = max(0.1, self.series.body_width - 0.1)
        self.chart_view.repaint()

    def squeeze_out(self):
        # Increase body width (maximum 1.0)
        self.series.body_width = min(1.0, self.series.body_width + 0.1)
        self.chart_view.repaint()

    def zoom_in(self):
        # Decrease visible points (minimum 5)
        new_max = max(5, self.max_visible_points - 5)
        if new_max != self.max_visible_points:
            self.max_visible_points = new_max
            self.update_series_from_df()

    def zoom_out(self):
        # Increase visible points
        self.max_visible_points += 5
        self.update_series_from_df()

    def update_series_from_df(self):
        # Clear existing series and reload from df
        self.series.clear()
        visible_df = self.df.iloc[-self.max_visible_points:] if len(self.df) >= self.max_visible_points else self.df
        for _, row in visible_df.iterrows():
            self.add_candle(row)
        # Update scroll bar range and position
        self.scroll_bar.setMaximum(max(0, len(self.df) - self.max_visible_points))
        self.scroll_bar.setValue(max(0, len(self.df) - self.max_visible_points))
        # Update axis ranges
        self.update_axis_ranges()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("fusion")
    window = CandlestickChartWindow()
    window.show()
    sys.exit(app.exec())
