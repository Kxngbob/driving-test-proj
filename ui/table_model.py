from PyQt6.QtCore import QAbstractTableModel, Qt


class ExamTableModel(QAbstractTableModel):
    def __init__(self, rows):
        super().__init__()
        self.rows = rows
        self.columns = rows[0].keys() if rows else []

    def rowCount(self, parent=None):
        return len(self.rows)

    def columnCount(self, parent=None):
        return len(self.columns)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            row = self.rows[index.row()]
            column = list(self.columns)[index.column()]
            return str(row[column])

        return None

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return list(self.columns)[section]
        return None
