import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json, os
from PIL import Image
import numpy as np
import cv2, sys, shutil
from pathlib import Path

class mod_image():
        def __init__(self, oldimage :Image, newimage :Image, location :Path):
            self.oldimage = oldimage
            self.newimage = newimage
            self.location = location
class SpriteLocatorApp:
    def __init__(self, master, *args):
        self.master = master
        
        master.title("Sprite Locator")
        self.data = None
        self.sprite_images = {}
        self.source_sheet = None
        self.new_sheet = None

        if len(args) >= 5:
            self.load_json(args[2])
            self.load_source_sheet(args[0])
            self.extract_sprites()
            self.load_new_sheet(args[1])
            self.locate_sprites(args[3],args[4])
        else:
            tk.Button(master, text="Load JSON Data", command=self.load_json).pack(fill="x")
            tk.Button(master, text="Load Source Sheet PNG", command=self.load_source_sheet).pack(fill="x")
            tk.Button(master, text="Extract & Save Cropped Sprites", command=lambda: self.extract_sprites()).pack(fill="x")
            tk.Button(master, text="Load New Sheet PNG", command=self.load_new_sheet).pack(fill="x")
            tk.Button(master, text="Locate Sprites on New Sheet", command=self.locate_sprites).pack(fill="x")

    # ------------------------
    # LOAD JSON
    # ------------------------
    def load_json(self, fpath=None):
        if fpath is None:
            fpath = filedialog.askopenfilename(
                title="Select JSON File",
                filetypes=[("JSON files", "*.json")]
            )
        if not fpath:
            return

        with open(fpath, "r") as f:
            self.data = json.load(f)

    # ------------------------
    # LOAD SOURCE SHEET
    # ------------------------
    def load_source_sheet(self,fpath=None):
        if fpath is None:
            fpath = filedialog.askopenfilename(
                title="Select PNG Sheet",
                filetypes=[("PNG", "*.png")]
            )
        if not fpath:
            return

        self.source_sheet = Image.open(fpath)

    # ------------------------
    # CROP SPRITES
    # ------------------------
    def extract_sprites(self):
        if self.data is None or self.source_sheet is None:
            messagebox.showerror("Error", "Load JSON and PNG first.")
            return

        for entry in self.data["DETAILS"]:
            ID = entry["ID"]
            box = entry["SearchBBOX"]   # [x1, y1, x2, y2]

            # crop directly
            crop = self.source_sheet.crop(tuple(box))

            # save_path = os.path.join(outdir, f"{ID}.png")
            # crop.save(save_path)

            self.sprite_images[ID] = crop


    # ------------------------
    # LOAD NEW SHEET
    # ------------------------
    def load_new_sheet(self,fpath=None):
        if fpath is None:
            fpath = filedialog.askopenfilename(
                title="Select NEW PNG Sheet",
                filetypes=[("PNG", "*.png")]
            )
        if not fpath:
            return
        self.new_image = Image.open(fpath)
        self.new_sheet = cv2.imread(fpath, cv2.IMREAD_COLOR)
        if self.new_sheet is None:
            messagebox.showerror("Error", "Failed to load PNG.")
            return

    # ------------------------
    # FAST IMAGE LOCATION
    # ------------------------

    def locate_sprites(self,out_json_path=None,modpath=None):
        if self.new_sheet is None:
            messagebox.showerror("Error", "Load new sheet first.")
            return
        if out_json_path is None:
            out_json_path = filedialog.asksaveasfilename(
                title="Save Output JSON",
                defaultextension=".json",
                filetypes=[("JSON", "*.json")]
            )
        if not out_json_path:
            return

        original = self.data
        updated_details = []
        # Create loading window
        self.master.withdraw()
        loading_window = tk.Toplevel()
        loading_window.title("Processing...")
        loading_window.grab_set()
        loading_window.resizable(False, False)

        # --- Center on screen ---
        loading_window.update_idletasks()
        w, h = 300, 120
        x = (loading_window.winfo_screenwidth() // 2) - (w // 2)
        y = (loading_window.winfo_screenheight() // 2) - (h // 2)
        loading_window.geometry(f"{w}x{h}+{x}+{y}")

        # --- Layout ---
        frame = ttk.Frame(loading_window, padding=20)
        frame.pack(fill="both", expand=True)

        label = ttk.Label(frame, text="Finding New Locations... (0%)")
        label.pack(pady=(0, 10))

        progress_var = tk.IntVar(value=0)
        progressbar = ttk.Progressbar(
            frame,
            orient="horizontal",
            length=250,
            mode="determinate",
            maximum=100,
            variable=progress_var
        )
        progressbar.pack()

        loading_window.update_idletasks()
        loading_window.update()

        # move icons on modded sheets
        update_mods : list[mod_image] = []
        if modpath is not None:
            for mod in Path(modpath).iterdir(): #mod directory
                for sheets in mod.iterdir(): #sheets in mod
                    olddirectory = sheets / "current"
                    oldsheetpath = olddirectory /f"{original['SHEETNAME']}.png"
                    if oldsheetpath.exists():
                        oldsheet = Image.open(oldsheetpath)
                        newsheet = self.new_image.copy()
                        update_mods.append(mod_image(oldsheet,newsheet,sheets))
                        

        for i,entry in enumerate(original["DETAILS"]):
            ID = entry["ID"]

            old_search = entry["SearchBBOX"]       # [sx1, sy1, sx2, sy2]
            old_expand = entry["ExpandedBBOX"]     # [ex1, ey1, ex2, ey2]

            # The reference template is the old search box crop
            sx1, sy1, sx2, sy2 = old_search
            size_w = sx2 - sx1
            size_h = sy2 - sy1

            print(f"Finding {ID}...")

            # Load stored sprite image
            template = cv2.cvtColor(np.array(self.sprite_images[ID]), cv2.COLOR_RGB2BGR)

            # Template match
            result = cv2.matchTemplate(self.new_sheet, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)

            if max_val < 0.8:
                print(f"Low confidence match for {ID} ({max_val:.2f})")
                continue

            # Found new top-left corner of search box
            new_sx1 = max_loc[0]
            new_sy1 = max_loc[1]
            new_sx2 = new_sx1 + size_w
            new_sy2 = new_sy1 + size_h

            new_search = [new_sx1, new_sy1, new_sx2, new_sy2]

            # BLACK OUT THE FOUND REGION SO IT WON'T MATCH AGAIN
            cv2.rectangle(self.new_sheet, (new_sx1, new_sy1), (new_sx2, new_sy2), (0, 0, 0), thickness=-1)

            # Calculate relative offsets for expanded box
            dx1 = old_expand[0] - old_search[0]
            dy1 = old_expand[1] - old_search[1]
            dx2 = old_expand[2] - old_search[2]
            dy2 = old_expand[3] - old_search[3]

            # Apply offsets to new search box
            new_expand = [
                new_sx1 + dx1,
                new_sy1 + dy1,
                new_sx2 + dx2,
                new_sy2 + dy2
            ]

            # Build updated entry
            updated_details.append({
                "Order": entry.get("Order", 0),
                "SaveID": entry.get("SaveID", 0),
                "ID": ID,
                "DESCRIPTION": entry.get("DESCRIPTION", ""),
                "Group": entry.get("Group", "DEFAULT"),
                "SearchBBOX": new_search,
                "ExpandedBBOX": new_expand
            })

            for mod in update_mods:
                crop = mod.oldimage.crop(old_expand)
                mod.newimage.paste(crop, (int(new_expand[0]), int(new_expand[1])))

            progress = int((i / len(original["DETAILS"])) * 100)
            label.config(text=f"Finding New Locations... ({progress}%)")
            progress_var.set(progress)
            loading_window.update_idletasks()
            loading_window.update()

        for mod in update_mods:
            new_path = mod.location / "current"
            old_path = None
            if new_path.exists():
                temp_path = mod.location / "old"
                index = 0
                old_path = temp_path
                while (old_path).exists():
                    index += 1
                    old_path = Path(str(temp_path) + "_" + str(index))
                os.rename(new_path, old_path)
            os.makedirs(new_path)
            mod.newimage.save(new_path / f"{original['SHEETNAME']}.png")

        loading_window.destroy()
        self.master.deiconify()

        # Build full JSON, replacing only DETAILS
        final_json = original.copy()
        final_json["DETAILS"] = updated_details

        with open(out_json_path, "w") as f:
            json.dump(final_json, f, indent=4)


# ------------------------
# RUN APP
# ------------------------
def main(args):
    root = tk.Tk()
    app = SpriteLocatorApp(root, *args)
    if not args:
        root.mainloop()
    else:
        root.destroy()

if __name__ == "__main__":
    args = sys.argv[1:]
    main(args)




