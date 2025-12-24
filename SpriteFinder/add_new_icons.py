import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk, ImageDraw
import threading, os, json, uuid, glob, math
import findspriteinbbox
from findspriteinbbox import spriteBox
from findspriteinbbox import modeenum
from collections import Counter
from Queue import Queue



class ImageViewer(tk.Tk):
    
    def __init__(self, *args):
        super().__init__()
        self.title("Tkinter Image Viewer with Zoom and Pan")
        self.geometry("800x600")

        # Variables
        self.scale = 1.0
        self.image = None
        self.tk_image = None
        self.canvas_image = None
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.rect = None
        self.mousex1 = 0
        self.mousey1 = 0
        self.mbpressed = 0

        self.boxQueue = Queue()
        self.removeQueue = Queue()
        self.foundimages = []
        self.imageids = []
        self.bbox_list: list[spriteBox] = [] 
        self.file_path = None
        self.bgcolor = None
        self.sheetname = None

        self.mwthread = None
        self.data = None
        

        # Set up the UI
        self.setup_ui()

        # If an argument was passed (folder or file), handle it
        if len(args) > 1 and args[0] and args[1]:
            self.file_path = args[0]
            self.sheetname = args[1]
            candidate =  os.path.join(self.file_path,"original", self.sheetname + ".png")
            if os.path.isfile(candidate):
                try:
                    self.open_image(candidate)
                    self.load_locations()
                except Exception as e:
                    print(f"Error processing file '{candidate}': {e}")
        


    def setup_ui(self):
        # Create canvas inside a frame with scrollbars
        self.frame = tk.Frame(self)
        self.frame.pack(fill=tk.BOTH, expand=True, side=tk.RIGHT)

        self.canvas = tk.Canvas(self.frame, bg="gray", cursor="arrow")
        self.canvas.grid(row=0, column=0, sticky="nsew")

        # Scrollbars
        self.h_scrollbar = tk.Scrollbar(self.frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.v_scrollbar = tk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.h_scrollbar.grid(row=1, column=0, sticky="we")
        self.v_scrollbar.grid(row=0, column=1, sticky="ns")

        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        self.canvas.configure(xscrollcommand=self.h_scrollbar.set, yscrollcommand=self.v_scrollbar.set)

        # Buttons for zoom in/out at the bottom
        bottom_frame = tk.Frame(self)
        bottom_frame.pack(side=tk.LEFT, fill=tk.X)

        # open_button = tk.Button(bottom_frame, text="Open", command=self.open_image)
        # open_button.pack(side=tk.LEFT, padx=5, pady=5)
        mode_frame = tk.Frame(bottom_frame, borderwidth=2, relief="groove")
        mode_frame.pack(side=tk.TOP, padx=5, pady=5)

        self.mode = tk.IntVar()
        self.mode.set(modeenum.MODE_FINDSPRITE.value)  # default value

        select_button = tk.Radiobutton(mode_frame, text="Auto Find Sprites", variable=self.mode, value=modeenum.MODE_FINDSPRITE.value)
        select_button.pack(side=tk.TOP, anchor="w")

        select_button = tk.Radiobutton(mode_frame, text="Manualy Select Sprites", variable=self.mode, value=modeenum.MODE_MANUALSPRITE.value)
        select_button.pack(side=tk.TOP, anchor="w")

        move_button = tk.Radiobutton(mode_frame, text="Move Bounds", variable=self.mode, value=modeenum.MODE_MOVE.value)
        move_button.pack(side=tk.TOP, anchor="w")

        move_button = tk.Radiobutton(mode_frame, text="Name Icons", variable=self.mode, value=modeenum.MODE_DESCRIPTION.value)
        move_button.pack(side=tk.TOP, anchor="w")

        zoom_in_button = tk.Button(bottom_frame, text="Zoom In (+)", command=lambda: self.zoom(1.5))
        zoom_in_button.pack(side=tk.TOP, padx=5, pady=5)

        zoom_out_button = tk.Button(bottom_frame, text="Zoom Out (-)", command=lambda: self.zoom(1/1.5))
        zoom_out_button.pack(side=tk.TOP, padx=5, pady=5)

        save_button = tk.Button(bottom_frame, text="Save", command=self.save_locations)
        save_button.pack(side=tk.TOP, padx=5, pady=5)

        tk.Label(bottom_frame, text="Min Size:").pack(side=tk.TOP, padx=5, pady=5)

        bbox_dim_frame = tk.Frame(bottom_frame)

        vcmd = (self.frame.register(self.validate_int), "%P")

        self.min_bbox_width = tk.StringVar(value="32")
        self.standard_bbox_width_entry = tk.Entry(
            bbox_dim_frame,
            textvariable=self.min_bbox_width,
            width=5,
            validate="key",
            validatecommand=vcmd
        )
        self.standard_bbox_width_entry.pack(side=tk.LEFT, padx=1, pady=5)

        tk.Label(bbox_dim_frame, text="x").pack(side=tk.LEFT, padx=1, pady=5)
        self.min_bbox_height = tk.StringVar(value="32")
        self.standard_bbox_height_entry = tk.Entry(
            bbox_dim_frame,
            textvariable=self.min_bbox_height,
            width=5,
            validate="key",
            validatecommand=vcmd
        )
        self.standard_bbox_height_entry.pack(side=tk.LEFT, padx=1, pady=5)

        bbox_dim_frame.pack(side=tk.TOP, padx=5, pady=5)

        # Bind mouse and keyboard events
        self.bind_events()
        self.canvas_refresh()

    def save_locations(self):
        details_by_id = {
            str(d["ID"]): d
            for d in self.data.get("DETAILS", [])
        } if self.data else {}
        if not  self.bbox_list or not self.file_path:
            return
        savedata = {}
        name = os.path.splitext(os.path.basename(self.file_path))[0]
        savedata["SHEETNAME"] = name
        savedata["DEFAULTMINBBOX"] = [int(self.min_bbox_width.get()), int(self.min_bbox_height.get())]
        savedata["DETAILS"] = []
        for each in self.bbox_list:
            x1, y1, x2, y2 = each.bbox
            exx1, exy1, exx2, exy2 = each.expandedbbox
            id_str = str(each.id)
            description = each.description
            
            found = details_by_id.get(id_str, {})

            newdata = {
                "Order": found.get("Order", 0),
                "SaveID": found.get("SaveID", 0),
                "ID": id_str,
                "DESCRIPTION": description,
                "Group": found.get("Group", "DEFAULT"),
                "SearchBBOX": f"[{x1}, {y1}, {x2}, {y2}]",
                "ExpandedBBOX": f"[{exx1}, {exy1}, {exx2}, {exy2}]",
            }

            savedata["DETAILS"].append(newdata)
        file_path = os.path.join(os.path.dirname(self.file_path), f"{name}.json")
        with open(file_path, 'w') as f:
            json.dump(savedata, f, indent=4)  # Compact formatting
         # Post-process file to remove quotes around numbers
        with open(file_path, 'r') as f:
            lines = f.readlines()

        with open(file_path, 'w') as f:
            for line in lines:
                if '[' in line and ']' in line and any(char.isdigit() for char in line):
                    f.write(line.replace('"[', '[').replace(']"', ']'))  # Remove quotes around bbox
                else:
                    f.write(line)  # Write other lines as-is

        cropped_savepath = os.path.join(os.path.dirname(self.file_path), "cropped_icons")
        if not os.path.exists(cropped_savepath):
            os.makedirs(cropped_savepath)
        
        for each in self.bbox_list:
            x1, y1, x2, y2 = each.expandedbbox
            croppedimage = self.image.crop((x1, y1, x2, y2))
            croppedimage.save(os.path.join(cropped_savepath, f"{each.id}.png"))

    def load_locations(self):
        
        if not self.file_path or not self.sheetname:
            return
        jsonpath = os.path.join(os.path.dirname(self.file_path), f"{self.sheetname}.json")
        if not os.path.isfile(jsonpath):
            print(f"JSON file not found: {jsonpath}")
            return
        with open(jsonpath, 'r') as f:
            self.data = json.load(f)
            self.bbox_list = []
            minwidth, minheight = self.load_items(self.data, "DEFAULTMINBBOX", [32,32])
            self.min_bbox_width.set(str(minwidth))
            self.min_bbox_height.set(str(minheight))

            for entry in self.data["DETAILS"]:
                bbox = [int(x) for x in entry["SearchBBOX"]]
                expandedbbox = [int(x) for x in entry["ExpandedBBOX"]]
                id = entry["ID"]
                description = entry["DESCRIPTION"]
                self.bbox_list.append(spriteBox(bbox, expandedbbox, id, description))
            self.redraw_boxes()

    def load_items(self, data, name, default=None):
        try:
            return data[name]
        except:
            return default
        
    def validate_int(self, new_value: str):
        if new_value == "":
            return True  # allow empty temporarily
        return new_value.isdigit()

    def do_boxes_overlap(self, boxes1: spriteBox, boxes2: spriteBox) -> bool:
        """
        Check if two bounding boxes overlap.
        Each bounding box is defined by (x1, y1, x2, y2).
        """
        x1_1, y1_1, x2_1, y2_1 = boxes1.bbox
        x1_2, y1_2, x2_2, y2_2 = boxes2.bbox
        
        # Check if they do not overlap horizontally or vertically
        if x2_1 <= x1_2 or x2_2 <= x1_1 or y2_1 <= y1_2 or y2_2 <= y1_1:
            return False
        return True

    def display_box(self, bboxs: spriteBox, forcedraw=False):
        """
        Displays a bounding box on the canvas, scaled by the current zoom level.
        """
        if not forcedraw:
            for oldboxes in self.bbox_list:
                if(self.do_boxes_overlap(oldboxes, bboxs)):
                    return
        # Unpack the bounding box
        x1, y1, x2, y2 = bboxs.expandedbbox
        ix1, iy1, ix2, iy2 = bboxs.bbox
        description = bboxs.description
        

        # Apply the zoom level to position and size
        zoom = self.scale  # Example: 1.0 = 100%, 2.0 = 200%, etc.
        
        scaled_x1 = int(x1 * zoom)
        scaled_y1 = int(y1 * zoom)
        scaled_x2 = int(x2 * zoom)
        scaled_y2 = int(y2 * zoom)
        scaled_ix1 = int(ix1 * zoom)
        scaled_iy1 = int(iy1 * zoom)        
        scaled_ix2 = int(ix2 * zoom)
        scaled_iy2 = int(iy2 * zoom)

        xsize = scaled_x2 - scaled_x1
        ysize = scaled_y2 - scaled_y1

        ix1 = scaled_ix1 - scaled_x1
        iy1 = scaled_iy1 - scaled_y1
        ixsize = scaled_ix2 - scaled_ix1
        iysize = scaled_iy2 - scaled_iy1

        

        if xsize <= 0 or ysize <= 0:
            print(f"Invalid box size after scaling: ({xsize}, {ysize})")
            return

        self.bbox_list.append(bboxs)

        # Create a transparent image for the box overlay
        box_img = Image.new('RGBA', (xsize, ysize), (0, 0, 0, 0))  # fully transparent

        # Draw a semi-transparent red rectangle on the transparent image
        draw = ImageDraw.Draw(box_img)
        draw.rectangle([(0, 0), (xsize-1, ysize-1)], outline=(255, 0, 0, 255), fill=(255, 0, 0, 64),  width=1)  # Red
        text = str(description)
        bbox = draw.textbbox((0, 0), text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Padding around text
        offset = 6
        padding = 4

        # Background box under text
        text_bg_box = [
            offset - padding,
            offset - padding,
            offset + text_width + padding,
            offset + text_height + padding
        ]

        draw.rectangle(
            text_bg_box,
            fill=(0, 0, 0, 64)  # semi-transparent black
        )

        # Draw text on top
        draw.text((offset, offset), text, fill=(255, 255, 255, 255))

        # Convert to Tkinter-compatible image
        tk_box_img = ImageTk.PhotoImage(box_img)

        # Save the image reference to prevent garbage collection
        self.foundimages.append(tk_box_img)

        # Create the image on the canvas at the scaled position
        box_id = self.canvas.create_image(scaled_x1, scaled_y1, anchor="nw", image=tk_box_img)
        bboxs.set_canvas(self,self.canvas,box_id,self.mode,self.scale)

        # Store the canvas object ID
        self.imageids.append(box_id)

    def remove_box(self, bbox: spriteBox):
        for i in range(len(self.bbox_list) - 1, -1, -1):
            if(self.do_boxes_overlap(self.bbox_list[i], bbox)):
                del self.bbox_list [i]
        self.redraw_boxes()


    def canvas_refresh(self):
        while not self.boxQueue.is_empty():
            boxs = self.boxQueue.dequeue()
            thread = threading.Thread(target = self.display_box, args=(boxs,))
            thread.start()
        while not self.removeQueue.is_empty():
            boxs = self.removeQueue.dequeue()
            thread = threading.Thread(target = self.remove_box, args=(boxs,))
            thread.start()
        self.frame.after(1000, self.canvas_refresh)
        

    def bind_events(self):
        # Mouse wheel scrolling and zoom
        self.canvas.bind("<MouseWheel>", self.mouse_wheel_event)  # Windows
        self.canvas.bind("<Shift-MouseWheel>", self.shift_mouse_wheel_event)
        self.bind("<Control-MouseWheel>", self.ctrl_mouse_wheel_zoom)

        # Linux systems - Button-4 (up), Button-5 (down)
        self.canvas.bind("<Button-4>", self.mouse_wheel_event)
        self.canvas.bind("<Button-5>", self.mouse_wheel_event)

        # Middle mouse button for panning
        self.canvas.bind("<ButtonPress-2>", self.start_pan)
        self.canvas.bind("<B2-Motion>", self.do_pan)

        # Find boxes
        self.canvas.bind("<ButtonPress-1>",self.on_mouse1_button_press)
        self.canvas.bind("<B1-Motion>",self.on_mouse1_drag)
        self.canvas.bind("<ButtonRelease-1>",self.on_mouse1_release)

        #Remove boxes
        self.canvas.bind("<ButtonPress-3>",self.on_mouse3_button_press)
        self.canvas.bind("<B3-Motion>",self.on_mouse3_drag)
        self.canvas.bind("<ButtonRelease-3>",self.on_mouse3_release)

        # Keyboard shortcuts
        self.bind('<Key-equal>', lambda e: self.zoom(1.5))
        self.bind('<Key-minus>', lambda e: self.zoom(1/1.5))
        self.bind('<Control-s>', lambda e: self.save_locations)
                

    def open_image(self, file_path=None):
        if file_path is None:
            file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")])
        if not file_path:
            return
        self.bbox_list = []
        self.imageids = []
        self.foundimages = []
        self.boxQueue = Queue()
        self.file_path = file_path
        self.image = Image.open(file_path)
        self.scale = 1.0
        self.display_image()
        self.bgcolor = self.get_most_common_corner_color(self.image)

    def display_image(self):
        if self.image is None:
            return

        width, height = self.image.size
        scaled_width = int(width * self.scale)
        scaled_height = int(height * self.scale)

        resample_method = Image.Resampling.LANCZOS 

        resized_image = self.image.resize((scaled_width, scaled_height), resample=resample_method)
        self.tk_image = ImageTk.PhotoImage(resized_image)

        self.canvas.delete("all")  # Clear canvas
        self.canvas_image = self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)

        # Configure scroll region to new image size
        self.canvas.config(scrollregion=(0, 0, scaled_width, scaled_height))

    def zoom(self, factor):
        if self.image is None:
            return
        self.scale *= factor
        self.display_image()
        self.redraw_boxes()  # You can recreate/redraw boxes after zooming in or out

    def redraw_boxes(self):
    # Clear all previous box overlays
        for box_id in self.imageids:
            self.canvas.delete(box_id)

        self.imageids.clear()
        self.foundimages.clear()

        #create a copy since cant redraw originals
        templist = self.bbox_list.copy()
        self.bbox_list.clear()

        # Redraw each box at the new zoom level
        for each in templist:  # Assuming you keep track of all bounding boxes
            self.display_box(each)

    def ctrl_mouse_wheel_zoom(self, event):
        """
        Zoom in/out by a factor when the Ctrl key is pressed and the mouse wheel is scrolled.
        """
        self.scale *= 10/9 if event.delta > 0 else 9/10
        if self.mwthread:
            self.frame.after_cancel(self.mwthread)
        self.mwthread = self.frame.after(100, self.zoom(1))

    def mouse_wheel_event(self, event):
        # Normal vertical scrolling
        if event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")

    def shift_mouse_wheel_event(self, event):
        # Horizontal scrolling with shift + mousewheel
        if event.delta > 0:
            self.canvas.xview_scroll(-1, "units")
        elif event.delta < 0:
            self.canvas.xview_scroll(1, "units")

    def get_most_common_corner_color(self, image):
        """Get the most common color from the 4 corners of the image."""
        width, height = image.size
        pixels = image.load()

        corner_pixels = []
        corner_pixels.append(pixels[0, 0])
        corner_pixels.append(pixels[width-1, 0])
        corner_pixels.append(pixels[0, height-1])
        corner_pixels.append(pixels[width-1,height-1])

        # Count occurrences of each color
        color_counter = Counter(corner_pixels)

        # Get the most common color
        most_common_color, count = color_counter.most_common(1)[0]
        print(f"Most common corner color: {most_common_color} (found {count} times)")
        return most_common_color

    def on_mouse1_button_press(self,event):
        if self.mbpressed != 0:
            return
        match self.mode.get():
            case modeenum.MODE_FINDSPRITE.value | modeenum.MODE_MANUALSPRITE.value:
                self.mbpressed = 1
                # Save the starting point
                self.mousex1,self.mousey1 = (self.canvas.canvasx(event.x),self.canvas.canvasy(event.y))
                # Create a rectangle (empty for now)
                self.rect = self.canvas.create_rectangle(self.mousex1, self.mousey1, self.mousex1, self.mousey1, outline='green', width=2)
            case _:
                return
    def on_mouse1_drag(self,event):
        if self.mbpressed != 1:
            return
        # Update the rectangle as you drag
        match self.mode.get():
            case modeenum.MODE_FINDSPRITE.value | modeenum.MODE_MANUALSPRITE.value:
                cur_x, cur_y = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
                # Modify the coordinates of the rectangle
                self.canvas.coords(self.rect, self.mousex1, self.mousey1, cur_x, cur_y)
                self.canvas.update()
            case _:
                return


    def on_mouse1_release(self, event):
        if self.mbpressed != 1:
            return
        match self.mode.get():
            case modeenum.MODE_FINDSPRITE.value | modeenum.MODE_MANUALSPRITE.value:
                self.mbpressed = 0
                self.canvas.delete(self.rect)
                # Final rectangle coordinates in canvas space
                end_x = self.canvas.canvasx(event.x)
                end_y = self.canvas.canvasy(event.y)
                #make sure box is at least 1 pixel
                if end_x == self.mousex1:
                    end_x += 1
                if end_y == self.mousey1:
                    end_y += 1

                # Get selection box in canvas coords
                mousebbox_canvas = (
                    min(self.mousex1, end_x),
                    min(self.mousey1, end_y),
                    max(self.mousex1, end_x),
                    max(self.mousey1, end_y)
                )

                print(f"Canvas box coordinates: {mousebbox_canvas}")

                if not self.image:
                    print("No image loaded.")
                    return

                # Convert canvas coordinates to original image coordinates by scaling factor
                scale_factor = self.scale
                mousebbox_image = (
                    int(mousebbox_canvas[0] / scale_factor),
                    int(mousebbox_canvas[1] / scale_factor),
                    int(mousebbox_canvas[2] / scale_factor),
                    int(mousebbox_canvas[3] / scale_factor)
                )

                print(f"Original image box coordinates: {mousebbox_image}")
                manual = True if self.mode.get() == modeenum.MODE_MANUALSPRITE.value else False
                # Start a new thread to run find_sprite_route, passing the cropped image and background color
                thread = threading.Thread(target=findspriteinbbox.find_non_background_pixels, args=(self.image, mousebbox_image, self.bgcolor, self.boxQueue, int(self.min_bbox_width.get()), int(self.min_bbox_height.get()),manual))
                thread.start()
            case _:
                return
        

    def on_mouse3_button_press(self,event):
        if self.mbpressed != 0:
            return
        match self.mode.get():
            case modeenum.MODE_FINDSPRITE.value | modeenum.MODE_MANUALSPRITE.value:
                self.mbpressed = 2
                # Save the starting point
                self.mousex1,self.mousey1 = (self.canvas.canvasx(event.x),self.canvas.canvasy(event.y))

                # Create a rectangle (empty for now)
                self.rect = self.canvas.create_rectangle(self.mousex1, self.mousey1, self.mousex1, self.mousey1, outline='red', width=2)

    def on_mouse3_drag(self,event):
        if self.mbpressed != 2:
            return
        # Update the rectangle as you drag
        match self.mode.get():
            case modeenum.MODE_FINDSPRITE.value | modeenum.MODE_MANUALSPRITE.value:
                cur_x, cur_y = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
                # Modify the coordinates of the rectangle
                self.canvas.coords(self.rect, self.mousex1, self.mousey1, cur_x, cur_y)
                self.canvas.update()


    def on_mouse3_release(self, event):
        if self.mbpressed != 2:
            return
        match self.mode.get():
            case modeenum.MODE_FINDSPRITE.value | modeenum.MODE_MANUALSPRITE.value:
                self.mbpressed = 0
                self.canvas.delete(self.rect)

                # Final rectangle coordinates in canvas space
                end_x = self.canvas.canvasx(event.x)
                end_y = self.canvas.canvasy(event.y)

                #make sure box is at least 1 pixel
                if end_x == self.mousex1:
                    end_x += 1
                if end_y == self.mousey1:
                    end_y += 1

                # Get selection box in canvas coords
                mousebbox_canvas = (
                    min(self.mousex1, end_x),
                    min(self.mousey1, end_y),
                    max(self.mousex1, end_x),
                    max(self.mousey1, end_y)
                )

                print(f"Canvas box coordinates: {mousebbox_canvas}")

                if not self.image:
                    print("No image loaded.")
                    return

                # Convert canvas coordinates to original image coordinates by scaling factor
                scale_factor = self.scale
                mousebbox_image = (
                    int(mousebbox_canvas[0] / scale_factor),
                    int(mousebbox_canvas[1] / scale_factor),
                    int(mousebbox_canvas[2] / scale_factor),
                    int(mousebbox_canvas[3] / scale_factor)
                )

                print(f"Canvas box coordinates: {mousebbox_canvas}")

                if not self.image:
                    print("No image loaded.")
                    return
                
                bbox = [mousebbox_image[0], mousebbox_image[1], mousebbox_image[2], mousebbox_image[3]]
                
                self.removeQueue.push(spriteBox(bbox,bbox,0))


    def start_pan(self, event):
        # Store initial position for dragging
        self.canvas.scan_mark(event.x, event.y)

    def do_pan(self, event):
        # Move the canvas to new position relative to mark
        self.canvas.scan_dragto(event.x, event.y, gain=1)


if __name__ == "__main__":
    import sys
    app = ImageViewer(*sys.argv[1:])
    app.mainloop()
