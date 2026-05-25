import sys
import re

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTableView,
    QTabWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QComboBox,
    QCompleter,
    QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtSql import QSqlDatabase, QSqlQuery, QSqlQueryModel
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg

from services.database import Database
from services.csv_importer import CSVImporter
from services.charts import create_pass_chart
from services.reports import export_table_pdf, export_chart_pdf


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Driving Exams Analyzer")
        self.resize(1250, 720)

        # ================= DATABASE =================
        self.db = Database()

        self.qt_db = QSqlDatabase.addDatabase("QSQLITE")
        self.qt_db.setDatabaseName(str(self.db.db_path))

        if not self.qt_db.open():
            QMessageBox.critical(
                self,
                "Database Error",
                "Could not open SQLite database."
            )

        # Sorting state
        self.current_order_by = "desc_provincia"
        self.current_order_dir = "ASC"

        self.sort_columns = {
            0: "id",
            1: "desc_provincia",
            2: "centro_examen",
            3: "codigo_autoescuela",
            4: "codigo_seccion",
            5: "mes",
            6: "anyo",
            7: "tipo_examen",
            8: "nombre_permiso",
            9: "num_aptos",
            10: "num_no_aptos",
        }

        self.init_ui()
        self.create_menu()
        self.load_filter_values()
        self.apply_filters()

    # ======================================================
    # UI
    # ======================================================
    def init_ui(self):
        central = QWidget()
        main_layout = QVBoxLayout()
        central.setLayout(main_layout)
        self.setCentralWidget(central)

        # ---------- FILTER BAR ----------
        filter_layout = QHBoxLayout()

        self.province_cb = QComboBox()
        self.province_cb.setEditable(True)

        self.year_cb = QComboBox()
        self.month_cb = QComboBox()

        self.exam_type_cb = QComboBox()
        self.exam_type_cb.setEditable(True)

        self.permit_cb = QComboBox()
        self.permit_cb.setEditable(True)

        self.limit_cb = QComboBox()
        self.limit_cb.addItems(["50", "100", "200", "500", "1000"])
        self.limit_cb.setCurrentText("100")

        self.group_cb = QComboBox()
        self.group_cb.addItem("Province", "desc_provincia")
        self.group_cb.addItem("Exam Type", "tipo_examen")
        self.group_cb.addItem("Permit", "nombre_permiso")
        self.group_cb.addItem("Month", "mes")

        apply_btn = QPushButton("Apply Filters")
        apply_btn.clicked.connect(self.apply_filters)

        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self.reset_filters)

        filter_layout.addWidget(QLabel("Province:"))
        filter_layout.addWidget(self.province_cb)

        filter_layout.addWidget(QLabel("Year:"))
        filter_layout.addWidget(self.year_cb)

        filter_layout.addWidget(QLabel("Month:"))
        filter_layout.addWidget(self.month_cb)

        filter_layout.addWidget(QLabel("Exam Type:"))
        filter_layout.addWidget(self.exam_type_cb)

        filter_layout.addWidget(QLabel("Permit:"))
        filter_layout.addWidget(self.permit_cb)

        filter_layout.addWidget(QLabel("Limit:"))
        filter_layout.addWidget(self.limit_cb)

        filter_layout.addWidget(QLabel("Group by:"))
        filter_layout.addWidget(self.group_cb)

        filter_layout.addWidget(apply_btn)
        filter_layout.addWidget(reset_btn)

        main_layout.addLayout(filter_layout)

        # ---------- TABS ----------
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # ---------- TABLE TAB ----------
        table_tab = QWidget()
        table_layout = QVBoxLayout()
        table_tab.setLayout(table_layout)

        self.table_view = QTableView()
        self.table_model = QSqlQueryModel()
        self.table_view.setModel(self.table_model)

        # We rebuild SQL manually when the user clicks headers.
        self.table_view.setSortingEnabled(False)
        self.table_view.horizontalHeader().sectionClicked.connect(self.sort_table)

        export_table_btn = QPushButton("Export Table to PDF")
        export_table_btn.clicked.connect(self.export_table)

        table_layout.addWidget(self.table_view)
        table_layout.addWidget(export_table_btn)

        self.tabs.addTab(table_tab, "Table")

        # ---------- CHART TAB ----------
        chart_tab = QWidget()
        self.chart_layout = QVBoxLayout()
        chart_tab.setLayout(self.chart_layout)

        self.fig = create_pass_chart([])
        self.canvas = FigureCanvasQTAgg(self.fig)

        export_chart_btn = QPushButton("Export Chart to PDF")
        export_chart_btn.clicked.connect(self.export_chart)

        self.chart_layout.addWidget(self.canvas)
        self.chart_layout.addWidget(export_chart_btn)

        self.tabs.addTab(chart_tab, "Chart")

        self.statusBar().showMessage("Ready")

    # ======================================================
    # MENU
    # ======================================================
    def create_menu(self):
        menu = self.menuBar()

        file_menu = menu.addMenu("File")

        import_action = file_menu.addAction("Import CSV")
        import_action.triggered.connect(self.import_csv)

        export_table_action = file_menu.addAction("Export Table PDF")
        export_table_action.triggered.connect(self.export_table)

        export_chart_action = file_menu.addAction("Export Chart PDF")
        export_chart_action.triggered.connect(self.export_chart)

        file_menu.addSeparator()

        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)

    # ======================================================
    # FILTER VALUES
    # ======================================================
    def load_filter_values(self):
        self.province_cb.clear()
        self.year_cb.clear()
        self.month_cb.clear()
        self.exam_type_cb.clear()
        self.permit_cb.clear()

        provinces = [
            str(v) for v in self.db.get_distinct_values("desc_provincia")
        ]
        years = [
            str(v) for v in self.db.get_distinct_values("anyo")
        ]
        months = [
            str(v) for v in self.db.get_distinct_values("mes")
        ]
        exam_types = [
            str(v) for v in self.db.get_distinct_values("tipo_examen")
        ]
        permits = [
            str(v).strip()
            for v in self.db.get_distinct_values("nombre_permiso")
        ]

        self.province_cb.addItem("")
        self.province_cb.addItems(provinces)

        self.year_cb.addItem("")
        self.year_cb.addItems(years)

        self.month_cb.addItem("")
        self.month_cb.addItems(months)

        self.exam_type_cb.addItem("")
        self.exam_type_cb.addItems(exam_types)

        self.permit_cb.addItem("")
        self.permit_cb.addItems(permits)

        self.set_completer(self.province_cb, provinces)
        self.set_completer(self.exam_type_cb, exam_types)
        self.set_completer(self.permit_cb, permits)

    def set_completer(self, combo, values):
        completer = QCompleter(values)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        combo.setCompleter(completer)

    # ======================================================
    # FILTER HELPERS
    # ======================================================
    def current_filters(self):
        provincia = self.province_cb.currentText().strip() or None

        anyo = (
            int(self.year_cb.currentText())
            if self.year_cb.currentText().strip()
            else None
        )

        mes = (
            int(self.month_cb.currentText())
            if self.month_cb.currentText().strip()
            else None
        )

        tipo_examen = self.exam_type_cb.currentText().strip() or None
        permiso = self.permit_cb.currentText().strip() or None
        limit = int(self.limit_cb.currentText())
        group_by = self.group_cb.currentData()

        return provincia, anyo, mes, tipo_examen, permiso, limit, group_by

    # ======================================================
    # APPLY / RESET FILTERS
    # ======================================================
    def apply_filters(self):
        (
            provincia,
            anyo,
            mes,
            tipo_examen,
            permiso,
            limit,
            group_by
        ) = self.current_filters()

        self.update_table(
            provincia=provincia,
            anyo=anyo,
            mes=mes,
            tipo_examen=tipo_examen,
            permiso=permiso,
            limit=limit,
            order_by=self.current_order_by,
            order_dir=self.current_order_dir
        )

        self.update_chart(
            provincia=provincia,
            anyo=anyo,
            mes=mes,
            tipo_examen=tipo_examen,
            permiso=permiso,
            group_by=group_by
        )

        self.statusBar().showMessage("Filters applied")

    def reset_filters(self):
        self.province_cb.setCurrentText("")
        self.year_cb.setCurrentText("")
        self.month_cb.setCurrentText("")
        self.exam_type_cb.setCurrentText("")
        self.permit_cb.setCurrentText("")
        self.limit_cb.setCurrentText("100")
        self.group_cb.setCurrentIndex(0)

        self.current_order_by = "desc_provincia"
        self.current_order_dir = "ASC"

        self.apply_filters()
        self.statusBar().showMessage("Filters reset")

    # ======================================================
    # TABLE
    # ======================================================
    def update_table(
        self,
        provincia=None,
        anyo=None,
        mes=None,
        tipo_examen=None,
        permiso=None,
        limit=100,
        order_by="desc_provincia",
        order_dir="ASC"
    ):
        sql, params = self.db.build_table_query(
            provincia=provincia,
            anyo=anyo,
            mes=mes,
            tipo_examen=tipo_examen,
            permiso=permiso,
            limit=limit,
            order_by=order_by,
            order_dir=order_dir
        )

        query = QSqlQuery(self.qt_db)
        query.prepare(sql)

        for value in params:
            query.addBindValue(value)

        if not query.exec():
            QMessageBox.critical(
                self,
                "SQL Error",
                query.lastError().text()
            )
            return

        self.table_model.setQuery(query)
        self.table_view.resizeColumnsToContents()

    def sort_table(self, column_index):
        selected_column = self.sort_columns.get(column_index)

        if not selected_column:
            return

        if self.current_order_by == selected_column:
            if self.current_order_dir == "ASC":
                self.current_order_dir = "DESC"
            else:
                self.current_order_dir = "ASC"
        else:
            self.current_order_by = selected_column
            self.current_order_dir = "ASC"

        self.apply_filters()
        self.statusBar().showMessage(
            f"Sorted by {selected_column} {self.current_order_dir}"
        )

    # ======================================================
    # CHART
    # ======================================================
    def update_chart(
        self,
        provincia=None,
        anyo=None,
        mes=None,
        tipo_examen=None,
        permiso=None,
        group_by="desc_provincia"
    ):
        grouped_rows = self.db.get_grouped_results(
            provincia=provincia,
            anyo=anyo,
            mes=mes,
            tipo_examen=tipo_examen,
            permiso=permiso,
            group_by=group_by
        )

        group_label = self.group_cb.currentText()

        self.canvas.setParent(None)
        self.fig = create_pass_chart(grouped_rows, group_label)
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.chart_layout.insertWidget(0, self.canvas)

    # ======================================================
    # CSV IMPORT
    # ======================================================
    def import_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import DGT CSV/TXT",
            "",
            "CSV/TXT Files (*.csv *.txt)"
        )

        if not file_path:
            return

        year, month = self.extract_year_month(file_path)

        if year is None or month is None:
            QMessageBox.warning(
                self,
                "Import Error",
                "Could not detect year and month from filename.\n"
                "Expected format similar to export_auto_20251201_20251231.txt"
            )
            return

        try:
            importer = CSVImporter()
            imported = importer.import_file(file_path, year, month)

            if imported:
                QMessageBox.information(
                    self,
                    "Import Complete",
                    f"CSV imported successfully for {month}/{year}."
                )
            else:
                QMessageBox.information(
                    self,
                    "Already Imported",
                    f"Data for {month}/{year} was already imported."
                )

            self.load_filter_values()
            self.apply_filters()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Import Failed",
                f"The CSV file could not be imported.\n\nError:\n{e}"
            )

    def extract_year_month(self, file_path):
        """
        Extracts year and month from filenames such as:
        export_auto_20251201_20251231.txt
        """

        match = re.search(r"(\d{4})(\d{2})\d{2}", file_path)

        if not match:
            return None, None

        year = int(match.group(1))
        month = int(match.group(2))

        if month < 1 or month > 12:
            return None, None

        return year, month

    # ======================================================
    # PDF EXPORT
    # ======================================================
    def export_table(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Table PDF",
            "",
            "PDF Files (*.pdf)"
        )

        if not file_path:
            return

        (
            provincia,
            anyo,
            mes,
            tipo_examen,
            permiso,
            limit,
            group_by
        ) = self.current_filters()

        rows = self.db.get_filtered_results(
            provincia=provincia,
            anyo=anyo,
            mes=mes,
            tipo_examen=tipo_examen,
            permiso=permiso,
            limit=limit,
            order_by=self.current_order_by,
            order_dir=self.current_order_dir
        )

        export_table_pdf(
            file_path,
            rows,
            provincia=provincia,
            anyo=anyo,
            mes=mes,
            tipo_examen=tipo_examen,
            permiso=permiso
        )

        self.statusBar().showMessage("Table PDF exported")

    def export_chart(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Chart PDF",
            "",
            "PDF Files (*.pdf)"
        )

        if not file_path:
            return

        export_chart_pdf(file_path, self.fig)
        self.statusBar().showMessage("Chart PDF exported")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())