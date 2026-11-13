"""DaycoNet dashboard application."""

import sys
from datetime import date, timedelta

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTabWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QFileDialog,
    QAbstractItemView,
    QHeaderView,
    QComboBox,
    QStackedWidget,
)

try:
    import queries
    _QUERIES_AVAILABLE = True
    _QUERIES_IMPORT_ERROR = ""
except Exception as _exc:
    queries = None
    _QUERIES_AVAILABLE = False
    _QUERIES_IMPORT_ERROR = str(_exc)

try:
    from chart import ChartWidget, BarChartWidget, PieChartWidget
    _CHART_AVAILABLE = True
    _CHART_ERROR = ""
except Exception as _exc:
    ChartWidget = None
    BarChartWidget = None
    PieChartWidget = None
    _CHART_AVAILABLE = False
    _CHART_ERROR = str(_exc)

try:
    import pdf_export
    _PDF_AVAILABLE = True
    _PDF_ERROR = ""
except Exception as _exc:
    pdf_export = None
    _PDF_AVAILABLE = False
    _PDF_ERROR = str(_exc)


APP_NAME = "DaycoNet"
APP_VERSION = "0.1.0"
TOP_N = 20
TABS = [
    ("Daily",   1,   "hour"),
    ("Weekly",  7,   "day"),
    ("Monthly", 30,  "day"),
    ("Yearly",  365, "month"),
]   # (name, days_back, chart_period)

_POOL = None

DARK_STYLESHEET = """
QMainWindow { background-color: #1e1f22; }
QWidget { color: #e6e6e6; font-family: "Segoe UI", "Inter", sans-serif; font-size: 10pt; }
QTabWidget::pane { border: 1px solid #3a3b40; border-radius: 6px; }
QTabBar::tab { background: #2b2d31; color: #b0b3b8; padding: 8px 18px; border-radius: 6px; margin-right: 4px; }
QTabBar::tab:selected { background: #4a6cf7; color: #ffffff; }
QPushButton { background-color: #4a6cf7; color: white; border: none; padding: 6px 14px; border-radius: 4px; }
QPushButton:disabled { background-color: #3a3b40; color: #8a8d92; }
QComboBox { background-color: #2b2d31; border: 1px solid #3a3b40; padding: 4px 8px; border-radius: 4px; }
QTableWidget { background-color: #232428; alternate-background-color: #2b2d31; gridline-color: #3a3b40; border: 1px solid #3a3b40; border-radius: 6px; }
QHeaderView::section { background-color: #2b2d31; color: #b0b3b8; padding: 6px; border: none; border-bottom: 1px solid #3a3b40; }
QLabel#TotalsLabel { color: #9fc3ff; font-weight: bold; }
QStatusBar { background: #1e1f22; color: #8a8d92; }
"""


def format_bytes(n: int) -> str:
    """Format a byte count as a human-readable string with two decimals."""
    if n < 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(n)
    idx = 0
    while value >= 1024.0 and idx < len(units) - 1:
        value /= 1024.0
        idx += 1
    if idx == 0:
        return f"{int(value)} B"
    return f"{value:.2f} {units[idx]}"


def format_speed(bps: int) -> str:
    """Format a bytes-per-second value as KB/s or MB/s."""
    if bps <= 0:
        return "0 B/s"
    if bps < 1024:
        return f"{bps} B/s"
    if bps < 1024 * 1024:
        return f"{bps / 1024:.2f} KB/s"
    return f"{bps / (1024 * 1024):.2f} MB/s"


def get_pool():
    """Return a cached read-only pool, creating it on first call. Raises on failure."""
    global _POOL
    if _POOL is None:
        if not _QUERIES_AVAILABLE:
            raise RuntimeError(f"queries module unavailable: {_QUERIES_IMPORT_ERROR}")
        _POOL = queries.make_reader_pool()
    return _POOL


class FetchWorker(QThread):
    """Worker thread that fetches totals, breakdown, and time series for a date range."""

    result_ready = Signal(object)

    def __init__(self, start_date, end_date, chart_period):
        super().__init__()
        self.start_date = start_date
        self.end_date = end_date
        self.chart_period = chart_period

    def run(self):
        try:
            pool = get_pool()
            totals = queries.fetch_totals(pool, self.start_date, self.end_date)
            duration_seconds = int(totals.get("duration_seconds", 1))
            breakdown = queries.fetch_process_breakdown(
                pool, self.start_date, self.end_date, limit=TOP_N, duration_seconds=duration_seconds
            )
            series = queries.fetch_time_series(pool, self.chart_period, self.start_date, self.end_date)
            self.result_ready.emit({
                "ok": True,
                "totals": totals,
                "breakdown": breakdown,
                "series": series,
            })
        except Exception as exc:
            self.result_ready.emit({"ok": False, "error": str(exc)})


class ReportTab(QWidget):
    """One report tab: header, totals, top-process table, chart stack."""

    def __init__(self, period_name: str, days_back: int, chart_period: str):
        super().__init__()
        self.period_name = period_name
        self.days_back = days_back
        self.chart_period = chart_period
        self._worker = None
        self._last_result = None
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        self.period_label = QLabel("Loading...")
        self.period_label.setStyleSheet("font-weight: bold;")
        button_row = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh)
        button_row.addWidget(self.refresh_button)
        button_row.addStretch()
        self.totals_label = QLabel("Totals: -")
        self.totals_label.setObjectName("TotalsLabel")
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Process", "Sent", "Received", "Total", "Speed"])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        chart_row = QHBoxLayout()
        chart_label = QLabel("Chart view:")
        self.chart_type = QComboBox()
        self.chart_type.addItems(["Line (time)", "Bar (top processes)", "Pie (share)"])
        self.chart_type.currentIndexChanged.connect(self._on_chart_type_changed)
        chart_row.addWidget(chart_label)
        chart_row.addWidget(self.chart_type)
        chart_row.addStretch()
        if _CHART_AVAILABLE:
            self.chart_line = ChartWidget()
            self.chart_bar = BarChartWidget()
            self.chart_pie = PieChartWidget()
            self.chart_stack = QStackedWidget()
            self.chart_stack.addWidget(self.chart_line)
            self.chart_stack.addWidget(self.chart_bar)
            self.chart_stack.addWidget(self.chart_pie)
            self.chart_stack.setCurrentIndex(0)
            self.chart_stack.setMinimumHeight(220)
        else:
            self.chart_stack = QLabel(f"Chart unavailable: {_CHART_ERROR}")
            self.chart_stack.setAlignment(Qt.AlignCenter)
            self.chart_stack.setMinimumHeight(220)
            self.chart_stack.setStyleSheet("border: 1px dashed #999; color: #777;")
        layout.addWidget(self.period_label)
        layout.addLayout(button_row)
        layout.addWidget(self.totals_label)
        layout.addLayout(chart_row)
        layout.addWidget(self.table)
        layout.addWidget(self.chart_stack)

    def refresh(self):
        """Start a worker thread to fetch this tab's data for the current range."""
        if self._worker is not None and self._worker.isRunning():
            return
        today = date.today()
        end = today + timedelta(days=1)
        start = today - timedelta(days=self.days_back - 1)
        self.period_label.setText(f"Period: {start} to {end - timedelta(days=1)} ({self.period_name})")
        self.totals_label.setText("Loading...")
        self.table.setRowCount(0)
        self.refresh_button.setEnabled(False)
        self._worker = FetchWorker(start, end, self.chart_period)
        self._worker.result_ready.connect(self._on_result)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()

    def _on_worker_finished(self):
        self.refresh_button.setEnabled(True)

    def _on_result(self, result):
        if not result.get("ok"):
            self.totals_label.setText(f"Error: {result.get('error', 'unknown')}")
        else:
            totals = result["totals"]
            breakdown = result["breakdown"]
            self.totals_label.setText(
                f"Sent: {format_bytes(totals['bytes_sent'])}  |  "
                f"Received: {format_bytes(totals['bytes_recv'])}  |  "
                f"Total: {format_bytes(totals['total_bytes'])}  |  "
                f"Processes: {totals['process_count']}"
            )
            self.table.setRowCount(len(breakdown))
            for row_idx, item in enumerate(breakdown):
                cells = [
                    item["process_name"],
                    format_bytes(item["bytes_sent"]),
                    format_bytes(item["bytes_recv"]),
                    format_bytes(item["total_bytes"]),
                    format_speed(item["avg_bytes_per_sec"]),
                ]
                for col_idx, text in enumerate(cells):
                    cell = QTableWidgetItem(text)
                    if col_idx > 0:
                        cell.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.table.setItem(row_idx, col_idx, cell)
            if _CHART_AVAILABLE:
                rows = breakdown
                if self.chart_line is not None:
                    self.chart_line.update_data(result["series"], self.chart_period)
                if self.chart_bar is not None:
                    self.chart_bar.update_data(rows)
                if self.chart_pie is not None:
                    self.chart_pie.update_data(rows)
        self._last_result = result

    def _on_chart_type_changed(self, index):
        if not _CHART_AVAILABLE:
            return
        self.chart_stack.setCurrentIndex(index)
        if self._last_result and self._last_result.get("ok"):
            rows = self._last_result["breakdown"]
            if index == 1 and self.chart_bar is not None:
                self.chart_bar.update_data(rows)
            elif index == 2 and self.chart_pie is not None:
                self.chart_pie.update_data(rows)

    def grab_active_chart_png(self):
        """Return PNG bytes of the currently visible chart, or None."""
        if not _CHART_AVAILABLE:
            return None
        widget = self.chart_stack.currentWidget()
        if hasattr(widget, "grab_png"):
            return widget.grab_png()
        return None

    def export_pdf(self):
        """Prompt for a path and export the current tab data to PDF."""
        if not _PDF_AVAILABLE:
            QMessageBox.warning(self, APP_NAME, f"PDF export not available:\n{_PDF_ERROR}")
            return
        if self._last_result is None or not self._last_result.get("ok"):
            QMessageBox.information(self, APP_NAME, "No data loaded. Press Refresh first.")
            return
        default_name = f"dayconet_{self.period_name.lower()}.pdf"
        path, _ = QFileDialog.getSaveFileName(self, "Export PDF", default_name, "PDF files (*.pdf)")
        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path = path + ".pdf"
        chart_png = None
        if _CHART_AVAILABLE:
            chart_png = self.grab_active_chart_png()
        period_label = self.period_label.text()
        totals = self._last_result["totals"]
        breakdown = self._last_result["breakdown"]
        duration_seconds = totals.get("duration_seconds", 1)
        try:
            pdf_export.export_report(
                path, self.period_name, period_label, totals, breakdown, chart_png,
                duration_seconds=duration_seconds,
            )
            QMessageBox.information(self, APP_NAME, f"PDF saved to:\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, APP_NAME, f"PDF export failed:\n{exc}")


class MainWindow(QMainWindow):
    """Main dashboard window with four report tabs."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} - Internet Usage Monitor")
        self.resize(1100, 750)
        self.setStyleSheet(DARK_STYLESHEET)
        tabs_widget = QTabWidget()
        for name, days_back, chart_period in TABS:
            tabs_widget.addTab(ReportTab(name, days_back, chart_period), name)
        self.setCentralWidget(tabs_widget)
        self._tabs = tabs_widget
        self._build_menu()
        self._build_statusbar()
        if not _QUERIES_AVAILABLE:
            QMessageBox.warning(self, APP_NAME, f"queries module not available:\n{_QUERIES_IMPORT_ERROR}")
        if not _CHART_AVAILABLE:
            QMessageBox.warning(self, APP_NAME, f"chart module not available:\n{_CHART_ERROR}")
        if not _PDF_AVAILABLE:
            QMessageBox.warning(self, APP_NAME, f"PDF export module not available:\n{_PDF_ERROR}")

    def _build_menu(self):
        file_menu = self.menuBar().addMenu("&File")
        export_action = QAction("&Export PDF...", self)
        export_action.setEnabled(True)
        export_action.setToolTip("Export the current tab to PDF")
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.triggered.connect(self._on_export_current)
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(export_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

    def _on_export_current(self):
        """Forward the Export PDF action to the currently active report tab."""
        widget = self._tabs.currentWidget()
        if isinstance(widget, ReportTab):
            widget.export_pdf()

    def _build_statusbar(self):
        if _QUERIES_AVAILABLE:
            msg = "Ready. Read-only report queries loaded."
        else:
            msg = "queries module unavailable. Check the message box for details."
        if _PDF_AVAILABLE:
            msg = msg + " | Export PDF ready."
        else:
            msg = msg + " | PDF export unavailable."
        self.statusBar().showMessage(msg)


def main() -> int:
    """Create QApplication, show main window, run event loop."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
