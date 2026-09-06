import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json, os
from PIL import Image
import numpy as np
import cv2, sys, shutil
from pathlib import Path
import customtkinter as ctk

class mod_image():
        def __init__(self, oldimage :Image, newimage :Image, location :Path):
            self.oldimage = oldimage
            self.newimage = newimage
            self.location = location
class SpriteLocatorApp:
    def __init__(self, oldsheet,newsheet,oldjson,newjson,mod_path):
        self.data = None
        self.sprite_images = {}
        self.source_sheet = None
        self.new_sheet = None

        self.load_json(oldjson)
        self.load_source_sheet(oldsheet)
        self.extract_sprites()
        self.load_new_sheet(newsheet)
        self.locate_sprites(newjson,mod_path)
    

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
        loading_window = ctk.CTkToplevel()
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
        frame = ctk.CTkFrame(loading_window)
        frame.pack(fill="both", expand=True)

        label = ctk.CTkLabel(frame, text="Finding New Locations... (0%)")
        label.pack(pady=(0, 10))

        progressbar = ctk.CTkProgressBar(
            frame,
            orientation="horizontal",
            mode="determinate",
        )
        progressbar.set(0)
        progressbar.pack()

        loading_window.update_idletasks()
        loading_window.update()

        # move icons on modded sheets
        update_mods : list[mod_image] = []
        if modpath is not None and modpath.exists():
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

            progress = (i / len(original["DETAILS"]))
            label.configure(text=f"Finding New Locations... ({int(progress * 100)}%)")
            progressbar.set(progress)
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

        # Build full JSON, replacing only DETAILS
        final_json = original.copy()
        final_json["DETAILS"] = updated_details

        with open(out_json_path, "w") as f:
            json.dump(final_json, f, indent=4)


def migrate_mod_sheet_with_base(old_json_path, new_json_path, mod_image_path, new_base_sheet_path, out_image_path):
    """
    Loads an old modded sheet, extracts modded icons using the old JSON's ExpandedBBOX,
    and pastes them onto a copy of the NEW original base sheet using the updated JSON's positions.
    """
    new_combined_sheet = old_mod_sheet = Image.open(mod_image_path)
    if old_json_path is not new_json_path:
        # 1. Load both JSON layouts
        with open(old_json_path, "r") as f:
            old_data = json.load(f)
            
        with open(new_json_path, "r") as f:
            new_data = json.load(f)
        
        # We copy the new original base sheet so we don't overwrite the original source asset
        new_combined_sheet = Image.open(new_base_sheet_path).copy()

        # 3. Map the new positions by ID for O(1) matching efficiency
        new_positions = {entry["ID"]: entry["ExpandedBBOX"] for entry in new_data["DETAILS"]}

        print("Migrating modded icons onto the new base sheet layout...")
        
        # 4. Extract from old mod positions and paste onto the new base canvas
        for entry in old_data["DETAILS"]:
            sprite_id = entry["ID"]
            old_bbox = entry["ExpandedBBOX"]

            # Only process if this icon still exists in the new version setup
            if sprite_id in new_positions:
                new_bbox = new_positions[sprite_id]

                try:
                    # Crop the modified icon from your old custom sheet
                    icon_crop = old_mod_sheet.crop(tuple(old_bbox))

                    # Paste it onto the new base sheet at its updated coordinates
                    # Converting to RGBA ensures alpha transparent masks are preserved properly
                    paste_x = int(new_bbox[0])
                    paste_y = int(new_bbox[1])
                    
                    new_combined_sheet.paste(icon_crop, (paste_x, paste_y), icon_crop.convert("RGBA"))
                except Exception as e:
                    print(f"Skipping {sprite_id}: Error migrating asset ({e})")
            else:
                print(f"Notice: Sprite ID '{sprite_id}' is not in the new layout. Skipping.")

    new_combined_sheet.save(out_image_path)
    print(f"Successfully updated mod sheet! Saved to: {out_image_path}")


def main(oldsheet,newsheet,oldjson,newjson,mod_path):
    app = SpriteLocatorApp(oldsheet,newsheet,oldjson,newjson,mod_path)




