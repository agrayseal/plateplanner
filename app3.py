import numpy as np
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox,
    QDialog, QLabel, QLineEdit, QGridLayout, QMenu
)
from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QDrag, QAction

class InputWindow(QDialog):
    def __init__(self, parent, data, pos):
        super().__init__(parent)
        self.data = data
        self.pos = pos

        self.setWindowTitle(f"Edit {pos}")
        self.create_widgets()

    def create_widgets(self):
        layout = QGridLayout()

        layout.addWidget(QLabel("Sample"), 0, 0)
        self.sample_entry = QLineEdit()
        self.sample_entry.setText(self.data.loc[self.pos]["sample"])
        layout.addWidget(self.sample_entry, 0, 1)
        
        layout.addWidget(QLabel("Primers"), 1, 0)
        self.primers_entry = QLineEdit()
        self.primers_entry.setText(self.data.loc[self.pos]["primers"])
        layout.addWidget(self.primers_entry, 1, 1)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.ok)
        layout.addWidget(self.ok_button, 2, 0, 1, 2)

        self.setLayout(layout)

    def ok(self):
        self.result = (self.sample_entry.text(), self.primers_entry.text())
        self.accept()

class PlatePlannerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Plate Planner")
        self.resize(900, 400)

        row = [chr(65+i) for i in range(8)] * 12
        col = np.repeat(range(1, 13), 8)
        self.df = pd.DataFrame(np.full((96, 2), ""), columns=["sample", "primers"], index=[f"{r}{c}" for r, c in zip(row, col)])

        self.create_widgets()

    def create_widgets(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        panel1 = QWidget()
        panel1_layout = QVBoxLayout(panel1)
        panel1_layout.addWidget(QLabel("Plate layout"))

        self.plate_table = QTableWidget(8, 12)
        self.plate_table.setHorizontalHeaderLabels([str(i) for i in range(1, 13)])
        self.plate_table.setVerticalHeaderLabels([chr(65+i) for i in range(8)])
        self.plate_table.setSelectionMode(QTableWidget.MultiSelection)
        self.plate_table.setEditTriggers(QTableWidget.DoubleClicked)
        self.plate_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.plate_table.customContextMenuRequested.connect(self.show_context_menu)
        self.plate_table.itemDoubleClicked.connect(self.edit_sample)

        panel1_layout.addWidget(self.plate_table)
        main_layout.addWidget(panel1, 2)
        
        panel2 = QWidget()
        panel2_layout = QVBoxLayout(panel2)
        load_button = QPushButton("Load CSV")
        load_button.clicked.connect(self.load_csv)
        panel2_layout.addWidget(load_button)
        save_button = QPushButton("Save CSV")
        panel2_layout.addWidget(save_button)
        
        table_frame = QWidget()
        table_layout = QVBoxLayout(table_frame)
        
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["pos", "sample", "primers"])
        table_layout.addWidget(self.table)
        panel2_layout.addWidget(table_frame)
        main_layout.addWidget(panel2, 1)

        self.update_plate()
        self.update_table()

    def edit_sample(self, item):
        row, col = item.row(), item.column()
        pos = f"{chr(65+row)}{col+1}"
        dialog = InputWindow(self, self.df, pos)
        if dialog.exec():
            result = dialog.result
            if result:
                self.df.loc[pos, "sample"] = result[0]
                self.df.loc[pos, "primers"] = result[1]
                self.update_plate()
                self.update_table()

    def update_plate(self):
        for row in range(8):
            for col in range(12):
                pos = f"{chr(65+row)}{col+1}"
                sample = self.df.loc[pos, "sample"]
                item = QTableWidgetItem(sample)
                self.plate_table.setItem(row, col, item)

    def update_table(self):
        self.table.setRowCount(0)
        for pos, row in self.df.iterrows():
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)
            self.table.setItem(row_position, 0, QTableWidgetItem(pos))
            self.table.setItem(row_position, 1, QTableWidgetItem(row["sample"]))
            self.table.setItem(row_position, 2, QTableWidgetItem(row["primers"]))

    def load_csv(self):
        file_dialog = QFileDialog(self)
        file_path, _ = file_dialog.getOpenFileName(self, "Open CSV", "", "CSV files (*.csv)")
        if file_path:
            try:
                df = pd.read_csv(file_path, dtype=str, keep_default_na=False)
                if "pos" not in df.columns:
                    df["pos"] = df["row"].astype(str) + df["col"].astype(str)
                df.set_index("pos", inplace=True)

                self.df = df
                self.update_plate()
                self.update_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load CSV file: {e}")

    def show_context_menu(self, position):
        menu = QMenu()

        edit_action = QAction("Edit", self)
        edit_action.triggered.connect(self.bulk_edit)
        menu.addAction(edit_action)

        swap_action = QAction("Swap", self)
        swap_action.triggered.connect(self.swap_cells)
        menu.addAction(swap_action)

        menu.exec(self.plate_table.viewport().mapToGlobal(position))

    def bulk_edit(self):
        selected_items = self.plate_table.selectedItems()
        if not selected_items:
            return

        sample, primers = "", ""
        item = selected_items[0]
        row, col = item.row(), item.column()
        pos = f"{chr(65+row)}{col+1}"
        dialog = InputWindow(self, self.df, pos)
        if dialog.exec():
            sample, primers = dialog.result

        for item in selected_items:
            row, col = item.row(), item.column()
            pos = f"{chr(65+row)}{col+1}"
            self.df.loc[pos, "sample"] = sample
            self.df.loc[pos, "primers"] = primers

        self.update_plate()
        self.update_table()

    def swap_cells(self):
        selected_items = self.plate_table.selectedItems()
        if len(selected_items) != 2:
            QMessageBox.warning(self, "Warning", "Select exactly two cells to swap.")
            return

        item1, item2 = selected_items
        row1, col1 = item1.row(), item1.column()
        row2, col2 = item2.row(), item2.column()

        pos1 = f"{chr(65+row1)}{col1+1}"
        pos2 = f"{chr(65+row2)}{col2+1}"

        sample1, primers1 = self.df.loc[pos1]
        sample2, primers2 = self.df.loc[pos2]

        self.df.loc[pos1] = [sample2, primers2]
        self.df.loc[pos2] = [sample1, primers1]

        self.update_plate()
        self.update_table()

if __name__ == "__main__":
    app = QApplication([])
    window = PlatePlannerApp()
    window.show()
    app.exec()
