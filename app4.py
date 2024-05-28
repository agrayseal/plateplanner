# import matplotlib.colormaps as cmaps
from matplotlib import cm
from matplotlib.colors import to_hex
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

class BulkEditDialog(QDialog):
    def __init__(self, data, positions):
        super().__init__()
        self.setWindowTitle("Edit Multiple Wells")
        samples = {data.loc[pos, "sample"] for pos in positions if pos in data.index}
        primers = {data.loc[pos, "primers"] for pos in positions if pos in data.index}

        layout = QGridLayout()
        layout.setColumnStretch(0, 3)
        layout.setColumnStretch(0, 7)
        
        self.sample_label = QLabel("Sample:")
        self.sample = QLineEdit("" if len(samples) > 1 else samples.pop())
        self.primers_label = QLabel("Primers:")
        self.primers = QLineEdit("" if len(primers) > 1 else primers.pop())
        layout.addWidget(self.sample_label, 0, 0)
        layout.addWidget(self.sample, 0, 1)
        layout.addWidget(self.primers_label, 1, 0)
        layout.addWidget(self.primers, 1, 1)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box, 2, 0, 1, 2)
        
        self.setLayout(layout)

    def get_data(self):
        return self.sample.text(), self.primers.text()

class SingleEditDialog(QDialog):
    def __init__(self, sample, primers):
        super().__init__()
        layout = QGridLayout()
        layout.setColumnStretch(0, 3)
        layout.setColumnStretch(0, 7)
        
        self.sample_label = QLabel("Sample:")
        self.sample = QLineEdit(sample)
        self.primers_label = QLabel("Primers:")
        self.primers = QLineEdit(primers)
        layout.addWidget(self.sample_label, 0, 0)
        layout.addWidget(self.sample, 0, 1)
        layout.addWidget(self.primers_label, 1, 0)
        layout.addWidget(self.primers, 1, 1)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box, 2, 0, 1, 2)

        self.setLayout(layout)
        self.sample.setFocus()

    def get_data(self):
        return self.sample.text(), self.primers.text()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Plate Planner")
        w,h = 800, 400
        self.setGeometry(100, 100, w, h)  # Set initial window size

        # Create a vertical splitter with two panels
        self.divider = QSplitter(Qt.Horizontal, self)
        self.left_panel = QWidget(self.divider)
        self.right_panel = QWidget(self.divider)
        self.divider.setSizes([w*2/3, w*1/3])

        # Right panel layout
        self.right_layout = QVBoxLayout(self.right_panel)
        
        # Button to load CSV
        self.load_button = QPushButton("Load CSV", self.right_panel)
        self.load_button.clicked.connect(self.load_data)
        self.right_layout.addWidget(self.load_button)

        # Button to save CSV
        self.save_button = QPushButton("Save CSV", self.right_panel)
        self.save_button.clicked.connect(self.save_data)
        self.right_layout.addWidget(self.save_button)

        # Initialise dataframe
        row = [chr(65+i) for i in range(8)] * 12
        col = np.repeat(range(1, 13), 8)
        self.positions = pd.Index([f"{r}{c}" for r, c in zip(row, col)], name="pos")
        self.data = pd.DataFrame(np.full((96, 2), ""), columns=["sample", "primers"], index=self.positions)

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

        # Plate map / grid / right panel
        self.left_layout = QGridLayout(self.left_panel)
        self.left_layout.setSpacing(10)
        # Number of rows and columns
        num_rows = 1 + 8
        num_cols = 1 + 12

        # Set equal stretch to all rows and columns
        for i in range(num_rows):
            self.left_layout.setRowStretch(i, 1)
        for j in range(num_cols):
            self.left_layout.setColumnStretch(j, 1)
        
        self.well_buttons = {}
        self.init_plate_map()
        self.selected_cells = []

        ## Shortcuts
        # Shortcut for closing window
        close_kb = QShortcut(QKeySequence("Ctrl+W"), self)
        close_kb.activated.connect(self.close)
        deselect_kb = QShortcut(QKeySequence("Ctrl+A"), self)
        deselect_kb.activated.connect(self.deselect_all)

    def set_sel_mode(self):
        self.sel_mode_idx = (self.sel_mode_idx+1) % len(self.sel_modes)
        self.sel_mode = self.sel_modes[self.sel_mode_idx]

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
        # unique_primers = self.data["primers"].unique()
        # colormap = cm.get_cmap('tab20', len(unique_primers))  # Using tab20 colormap
        # primer_to_color = {primer: to_hex(colormap(i)) for i, primer in enumerate(unique_primers)}

        for pos, button in self.well_buttons.items():
            if pos in self.data.index:
                # print(pos, button)
                # button.setText(self.data.loc[pos, "sample"])
                sample = self.data.loc[pos, "sample"]
                primers = self.data.loc[pos, "primers"]
                button.setText(sample)
                # button.setStyleSheet(f"{self.button_style['default']} background-color: {primer_to_color[primers]};")
            else:
                button.setText("")
                # button.setStyleSheet(self.button_style["default"])

    def load_data(self, file_path):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv)")
        if file_path:
            try:
                df = pd.read_csv(file_path, dtype=str, keep_default_na=False)
                if "pos" not in df.columns:
                    if "row" not in df.columns or "col" not in df.columns:
                        # print(len(df))
                        if len(df) > 96:
                            df = df[:96]
                        # print(len(df))
                        df["pos"] = self.positions
                        QMessageBox.critical(self, "Note", "No position information, generating.")
                    else:
                        df["pos"] = df["row"].astype(str) + df["col"].astype(str)
                df = df[["pos", "sample", "primers"]]
                df.set_index("pos", inplace=True)
                # print(df)
                # print(self.positions)
                # print(df)
                self.data = df.reindex(self.positions, fill_value="")
                # blank_df = pd.DataFrame({"pos": self.positions})
                # self.data = blank_df.set_index("pos").combine_first(df.set_index("pos"))

                self.update_plate()
                self.update_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load CSV file: {e}")

    def save_data(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save CSV File", "", "CSV Files (*.csv)")
        if file_path:
            try:
                self.data.to_csv(file_path)
                QMessageBox.information(self, "Success", f"Data successfully saved to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save CSV file: {e}")

    def init_plate_map(self):
        # Default button style sheet
        self.button_style = {
            "default": "font-size: 12pt;",
            "highlight": "font-size: 12pt; border: 2px solid grey;"
        }
        # Assuming 8 rows and 12 columns for a 96-well plate
        rows = ["A", "B", "C", "D", "E", "F", "G", "H"]
        cols = range(1, 13)
        self.left_layout.addWidget(QLabel(""), 0, 0)  # Top-left empty corner

        # unique_primers = self.data["primers"].unique()
        # colormap = cm.get_cmap('tab20', len(unique_primers))
        # primer_to_color = {primer: to_hex(colormap(i)) for i, primer in enumerate(unique_primers)}

        for j, col in enumerate(cols):
            col_label = QLabel(str(col))
            col_label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Expanding)
            self.left_layout.addWidget(col_label, 0, j+1)
        for i, row in enumerate(rows):
            row_label = QLabel(row)
            row_label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Expanding)
            self.left_layout.addWidget(row_label, i+1, 0)
            for j, col in enumerate(cols):
                pos = f"{row}{col}"
                sample = self.data.loc[pos, "sample"]
                primers = self.data.loc[pos, "primers"]
                button = QPushButton(sample)
                # button.setStyleSheet(f"{self.button_style['default']} background-color: {primer_to_color[primers]};")
                button.setMinimumSize(10, 10)  # needed to let plate shrink
                button.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
                button.clicked.connect(lambda ch, p=pos: self.select_well(p))
                self.left_layout.addWidget(button, i+1, j+1)
                self.well_buttons[pos] = button

    def select_well(self, pos):
        # Bulk selection with control
        if QApplication.keyboardModifiers() == Qt.ControlModifier:
            if pos in self.selected_cells:
                self.selected_cells.remove(pos)
                self.well_buttons[pos].setStyleSheet(self.button_style["default"])
            else:
                self.selected_cells.append(pos)
                self.well_buttons[pos].setStyleSheet(self.button_style["highlight"])
                # self.highlight_cell(pos)
        # Single cell selection
        else:
            if self.selected_cells and pos not in self.selected_cells:
                self.move_selected_cells(pos)
            else:
                self.edit_well(pos)

    def move_selected_cells(self, target_pos):
        if not self.selected_cells:
            return
        # Calculate the offset based on the first selected cell
        first_selected = self.selected_cells[0]
        target_row, target_col = self.get_row_col(target_pos)
        first_row, first_col = self.get_row_col(first_selected)
        row_offset = target_row - first_row
        col_offset = target_col - first_col

        new_positions = {}
        for pos in self.selected_cells:
            old_row, old_col = self.get_row_col(pos)
            new_row = old_row + row_offset
            new_col = old_col + col_offset
            new_pos = f"{chr(65 + new_row)}{new_col + 1}"
            new_positions[pos] = new_pos

        self.apply_move(new_positions)

    def get_row_col(self, pos):
        row = ord(pos[0]) - 65
        col = int(pos[1:]) - 1
        return row, col

    def apply_move(self, new_positions):
        if len(new_positions) != len(self.selected_cells):
            return
        
        for old_pos, new_pos in new_positions.items():
            if self.data.loc[new_pos]["sample"] != "":
                raise ValueError(f"Cannot move to {new_pos} because it is already occupied.")
            # Move data from old_pos to new_pos
            self.data.loc[new_pos] = self.data.loc[old_pos]
            self.data.loc[old_pos] = {"sample": "", "primers": ""}

        self.update_table()
        self.update_plate()
        self.deselect_all()

    def deselect_all(self):
        for pos in self.selected_cells:
            self.well_buttons[pos].setStyleSheet(self.button_style["default"])
        self.selected_cells.clear()

    def edit_well(self, pos):
        sample, primers = self.data.loc[pos][["sample", "primers"]]
        dialog = SingleEditDialog(sample, primers)
        if dialog.exec():
            new_sample, new_primers = dialog.get_data()
            self.data.loc[pos, "sample"] = new_sample
            self.data.loc[pos, "primers"] = new_primers
            self.well_buttons[pos].setText(new_sample)
            
            self.update_table()

    def bulk_edit_wells(self):
        dialog = BulkEditDialog(self.data, self.selected_cells)
        if dialog.exec():
            new_sample, new_primers = dialog.get_data()
            for pos in self.selected_cells:
                if new_sample:  # Only update if a new value is provided
                    self.data.loc[pos, "sample"] = new_sample
                    self.well_buttons[pos].setText(new_sample)
                if new_primers:
                    self.data.loc[pos, "primers"] = new_primers
            self.update_table()
            for pos in self.selected_cells:  # Clear selections after editing
                self.well_buttons[pos].setStyleSheet(self.button_style["default"])
            self.selected_cells.clear()

    def highlight_cell(self, pos):
        self.well_buttons[pos].setStyleSheet(self.button_style["highlight"])
        QTimer.singleShot(200, lambda: self.well_buttons[pos].setStyleSheet(self.button_style["default"]))

    def swap_cells(self, pos1, pos2):
        # Update data and table
        self.data.loc[[pos1, pos2], ["sample", "primers"]] = self.data.loc[[pos2, pos1], ["sample", "primers"]].values
        self.update_table()

        # Update buttons
        self.well_buttons[pos1].setText(self.data.loc[pos1, "sample"])
        self.well_buttons[pos2].setText(self.data.loc[pos2, "sample"])

if __name__ == "__main__":
    app = QApplication([])
    mw = MainWindow()
    mw.show()
    app.exec()
