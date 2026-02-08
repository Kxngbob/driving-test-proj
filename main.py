"""
NOTE:
The UI for this application is created programmatically in Python.
Qt Designer .ui files are not used to allow dynamic updates
to tables, charts, and filters.
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTableView, QTabWidget,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QComboBox
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

        # ================= WINDOW =================
        self.setWindowTitle("Driving Exams Analyzer")
        self.resize(1100, 650)

        # ================= GLOBAL DARK THEME =================
        self.setStyleSheet("""
        QMainWindow {
            background-color: #1e1e1e;
            color: #e6e6e6;
        }

        QLabel {
            color: #e6e6e6;
            font-size: 13px;
        }

        /* ===== FILTER PANEL ===== */
        QWidget#FilterPanel {
            background-color: #252525;
            border: 1px solid #3a3a3a;
            border-radius: 8px;
        }

        /* ===== INPUTS ===== */
        QLineEdit, QComboBox {
            background-color: #2a2a2a;
            color: #ffffff;
            border: 1px solid #444;
            border-radius: 4px;
            padding: 6px;
            min-width: 140px;
        }

        QLineEdit::placeholder {
            color: #9ca3af;
        }

        QComboBox QAbstractItemView {
            background-color: #2a2a2a;
            color: #ffffff;
            selection-background-color: #3b82f6;
        }

        /* ===== BUTTONS ===== */
        QPushButton {
            background-color: #3b82f6;
            color: white;
            padding: 7px 18px;
            border-radius: 6px;
            font-weight: bold;
        }

        QPushButton:hover {
            background-color: #2563eb;
        }

        /* ===== TABS ===== */
        QTabWidget::pane {
            border: none;
            background-color: #1e1e1e;
        }

        QTabBar {
            background-color: #1e1e1e;
        }

        QTabBar::tab {
            background-color: #2a2a2a;
            color: #cccccc;
            padding: 10px 20px;
            margin-right: 4px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
        }

        QTabBar::tab:selected {
            background-color: #3a3a3a;
            color: white;
            font-weight: bold;
        }

        /* ===== TABLE ===== */
        QTableView {
            background-color: #252525;
            alternate-background-color: #1f1f1f;
            color: #e6e6e6;
            gridline-color: #3a3a3a;
            selection-background-color: #3b82f6;
        }

        QHeaderView::section {
            background-color: #333333;
            color: white;
            padding: 6px;
            border: 1px solid #444;
            font-weight: bold;
        }
        """)

        # ================= LOAD DATA =================
        self.db = Database()
        self.rows = self.db.get_all_results()

        self.all_provinces = sorted({r["desc_provincia"] for r in self.rows})
        self.all_years = sorted({r["anyo"] for r in self.rows})

        # ================= CENTRAL LAYOUT =================
        central = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(14)
        central.setLayout(main_layout)
        self.setCentralWidget(central)

        # ================= FILTER PANEL =================
        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(12, 8, 12, 8)
        filter_layout.setSpacing(10)

        filter_layout.addWidget(QLabel("<b>Filters</b>"))

        self.province_cb = QComboBox()
        self.province_cb.addItem("All Provinces")
        self.province_cb.addItems(self.all_provinces)

        self.year_cb = QComboBox()
        self.year_cb.addItem("All Years")
        self.year_cb.addItems([str(y) for y in self.all_years])

        apply_btn = QPushButton("Apply")

        apply_btn.clicked.connect(self.apply_filters)

        filter_layout.addWidget(QLabel("Province:"))
        filter_layout.addWidget(self.province_cb)
        filter_layout.addWidget(QLabel("Year:"))
        filter_layout.addWidget(self.year_cb)
        filter_layout.addWidget(apply_btn)
        filter_layout.addStretch()

        filter_container = QWidget()
        filter_container.setObjectName("FilterPanel")
        filter_container.setLayout(filter_layout)

        main_layout.addWidget(filter_container)

        # ================= TABS =================
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # ================= TABLE TAB =================
        table_tab = QWidget()
        table_layout = QVBoxLayout()
        table_layout.setSpacing(10)
        table_tab.setLayout(table_layout)

        table_layout.addWidget(QLabel("<b>Exam Results</b>"))

        self.table_view = QTableView()
        self.table_model = ExamTableModel(self.rows)
        self.table_view.setModel(self.table_model)
        self.table_view.resizeColumnsToContents()
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setSortingEnabled(True)

        export_table_btn = QPushButton("Export Table to PDF")
        export_table_btn.clicked.connect(self.export_table)

        table_layout.addWidget(self.table_view)
        table_layout.addWidget(export_table_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        self.tabs.addTab(table_tab, "Table")

        # ================= CHART TAB =================
        chart_tab = QWidget()
        chart_layout = QVBoxLayout()
        chart_layout.setSpacing(10)
        chart_tab.setLayout(chart_layout)

        chart_layout.addWidget(QLabel("<b>Statistics Overview</b>"))

        self.fig = create_pass_chart(self.rows)
        self.canvas = FigureCanvasQTAgg(self.fig)

        export_chart_btn = QPushButton("Export Chart to PDF")
        export_chart_btn.clicked.connect(self.export_chart)

        chart_layout.addWidget(self.canvas)
        chart_layout.addWidget(export_chart_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        self.tabs.addTab(chart_tab, "Chart")

    # ================= FILTER LOGIC =================
    def apply_filters(self):
        provincia = self.province_cb.currentText()
        year_text = self.year_cb.currentText()

        if provincia == "All Provinces":
            provincia = None

        if year_text == "All Years":
            anyo = None
        else:
            anyo = int(year_text)

        self.rows = self.db.get_filtered_results(provincia, anyo)

        self.table_model = ExamTableModel(self.rows)
        self.table_view.setModel(self.table_model)
        self.table_view.resizeColumnsToContents()

        self.fig.clear()
        new_fig = create_pass_chart(self.rows)
        self.fig.axes.extend(new_fig.axes)
        self.canvas.draw()

    # ================= PDF EXPORT =================
    def export_table(self):
        file, _ = QFileDialog.getSaveFileName(
            self, "Save Table PDF", "", "PDF Files (*.pdf)"
        )
        if file:
            export_table_pdf(file, self.rows)

    def export_chart(self):
        file, _ = QFileDialog.getSaveFileName(
            self, "Save Chart PDF", "", "PDF Files (*.pdf)"
        )
        if file:
            export_chart_pdf(file, self.fig)


# ================= APP START =================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
