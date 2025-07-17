# app.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from main import convert_all
import threading
import time
import requests

def check_markitdown_version(local_version_file="markitdown_version.txt"):
    try:
        response = requests.get("https://api.github.com/repos/microsoft/markitdown/releases/latest", timeout=5)
        latest = response.json().get("tag_name", "").strip()
        with open(local_version_file, "r", encoding="utf-8") as f:
            local = f.read().strip()
        if local != latest:
            print(f"[!] MarkItDown version mismatch: local={local}, latest={latest}")
            return False
        return True
    except Exception as e:
        print(f"Version check failed: {e}")
        return True  # Fail silently to avoid blocking

class OhHiMarkItDownApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OhHiMarkItDown")
        self.root.geometry("600x300")
        self.root.configure(bg="#1e1e1e")
        self.style = ttk.Style()
        self.dark_mode = True
        self.configure_style()

        self.source_var = tk.StringVar()
        self.dest_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready")
        self.count_var = tk.StringVar(value="0 files converted")
        self.time_var = tk.StringVar(value="Elapsed: 0s")

        self.build_ui()

    def configure_style(self):
        self.style.theme_use("clam")
        self.style.configure("TLabel", foreground="white", background="#1e1e1e")
        self.style.configure("TButton", foreground="white", background="#333", padding=6)
        self.style.configure("TEntry", fieldbackground="#2e2e2e", foreground="white")

    def build_ui(self):
        ttk.Label(self.root, text="Source Folder:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        ttk.Entry(self.root, textvariable=self.source_var, width=50).grid(row=0, column=1)
        ttk.Button(self.root, text="Browse", command=self.select_source).grid(row=0, column=2)

        ttk.Label(self.root, text="Destination Folder:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        ttk.Entry(self.root, textvariable=self.dest_var, width=50).grid(row=1, column=1)
        ttk.Button(self.root, text="Browse", command=self.select_dest).grid(row=1, column=2)

        ttk.Button(self.root, text="Run Conversion", command=self.run_conversion).grid(row=2, column=1, pady=20)

        ttk.Label(self.root, textvariable=self.status_var).grid(row=3, column=1)
        ttk.Label(self.root, textvariable=self.count_var).grid(row=4, column=1)
        ttk.Label(self.root, textvariable=self.time_var).grid(row=5, column=1)

        ttk.Button(self.root, text="Toggle Dark Mode", command=self.toggle_theme).grid(row=6, column=1, pady=10)

    def select_source(self):
        folder = filedialog.askdirectory()
        if folder:
            self.source_var.set(folder)

    def select_dest(self):
        folder = filedialog.askdirectory()
        if folder:
            self.dest_var.set(folder)

    def run_conversion(self):
        thread = threading.Thread(target=self.convert_thread)
        thread.start()

    def convert_thread(self):
        start_time = time.time()
        source = Path(self.source_var.get())
        dest = Path(self.dest_var.get())
        self.status_var.set("Converting...")
        count = convert_all(source, dest, self.status_var)
        elapsed = int(time.time() - start_time)
        self.count_var.set(f"{count} files converted")
        self.time_var.set(f"Elapsed: {elapsed}s")
        self.status_var.set("Done")

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        bg = "#1e1e1e" if self.dark_mode else "#f0f0f0"
        fg = "white" if self.dark_mode else "black"
        self.root.configure(bg=bg)
        self.style.configure("TLabel", background=bg, foreground=fg)
        self.style.configure("TButton", background="#333" if self.dark_mode else "#ddd", foreground=fg)
        self.style.configure("TEntry", fieldbackground="#2e2e2e" if self.dark_mode else "#fff", foreground=fg)

if __name__ == "__main__":
    root = tk.Tk()

    # Show version warning before launching the app
    if not check_markitdown_version():
        messagebox.showwarning("Version Mismatch", "Your MarkItDown version is outdated. Consider updating.")

    app = OhHiMarkItDownApp(root)
    root.mainloop()
