import csv
from services.database import Database


class CSVImporter:
    def __init__(self):
        self.db = Database()

    def import_file(self, filepath, anyo, mes):
        """
        Imports a DGT CSV/TXT file into SQLite.

        Features:
        - Reads using CSV headers
        - Validates required columns
        - Prevents duplicate month/year imports
        - Uses transaction control
        - Rolls back if import fails
        - Confirms the file content matches the selected month/year
        """

        if self.db.is_imported(anyo, mes):
            print("Data already imported")
            return False

        required_columns = [
            "DESC_PROVINCIA",
            "CENTRO_EXAMEN",
            "CODIGO_AUTOESCUELA",
            "CODIGO_SECCION",
            "MES",
            "ANYO",
            "TIPO_EXAMEN",
            "NOMBRE_PERMISO",
            "NUM_APTOS",
            "NUM_NO_APTOS"
        ]

        try:
            with open(filepath, encoding="latin-1") as f:
                reader = csv.reader(f, delimiter=";")

                header = next(reader)
                header = [h.strip() for h in header]

                idx = {name: i for i, name in enumerate(header)}

                for column in required_columns:
                    if column not in idx:
                        raise ValueError(f"Missing required column: {column}")

                cur = self.db.conn.cursor()

                # Start transaction manually.
                cur.execute("BEGIN")

                inserted_rows = 0

                for row in reader:
                    if not row:
                        continue

                    if not row[idx["DESC_PROVINCIA"]].strip():
                        continue

                    row_mes = int(row[idx["MES"]])
                    row_anyo = int(row[idx["ANYO"]])

                    if row_mes != mes or row_anyo != anyo:
                        raise ValueError(
                            f"File contains data from {row_mes}/{row_anyo}, "
                            f"but expected {mes}/{anyo}."
                        )

                    cur.execute("""
                    INSERT INTO exam_results (
                        desc_provincia,
                        centro_examen,
                        codigo_autoescuela,
                        codigo_seccion,
                        mes,
                        anyo,
                        tipo_examen,
                        nombre_permiso,
                        num_aptos,
                        num_no_aptos
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row[idx["DESC_PROVINCIA"]].strip(),
                        row[idx["CENTRO_EXAMEN"]].strip(),
                        row[idx["CODIGO_AUTOESCUELA"]].strip(),
                        row[idx["CODIGO_SECCION"]].strip(),
                        row_mes,
                        row_anyo,
                        row[idx["TIPO_EXAMEN"]].strip(),
                        row[idx["NOMBRE_PERMISO"]].strip(),
                        int(row[idx["NUM_APTOS"]]),
                        int(row[idx["NUM_NO_APTOS"]])
                    ))

                    inserted_rows += 1

                cur.execute(
                    "INSERT INTO imported_periods (anyo, mes) VALUES (?, ?)",
                    (anyo, mes)
                )

                self.db.conn.commit()

                print(f"Import completed. Rows inserted: {inserted_rows}")
                return True

        except Exception as e:
            self.db.conn.rollback()
            print("Import failed:", e)
            raise