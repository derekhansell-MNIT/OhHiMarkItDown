import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from main import convert_all
import threading, time, requests
import os
from utils import get_conversion_mode

MAX_FILENAME_LENGTH = 50

def on_close():
    app.source_var.set("")
    app.dest_var.set("")
    root.destroy()

class OhHiMarkItDownApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OhHiMarkItDown")
        self.root.geometry("600x360")
        self.root.configure(bg="#1e1e1e")
        self.style = ttk.Style()
        self.dark_mode = True
        self.stop_requested = False
        self.conversion_mode = get_conversion_mode()
        self.configure_style()

        self.source_var = tk.StringVar()
        self.dest_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready")
        self.count_var = tk.StringVar(value="")
        self.time_var = tk.StringVar(value="")
        self.mode_var = tk.StringVar(value=f"Marker PDF Conversion mode: {self.conversion_mode}")

        self.build_ui()
        self.load_previous_paths()

    def configure_style(self):
        self.style.theme_use("clam")
        self.style.configure("Container.TFrame", background="#1e1e1e")
        self.style.configure("TLabel", foreground="white", background="#1e1e1e")
        self.style.configure("TButton", foreground="white", background="#333", padding=6)
        self.style.configure("TEntry", fieldbackground="#2e2e2e", foreground="white")

        mode_color = "#4caf50" if self.conversion_mode == "GPU" else "#ff9800"
        self.style.configure("Mode.TLabel", foreground=mode_color, background="#1e1e1e")

    def build_ui(self):
        self.container = ttk.Frame(self.root, style="Container.TFrame")
        self.container.pack(expand=True, fill="both", anchor="center", padx=20, pady=10)
        self.container.columnconfigure(1, weight=1)

        ttk.Label(self.container, text="Source Folder:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        ttk.Entry(self.container, textvariable=self.source_var).grid(row=0, column=1, sticky="ew", padx=(0, 10))
        ttk.Button(self.container, text="Browse", command=self.select_source).grid(row=0, column=2, padx=(10, 10))

        ttk.Label(self.container, text="Destination Folder:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        ttk.Entry(self.container, textvariable=self.dest_var).grid(row=1, column=1, sticky="ew", padx=(0, 10))
        ttk.Button(self.container, text="Browse", command=self.select_dest).grid(row=1, column=2, padx=(10, 10))

        self.run_btn = ttk.Button(self.container, text="Run Conversion", command=self.run_conversion)
        self.run_btn.grid(row=2, column=1, pady=(10, 2), sticky="ew")

        self.stop_btn = ttk.Button(self.container, text="Stop Conversion", command=self.stop_conversion)
        self.stop_btn.grid(row=3, column=1, pady=(2, 10), sticky="ew")
        self.stop_btn.state(["disabled"])

        ttk.Label(self.container, textvariable=self.status_var, anchor="center", justify="center").grid(row=4, column=1, sticky="ew", pady=(5, 2))
        ttk.Label(self.container, textvariable=self.count_var, anchor="center", justify="center").grid(row=5, column=1, sticky="ew", pady=2)
        ttk.Label(self.container, textvariable=self.time_var, anchor="center", justify="center").grid(row=6, column=1, sticky="ew", pady=2)

        ttk.Button(self.container, text="Toggle Dark Mode", command=self.toggle_theme).grid(row=7, column=1, pady=5)
        ttk.Button(self.container, text="Open Logs Folder", command=self.open_logs_folder).grid(row=8, column=1, pady=5)

        ttk.Label(self.container, textvariable=self.mode_var, style="Mode.TLabel", anchor="center", justify="center").grid(row=9, column=1, sticky="ew", pady=(5, 2))

    def select_source(self):
        folder = filedialog.askdirectory()
        if folder:
            self.source_var.set(folder)

    def select_dest(self):
        folder = filedialog.askdirectory()
        if folder:
            self.dest_var.set(folder)

    def run_conversion(self):
        self.stop_requested = False
        thread = threading.Thread(target=self.convert_thread)
        thread.start()

    def stop_conversion(self):
        self.stop_requested = True
        self.status_var.set("Stopping...")
        self.stop_btn.state(["disabled"])

    def convert_thread(self):
        self.status_var.set("Starting conversion...")
        self.run_btn.state(["disabled"])
        self.stop_btn.state(["!disabled"])

        if not self.source_var.get() or not self.dest_var.get():
            self.status_var.set("Please select both source and destination folders.")
            self.run_btn.state(["!disabled"])
            self.stop_btn.state(["disabled"])
            return

        start_time = time.time()
        source = Path(self.source_var.get())
        dest = Path(self.dest_var.get())

        def status_callback():
            class Callback:
                def set(inner_self, msg):
                    filename = self.abbreviate_filename(msg)
                    self.status_var.set(f"Converting: {filename}")
                def should_stop(inner_self):
                    return self.stop_requested
            return Callback()

        count = convert_all(source, dest, status_callback())
        elapsed = int(time.time() - start_time)

        if self.stop_requested:
            self.status_var.set("Conversion stopped.")
        else:
            self.status_var.set("Done")
            self.count_var.set(f"{count} files converted")
            self.time_var.set(f"Time elapsed: {elapsed}s")

        self.save_paths()

        self.run_btn.state(["!disabled"])
        self.stop_btn.state(["disabled"])

    def abbreviate_filename(self, name):
        return name if len(name) <= MAX_FILENAME_LENGTH else name[:MAX_FILENAME_LENGTH - 3] + "..."

    def open_logs_folder(self):
        logs_path = os.path.abspath("logs")
        os.makedirs(logs_path, exist_ok=True)
        os.startfile(logs_path)

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode

        bg = "#1e1e1e" if self.dark_mode else "#f0f0f0"
        fg = "white" if self.dark_mode else "black"
        entry_bg = "#2e2e2e" if self.dark_mode else "#ffffff"
        button_bg = "#333" if self.dark_mode else "#dddddd"

        self.root.configure(bg=bg)
        self.style.configure("Container.TFrame", background=bg)
        self.style.configure("TLabel", background=bg, foreground=fg)
        self.style.configure("TButton", background=button_bg, foreground=fg)
        self.style.configure("TEntry", fieldbackground=entry_bg, foreground=fg)
        self.style.configure("Mode.TLabel", background=bg)

    def load_previous_paths(self):
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        paths_file = logs_dir / "last_paths.txt"
        try:
            with open(paths_file, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()
                if len(lines) >= 2:
                    self.source_var.set(lines[0])
                    self.dest_var.set(lines[1])
        except FileNotFoundError:
            pass

    def save_paths(self):
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        paths_file = logs_dir / "last_paths.txt"
        with open(paths_file, "w", encoding="utf-8") as f:
            f.write(self.source_var.get() + "\n")
            f.write(self.dest_var.get() + "\n")

if __name__ == "__main__":
    root = tk.Tk()
    print("[*] Launching OhHiMarkItDown...")
    app = OhHiMarkItDownApp(root)
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()
