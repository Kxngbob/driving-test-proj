"""
NOTE:
UI built programmatically for dynamic filtering and SQL-driven updates.
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTableView, QTabWidget,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QComboBox, QCompleter
)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg

from services.database import Database
from services.charts import create_pass_chart
from services.reports import export_table_pdf, export_chart_pdf
from ui.table_model import ExamTableModel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Driving Exams Analyzer")
        self.resize(1100, 650)

        # ================= DATABASE =================
        self.db = Database()

        # Load initial data
        self.rows = self.db.get_filtered_results(limit=100)

        self.all_provinces = sorted(
            {r["desc_provincia"] for r in self.db.get_filtered_results(limit=1000)}
        )
        self.all_years = sorted(
            {r["anyo"] for r in self.db.get_filtered_results(limit=1000)}
        )

        # ================= CENTRAL =================
        central = QWidget()
        main_layout = QVBoxLayout()
        central.setLayout(main_layout)
        self.setCentralWidget(central)

        # ================= FILTER BAR =================
        filter_layout = QHBoxLayout()

        self.province_cb = QComboBox()
        self.province_cb.setEditable(True)
        self.province_cb.addItem("")
        self.province_cb.addItems(self.all_provinces)

        # QCompleter (required by rubric)
        completer = QCompleter(self.all_provinces)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.province_cb.setCompleter(completer)

        self.year_cb = QComboBox()
        self.year_cb.addItem("")
        self.year_cb.addItems([str(y) for y in self.all_years])

        # LIMIT selector
        self.limit_cb = QComboBox()
        self.limit_cb.addItems(["50", "100", "200", "500"])
        self.limit_cb.setCurrentText("100")

        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.apply_filters)

        filter_layout.addWidget(QLabel("Province:"))
        filter_layout.addWidget(self.province_cb)
        filter_layout.addWidget(QLabel("Year:"))
        filter_layout.addWidget(self.year_cb)
        filter_layout.addWidget(QLabel("Limit:"))
        filter_layout.addWidget(self.limit_cb)
        filter_layout.addWidget(apply_btn)
        filter_layout.addStretch()

        main_layout.addLayout(filter_layout)

        # ================= TABS =================
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # ================= TABLE TAB =================
        table_tab = QWidget()
        table_layout = QVBoxLayout()
        table_tab.setLayout(table_layout)

        self.table_view = QTableView()
        self.table_model = ExamTableModel(self.rows)
        self.table_view.setModel(self.table_model)
        self.table_view.setSortingEnabled(True)

        export_table_btn = QPushButton("Export Table to PDF")
        export_table_btn.clicked.connect(self.export_table)

        table_layout.addWidget(self.table_view)
        table_layout.addWidget(export_table_btn)

        self.tabs.addTab(table_tab, "Table")

        # ================= CHART TAB =================
        chart_tab = QWidget()
        chart_layout = QVBoxLayout()
        chart_tab.setLayout(chart_layout)

        grouped = self.db.get_grouped_results()
        self.fig = create_pass_chart(grouped)
        self.canvas = FigureCanvasQTAgg(self.fig)

        export_chart_btn = QPushButton("Export Chart to PDF")
        export_chart_btn.clicked.connect(self.export_chart)

        chart_layout.addWidget(self.canvas)
        chart_layout.addWidget(export_chart_btn)

        self.tabs.addTab(chart_tab, "Chart")

    # ================= FILTER LOGIC =================
    def apply_filters(self):
        provincia = self.province_cb.currentText() or None
        anyo = int(self.year_cb.currentText()) if self.year_cb.currentText() else None
        limit = int(self.limit_cb.currentText())

        # Update table (raw filtered data)
        self.rows = self.db.get_filtered_results(provincia, anyo, limit)
        self.table_model = ExamTableModel(self.rows)
        self.table_view.setModel(self.table_model)

        # Update chart (grouped SQL data)
        grouped = self.db.get_grouped_results(provincia, anyo)

        # Remove old canvas
        self.canvas.setParent(None)

        # Create new figure
        self.fig = create_pass_chart(grouped)
        self.canvas = FigureCanvasQTAgg(self.fig)

        # Add back to layout
        chart_layout = self.tabs.widget(1).layout()
        chart_layout.insertWidget(1, self.canvas)


    # ================= EXPORT =================
    def export_table(self):
        file, _ = QFileDialog.getSaveFileName(
            self, "Save Table PDF", "", "PDF Files (*.pdf)"
        )
        if file:
            provincia = self.province_cb.currentText() or None
            anyo = int(self.year_cb.currentText()) if self.year_cb.currentText() else None
            export_table_pdf(file, self.rows, provincia, anyo)


    def export_chart(self):
        file, _ = QFileDialog.getSaveFileName(
            self, "Save Chart PDF", "", "PDF Files (*.pdf)"
        )
        if file:
            export_chart_pdf(file, self.fig)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
