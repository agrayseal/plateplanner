import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog, messagebox
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

class PCRPlannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PCR Planner")
        
        self.samples = pd.DataFrame(np.full((8, 12), ''), columns=[f'Col{i+1}' for i in range(12)], index=[f'Row{chr(65+i)}' for i in range(8)])
        
        self.create_widgets()
    
    def create_widgets(self):
        # Main frame
        main_frame = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=5)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # # Configure grid layout
        # main_frame.grid_columnconfigure(0, weight=2)
        # main_frame.grid_columnconfigure(1, weight=4)
        # main_frame.grid_rowconfigure(0, weight=1)

        # Plate Map
        self.plate_frame = tk.Frame(main_frame)
        # self.plate_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        main_frame.add(self.plate_frame)

        self.plate_buttons = {}
        for row in range(8):
            self.plate_frame.grid_rowconfigure(row, weight=1)
            for col in range(12):
                self.plate_frame.grid_columnconfigure(col, weight=1)
                button = tk.Button(self.plate_frame, text='', command=lambda r=row, c=col: self.edit_sample(r, c))
                button.grid(row=row, column=col, padx=1, pady=1, sticky="nsew")
                self.plate_buttons[(row, col)] = button

        # Side panel
        side_panel = tk.Frame(main_frame)
        # side_panel.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        main_frame.add(side_panel)

        # Configure side panel grid
        side_panel.grid_propagate(False)
        side_panel.grid_columnconfigure(0, weight=1)
        side_panel.grid_rowconfigure(2, weight=1)

        # Load and Save buttons
        load_button = tk.Button(side_panel, text="Load CSV", command=self.load_csv)
        load_button.grid(row=0, column=0, sticky="ew", pady=5)
        
        save_button = tk.Button(side_panel, text="Save CSV", command=self.save_csv)
        save_button.grid(row=1, column=0, sticky="ew", pady=5)

        # Treeview
        self.tree = ttk.Treeview(side_panel, columns=("pos", "sample", "primers"), show='headings')
        self.tree.heading('pos', text='Position')
        self.tree.heading('sample', text='Sample')
        self.tree.heading('primers', text='Primers')
        
        # Adjust column widths
        self.tree.column('pos', width=50)
        self.tree.column('sample', width=100)
        self.tree.column('primers', width=100)

        self.tree.grid(row=2, column=0, sticky="nsew")

        self.initialize_dataframe()
        self.update_plate()
        self.update_treeview()

    def initialize_dataframe(self):
        pos_list = [f"{chr(65+row)}{col+1}" for row in range(8) for col in range(12)]
        self.samples = pd.DataFrame({
            "pos": pos_list,
            "sample": [""] * 96,
            "primers": [""] * 96
        })
        self.samples.set_index('pos', inplace=True)

    def edit_sample(self, row, col):
        pos = f"{chr(65+row)}{col+1}"
        sample_name = tk.simpledialog.askstring("Input", f"Enter sample name for position {pos}:")
        if sample_name is not None:
            self.samples.loc[pos, "sample"] = sample_name
            self.update_plate()
            self.update_treeview()
        
    def update_treeview(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        df_with_blanks = self.samples.fillna('')
        for pos, row in df_with_blanks.iterrows():
            self.tree.insert("", "end", values=(pos, row["sample"], row["primers"]))

    def update_plate(self):
        for (row, col), button in self.plate_buttons.items():
            pos = f"{chr(65+row)}{col+1}"
            sample = self.samples.loc[pos, "sample"]
            button.config(text=sample, font=('Helvetica', 10))  # Adjust font size as needed
    
    def load_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            try:
                df = pd.read_csv(file_path, dtype=str, keep_default_na=False)
                required_columns1 = {"pos", "sample", "primers"}
                required_columns2 = {"row", "col", "sample", "primers"}
                # if not (required_columns1.issubset(df.columns) or required_columns2.issubset(df.columns)):
                #     messagebox.showerror("Error", "CSV file is missing required columns.")
                #     return
                if required_columns2.issubset(df.columns):
                    df["pos"] = df["row"].astype(str) + df["col"].astype(str)
                    print(df)
                elif not required_columns1.issubset(df.columns):
                    messagebox.showerror("Error", "CSV file is missing required columns.")
                    return

                df.set_index("pos", inplace=True)
                self.samples = df
                self.update_plate()
                self.update_treeview()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load CSV file: {e}")
    
    def save_csv(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if file_path:
            self.samples.to_csv(file_path)
            messagebox.showinfo("Save CSV", f"CSV saved to {file_path}")
    
    def save_plate_map(self):
        fig, ax = plt.subplots()
        ax.axis('tight')
        ax.axis('off')
        table = ax.table(cellText=self.samples.values, colLabels=self.samples.columns, rowLabels=self.samples.index, cellLoc='center', loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        fig.tight_layout()
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if file_path:
            plt.savefig(file_path)
            plt.close()
            messagebox.showinfo("Save Plate Map", f"Plate map saved to {file_path}")
        else:
            plt.close()

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("900x400")  # Set initial size to 800x600
    app = PCRPlannerApp(root)
    root.mainloop()
