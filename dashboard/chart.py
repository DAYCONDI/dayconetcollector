"""Line chart widget for period time series."""

from PySide6.QtCore import Qt, QDateTime, QBuffer, QIODevice
from typing import Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtGui import QPainter
from PySide6.QtCharts import (QChart, QChartView, QLineSeries, QDateTimeAxis, QValueAxis,
    QBarSeries, QBarSet, QBarCategoryAxis, QPieSeries)


def _pick_scale(max_bytes: int) -> tuple[int, str]:
    """Return (divisor, unit_label) so axis values are human-readable."""
    if max_bytes < 1024:
        return (1, "B")
    if max_bytes < 1024 ** 2:
        return (1024, "KB")
    if max_bytes < 1024 ** 3:
        return (1024 ** 2, "MB")
    if max_bytes < 1024 ** 4:
        return (1024 ** 3, "GB")
    return (1024 ** 4, "TB")


def _x_format(period: str) -> str:
    """Return QDateTimeAxis label format for a given period granularity."""
    formats = {
        "hour": "HH:mm",
        "day": "MMM d",
        "week": "MMM d",
        "month": "MMM yyyy",
        "year": "yyyy",
    }
    return formats.get(period, "MMM d")


class ChartWidget(QWidget):
    """Line chart of total bytes over time."""

    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._chart = QChart()
        self._chart.setTitle("Total bytes over time")
        self._chart.legend().setVisible(False)
        self._chart.setAnimationOptions(QChart.SeriesAnimations)
        self._view = QChartView(self._chart)
        self._view.setRenderHint(QPainter.Antialiasing)
        self._view.setMinimumHeight(220)
        layout.addWidget(self._view)

    def update_data(self, rows: list, period: str) -> None:
        """Replace the chart contents with the given period_start/total_bytes rows."""
        for series in list(self._chart.series()):
            self._chart.removeSeries(series)
        for axis in list(self._chart.axes()):
            self._chart.removeAxis(axis)
        if not rows:
            self._chart.setTitle("No data for this period")
            return
        points = []
        max_value = 0
        min_ms = None
        max_ms = None
        for r in rows:
            ms = int(r["period_start"].timestamp() * 1000)
            value = int(r["total_bytes"])
            points.append((ms, value))
            if value > max_value:
                max_value = value
            if min_ms is None or ms < min_ms:
                min_ms = ms
            if max_ms is None or ms > max_ms:
                max_ms = ms
        divisor, unit = _pick_scale(max_value)
        series = QLineSeries()
        series.setName("Total")
        for ms, value in points:
            series.append(float(ms), float(value) / divisor)
        self._chart.addSeries(series)
        axis_x = QDateTimeAxis()
        axis_x.setTickCount(min(len(points), 8))
        axis_x.setFormat(_x_format(period))
        axis_x.setRange(QDateTime.fromMSecsSinceEpoch(min_ms), QDateTime.fromMSecsSinceEpoch(max_ms))
        self._chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        axis_y = QValueAxis()
        axis_y.setTitleText(f"Total ({unit})")
        axis_y.setLabelFormat("%.1f")
        y_max = max_value / divisor
        if y_max <= 0:
            y_max = 1.0
        axis_y.setRange(0, y_max * 1.1)
        self._chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
        self._chart.setTitle(f"Total bytes over time ({period})")

    def grab_png(self) -> Optional[bytes]:
        """Render the chart view to a PNG byte string, or None on failure."""
        try:
            buffer = QBuffer()
            buffer.open(QIODevice.WriteOnly)
            pixmap = self._view.grab()
            ok = pixmap.save(buffer, "PNG")
            buffer.close()
            if not ok:
                return None
            data = bytes(buffer.data())
            if not data:
                return None
            return data
        except Exception:
            return None


class BarChartWidget(QWidget):
    """Horizontal comparison of top processes by total bytes."""

    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._chart = QChart()
        self._chart.setTitle("Top processes by total bytes")
        self._chart.legend().setVisible(False)
        self._chart.setAnimationOptions(QChart.SeriesAnimations)
        self._view = QChartView(self._chart)
        self._view.setRenderHint(QPainter.Antialiasing)
        self._view.setMinimumHeight(220)
        layout.addWidget(self._view)

    def update_data(self, rows: list) -> None:
        """Replace chart with a horizontal bar series of the top processes by total bytes."""
        self._chart.removeAllSeries()
        for ax in list(self._chart.axes()):
            self._chart.removeAxis(ax)
        if not rows:
            self._chart.setTitle("No data for this period")
            return
        rows = rows[:10]
        bar_set = QBarSet("Total bytes")
        categories = []
        max_value = 0
        for r in rows:
            v = int(r["total_bytes"])
            bar_set.append(v)
            categories.append(r["process_name"])
            if v > max_value:
                max_value = v
        series = QBarSeries()
        series.append(bar_set)
        self._chart.addSeries(series)
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        axis_x.setLabelsAngle(-45)
        self._chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        axis_y = QValueAxis()
        axis_y.setTitleText("Total bytes")
        axis_y.setLabelFormat("%.0f")
        axis_y.setRange(0, max_value * 1.1 if max_value > 0 else 1.0)
        self._chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
        self._chart.setTitle("Top processes by total bytes")

    def grab_png(self):
        try:
            buffer = QBuffer()
            buffer.open(QIODevice.WriteOnly)
            pixmap = self._view.grab()
            ok = pixmap.save(buffer, "PNG")
            buffer.close()
            if not ok:
                return None
            data = bytes(buffer.data())
            return data if data else None
        except Exception:
            return None


class PieChartWidget(QWidget):
    """Pie chart showing the share of each top process by total bytes."""

    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._chart = QChart()
        self._chart.setTitle("Share of total bytes by process")
        self._chart.legend().setAlignment(Qt.AlignRight)
        self._chart.setAnimationOptions(QChart.SeriesAnimations)
        self._view = QChartView(self._chart)
        self._view.setRenderHint(QPainter.Antialiasing)
        self._view.setMinimumHeight(220)
        layout.addWidget(self._view)

    def update_data(self, rows: list) -> None:
        """Replace the pie with the top processes by total bytes."""
        self._chart.removeAllSeries()
        if not rows:
            self._chart.setTitle("No data for this period")
            return
        series = QPieSeries()
        for r in rows[:10]:
            series.append(r["process_name"], int(r["total_bytes"]))
        series.setLabelsVisible(True)
        self._chart.addSeries(series)
        self._chart.setTitle("Share of total bytes by process")

    def grab_png(self):
        try:
            buffer = QBuffer()
            buffer.open(QIODevice.WriteOnly)
            pixmap = self._view.grab()
            ok = pixmap.save(buffer, "PNG")
            buffer.close()
            if not ok:
                return None
            data = bytes(buffer.data())
            return data if data else None
        except Exception:
            return None
