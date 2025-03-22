import os
import shutil
import platform
import psutil
import ctypes
from pathlib import Path
import time
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess

style_colors = {
    "bg": "#0d0d0d",
    "fg": "#00f7ff",
    "accent": "#f700ff",
    "button_bg": "#1a1a1a",
    "log_bg": "#1f1f1f",
    "ok": "#00ff00",
    "error": "#ff3c00",
    "info": "#39ff14"
}

class AnimatedLabel(tk.Label):
    def animate(self, text, delay=50):
        self.config(text="")
        def loop(i=0):
            if i <= len(text):
                self.config(text=text[:i])
                self.after(delay, loop, i+1)
        loop()

def try_delete(path):
    try:
        size = path.stat().st_size if path.exists() else 0
        if path.is_file() or path.is_symlink():
            path.unlink()
            return True, size
        elif path.is_dir():
            total_size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
            shutil.rmtree(path, ignore_errors=True)
            return True, total_size
    except Exception:
        return False, 0

def analyze_directory_size(directory):
    total_size = 0
    file_count = 0
    if directory.exists():
        for f in directory.rglob('*'):
            if f.is_file():
                file_count += 1
                total_size += f.stat().st_size
    return file_count, total_size

class CleanerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ULTIMATE CLEANER — CYBER MODE")
        self.root.geometry("800x680")
        self.root.configure(bg=style_colors["bg"])
        self.root.resizable(False, False)
        self.create_widgets()

    def create_widgets(self):
        ascii_banner = """

██████╗░██████╗░░█████╗░░█████╗░████████╗██╗░█████╗░  ██╗░░░██╗░░███╗░░██████╗░░░░██████╗░░░░██████╗░
██╔══██╗██╔══██╗██╔══██╗██╔══██╗╚══██╔══╝██║██╔══██╗  ██║░░░██║░████║░░╚════██╗░░░╚════██╗░░░╚════██╗
██████╔╝██████╔╝███████║██║░░╚═╝░░░██║░░░██║██║░░╚═╝  ╚██╗░██╔╝██╔██║░░░░███╔═╝░░░░░███╔═╝░░░░░███╔═╝
██╔═══╝░██╔══██╗██╔══██║██║░░██╗░░░██║░░░██║██║░░██╗  ░╚████╔╝░╚═╝██║░░██╔══╝░░░░░██╔══╝░░░░░██╔══╝░░
██║░░░░░██║░░██║██║░░██║╚█████╔╝░░░██║░░░██║╚█████╔╝  ░░╚██╔╝░░███████╗███████╗██╗███████╗██╗███████╗
╚═╝░░░░░╚═╝░░╚═╝╚═╝░░╚═╝░╚════╝░░░░╚═╝░░░╚═╝░╚════╝░  ░░░╚═╝░░░╚══════╝╚══════╝╚═╝╚══════╝╚═╝╚══════╝
        """
        self.banner = AnimatedLabel(self.root, font=("Courier New", 10), fg=style_colors["accent"], bg=style_colors["bg"])
        self.banner.pack(pady=5)
        self.banner.animate(ascii_banner, delay=3)

        frame = tk.Frame(self.root, bg=style_colors["bg"])
        frame.pack(pady=10)

        self.vars = [tk.BooleanVar(value=True) for _ in range(6)]
        labels = ["🧹 Temp Files", "🗑️ Recycle Bin", "🗂️ App Cache", "🎮 Shader Cache", "⚡ Gaming Boost", "🗒️ Logs Clean"]
        for idx, (label, var) in enumerate(zip(labels, self.vars)):
            row, col = divmod(idx, 2)
            chk = tk.Checkbutton(
                frame, text=label, variable=var,
                bg=style_colors["bg"], fg=style_colors["fg"],
                activebackground=style_colors["bg"], activeforeground=style_colors["accent"],
                selectcolor=style_colors["bg"], font=("Courier New", 10, "bold")
            )
            chk.grid(row=row, column=col, sticky='w', padx=10, pady=5)

        style = ttk.Style()
        style.theme_use('default')
        style.configure("TProgressbar", thickness=20, troughcolor=style_colors["log_bg"], background=style_colors["accent"])
        self.progress = ttk.Progressbar(self.root, length=750, mode='determinate')
        self.progress.pack(pady=10)

        self.status_label = AnimatedLabel(self.root, anchor='w', bg=style_colors["bg"], fg=style_colors["info"], font=("Courier New", 10, "bold"))
        self.status_label.pack()
        self.status_label.animate("[ACCESS GRANTED] SYSTEM READY", delay=10)

        self.log_text = scrolledtext.ScrolledText(self.root, width=95, height=15, bg=style_colors["log_bg"], fg=style_colors["fg"], font=("Courier New", 10))
        self.log_text.pack(pady=10)

        btn_frame = tk.Frame(self.root, bg=style_colors["bg"])
        btn_frame.pack(pady=5)

        self.analyze_button = tk.Button(
            btn_frame, text="📊 ANALYZE", command=self.analyze_cleaning,
            bg=style_colors["button_bg"], fg=style_colors["fg"],
            activebackground=style_colors["accent"], activeforeground=style_colors["bg"],
            font=("Courier New", 10, "bold"), relief="flat", padx=10, pady=3
        )
        self.analyze_button.grid(row=0, column=0, padx=5)

        self.start_button = tk.Button(
            btn_frame, text="🚀 EXECUTE CLEAN", command=self.start_cleaning,
            bg=style_colors["button_bg"], fg=style_colors["fg"],
            activebackground=style_colors["accent"], activeforeground=style_colors["bg"],
            font=("Courier New", 10, "bold"), relief="flat", padx=10, pady=3
        )
        self.start_button.grid(row=0, column=1, padx=5)

    def log_message(self, text):
        self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)

    def update_progress(self, step):
        self.progress['value'] += step
        self.root.update_idletasks()

    def analyze_cleaning(self):
        self.log_text.delete('1.0', tk.END)
        self.status_label.animate("[ANALYSIS] SCANNING...")
        total_files = 0
        total_size = 0

        paths = [
            Path(os.getenv("TEMP", "")),
            Path.home() / 'AppData/Local/Google/Chrome/User Data/Default/Cache'
        ]

        for path in paths:
            files, size = analyze_directory_size(path)
            total_files += files
            total_size += size
            self.log_message(f"[ANALYZE] {path}: FILES {files}, SIZE {round(size / (1024 * 1024), 2)} MB")

        self.log_message(f"[TOTAL] FILES: {total_files}, SIZE: {round(total_size / (1024 * 1024), 2)} MB")
        self.status_label.animate("[ANALYSIS COMPLETE]")

    def start_cleaning(self):
        self.log_text.delete('1.0', tk.END)
        self.progress['value'] = 0
        self.status_label.animate("[EXECUTION] CLEANING INITIATED...")

        self.log_message("[INFO] TERMINATING PROCESSES...")
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] and any(p in proc.info['name'].lower() for p in ['onedrive', 'teams']):
                    psutil.Process(proc.info['pid']).terminate()
                    self.log_message(f"[KILL] {proc.info['name']}")
            except Exception:
                continue
        self.update_progress(10)

        self.log_message("[INFO] CLEANING TEMP FILES...")
        temp_dir = Path(os.getenv("TEMP", ""))
        for item in temp_dir.iterdir():
            try_delete(item)
        self.update_progress(10)

        self.log_message("[INFO] EMPTYING RECYCLE BIN...")
        if platform.system() == "Windows":
            try:
                ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0x0007)
                self.log_message("[OK] RECYCLE BIN EMPTIED")
            except Exception:
                self.log_message("[ERROR] FAILED TO EMPTY RECYCLE BIN")
        self.update_progress(10)

        self.log_message("[INFO] CLEARING CHROME CACHE...")
        chrome_cache = Path.home() / 'AppData/Local/Google/Chrome/User Data/Default/Cache'
        if chrome_cache.exists():
            shutil.rmtree(chrome_cache, ignore_errors=True)
            self.log_message("[OK] CHROME CACHE CLEARED")
        self.update_progress(10)

        self.log_message("[INFO] DELETING SHADER CACHE...")
        shader_dirs = [
            Path.home() / 'AppData/Local/NVIDIA/DXCache',
            Path.home() / 'AppData/Local/NVIDIA/GLCache',
        ]
        for d in shader_dirs:
            if d.exists():
                shutil.rmtree(d, ignore_errors=True)
                self.log_message(f"[OK] {d} CLEARED")
        self.update_progress(10)

        self.log_message("[INFO] PURGING GAME LOGS...")
        game_logs = Path.home() / 'Documents/My Games'
        if game_logs.exists():
            for item in game_logs.iterdir():
                try_delete(item)
        self.update_progress(10)

        self.log_message("[INFO] CLEANING WINDOWS PREFETCH...")
        prefetch_dir = Path("C:/Windows/Prefetch")
        if prefetch_dir.exists():
            try:
                for item in prefetch_dir.iterdir():
                    try_delete(item)
            except PermissionError:
                self.log_message("[ERROR] ACCESS DENIED: PREFETCH")
        self.update_progress(10)

        self.log_message("[INFO] CLEANING WINDOWS LOGS...")
        logs_dir = Path("C:/Windows/Logs")
        if logs_dir.exists():
            for item in logs_dir.iterdir():
                try_delete(item)
        self.update_progress(10)

        self.log_message("[INFO] CLEANING STEAM CACHE...")
        steam_cache = Path("C:/Program Files (x86)/Steam/steamapps/downloading")
        if steam_cache.exists():
            for item in steam_cache.iterdir():
                try_delete(item)
        self.update_progress(10)

        self.status_label.animate("[CLEANING COMPLETE] SYSTEM OPTIMIZED")
        messagebox.showinfo("COMPLETE", "SYSTEM CLEANED SUCCESSFULLY")

if __name__ == "__main__":
    root = tk.Tk()
    app = CleanerApp(root)
    root.mainloop()
