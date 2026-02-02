import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
import os
import export_icons as ei
import subprocess, shutil
from pathlib import Path
import IconFinder as IconF
import add_new_icons as AddIcon
from tkinterdnd2 import TkinterDnD
import customtkinter as ctk
from CTkListbox import *
from tktooltip import ToolTip

version = "0.1.0"

fgroundbutton = ("RoyalBlue2", "RoyalBlue4")
hoverbutton = ("RoyalBlue3", "RoyalBlue3")

class SheetManagerGUI(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)

        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")


        self.title("HD2 Sprite Sheet Manager v" + version)
        self.geometry("1200x800")

        self.sheet_path = Path("./originals")
        self.mod_path = Path("./mods")
        self.sheet_path.mkdir(exist_ok=True)

        self.selected_sheet = None
        self.selected_mod = None

        # self.create_menu()
        self.create_top_buttons()
        self.create_content()
        self.create_bindings()

        self.load_sheet_list()
        self.load_mod_sheet_list(reset=True)


    # ------------------------------- MENU BAR -------------------------------
    def create_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # Room for more menus
        menubar.add_cascade(label="Tools")
        menubar.add_cascade(label="Help")

    # ------------------------------- TOP BUTTONS -------------------------------
    def create_top_buttons(self):
        frame = ctk.CTkFrame(self)
        frame.pack(fill="x", anchor="nw",expand=False)

        btn_card_frame = ctk.CTkFrame(frame)
        btn_card_frame.pack(side="left", padx=10, pady=5, fill="both", expand=True)

        # ACTION BUTTONS (start disabled)
        ctk.CTkLabel(btn_card_frame, text="Sheet Tools", font=("Segoe UI", 12, "bold")).pack(side="top", padx=10, expand=True)
        btn_frame = ctk.CTkFrame(btn_card_frame)
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.pack(side="top", padx=10, pady=5, fill="both", expand=True)

        self.btn_select_update = ctk.CTkButton(btn_frame, 
                                               text="Update Sheet and Mods",
                                               image = ImageTk.PhotoImage(Image.open("./icons/update.png").resize((20,20))),
                                               state="disabled", 
                                               command=self.update_sheet,
                                               fg_color=("purple1","purple4"),
                                               hover_color=("purple2","purple3"),
                                               border_color="black",
                                               border_width=2)
        ToolTip(self.btn_select_update, msg="Updates the selected sheet to a new image. Finds new icon positions on the new sheet and updates all currently managed mods to match.", delay=0.5)
        self.btn_add_icons = ctk.CTkButton(btn_frame, 
                                           text="Update Icon Positions",
                                           image = ImageTk.PhotoImage(Image.open("./icons/wrench.png").resize((20,20))),
                                           state="disabled", 
                                           command=self.modify_icon_positions,
                                           fg_color=fgroundbutton,
                                           hover_color=hoverbutton,
                                           border_color="black",
                                           border_width=2)
        ToolTip(self.btn_add_icons, msg="Capture and name icon positions on the selected sheet. Each icon selected here will be used when finding new positions during a sheet update.", delay=0.5)
        self.btn_sheet_list = [self.btn_select_update, self.btn_add_icons]

        btn_mod_card_frame = ctk.CTkFrame(frame)
        btn_mod_card_frame.pack(side="left", padx=10, pady=5, fill="both", expand=True, anchor="w")

        ctk.CTkLabel(btn_mod_card_frame, text="Mod Sheet Tools", font=("Segoe UI", 12, "bold")).pack(side="top", padx=10, expand=True)
        mod_btn_frame = ctk.CTkFrame(btn_mod_card_frame)
        mod_btn_frame.grid_columnconfigure(0, weight=1)
        mod_btn_frame.grid_columnconfigure(1, weight=1)
        mod_btn_frame.pack(side="top", padx=10, pady=5, fill="both", expand=True)

        self.btn_edit_mod_icons = ctk.CTkButton(mod_btn_frame, 
                                                text="Edit Modded Icons", 
                                                image = ImageTk.PhotoImage(Image.open("./icons/wrench.png").resize((20,20))),
                                                state="disabled", 
                                                command=self.modify_mod_icons,
                                                fg_color=fgroundbutton,
                                                hover_color=hoverbutton,
                                                border_color="black",
                                                border_width=2)
        ToolTip(self.btn_edit_mod_icons, msg="View selected sheet's modded icon positions and replace icons on the modded sheet.", delay=0.5)
        self.btn_import_mod_sheet = ctk.CTkButton(mod_btn_frame, 
                                                  text="Upload Existing Mod Sheet",
                                                  image = ImageTk.PhotoImage(Image.open("./icons/upload.png").resize((20,20))),
                                                  state="disabled", 
                                                  command=self.import_modded_sheet,
                                           fg_color=fgroundbutton,
                                           hover_color=hoverbutton,
                                           border_color="black",
                                           border_width=2)
        ToolTip(self.btn_import_mod_sheet, msg="Upload a modded sheet that has been created previously to the selected mod. The uploadedsheet should match the currently selected sheet's icon positions.", delay=0.5)
        self.btn_delete_mod_sheet = ctk.CTkButton(mod_btn_frame, 
                                                text="Delete Modded Sheet", 
                                                image = ImageTk.PhotoImage(Image.open("./icons/delete.png").resize((20,20))),
                                                state="disabled", 
                                                command=self.delete_modded_sheet,
                                                fg_color=fgroundbutton,
                                                hover_color=hoverbutton,
                                                border_color="black",
                                                border_width=2)
        ToolTip(self.btn_delete_mod_sheet, msg="Delete the currently selected mod sheet.", delay=0.5)
        
        self.btn_mod_sheet_list = [self.btn_import_mod_sheet, self.btn_delete_mod_sheet,self.btn_edit_mod_icons]
        self.btn_mod_only_list = []

        for i,btn in enumerate(self.btn_sheet_list):
            btn.grid(row=i, column=0, padx=5, pady=5, sticky="ew")
        
        for i,btn in enumerate(self.btn_mod_sheet_list):
            btn.grid(row=i//2, column=i%2, padx=5, pady=5, sticky="ew")

    # ------------------------------- MAIN CONTENT -------------------------------
    def create_content(self):
        main = ctk.CTkFrame(self)
        main.pack(fill="both", expand=True)

        listboxes = ctk.CTkFrame(main)
        listboxes.pack(fill="both", expand=False, side="left")
        xpad = 5
        ypad = 1

        # Allow full-window resize
        listboxes.columnconfigure(0, weight=0)
        listboxes.columnconfigure(1, weight=0)
        listboxes.rowconfigure(1, weight=1)
        listboxes.rowconfigure(2, weight=0)
        listboxes.rowconfigure(3, weight=0)
        listboxes.rowconfigure(4, weight=0)
        listboxes.rowconfigure(5, weight=0)

        # Left title
        ctk.CTkLabel(listboxes, text="Original Sheet", font=("Segoe UI", 12, "bold"))\
            .grid(row=0, column=0, sticky="nsew")

        # Right title
        ctk.CTkLabel(listboxes, text="Mods", font=("Segoe UI", 12, "bold"))\
            .grid(row=0, column=1, sticky="nsew")

        # Left listbox
        self.sheet_listbox = CTkListbox(listboxes)
        self.sheet_listbox.grid(row=1, column=0, sticky="nsew", padx=xpad, pady=ypad)

        # Right listbox
        self.moded_sheet_listbox = CTkListbox(listboxes)
        self.moded_sheet_listbox.grid(row=1, column=1, sticky="nsew", padx=xpad, pady=ypad)

        # Left buttons
        self.new_sheet_button = ctk.CTkButton(listboxes, 
                                                 text="New Sheet", 
                                                 image = ImageTk.PhotoImage(Image.open("./icons/new.png").resize((20,20))),
                                                 command=self.import_new_sheet,
                                           fg_color=fgroundbutton,
                                           hover_color=hoverbutton,
                                           border_color="black",
                                           border_width=2)
        ToolTip(self.new_sheet_button, msg="Import a new orignal sheet.", delay=0.5)
        self.new_sheet_button.grid(row=2, column=0, sticky="ew", padx=xpad, pady=ypad)
        self.delete_sheet_button = ctk.CTkButton(listboxes, 
                                            text="Delete Sheet", 
                                            image = ImageTk.PhotoImage(Image.open("./icons/delete.png").resize((20,20))),
                                            state="disabled",
                                            command=self.delete_sheet,
                                            fg_color=fgroundbutton,
                                            hover_color=hoverbutton,
                                            border_color="black",
                                            border_width=2)
        ToolTip(self.delete_sheet_button, msg="Delete the currently selected orignal sheet.", delay=0.5)
        self.btn_sheet_list.append(self.delete_sheet_button)
        self.delete_sheet_button.grid(row=3, column=0, sticky="ew", padx=xpad, pady=ypad)

        self.btn_export_sheet = ctk.CTkButton(listboxes, text="Export Sheet", state="disabled", command=lambda: self.export_sheet(export_icons=False),
                                           fg_color=fgroundbutton,
                                           hover_color=hoverbutton,
                                           border_color="black",
                                           border_width=2)
        ToolTip(self.btn_export_sheet, msg="Export the currently selected orignal sheet.", delay=0.5)
        self.btn_export_sheet.grid(row=4, column=0, sticky="ew", padx=xpad, pady=ypad)
        self.btn_sheet_list.append(self.btn_export_sheet)
        self.btn_export_icons = ctk.CTkButton(listboxes, text="Export Icons", state="disabled", command=lambda: self.export_sheet(export_icons=True),
                                           fg_color=fgroundbutton,
                                           hover_color=hoverbutton,
                                           border_color="black",
                                           border_width=2)
        ToolTip(self.btn_export_icons, msg="Export the each identified icon of the currently selected orignal sheet.", delay=0.5)

        self.btn_export_icons.grid(row=5, column=0, sticky="ew", padx=xpad, pady=ypad)
        self.btn_sheet_list.append(self.btn_export_icons)
        #Right button
        self.new_moded_sheets_button = ctk.CTkButton(listboxes, 
                                                 text="New Mod", 
                                                 image = ImageTk.PhotoImage(Image.open("./icons/plus.png").resize((20,20))),
                                                 command=self.create_new_mod_folder,
                                           fg_color=fgroundbutton,
                                           hover_color=hoverbutton,
                                           border_color="black",
                                           border_width=2)
        ToolTip(self.new_moded_sheets_button, msg="Create and name a new mod to be managed.", delay=0.5)
        self.new_moded_sheets_button.grid(row=2, column=1, sticky="ew", padx=xpad, pady=ypad)

        self.moded_sheets_del_button = ctk.CTkButton(listboxes, 
                                                    text="Delete Mod", 
                                                    image = ImageTk.PhotoImage(Image.open("./icons/delete.png").resize((20,20))),
                                                    command=self.delete_mod_folder,
                                                    state="disabled",
                                                    fg_color=fgroundbutton,
                                                    hover_color=hoverbutton,
                                                    border_color="black",
                                                    border_width=2)
        ToolTip(self.moded_sheets_del_button, msg="Delete the currently selected mod and all sheets.", delay=0.5)
        self.moded_sheets_del_button.grid(row=3, column=1, sticky="ew", padx=xpad, pady=ypad)
        self.btn_mod_only_list.append(self.moded_sheets_del_button)
        self.btn_export_mod_sheet = ctk.CTkButton(listboxes, text="Export Mod Sheets", state="disabled", command=lambda: self.export_modded_sheet(export_icons=False),
                                           fg_color=fgroundbutton,
                                           hover_color=hoverbutton,
                                           border_color="black",
                                           border_width=2)
        ToolTip(self.btn_export_mod_sheet, msg="Export all sheets in the currently selected mod.", delay=0.5)
        self.btn_export_mod_sheet.grid(row=4, column=1, sticky="ew", padx=xpad, pady=ypad)
        self.btn_mod_only_list.append(self.btn_export_mod_sheet)
        self.btn_export_mod_icons = ctk.CTkButton(listboxes, text="Export Mod Icons", state="disabled", command=lambda: self.export_modded_sheet(export_icons=True),
                                           fg_color=fgroundbutton,
                                           hover_color=hoverbutton,
                                           border_color="black",
                                           border_width=2)
        ToolTip(self.btn_export_mod_icons, msg="Export all icons of all sheets in the currently selected mod.", delay=0.5)
        self.btn_export_mod_icons.grid(row=5, column=1, sticky="ew", padx=xpad, pady=ypad)
        self.btn_mod_only_list.append(self.btn_export_mod_icons)
        # Preview window

        self.preview_canvas = ctk.CTkCanvas(main, width=400, height=400, 
                                            borderwidth=0,
                                            highlightthickness=0,
                                            bg=main.cget("bg_color")[0 if ctk.get_appearance_mode() == "Light" else 1])
        self.preview_canvas.pack(fill="both", expand=True)

    # ------------------------------- BINDINGS -------------------------------
    def create_bindings(self):
        self.sheet_listbox.bind("<<ListboxSelect>>", self.on_sheet_select)
        self.moded_sheet_listbox.bind("<<ListboxSelect>>", self.on_mod_select)
        self._resize_after_id = None
        self.bind("<Configure>", self.on_resize)
    def on_resize(self, event):
            # Only respond to this widget's resize
            if event.widget is not self:
                return
            # Cancel any pending resize job
            if self._resize_after_id:
                self.after_cancel(self._resize_after_id)
            # Run once resizing stops
            self._resize_after_id = self.after(50, self.load_mod_preview if self.selected_sheet and self.selected_mod else self.load_image_preview)

        
    # ------------------------------- LOAD SHEET FOLDERS -------------------------------
    def load_sheet_list(self):
        self.sheet_listbox.delete(0, tk.END)

        folders = [f.name for f in self.sheet_path.iterdir() if f.is_dir()]

        for folder in folders:
            self.sheet_listbox.insert(tk.END, folder)

    def load_mod_sheet_list(self,reset=False):
        if reset:
            self.moded_sheet_listbox.delete(0, tk.END)

        modded_path = self.mod_path
        if not modded_path.exists():
            return

        mod_folders = [f.name for f in modded_path.iterdir() if f.is_dir()]

        for i,mod_folder in enumerate(mod_folders):
            if reset:
                self.moded_sheet_listbox.insert(tk.END, mod_folder)
            has_sheet = (
                self.selected_sheet
                and (modded_path / mod_folder / self.selected_sheet).exists()
            )
            btn_key = list(self.moded_sheet_listbox.buttons.keys())[i]
            
            self.moded_sheet_listbox.buttons[btn_key].configure(bg_color=("SpringGreen3", "dark green") if has_sheet else ("grey", "dim grey"))
            self.moded_sheet_listbox.buttons[btn_key].configure(hover_color=("SpringGreen2", "SpringGreen4") if has_sheet else ("dim grey", "grey"))

    # ------------------------------- EVENTS -------------------------------
    def on_sheet_select(self, event):
        if self.sheet_listbox.curselection() is None:
            self.selected_sheet = None
        else:
            index = self.sheet_listbox.curselection()
            folder_name = self.sheet_listbox.get(index)
            if folder_name == self.selected_sheet:
                self.selected_sheet = None
            else:
                self.selected_sheet = folder_name

        # Enable buttons
        if self.selected_sheet is not None:
            for btn in self.btn_sheet_list:
                btn.configure(state="normal")
        else:
            for btn in self.btn_sheet_list:
                    btn.configure(state="disabled")
            self.selected_sheet = None
            if self.sheet_listbox.curselection() is not None:
                self.sheet_listbox.deactivate("all")
        self.load_image_preview()
        self.load_mod_sheet_list() #set colors
        self.on_mod_select(None)
    
    def on_mod_select(self, event):
        if self.moded_sheet_listbox.curselection() is None:
            self.selected_mod = None
        else:
            index = self.moded_sheet_listbox.curselection()
            folder_name = self.moded_sheet_listbox.get(index)
            if folder_name == self.selected_mod:
                self.selected_mod = None
            else:
                self.selected_mod = folder_name

        if self.selected_mod is not None:
            if self.selected_sheet:
                for btn in self.btn_mod_only_list:
                    btn.configure(state="normal")
                for btn in self.btn_mod_sheet_list:
                    btn.configure(state="normal")
            else:
                for btn in self.btn_mod_only_list:
                    btn.configure(state="normal")
                for btn in self.btn_mod_sheet_list:
                    btn.configure(state="disabled")
        else:
            for btn in self.btn_mod_only_list:
                btn.configure(state="disabled")
            for btn in self.btn_mod_sheet_list:
                btn.configure(state="disabled")
            if self.moded_sheet_listbox.curselection() is not None:
                self.moded_sheet_listbox.deactivate("all")
        # Enable buttons
        if self.selected_sheet and self.selected_mod:
            self.load_mod_preview()
    def find_scale(self, canvas, image):

        orig_width, orig_height = image.size
        scale = min(canvas.winfo_width() / orig_width, canvas.winfo_height() / orig_height)
        new_width = int(orig_width * scale)
        new_height = int(orig_height * scale)

        return new_width, new_height
    def load_image_preview(self):
        if not self.selected_sheet:
            self.preview_canvas.delete("all")
            return
        selected_sheet_path = self.sheet_path / self.selected_sheet / "original" / f"{self.selected_sheet}.png"
        if selected_sheet_path.exists():
            self.preview_image = Image.open(selected_sheet_path)
            new_width, new_height = self.find_scale(self.preview_canvas, self.preview_image)
            self.preview_image = self.preview_image.resize((new_width, new_height), Image.NEAREST)
            self.preview_image = ImageTk.PhotoImage(self.preview_image)
            self.preview_canvas.create_image(0, 0, image=self.preview_image, anchor="nw")
            self.preview_canvas.config(scrollregion=self.preview_canvas.bbox("all"))

    def load_mod_preview(self):
        selected_mod_sheet_path = self.mod_path / self.selected_mod / self.selected_sheet/ "current" / f"{self.selected_sheet}.png"
        if selected_mod_sheet_path.exists():
            self.preview_image = Image.open(selected_mod_sheet_path)
            new_width, new_height = self.find_scale(self.preview_canvas, self.preview_image)
            self.preview_image = self.preview_image.resize((new_width, new_height), Image.NEAREST)
            self.preview_image = ImageTk.PhotoImage(self.preview_image)
            self.preview_canvas.create_image(0, 0, image=self.preview_image, anchor="nw")
            self.preview_canvas.config(scrollregion=self.preview_canvas.bbox("all"))
        else:
            self.load_image_preview()

    def import_new_sheet(self ,new_folder_name=None):
        sheet = filedialog.askopenfilename(filetypes=[("PNG Files", "*.png")], title="Select new sheet")
        if not sheet:
            return None,None
        if not new_folder_name:
            new_folder_name = Path(sheet).stem
            if (Path(self.sheet_path) / new_folder_name).exists():
                messagebox.showerror("Error", "A sheet with the same name already exists.")
                return
        new_path = self.sheet_path / new_folder_name / "original"
        old_path = None
        if new_path.exists():
            temp_path = self.sheet_path / new_folder_name / "old"
            index = 1
            old_path = temp_path
            while (old_path).exists():
                index += 1
                old_path = Path(str(temp_path) + "_" + str(index))
            os.rename(new_path, old_path)
        os.makedirs(new_path)
        destfile = new_path / f"{new_folder_name}.png"
        shutil.copy2(sheet, destfile)
        self.load_sheet_list()
        return new_path,old_path

    def delete_sheet(self):
        if not self.selected_sheet:
            return
        if not messagebox.askokcancel("Delete", "Are you sure you want to delete this sheet? This cannot be undone. And will delete all related mod sheets."):
            return
        shutil.rmtree(self.sheet_path / self.selected_sheet)
        for mod_folder in self.mod_path.iterdir():
            if (mod_folder / self.selected_sheet).exists():
                shutil.rmtree(mod_folder / self.selected_sheet)
        self.load_sheet_list()
        self.on_sheet_select(None)
        
    
    def create_new_mod_folder(self):
        mod_name = simpledialog.askstring("Input", "Enter Mod Name", parent=self)
        if not mod_name:
            return
        modded_path = self.mod_path / mod_name
        if not modded_path.exists():
            modded_path.mkdir(parents=True, exist_ok=True)
        else:
            messagebox.showerror("Error", "Mod already exists.")
            return None
        self.load_mod_sheet_list(reset=True)
    
    def delete_mod_folder(self):
        if not self.selected_mod:
            return
        modded_path = self.mod_path / self.selected_mod
        if len(os.listdir(modded_path)) != 0:
            if not messagebox.askokcancel("Delete", "Modded Sheets Exist for this mod.\n Are you sure you want to delete all of them? This cannot be undone."):
                return
        shutil.rmtree(modded_path)
        self.selected_mod = None
        self.load_mod_sheet_list(reset=True)

    def import_modded_sheet(self):
        if not self.selected_mod or not self.selected_sheet:
            return
        modded_sheet = filedialog.askopenfilename(filetypes=[("PNG Files", "*.png")], title="Select modded sheet")

        if not modded_sheet:
            return

        dest_path = self.mod_path / self.selected_mod / self.selected_sheet / "current"
        if not dest_path.exists():
            os.makedirs(dest_path)
        else:
            if not messagebox.askokcancel("Overwrite", "Modded sheet already exists. Do you want to overwrite it?"):
                return
            shutil.rmtree(dest_path)
            os.makedirs(dest_path)
        destfile = dest_path / f"{self.selected_sheet}.png"
        loadedsheet = Image.open(modded_sheet) #in case not png
        loadedsheet.save(destfile, "png")
        self.load_mod_sheet_list()
    def delete_modded_sheet(self):
        if not self.selected_mod or not self.selected_sheet:
            return
        modded_path = self.mod_path / self.selected_mod / self.selected_sheet
        if not modded_path.exists():
            return
        if not messagebox.askokcancel("Delete", "Are you sure you want to delete this mod sheet? This cannot be undone."):
            return
        shutil.rmtree(modded_path)
        self.load_mod_sheet_list()

    def export_modded_sheet(self, export_icons=False):
        if not self.selected_mod:
            return
        
        modded_path = self.mod_path / self.selected_mod
        if not modded_path.exists():
            return
        export_path = filedialog.askdirectory(title="Select export folder")
        if not export_path:
            return
        export_path = Path(export_path)
        for mod_folder in modded_path.iterdir():
            current_folder = mod_folder / "current"
            for file in current_folder.iterdir():
                if not file.name.endswith(".png"):
                    continue
                if not export_icons:
                    if not (export_path / self.selected_mod).exists():
                        os.makedirs(export_path / self.selected_mod)
                    shutil.copy2(file, export_path / self.selected_mod/ file.name)
                else:
                    jsonpath = self.sheet_path / mod_folder.name / "original"/ f"{mod_folder.name}.json"
                    ei.crop_images(self.selected_mod, export_path, jsonpath, file)

    def export_sheet(self, export_icons=False):
        if not self.selected_sheet:
            return
        export_path = filedialog.askdirectory(title="Select export folder")
        export_path = Path(export_path)
        if not export_path:
            return
        newpath = export_path / self.selected_sheet
        sheetpath = self.sheet_path / self.selected_sheet / "original" / f"{self.selected_sheet}.png"
        if not newpath.exists():
            os.makedirs(newpath)
        if not export_icons:
            shutil.copy2(sheetpath, newpath)
        else:
            jsonpath = self.sheet_path / self.selected_sheet / "original"/ f"{self.selected_sheet}.json"
            ei.crop_images(self.selected_sheet, export_path, jsonpath, sheetpath)


    # ------------------------------- PROGRAM LAUNCHERS -------------------------------
    def update_sheet(self):
        newpath, oldpath = self.import_new_sheet(new_folder_name=self.selected_sheet)
        if not oldpath or not newpath:    
            return
        oldsheet = f"{oldpath}\\{self.selected_sheet}.png"
        newsheet = f"{newpath}\\{self.selected_sheet}.png"
        oldjson = f"{oldpath}\\{self.selected_sheet}.json"
        newjson = f"{newpath}\\{self.selected_sheet}.json"
        IconF.main([oldsheet,newsheet,oldjson,newjson,self.mod_path])
        if self.selected_sheet in self.sheet_listbox.get(0, tk.END):
            index = self.sheet_listbox.get(0, tk.END).index(self.selected_sheet)
            self.sheet_listbox.selection_set(index)
        self.load_image_preview()


    def modify_icon_positions(self):
        image_path = self.sheet_path / self.selected_sheet / "original" / f"{self.selected_sheet}.png"
        save_path = self.sheet_path / self.selected_sheet / "original"
        AddIcon.viewMode(image_path,save_path,self.selected_sheet)
        #self.launch_python_program(".\\SpriteFinder\\add_new_icons.py",f"{Path(self.sheet_path)}\\{self.selected_sheet}",self.selected_sheet)
        #self.launch_exe_program(".\\deps\\add_new_icons.exe",f"{Path(self.sheet_path)}\\{self.selected_sheet}",self.selected_sheet)

    def modify_mod_icons(self):
        image_path = self.sheet_path / self.selected_sheet / "original" / f"{self.selected_sheet}.png"
        save_path = self.sheet_path / self.selected_sheet / "original"
        mod_image_path = self.mod_path / self.selected_mod / self.selected_sheet / "current" / f"{self.selected_sheet}.png"
        if not mod_image_path.exists():
            mod_image_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(image_path, mod_image_path)
            self.load_mod_sheet_list()
        AddIcon.viewMode(image_path,save_path,self.selected_sheet,mod_image_path)
    def launch_python_program(self, script_name, *args):
        """Launches another Python script."""
        if not self.selected_sheet:
            return

        full_path = Path(script_name)
        if full_path.exists():
            subprocess.Popen(["python", full_path, *args])
        else:
            messagebox.showerror("Error", f"Script not found: {script_name}")

    def launch_exe_program(self, exe_name, *args):
        """Launches an executable."""
        if not self.selected_sheet:
            return

        full_path = Path(exe_name)
        if full_path.exists():
            subprocess.Popen([full_path, *args])
        else:
            messagebox.showerror("Error", f"Executable not found: {exe_name}")

# ------------------------------- RUN APP -------------------------------
if __name__ == "__main__":
    app = SheetManagerGUI()
    app.iconbitmap("./icons/UIManagerLogo.ico")
    app.mainloop()
