from PIL import Image, ImageDraw, ImageEnhance, ImageTk
import json
import os
import tkinter as tk
from tkinter import filedialog, ttk

def load_image_and_json():
    root = tk.Tk()
    root.withdraw()
    image_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
    if not image_path:
        print("No image selected.")
        return None, None, None
    json_path = os.path.splitext(image_path)[0] + ".json"
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"JSON file not found: {json_path}")
        return None, None, None
    return Image.open(image_path), data, root

def draw_bounding_box(image, bbox, width, height, is_selected=False):
    overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    x1, y1, x2, y2 = bbox
    color = "red" if is_selected else "red"
    draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
    if not is_selected:
        draw.rectangle([0, 0, width, y1], fill=(128, 128, 128, 180))
        draw.rectangle([0, y2, width, height], fill=(128, 128, 128, 180))
        draw.rectangle([0, y1, x1, y2], fill=(128, 128, 128, 180))
        draw.rectangle([x2, y1, width, y2], fill=(128, 128, 128, 180))
    return Image.alpha_composite(image.convert("RGBA"), overlay)

def display_image(root, canvas, image, data, current_index):
    width, height = image.size
    bbox_str = data["DETAILS"][current_index]["BBOX"]
    bbox = list(map(int, bbox_str))
    output_image = draw_bounding_box(image, bbox, width, height, is_selected=True)
    output_image_tk = ImageTk.PhotoImage(output_image)
    canvas.delete("all")
    canvas.create_image(0, 0, anchor=tk.NW, image=output_image_tk)
    root.image_tk = output_image_tk
    center_window(root, bbox, width, height)

def center_window(root, bbox, image_width, image_height):
    x1, y1, x2, y2 = bbox
    box_width = x2 - x1
    box_height = y2 - y1
    root_width = min(image_width, box_width * 2)
    root_height = min(image_height, box_height * 2)
    root.geometry(f"{root_width}x{root_height}")
    root.update_idletasks()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width / 2) - (root_width / 2)
    y = (screen_height / 2) - (root_height / 2)
    root.geometry(f"+{int(x)}+{int(y)}")

def main():
    image, data, root = load_image_and_json()
    if image is None or data is None:
        return
    root.deiconify()
    root.title("Image Viewer")

    # Create a main frame to contain both the canvas and button frame
    main_frame = ttk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True)

    width, height = image.size
    canvas = tk.Canvas(main_frame, width=width, height=height)
    canvas.pack(fill=tk.BOTH, expand=True)
    canvas.config(width=max(width, 500), height=max(height, 500)) # Ensure minimum size

    current_index = 0
    display_image(root, canvas, image, data, current_index)

    def next_image():
        nonlocal current_index
        current_index = (current_index + 1) % len(data["DETAILS"])
        display_image(root, canvas, image, data, current_index)

    def prev_image():
        nonlocal current_index
        current_index = (current_index - 1) % len(data["DETAILS"])
        display_image(root, canvas, image, data, current_index)

    button_frame = ttk.Frame(main_frame)
    button_frame.pack(pady=10, fill=tk.X) # Fill in the x direction

    prev_button = ttk.Button(button_frame, text="Previous", command=prev_image)
    prev_button.pack(side=tk.LEFT, padx=5)

    next_button = ttk.Button(button_frame, text="Next", command=next_image)
    next_button.pack(side=tk.LEFT, padx=5)

    root.mainloop()

if __name__ == "__main__":
    main()