import sqlite3
from pathlib import Path
from PyQt6.QtCore import QStandardPaths, QCoreApplication


APP_NAME = "DrivingExamsAnalyzer"
ORG_NAME = "PoppiApps"


def get_db_path() -> Path:
    """
    Creates and returns the database path using QStandardPaths.
    This stores the database in the user's application data folder.
    """

    QCoreApplication.setOrganizationName(ORG_NAME)
    QCoreApplication.setApplicationName(APP_NAME)

    app_data_dir = Path(
        QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppDataLocation
        )
    )

    app_data_dir.mkdir(parents=True, exist_ok=True)

    return app_data_dir / "driving_exams.db"


class Database:
    def __init__(self):
        self.db_path = get_db_path()

        # Keep this print for screenshots in the packaging report.
        print("DATABASE PATH:", self.db_path)

        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    # ======================================================
    # TABLE CREATION
    # ======================================================
    def create_tables(self):
        cur = self.conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS exam_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            desc_provincia TEXT,
            centro_examen TEXT,
            codigo_autoescuela TEXT,
            codigo_seccion TEXT,
            mes INTEGER,
            anyo INTEGER,
            tipo_examen TEXT,
            nombre_permiso TEXT,
            num_aptos INTEGER,
            num_no_aptos INTEGER
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS imported_periods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            anyo INTEGER NOT NULL,
            mes INTEGER NOT NULL,
            imported_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(anyo, mes)
        )
        """)

        self.conn.commit()

    # ======================================================
    # IMPORT CONTROL
    # ======================================================
    def is_imported(self, anyo, mes):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT 1 FROM imported_periods WHERE anyo = ? AND mes = ?",
            (anyo, mes)
        )
        return cur.fetchone() is not None

    def mark_imported(self, anyo, mes):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO imported_periods (anyo, mes) VALUES (?, ?)",
            (anyo, mes)
        )
        self.conn.commit()

    # ======================================================
    # FILTER VALUES
    # ======================================================
    def get_distinct_values(self, column):
        allowed_columns = {
            "desc_provincia",
            "anyo",
            "mes",
            "tipo_examen",
            "nombre_permiso"
        }

        if column not in allowed_columns:
            raise ValueError(f"Invalid column name: {column}")

        cur = self.conn.cursor()

        if column == "nombre_permiso":
            cur.execute("""
                SELECT DISTINCT TRIM(nombre_permiso)
                FROM exam_results
                WHERE nombre_permiso IS NOT NULL
                ORDER BY TRIM(nombre_permiso)
            """)
        else:
            cur.execute(f"""
                SELECT DISTINCT {column}
                FROM exam_results
                WHERE {column} IS NOT NULL
                ORDER BY {column}
            """)

        return [row[0] for row in cur.fetchall()]

    # ======================================================
    # WHERE CLAUSE BUILDER
    # ======================================================
    def build_where_clause(
        self,
        provincia=None,
        anyo=None,
        mes=None,
        tipo_examen=None,
        permiso=None
    ):
        where = " WHERE 1=1 "
        params = []

        if provincia:
            where += " AND desc_provincia = ? "
            params.append(provincia)

        if anyo:
            where += " AND anyo = ? "
            params.append(anyo)

        if mes:
            where += " AND mes = ? "
            params.append(mes)

        if tipo_examen:
            where += " AND tipo_examen = ? "
            params.append(tipo_examen)

        if permiso:
            where += " AND TRIM(nombre_permiso) = ? "
            params.append(permiso.strip())

        return where, params

    # ======================================================
    # TABLE QUERY FOR QSqlQueryModel
    # ======================================================
    def build_table_query(
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
        allowed_order_columns = {
            "id",
            "desc_provincia",
            "centro_examen",
            "codigo_autoescuela",
            "codigo_seccion",
            "mes",
            "anyo",
            "tipo_examen",
            "nombre_permiso",
            "num_aptos",
            "num_no_aptos"
        }

        if order_by not in allowed_order_columns:
            order_by = "desc_provincia"

        if order_dir not in ("ASC", "DESC"):
            order_dir = "ASC"

        where, params = self.build_where_clause(
            provincia=provincia,
            anyo=anyo,
            mes=mes,
            tipo_examen=tipo_examen,
            permiso=permiso
        )

        sql = f"""
        SELECT
            id AS ID,
            desc_provincia AS Province,
            centro_examen AS Center,
            codigo_autoescuela AS School_Code,
            codigo_seccion AS Section,
            mes AS Month,
            anyo AS Year,
            tipo_examen AS Exam_Type,
            nombre_permiso AS Permit,
            num_aptos AS Passed,
            num_no_aptos AS Failed
        FROM exam_results
        {where}
        ORDER BY {order_by} {order_dir}
        LIMIT ?
        """

        params.append(limit)

        return sql, params

    # ======================================================
    # FILTERED ROWS FOR PDF EXPORT
    # ======================================================
    def get_filtered_results(
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
        sql, params = self.build_table_query(
            provincia=provincia,
            anyo=anyo,
            mes=mes,
            tipo_examen=tipo_examen,
            permiso=permiso,
            limit=limit,
            order_by=order_by,
            order_dir=order_dir
        )

        cur = self.conn.cursor()
        cur.execute(sql, params)

        return cur.fetchall()

    # ======================================================
    # GROUPED RESULTS FOR CHARTS
    # ======================================================
    def get_grouped_results(
        self,
        provincia=None,
        anyo=None,
        mes=None,
        tipo_examen=None,
        permiso=None,
        group_by="desc_provincia"
    ):
        allowed_groups = {
            "desc_provincia": "Province",
            "tipo_examen": "Exam Type",
            "nombre_permiso": "Permit",
            "mes": "Month"
        }

        if group_by not in allowed_groups:
            group_by = "desc_provincia"

        where, params = self.build_where_clause(
            provincia=provincia,
            anyo=anyo,
            mes=mes,
            tipo_examen=tipo_examen,
            permiso=permiso
        )

        sql = f"""
        SELECT
            {group_by} AS group_name,
            SUM(num_aptos) AS total_aptos,
            SUM(num_no_aptos) AS total_no_aptos,
            SUM(num_aptos + num_no_aptos) AS total_presentados
        FROM exam_results
        {where}
        GROUP BY {group_by}
        ORDER BY total_presentados DESC
        LIMIT 20
        """

        cur = self.conn.cursor()
        cur.execute(sql, params)

        return cur.fetchall()

    # ======================================================
    # TOTALS FOR PDF / STATUS
    # ======================================================
    def get_totals(
        self,
        provincia=None,
        anyo=None,
        mes=None,
        tipo_examen=None,
        permiso=None
    ):
        where, params = self.build_where_clause(
            provincia=provincia,
            anyo=anyo,
            mes=mes,
            tipo_examen=tipo_examen,
            permiso=permiso
        )

        sql = f"""
        SELECT
            SUM(num_aptos) AS total_aptos,
            SUM(num_no_aptos) AS total_no_aptos,
            SUM(num_aptos + num_no_aptos) AS total_presentados
        FROM exam_results
        {where}
        """

        cur = self.conn.cursor()
        cur.execute(sql, params)

        return cur.fetchone()