import numpy as np
import pandas as pd
import tkinter as tk
import tkinter.ttk as ttk

# https://realpython.com/python-gui-tkinter/#building-your-first-python-gui-application-with-tkinter

class InputWindow():
    def __init__(self, parent, title=None):
        self.parent = parent
        self.root = tk.Toplevel(parent)

        if title: self.root.title(title)

        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.root, text="Sample").grid(row=0, column=0)
        self.sample_entry = tk.Entry(self.root)
        self.sample_entry.grid(row=0, column=1)
        
        tk.Label(self.root, text="Primers").grid(row=1, column=0)
        self.primers_entry = tk.Entry(self.root)
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
        self.samples = pd.DataFrame(np.full((96, 2), ""), columns=["sample", "primers"], index=[f"{r}{c}" for r, c in zip(row, col)])

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
    
        # main_frame = tk.Frame(self.window, bg="red")
        
        # # Table format
        # side_frame = tk.Frame(self.window, bg="blue")
        
        # main_frame.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)
        # side_frame.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)

        ## Plate widget
        plate_frame = tk.Frame(panel1)
        plate_frame.pack(fill=tk.BOTH, expand=True)
        # main_frame.add(plate_widget)
        
        self.plate_buttons = {}
        for row in range(8):
            plate_frame.rowconfigure(row, weight=1)
            for col in range(12):
                plate_frame.columnconfigure(col, weight=1)
                button = tk.Button(plate_frame, text="", width=10, height=10,
                                   command=lambda r=row, c=col: self.edit_sample(r, c))
                button.grid(row=row, column=col, padx=1, pady=1, sticky="nsew")
                self.plate_buttons[(row, col)] = button
        # print(self.plate_buttons)

    def edit_sample(self, row, col):
        pos = f"{chr(65+row)}{col+1}"
        dialog = InputWindow(self.root, title=f"Edit {pos}")
        dialog.parent.wait_window(dialog.root)
        result = dialog.result

        if result is not None:
            self.samples.loc[pos, "sample"] = result[0]
            self.samples.loc[pos, "primers"] = result[1]
            self.update_plate()

    def update_plate(self):
        for (row, col), button in self.plate_buttons.items():
            pos = f"{chr(65+row)}{col+1}"
            sample = self.samples.loc[pos, "sample"]
            button.config(text=sample, font=("Helvetica", 10))

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("900x400")  # Set initial size to 800x600
    app = PlatePlannerApp(root)
    root.mainloop()