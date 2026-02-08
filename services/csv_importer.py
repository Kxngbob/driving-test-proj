import csv
from services.database import Database

class CSVImporter:
    def __init__(self):
        self.db = Database()

    def import_file(self, filepath, anyo, mes):
        if self.db.is_imported(anyo, mes):
            print("Data already imported")
            return False

        with open(filepath, encoding="latin-1") as f:
            reader = csv.reader(f, delimiter=";")

            header = next(reader)
            header = [h.strip() for h in header]
            idx = {name: i for i, name in enumerate(header)}

            cur = self.db.conn.cursor()

            for r in reader:
                if not r or not r[idx["DESC_PROVINCIA"]].strip():
                    continue

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
                    r[idx["DESC_PROVINCIA"]],
                    r[idx["CENTRO_EXAMEN"]],
                    r[idx["CODIGO_AUTOESCUELA"]],
                    r[idx["CODIGO_SECCION"]],
                    int(r[idx["MES"]]),
                    int(r[idx["ANYO"]]),
                    r[idx["TIPO_EXAMEN"]],
                    r[idx["NOMBRE_PERMISO"]],
                    int(r[idx["NUM_APTOS"]]),
                    int(r[idx["NUM_NO_APTOS"]])
                ))

        self.db.mark_imported(anyo, mes)
        self.db.conn.commit()
        print("Import completed")
        return True
