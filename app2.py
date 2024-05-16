import matplotlib.pyplot as plt
from matplotlib.colors import to_hex
import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
import tkinter.ttk as ttk
from tkmacosx import Button

# https://realpython.com/python-gui-tkinter/#building-your-first-python-gui-application-with-tkinter

class InputWindow():
    def __init__(self, parent, data, pos):
        self.parent = parent
        self.data = data
        self.pos = pos

        self.root = tk.Toplevel(parent)
        self.root.title(f"Edit {pos}")

        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.root, text="Sample").grid(row=0, column=0)
        self.sample_entry = tk.Entry(self.root)
        self.sample_entry.insert(tk.END, self.data.loc[self.pos]["sample"])
        self.sample_entry.grid(row=0, column=1)
        
        tk.Label(self.root, text="Primers").grid(row=1, column=0)
        self.primers_entry = tk.Entry(self.root)
        self.primers_entry.insert(tk.END, self.data.loc[self.pos]["primers"])
        self.primers_entry.grid(row=1, column=1)

        self.ok_button = tk.Button(self.root, text="OK", command=self.ok)
        self.ok_button.grid(row=2, column=0)

    def ok(self):
        self.result = (self.sample_entry.get(), self.primers_entry.get())
        self.cancel()
    
    def cancel(self):
        self.parent.focus_set()
        self.root.destroy()

class PlatePlannerApp:
    # Script to run on opening
    def __init__(self, root):
        self.root = root
        self.root.title("Plate Planner")

        row = [chr(65+i) for i in range(8)] * 12
        col = np.repeat(range(1, 13), 8)
        self.data = pd.DataFrame(np.full((96, 2), ""), columns=["sample", "primers"], index=[f"{r}{c}" for r, c in zip(row, col)])
        self.selected_cells = set()

        self.create_widgets()

    def create_widgets(self):
        ## Define layout
        window = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        window.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)

        panel1 = tk.Frame(window, bg="red")
        panel2 = tk.Frame(window, bg="blue")
        window.add(panel1, weight=2)
        window.add(panel2, weight=1)

        tk.Label(panel1, text="Plate layout").pack()
        tk.Label(panel2, text="testing2").pack()
    
        ## Plate widget
        plate_frame = tk.Frame(panel1)
        plate_frame.pack(fill=tk.BOTH, expand=True)
        
        self.plate_buttons = {}
        for row in range(8):
            plate_frame.rowconfigure(row, weight=1)
            for col in range(12):
                plate_frame.columnconfigure(col, weight=1)
                button = Button(plate_frame, text="", width=10, height=10,
                                   command=lambda r=row, c=col: self.edit_sample(r, c))
                button.grid(row=row, column=col, padx=1, pady=1, sticky="nesw")
                self.plate_buttons[(row, col)] = button

        ## Table widget
        # Load and save file
        tk.Button(panel2, text="Load CSV", command=self.load_csv).pack()
        tk.Button(panel2, text="Save CSV", command=self.save_csv).pack()

        # Table display
        table_frame = tk.Frame(panel2)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(table_frame)
        scrollbar = tk.Scrollbar(table_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(fill=tk.BOTH, expand=True)
        
        # table_grid = tk.Frame(canvas, bg="green")
        cols = ("pos", "sample", "primers")
        self.table = ttk.Treeview(canvas, columns=cols, show="headings")
        for i in cols:
            self.table.column(i, width=50)
            self.table.heading(i, text=i)
        
        self.table.pack(fill=tk.BOTH, expand=True)
        self.update_table()

    def edit_sample(self, row, col):
        pos = f"{chr(65+row)}{col+1}"
        dialog = InputWindow(self.root, data=self.data, pos=pos)
        dialog.parent.wait_window(dialog.root)
        result = dialog.result

        if result is not None:
            self.data.loc[pos, "sample"] = result[0]
            self.data.loc[pos, "primers"] = result[1]
            self.update_plate()
            self.update_table()

    def get_colour_map(self):
        primers = self.data["primers"].unique()
        primers = [i for i in primers if i]
        cmap = plt.get_cmap("tab20", len(primers))
        colour_map = {primer: to_hex(cmap(i)) for i, primer in enumerate(primers)}
        return colour_map

    def update_plate(self):
        colour_map = self.get_colour_map()
        # print(colour_map)
        for (row, col), button in self.plate_buttons.items():
            pos = f"{chr(65+row)}{col+1}"
            sample = self.data.loc[pos, "sample"]
            primers = self.data.loc[pos, "primers"]

            colour = colour_map.get(primers, "white")
            button.config(text=sample, font=("Helvetica", 10), highlightbackground=colour)

    def update_table(self):
        for i in self.table.get_children():
            self.table.delete(i)

        for pos, row in self.data.iterrows():
            self.table.insert("", "end", values=(pos, row["sample"], row["primers"]))

    def load_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        self.root.focus_force()
        if file_path:
            try:
                df = pd.read_csv(file_path, dtype=str, keep_default_na=False)
                if "pos" not in df.columns:
                    df["pos"] = df["row"].astype(str) + df["col"].astype(str)
                df.set_index("pos", inplace=True)

                self.data = df
                self.update_plate()
                self.update_table()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load CSV file: {e}")

    def save_csv(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if file_path:
            self.data.to_csv(file_path)
            messagebox.showinfo("Save CSV", f"CSV saved to {file_path}")

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("900x400")  # Set initial size to 800x600
    app = PlatePlannerApp(root)
    root.mainloop()