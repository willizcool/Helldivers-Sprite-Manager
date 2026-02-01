import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import json

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.create_widgets()
        self.bounding_boxes = []
        self.current_box_index = 0
        self.overlay = None

    def create_widgets(self):
        # Create frame for buttons
        self.button_frame = tk.Frame(self)
        self.button_frame.pack(side="left", fill="y")

        # Create buttons
        self.load_button = tk.Button(self.button_frame, text="Load Image", command=self.load_image)
        self.load_button.pack(side="top", fill="x")

        self.left_button = tk.Button(self.button_frame, text="Left", command=self.go_to_previous_box)
        self.left_button.pack(side="top", fill="x")

        self.right_button = tk.Button(self.button_frame, text="Right", command=self.go_to_next_box)
        self.right_button.pack(side="top", fill="x")

        self.quit_button = tk.Button(self.button_frame, text="Quit", command=self.master.destroy)
        self.quit_button.pack(side="bottom", fill="x")

        # Create frame for canvas and scrollbars
        self.canvas_frame = tk.Frame(self)
        self.canvas_frame.pack(side="right", fill="both", expand=True)

        # Create canvas and scrollbars
        self.v_scrollbar = tk.Scrollbar(self.canvas_frame, orient="vertical")
        self.v_scrollbar.pack(side="right", fill="y")

        self.h_scrollbar = tk.Scrollbar(self.canvas_frame, orient="horizontal")
        self.h_scrollbar.pack(side="bottom", fill="x")

        self.canvas = tk.Canvas(self.canvas_frame, width=800, height=600, yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)

        self.v_scrollbar.configure(command=self.canvas.yview)
        self.h_scrollbar.configure(command=self.canvas.xview)

        # Bind mouse wheel events
        self.canvas.bind_all("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind_all("<Button-4>", self.on_mouse_wheel)
        self.canvas.bind_all("<Button-5>", self.on_mouse_wheel)

    def load_image(self):
        # Open file dialog to select image
        filename = filedialog.askopenfilename(filetypes=[("Image Files", ".jpg .jpeg .png .bmp")])

        if filename:
            # Load image using PIL
            image = Image.open(filename)
            photo = ImageTk.PhotoImage(image)

            # Add image to canvas
            self.canvas.create_image(0, 0, image=photo, anchor="nw")
            self.canvas.image = photo  # Keep a reference to prevent garbage collection

            # Load JSON file
            json_filename = filename.replace(".jpg", ".json").replace(".jpeg", ".json").replace(".png", ".json").replace(".bmp", ".json")
            try:
                with open(json_filename, "r") as f:
                    json_data = json.load(f)
                    self.bounding_boxes = json_data["DETAILS"]
                    self.draw_bounding_boxes(self.bounding_boxes)
                    self.scroll_to_bounding_box(self.bounding_boxes[0]["BBOX"])
            except FileNotFoundError:
                print("JSON file not found")

            # Update scrollbars
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def draw_bounding_boxes(self, bounding_boxes):
        for box in bounding_boxes:
            x1, y1, x2, y2 = box["BBOX"]
            self.canvas.create_rectangle(x1, y1, x2, y2, outline="red")

    def scroll_to_bounding_box(self, bbox):
        x1, y1, x2, y2 = bbox
        width = x2 - x1
        height = y2 - y1
        x_center = (x1 + x2) / 2
        y_center = (y1 + y2) / 2
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        x_scroll = (x_center - canvas_width / 2) / self.canvas.winfo_reqwidth()
        y_scroll = (y_center - canvas_height / 2) / self.canvas.winfo_reqheight()
        self.canvas.xview_moveto(x_scroll)
        self.canvas.yview_moveto(y_scroll)
        self.add_overlay()

    def go_to_previous_box(self):
        if self.current_box_index > 0:
            self.current_box_index -= 1
            self.scroll_to_bounding_box(self.bounding_boxes[self.current_box_index]["BBOX"])

    def go_to_next_box(self):
        if self.current_box_index < len(self.bounding_boxes) - 1:
            self.current_box_index += 1
            self.scroll_to_bounding_box(self.bounding_boxes[self.current_box_index]["BBOX"])

    def on_mouse_wheel(self, event):
        if event.state & 0x0001:  # Check if Shift key is pressed
        # Horizontal scroll
            self.canvas.xview_scroll(-1 if event.delta > 0 else 1, "units")
        else:
        # Vertical scroll
            self.canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")
    
    def add_overlay(self):
        if self.overlay:
            self.canvas.delete(self.overlay)
        self.overlay = self.canvas.create_rectangle(0, 0, self.canvas.winfo_reqwidth(), self.canvas.winfo_reqheight(), fill="#AAAAAA", stipple="gray75")

root = tk.Tk()
app = Application(master=root)
app.mainloop()