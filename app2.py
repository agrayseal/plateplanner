import numpy as np
import pandas as pd
import tkinter as tk
import tkinter.ttk as ttk

# https://realpython.com/python-gui-tkinter/#building-your-first-python-gui-application-with-tkinter

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

        tk.Label(panel1, text="testing").pack()
        tk.Label(panel2, text="testing2").pack()
        
        # Plate widget
        plate_frame = tk.Frame(panel1).pack()
        
        
        
        # main_frame = tk.Frame(self.window, bg="red")
        
        # # Table format
        # side_frame = tk.Frame(self.window, bg="blue")
        
        # main_frame.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)
        # side_frame.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)

        ## Plate widget
        # plate_widget = tk.Frame(main_frame)
        # main_frame.add(plate_widget)
        
        # plate_buttons = {}
        # for row in range(8):
        #     for col in range(12):
        #         button = tk.Button(plate_widget)
        #         button.grid(row=row, column=col)
        #         plate_buttons[(row, col)] = button

        # main_frame.add(self.plate_widget)

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("900x400")  # Set initial size to 800x600
    app = PlatePlannerApp(root)
    root.mainloop()