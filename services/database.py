import sqlite3
from pathlib import Path

DB_PATH = Path("data/driving_exams.db")

class Database:
    def __init__(self):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

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

    def get_all_results(self):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM exam_results")
        return cur.fetchall()
    
    def get_filtered_results(self, provincia=None, anyo=None):
        sql = "SELECT * FROM exam_results WHERE 1=1"
        params = []

        if provincia:
            sql += " AND desc_provincia = ?"
            params.append(provincia)

        if anyo:
            sql += " AND anyo = ?"
            params.append(anyo)

        cur = self.conn.cursor()
        cur.execute(sql, params)
        return cur.fetchall()

