import numpy as np
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QWidget, QSplitter, QVBoxLayout, QTableWidget, 
    QTableWidgetItem, QPushButton, QFileDialog, QMessageBox,
    QGridLayout, QDialog, QLineEdit, QDialogButtonBox, QSizePolicy,
    QLabel
)
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtCore import Qt, QTimer

class EditDialog(QDialog):
    def __init__(self, sample, primers):
        super().__init__()
        self.sample = QLineEdit(sample)
        self.primers = QLineEdit(primers)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(self.sample)
        layout.addWidget(self.primers)
        layout.addWidget(self.button_box)
        self.setLayout(layout)

    def get_data(self):
        return self.sample.text(), self.primers.text()

# class ScalableButton(QPushButton):
#     def __init__(self, text, parent=None):
#         super().__init__(text, parent)

#     def resizeEvent(self, event):
#         super().resizeEvent(event)
#         font = self.font()
#         font.setPointSize(max(4, int(self.height()*0.2)))
#         self.setFont(font)

# class ScalableLabel(QLabel):
#     def __init__(self, text, parent=None):
#         super().__init__(text, parent)
#         self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Plate Planner")
        w,h = 800, 400
        self.setGeometry(100, 100, w, h)  # Set initial window size

        # Create a vertical splitter with two panels
        self.divider = QSplitter(Qt.Horizontal, self)
        
        # Create left and right panels as QWidget or any other derived class
        self.left_panel = QWidget(self.divider)
        self.right_panel = QWidget(self.divider)
        
        # Set the initial size of the panels
        self.divider.setSizes([w*2/3, w*1/3])

        # Right panel layout
        self.right_layout = QVBoxLayout(self.right_panel)
        
        # Button to load CSV
        self.load_button = QPushButton("Load CSV", self.right_panel)
        self.load_button.clicked.connect(self.load_data)
        self.right_layout.addWidget(self.load_button)

        # Initialise dataframe
        row = [chr(65+i) for i in range(8)] * 12
        col = np.repeat(range(1, 13), 8)
        self.data = pd.DataFrame(np.full((96, 2), ""), columns=["sample", "primers"], index=[f"{r}{c}" for r, c in zip(row, col)])

        # Table widget
        self.table_widget = QTableWidget(self.right_panel)
        self.right_layout.addWidget(self.table_widget)
        ## Format table
        self.table_widget.setColumnCount(3)
        self.table_widget.setHorizontalHeaderLabels(["Position", "Sample", "Primers"])
        self.table_widget.setColumnWidth(0, 50)  # Set width for Position column
        self.table_widget.setColumnWidth(1, 50)  # Set width for Sample column
        self.table_widget.setColumnWidth(2, 50)  # Set width for Primers column

        self.update_table()  # Initialize the table with empty values from data frame

        # Set the layout of the window
        layout = QVBoxLayout(self)
        layout.addWidget(self.divider)
        self.setLayout(layout)

        # Plate map
        self.left_layout = QGridLayout(self.left_panel)
        self.left_layout.setSpacing(1)
        self.well_buttons = {}
        self.init_plate_map()

        # Shortcut for closing window
        self.close_kb = QShortcut(QKeySequence("Ctrl+W"), self)
        self.close_kb.activated.connect(self.close)

        self.selected_first = None
        self.selected_second = None

    def update_table(self):
        self.table_widget.setRowCount(0) # Clear existing rows
        # Repopulate table
        self.table_widget.setRowCount(0)
        for pos, row in self.data.iterrows():
            row_position = self.table_widget.rowCount()
            self.table_widget.insertRow(row_position)
            self.table_widget.setItem(row_position, 0, QTableWidgetItem(pos))
            self.table_widget.setItem(row_position, 1, QTableWidgetItem(row["sample"]))
            self.table_widget.setItem(row_position, 2, QTableWidgetItem(row["primers"]))

    def update_plate(self):
        for pos, button in self.well_buttons.items():
            if pos in self.data.index:
                button.setText(self.data.loc[pos, "sample"])
            else:
                button.setText("")

    def load_data(self, file_path):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv)")
        if file_path:
            try:
                df = pd.read_csv(file_path, dtype=str, keep_default_na=False)
                if "pos" not in df.columns:
                    df["pos"] = df["row"].astype(str) + df["col"].astype(str)
                df.set_index("pos", inplace=True)
                print(df)
                self.data = df
                self.update_plate()
                self.update_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load CSV file: {e}")

    def init_plate_map(self):
        # Assuming 8 rows and 12 columns for a 96-well plate
        rows = ["A", "B", "C", "D", "E", "F", "G", "H"]
        cols = range(1, 13)
        # self.left_layout.addWidget(ScalableLabel(""), 0, 0)  # Top-left empty corner
        # for j, col in enumerate(cols):
        #     # col_label = QLabel(str(col))
        #     # col_label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Expanding)
        #     # self.left_layout.addWidget(ScalableLabel(str(col)), 0, j+1)
        for i, row in enumerate(rows):
            # row_label = QLabel(row)
            # row_label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Expanding)
            # self.left_layout.addWidget(ScalableLabel(row), i+1, 0)
            for j, col in enumerate(cols):
                pos = f"{row}{col}"
                button = QPushButton(self.data.loc[pos, "sample"])
                button.setStyleSheet("font-size: 8pt;")  # Font scales with CSS
                button.setMinimumSize(10, 10) # needed to let plate shrink
                button.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
                button.clicked.connect(lambda ch, p=pos: self.edit_well(p))
                self.left_layout.addWidget(button, i+1, j+1)
                self.well_buttons[pos] = button

    def edit_well(self, pos):
        if QApplication.keyboardModifiers() == Qt.ControlModifier:
            # Handle cell selection for swapping
            if not self.selected_first:
                self.selected_first = pos
                self.well_buttons[pos].setStyleSheet("border: 2px solid grey")  # Highlight the selected cell
            elif not self.selected_second and self.selected_first != pos:
                self.selected_second = pos
                self.highlight_cell(pos)
                self.swap_cells(self.selected_first, self.selected_second)
                self.well_buttons[self.selected_first].setStyleSheet("")  # Remove highlight
                self.selected_first = None
                self.selected_second = None
        else:
            print(self.data.loc[pos])
            sample, primers = self.data.loc[pos][["sample", "primers"]]
            dialog = EditDialog(sample, primers)
            if dialog.exec():
                new_sample, new_primers = dialog.get_data()
                self.data.loc[pos, "sample"] = new_sample
                self.data.loc[pos, "primers"] = new_primers
                self.well_buttons[pos].setText(new_sample)
                
                self.update_table()

    def highlight_cell(self, pos):
        self.well_buttons[pos].setStyleSheet("border: 2px solid grey;")
        QTimer.singleShot(1000, lambda: self.well_buttons[pos].setStyleSheet(""))

    def swap_cells(self, pos1, pos2):
        # Swap data in DataFrame
        self.data.loc[[pos1, pos2], ["sample", "primers"]] = self.data.loc[[pos2, pos1], ["sample", "primers"]].values

        # Update buttons
        self.well_buttons[pos1].setText(self.data.loc[pos1, "sample"])
        self.well_buttons[pos2].setText(self.data.loc[pos2, "sample"])

        # Refresh the table as well
        self.update_table()

if __name__ == "__main__":
    app = QApplication([])
    mw = MainWindow()
    mw.show()
    app.exec()
