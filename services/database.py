import sqlite3
from pathlib import Path

DB_PATH = Path("data/driving_exams.db")

class Database:
    def __init__(self):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    # ================= TABLES =================
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
            anyo INTEGER,
            mes INTEGER,
            UNIQUE(anyo, mes)
        )
        """)

        self.conn.commit()

    # ================= IMPORT CONTROL =================
    def is_imported(self, anyo, mes):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT 1 FROM imported_periods WHERE anyo=? AND mes=?",
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

    # ================= BASE QUERY BUILDER =================
    def build_where_clause(self, provincia=None, anyo=None):
        where = " WHERE 1=1 "
        params = []

        if provincia:
            where += " AND desc_provincia = ? "
            params.append(provincia)

        if anyo:
            where += " AND anyo = ? "
            params.append(anyo)

        return where, params

    # ================= RAW DATA =================
    def get_filtered_results(self, provincia=None, anyo=None, limit=100):
        where, params = self.build_where_clause(provincia, anyo)

        sql = f"""
        SELECT *
        FROM exam_results
        {where}
        ORDER BY desc_provincia, centro_examen
        LIMIT ?
        """

        params.append(limit)

        cur = self.conn.cursor()
        cur.execute(sql, params)
        return cur.fetchall()

    # ================= GROUPED DATA FOR CHARTS =================
    def get_grouped_results(self, provincia=None, anyo=None):
        where, params = self.build_where_clause(provincia, anyo)

        sql = f"""
        SELECT
            desc_provincia,
            SUM(num_aptos) as total_aptos,
            SUM(num_no_aptos) as total_no_aptos,
            SUM(num_aptos + num_no_aptos) as total_presentados
        FROM exam_results
        {where}
        GROUP BY desc_provincia
        ORDER BY total_aptos DESC
        """

        cur = self.conn.cursor()
        cur.execute(sql, params)
        return cur.fetchall()
