import numpy as np 
from Queue import Queue
import hashlib
import tkinter as tk
from tkinter import simpledialog
import time
import enum

class modeenum(enum.Enum):
    """enum for different modes of spriteBox"""
    MODE_FINDSPRITE = 0
    MODE_MOVE = 1
    MODE_DESCRIPTION = 2
    MODE_MANUALSPRITE = 3
class spriteBox:
    def __init__(self, bbox, expandedbbox, id, description=""):
        self.parent = None
        self.canvas :tk.Canvas = None
        self.imageid = None
        self.mode :tk.IntVar= None
        self.bbox = bbox
        self.expandedbbox = expandedbbox
        self.id = id
        self.mode = 0
        self.scale = None
        self.description = description
        self.drag_start = None
    

    def set_canvas(self, parent, canvas, imageid , mode, scale):
        self.parent = parent
        self.canvas = canvas
        self.mode = mode
        self.imageid = imageid
        self.scale = scale
        canvas.addtag_withtag(f"inner_{self.id}", imageid)
        canvas.tag_bind(f"inner_{self.id}", "<Button-1>", self.start_drag)
        canvas.tag_bind(f"inner_{self.id}", "<B1-Motion>", self.do_drag)
        canvas.tag_bind(f"inner_{self.id}", "<ButtonRelease-1>", self.end_drag)
    
    def start_drag(self, event):
        # save where drag began
        if self.mode.get() != modeenum.MODE_MOVE.value or self.canvas is None:
            return
        print("start drag")
        self.drag_start = (self.canvas.canvasx(event.x),self.canvas.canvasy(event.y))

    def do_drag(self, event):
        if self.drag_start is None or self.canvas is None or self.mode.get() != modeenum.MODE_MOVE.value:
            return

        drag_new = (self.canvas.canvasx(event.x),self.canvas.canvasy(event.y))
        # compute how much the mouse has moved
        dx = (drag_new[0] - self.drag_start[0]) / self.scale
        dy = (drag_new[1] - self.drag_start[1]) / self.scale

        # current coordinates
        x1, y1, x2, y2 = self.expandedbbox
        bx1, by1, bx2, by2 = self.bbox  # the constraint box

        has_bbox = True
        if x1 == bx1 and x2 == bx2 and y1 == by1 and y2 == by2:
            has_bbox = False

        new_x1 = x1 + dx
        new_y1 = y1 + dy
        new_x2 = x2 + dx
        new_y2 = y2 + dy

        # proposed new coordinates
        if has_bbox and (new_x1 > bx1 or new_x2 < bx2):
            dx = 0
        if has_bbox and (new_y1 > by1 or new_y2 < by2):
            dy = 0

        # apply movement
        self.expandedbbox = (x1 + dx, y1 + dy, x2 + dx, y2 + dy)
        if not has_bbox:
            self.bbox = self.expandedbbox
        self.canvas.moveto(self.imageid, self.expandedbbox[0]*self.scale, self.expandedbbox[1]*self.scale)

        print("do drag", dx, dy, self.scale)

        # update drag start for smooth continuous dragging
        self.drag_start = drag_new
    
    def end_drag(self, event):
        if self.drag_start is not None:
            self.drag_start = None
        if self.mode.get() == modeenum.MODE_DESCRIPTION.value:
            self.description = simpledialog.askstring("Name", "Rename Sprite", parent=self.canvas)
            if not self.description:
                self.description = ""
            self.canvas.delete(self.imageid)
            self.parent.display_box(self,True)


def collision_V_line(img,startx,starty,length,bgcolor,side,precision):
    for width in range(precision, 0 , -1):  
        for vline in range(length):
            if startx < 0 or starty + vline >= img.shape[0] or startx +((width-1)*side) >= img.shape[1] or startx +((width-1)*side) < 0:
                continue                  
            if not np.array_equal(img[starty+ vline, startx+ ((width-1)*side)], bgcolor):
                return width
    return -1

def collision_H_line(img,startx,starty,length,bgcolor,side,precision):
    for height in range(precision, 0 , -1): 
        for hline in range(length):   
            if startx < 0 or startx + hline>= img.shape[1] or starty +((height-1)*side) >= img.shape[0] or starty +((height-1)*side) < 0:     
                continue
            if not np.array_equal(img[starty+((height-1)*side), startx + hline], bgcolor):
                return height
    return -1

def find_sprite_routine(bgcolor, img, x, y, precision):
    xboxsize = 1 #start at 1 to handle vertical line
    yboxsize = 1
    while(yboxsize < 1000 and xboxsize < 1000 and x > 0 and y > 0 and x < img.shape[1] and y < img.shape[0]):
        yoff = 0 
        xoff = 0
        bump = False
        

        move = collision_H_line(img,x-(int(precision/2)),y,xboxsize+precision,bgcolor,-1,precision) #up
        if  move != -1:
            bump = True
            y -= move
            yboxsize -= max(move,1)

        move = collision_H_line(img,x-(int(precision/2)),y+yboxsize,xboxsize+precision,bgcolor,1,precision) #down
        if  move != -1:
            bump = True
            yboxsize += max(move,1)

        move = collision_V_line(img,x,y-(int(precision/2)),yboxsize+precision,bgcolor,-1,precision) #left
        if move != -1:
            bump = True
            x -= move
            xboxsize += max(move,1)

        move = collision_V_line(img,x+xboxsize,y-(int(precision/2)),yboxsize+precision,bgcolor,1,precision) #right
        if move != -1:
            bump = True
            xboxsize += max(move,1)

        if bump == False and yoff == 0 and xoff == 0:
            return [x,y,x+xboxsize,y+yboxsize]
    return None

def combine_bboxes(bbox1, bbox2):
    """
    Combine two bounding boxes into a single bounding box that encompasses both.
    """
    x1_1, y1_1, x2_1, y2_1 = bbox1
    x1_2, y1_2, x2_2, y2_2 = bbox2
    
    # Get the min x1, min y1, max x2, max y2 to encompass both boxes
    x1_combined = min(x1_1, x1_2)
    y1_combined = min(y1_1, y1_2)
    x2_combined = max(x2_1, x2_2)
    y2_combined = max(y2_1, y2_2)
    
    return [x1_combined, y1_combined, x2_combined, y2_combined]

def create_expanded_bbox(newbbox, min_width, min_height, max_box):
    x1, y1, x2, y2 = newbbox
    max_y, max_x, _ = max_box
    if min_width and x2 - x1 < min_width:
        x1 = max(x1 - (min_width - (x2 - x1)) // 2,0)
        x2 = min(x1 + min_width, max_x)
    if min_height and y2 - y1 < min_height:
        y1 = max(y1 - (min_height - (y2 - y1)) // 2,0)
        y2 = min(y1 + min_height, max_y)
    return [x1, y1, x2, y2]


def find_non_background_pixels(img, bbox, background_color, queue: Queue, min_bbox_width=None, min_bbox_height=None, manual=False):

    # Convert image to NumPy array
    img_array = np.array(img)
    
    # Get image dimensions
    startx = bbox[0]
    starty = bbox[1]
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    combined = None
    id = 0
    
    if manual:
        combined = bbox
    else:
        precision = 10 #start with a small precision and increase it to find larger boxes faster
        timeout = time.time() + 5 #timeout after 5 second if nothing is found
        for y in range(height):
            if time.time() > timeout:
                    break
            for x in range(width):
                if time.time() > timeout:
                    break
                if not np.array_equal(img_array[starty + y, startx + x], background_color):
                    newbbox = find_sprite_routine(background_color, img_array, startx + x, starty + y, precision)
                    if newbbox and newbbox[0]<newbbox[2] and newbbox[1]<newbbox[3]: #make sure its not a line
                        img_array[newbbox[1]:newbbox[3], newbbox[0]:newbbox[2]] = background_color #make sure you dont detect again
                        if combined:
                            combined = combine_bboxes(newbbox,combined)
                        else:
                            combined = newbbox
                        
    if combined:
        print(f"found box {combined}")
        crop = img.crop(combined)
        expanded_box = create_expanded_bbox(combined, min_bbox_width, min_bbox_height, img_array.shape)
        id = hashlib.md5(crop.tobytes()).hexdigest()
        queue.push(spriteBox(combined, expanded_box, id))