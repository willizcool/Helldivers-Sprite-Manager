import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
import os
import export_icons as ei
import subprocess, shutil
from pathlib import Path
import IconFinder as IconF

class SheetManagerGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("HD2 Sprite Sheet Manager")
        self.geometry("750x450")
        self.configure(bg="#e6e6e6")

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
        self.load_mod_sheet_list()


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
        frame = ttk.Frame(self, padding=10)
        frame.pack(fill="x")

        btn_sheet_frame = ttk.Frame(frame, borderwidth=2, relief="groove")
        btn_sheet_frame.pack(side="top", padx=10)

        # ACTION BUTTONS (start disabled)
        ttk.Label(btn_sheet_frame, text="Sheet Tools:", font=("Segoe UI", 12, "bold")).pack(side="left", padx=10)
        self.btn_select_update = ttk.Button(btn_sheet_frame, text="Import Updated Sheet", state="disabled", command=self.update_sheet)
        self.btn_add_icons = ttk.Button(btn_sheet_frame, text="Modify Icon Positions", state="disabled", command=self.modify_icon_positions)
        self.btn_export_sheet = ttk.Button(btn_sheet_frame, text="Export Sheet", state="disabled", command=lambda: self.export_sheet(export_icons=False))
        self.btn_export_icons = ttk.Button(btn_sheet_frame, text="Export Cropped Icons", state="disabled", command=lambda: self.export_sheet(export_icons=True))
        self.btn_sheet_list = [self.btn_select_update, self.btn_add_icons, self.btn_export_sheet, self.btn_export_icons]

        btn_mod_frame = ttk.Frame(frame, borderwidth=2, relief="groove")
        btn_mod_frame.pack(side="top", padx=10)

        ttk.Label(btn_mod_frame, text="Mod Tools:", font=("Segoe UI", 12, "bold")).pack(side="left", padx=10)
        self.btn_import_mod_sheet = ttk.Button(btn_mod_frame, text="Import New Mod Sheet", state="disabled", command=self.import_modded_sheet)
        self.btn_delete_mod_sheet = ttk.Button(btn_mod_frame, text="Delete Modded Sheet", state="disabled", command=self.delete_modded_sheet)
        self.btn_export_mod_sheet = ttk.Button(btn_mod_frame, text="Export Mod Sheets", state="disabled", command=lambda: self.export_modded_sheet(export_icons=False))
        self.btn_export_mod_icons = ttk.Button(btn_mod_frame, text="Export Cropped Mod Icons", state="disabled", command=lambda: self.export_modded_sheet(export_icons=True))
        self.btn_mod_list = [self.btn_import_mod_sheet, self.btn_delete_mod_sheet, self.btn_export_mod_sheet,self.btn_export_mod_icons]
        self.btn_mod_sheet_list = [self.btn_import_mod_sheet, self.btn_delete_mod_sheet]
        self.btn_mod_only_list = [self.btn_export_mod_sheet,self.btn_export_mod_icons]

        for btn in self.btn_sheet_list:
            btn.pack(side="left", padx=5)
        
        for btn in self.btn_mod_list:
            btn.pack(side="left", padx=5)

    # ------------------------------- MAIN CONTENT -------------------------------
    def create_content(self):
        main = ttk.Frame(self, padding=10)
        main.pack(fill="both", expand=True)

        # Allow full-window resize
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)
        main.columnconfigure(2, weight=1)
        main.rowconfigure(1, weight=1)

        # Left title
        ttk.Label(main, text="Original Sheet:", font=("Segoe UI", 12, "bold"))\
            .grid(row=0, column=0, sticky="w", padx=(0,10))

        # Right title
        ttk.Label(main, text="Mods", font=("Segoe UI", 12, "bold"))\
            .grid(row=0, column=1, sticky="w")

        # Left listbox
        self.sheet_listbox = tk.Listbox(main, exportselection=False)
        self.sheet_listbox.grid(row=1, column=0, sticky="nsew", padx=(0,10))

        # Right listbox
        self.moded_sheet_listbox = tk.Listbox(main, exportselection=False)
        self.moded_sheet_listbox.grid(row=1, column=1, sticky="nsew")

        # Left buttons
        self.import_sheet_button = ttk.Button(main, text="New Sheet", command=self.import_new_sheet)
        self.import_sheet_button.grid(row=2, column=0, sticky="ew", pady=(10,0))

        self.delete_sheet_button = ttk.Button(main, text="Delete Sheet", command=self.delete_sheet)
        self.delete_sheet_button.grid(row=3, column=0, sticky="ew", pady=(10,0))

        #Right button
        self.moded_sheets_button = ttk.Button(main, text="New Mod", command=self.create_new_mod_folder)
        self.moded_sheets_button.grid(row=2, column=1, sticky="ew", pady=(10,0))

        self.moded_sheets_del_button = ttk.Button(main, text="Delete Mod", command=self.delete_mod_folder)
        self.moded_sheets_del_button.grid(row=3, column=1, sticky="ew", pady=(10,0))

        # Preview window
        self.preview_window = ttk.Frame(main, borderwidth=2, relief="sunken")
        self.preview_window.grid(row=0, column=2, rowspan=2, sticky="nsew", padx=(10,0))

        self.preview_canvas = tk.Canvas(self.preview_window, width=400, height=400)
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
            self._resize_after_id = self.after(50, self.load_image_preview)

        
    # ------------------------------- LOAD SHEET FOLDERS -------------------------------
    def load_sheet_list(self):
        self.sheet_listbox.delete(0, tk.END)

        folders = [f.name for f in self.sheet_path.iterdir() if f.is_dir()]

        for folder in folders:
            self.sheet_listbox.insert(tk.END, folder)

    def load_mod_sheet_list(self):
        self.moded_sheet_listbox.delete(0, tk.END)

        modded_path = self.mod_path
        if not modded_path.exists():
            return

        mod_folders = [f.name for f in modded_path.iterdir() if f.is_dir()]

        for mod_folder in mod_folders:
            self.moded_sheet_listbox.insert(tk.END, mod_folder)
            has_sheet = (
                self.selected_sheet
                and (modded_path / mod_folder / self.selected_sheet).exists()
            )

            self.moded_sheet_listbox.itemconfig(
                tk.END,
                bg="green" if has_sheet else "grey"
            )

    # ------------------------------- EVENTS -------------------------------
    def on_sheet_select(self, event):
        if not self.sheet_listbox.curselection():
            self.selected_sheet = None
        else:
            index = self.sheet_listbox.curselection()[0]
            folder_name = self.sheet_listbox.get(index)
            if folder_name == self.selected_sheet:
                self.selected_sheet = None
            else:
                self.selected_sheet = folder_name

        # Enable buttons
        if self.selected_sheet:
            for btn in self.btn_sheet_list:
                btn.config(state="normal")
        else:
            for btn in self.btn_sheet_list:
                    btn.config(state="disabled")
            self.selected_sheet = None
            self.sheet_listbox.selection_clear(0, tk.END)
        self.load_image_preview()
        self.load_mod_sheet_list() #set colors
        self.on_mod_select(None)
    
    def on_mod_select(self, event):
        if not self.moded_sheet_listbox.curselection():
            self.selected_mod = None
        else:
            index = self.moded_sheet_listbox.curselection()[0]
            folder_name = self.moded_sheet_listbox.get(index)
            if folder_name == self.selected_mod:
                self.selected_mod = None
            else:
                self.selected_mod = folder_name

        if self.selected_mod:
            if self.selected_sheet:
                for btn in self.btn_mod_list:
                    btn.config(state="normal")
            else:
                for btn in self.btn_mod_only_list:
                    btn.config(state="normal")
                for btn in self.btn_mod_sheet_list:
                    btn.config(state="disabled")
        else:
            for btn in self.btn_mod_list:
                btn.config(state="disabled")
            self.moded_sheet_listbox.selection_clear(0, tk.END)
        # Enable buttons
        if self.selected_sheet and self.selected_mod:
            self.load_mod_preview()

    def load_image_preview(self):
        if not self.selected_sheet:
            self.preview_canvas.delete("all")
            return
        selected_sheet_path = self.sheet_path / self.selected_sheet / "original" / f"{self.selected_sheet}.png"
        if selected_sheet_path.exists():
            self.preview_image = Image.open(selected_sheet_path)
            self.preview_image = self.preview_image.resize((self.preview_canvas.winfo_width(), self.preview_canvas.winfo_height()), Image.NEAREST)
            self.preview_image = ImageTk.PhotoImage(self.preview_image)
            self.preview_canvas.create_image(0, 0, image=self.preview_image, anchor="nw")
            self.preview_canvas.config(scrollregion=self.preview_canvas.bbox("all"))

    def load_mod_preview(self):
        selected_mod_sheet_path = self.mod_path / self.selected_mod / self.selected_sheet/ "current" / f"{self.selected_sheet}.png"
        if selected_mod_sheet_path.exists():
            self.preview_image = Image.open(selected_mod_sheet_path)
            self.preview_image = self.preview_image.resize((self.preview_canvas.winfo_width(), self.preview_canvas.winfo_height()), Image.NEAREST)
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
        modded_path = self.mod_path / mod_name
        if not modded_path.exists():
            modded_path.mkdir(parents=True, exist_ok=True)
        else:
            messagebox.showerror("Error", "Mod already exists.")
            return None
        self.load_mod_sheet_list()
    
    def delete_mod_folder(self):
        if not self.selected_mod:
            return
        modded_path = self.mod_path / self.selected_mod
        if len(os.listdir(modded_path)) != 0:
            messagebox.showerror("Error", "Please Delete All Modded Sheets Before Deleting Mod.")
            return
        shutil.rmtree(modded_path)
        self.selected_mod = None
        self.load_mod_sheet_list()

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
        # self.launch_python_program(".\\IconFinder.py",oldsheet,newsheet,oldjson,newjson,self.mod_path)
        if self.selected_sheet in self.sheet_listbox.get(0, tk.END):
            index = self.sheet_listbox.get(0, tk.END).index(self.selected_sheet)
            self.sheet_listbox.selection_set(index)
        self.load_image_preview()


    def modify_icon_positions(self):
        self.launch_python_program(".\\SpriteFinder\\add_new_icons.py",f"{Path(self.sheet_path)}\\{self.selected_sheet}",self.selected_sheet)
        #self.launch_exe_program(".\\deps\\add_new_icons.exe",f"{Path(self.sheet_path)}\\{self.selected_sheet}",self.selected_sheet)

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
    app.mainloop()
