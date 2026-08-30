import json
from collections.abc import Callable

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .api import ParserApiClient
from .config import ConnectionProfile, ProfileStore
from .service import ParserRunService


class TaskThread(QThread):
    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(self, task: Callable):
        super().__init__()
        self.task = task

    def run(self):
        try:
            self.succeeded.emit(self.task())
        except Exception as exc:
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    COMPANY_COLUMNS = [
        "id",
        "name",
        "type",
        "active",
        "source_count",
        "location_name",
        "region_name",
        "country_name",
        "website",
    ]
    SOURCE_COLUMNS = [
        "id",
        "company_name",
        "category_slug",
        "source_type",
        "active",
        "is_due",
        "last_product_count",
        "url",
    ]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AgroMega Parser Studio")
        self.resize(1280, 820)
        self.store = ProfileStore()
        self.profile = self.store.load()[0]
        self.api = None
        self.sources = []
        self.task = None
        self._build_ui()
        self.host_input.setText(self.profile.base_url)
        self.token_input.setText(self.store.get_token(self.profile))

    def _build_ui(self):
        root = QWidget()
        layout = QVBoxLayout(root)
        connection = QHBoxLayout()
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("http://localhost:8000/")
        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.Password)
        self.token_input.setPlaceholderText("Parser API token")
        connect_button = QPushButton("Connect")
        connect_button.clicked.connect(self.connect_api)
        connection.addWidget(QLabel("Host"))
        connection.addWidget(self.host_input, 2)
        connection.addWidget(QLabel("Token"))
        connection.addWidget(self.token_input, 2)
        connection.addWidget(connect_button)
        layout.addLayout(connection)

        controls = QHBoxLayout()
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_all)
        preview_button = QPushButton("Dry run / Preview")
        preview_button.clicked.connect(self.preview_selected)
        run_button = QPushButton("Run selected")
        run_button.clicked.connect(self.run_selected)
        self.force_checkbox = QCheckBox("Force on-demand")
        self.force_checkbox.setChecked(True)
        controls.addWidget(refresh_button)
        controls.addWidget(preview_button)
        controls.addWidget(run_button)
        controls.addWidget(self.force_checkbox)
        controls.addStretch()
        layout.addLayout(controls)

        self.tabs = QTabWidget()
        self.companies_table = self._table(self.COMPANY_COLUMNS)
        self.sources_table = self._table(self.SOURCE_COLUMNS)
        self.attempts_table = self._table(
            ["created", "source_link_id", "status", "product_count", "worker_name", "error"]
        )
        self.products_table = self._table(
            ["id", "source_link_id", "name", "price", "currency", "active", "last_seen_at"]
        )
        self.prices_table = self._table(["observed_at", "product_name", "price", "currency", "worker_name"])
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.tabs.addTab(self.companies_table, "Companies")
        self.tabs.addTab(self.sources_table, "Sources")
        self.tabs.addTab(self.attempts_table, "Attempts")
        self.tabs.addTab(self.products_table, "Products")
        self.tabs.addTab(self.prices_table, "Prices")
        self.tabs.addTab(self.preview_text, "Preview")
        self.tabs.addTab(self.log_text, "Run log")
        layout.addWidget(self.tabs)
        self.setCentralWidget(root)

    @staticmethod
    def _table(columns):
        table = QTableWidget(0, len(columns))
        table.setHorizontalHeaderLabels(columns)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.horizontalHeader().setStretchLastSection(True)
        table.setProperty("columns", columns)
        return table

    def connect_api(self):
        host = self.host_input.text().strip()
        token = self.token_input.text().strip()
        if not host or not token:
            QMessageBox.warning(self, "Missing connection", "Enter both host and API token.")
            return
        self.profile = ConnectionProfile(name="Local AgroMega", base_url=host)
        self.store.save([self.profile])
        self.store.set_token(self.profile, token)
        self.api = ParserApiClient(self.profile.normalized_base_url, token)
        self._start_task(self.api.health_check, lambda _: self.refresh_all())

    def refresh_all(self):
        if not self.api:
            self.connect_api()
            return

        def load():
            return {
                "companies": self.api.list_companies(),
                "sources": self.api.list_sources(scope="all", limit=100),
                "attempts": self.api.list_attempts(),
                "products": self.api.list_products(),
                "prices": self.api.list_price_history(),
            }

        self._start_task(load, self._render_catalogs)

    def _render_catalogs(self, data):
        self.sources = data["sources"]
        self._fill(self.companies_table, data["companies"]["results"])
        self._fill(self.sources_table, self.sources)
        self._fill(self.attempts_table, data["attempts"]["results"])
        self._fill(self.products_table, data["products"]["results"])
        self._fill(self.prices_table, data["prices"]["results"])
        self.log(f"Loaded {len(self.sources)} parser sources.")

    @staticmethod
    def _fill(table, rows):
        columns = table.property("columns")
        table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column_index, key in enumerate(columns):
                value = row.get(key, "")
                table.setItem(row_index, column_index, QTableWidgetItem(str(value if value is not None else "")))
        table.resizeColumnsToContents()

    def selected_source(self):
        row = self.sources_table.currentRow()
        if row < 0 or row >= len(self.sources):
            QMessageBox.information(self, "Select source", "Select a parser source first.")
            return None
        return self.sources[row]

    def preview_selected(self):
        source = self.selected_source()
        if not source:
            return
        service = ParserRunService(self.api)
        self.log(f"Previewing source #{source['id']} …")
        self._start_task(lambda: service.preview(source), self._show_run_result)

    def run_selected(self):
        source = self.selected_source()
        if not source:
            return
        service = ParserRunService(self.api)
        force = self.force_checkbox.isChecked()
        self.log(f"Running source #{source['id']} (force={force}) …")
        self._start_task(lambda: service.run(source, force=force), self._show_run_result)

    def _show_run_result(self, result):
        self.preview_text.setPlainText(json.dumps(result.products, ensure_ascii=False, indent=2, default=str))
        self.tabs.setCurrentWidget(self.preview_text)
        self.log(f"Source #{result.source['id']}: {len(result.products)} products; receipt={result.receipt}")
        if result.receipt:
            self.refresh_all()

    def _start_task(self, task, callback):
        if self.task and self.task.isRunning():
            QMessageBox.information(self, "Busy", "Wait for the current operation to finish.")
            return
        self.task = TaskThread(task)
        self.task.succeeded.connect(callback)
        self.task.failed.connect(self._show_error)
        self.task.start()

    def _show_error(self, message):
        self.log(f"ERROR: {message}")
        QMessageBox.critical(self, "Parser Studio", message)

    def log(self, message):
        self.log_text.append(message)


def run_app():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.show()
    return app.exec()
