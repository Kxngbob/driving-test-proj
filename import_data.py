from services.csv_importer import CSVImporter

if __name__ == "__main__":
    importer = CSVImporter()

    importer.import_file(
        "data/raw/export_auto_20251201_20251231.txt",
        2025,
        12
    )

    print("IMPORT COMPLETE")
