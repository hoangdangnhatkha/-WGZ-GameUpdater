import tkinter as tk
from tkinter import ttk, messagebox
import requests
import zipfile
import os
import sys
import threading
import shutil
import subprocess
import time
import re
import queue
from packaging import version
from PIL import Image, ImageTk
import gdown
import sv_ttk
import pywinstyles

# --- CẤU HÌNH ---
GITHUB_JSON_URL = "https://raw.githubusercontent.com/hoangdangnhatkha/-WGZ-GameUpdater/refs/heads/main/CapNhatNightReignMod.json"

# [QUAN TRỌNG] ĐƯỜNG DẪN CÀI ĐẶT MỚI: %LOCALAPPDATA%\WGZ_Game_Launcher
# Ví dụ: C:\Users\Admin\AppData\Local\WGZ_Game_Launcher
INSTALL_DIR = os.path.join(os.environ['LOCALAPPDATA'], "WGZ_Game_Launcher")

APP_DIR_NAME = "GameUpdater" 
MAIN_EXE_NAME = "GameUpdater.exe"
VERSION_FILE = "version.txt"

def resource_path(relative_path):
    """ Lấy đường dẫn tài nguyên tuyệt đối (Hỗ trợ PyInstaller + Nuitka + Dev) """
    try:
        # PyInstaller tạo ra biến này
        base_path = sys._MEIPASS
    except Exception:
        # Nuitka hoặc chạy thường (Dev)
        # Nuitka onefile sẽ giải nén vào temp và __file__ sẽ trỏ tới đó
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)

def center_window(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    window.geometry(f'{width}x{height}+{x}+{y}')

# --- LỚP BẮT TIẾN TRÌNH TỪ GDOWN ---
class QueueIO:
    def __init__(self, q):
        self.queue = q
    def write(self, text):
        percent_match = re.search(r'(\d+)\%', text)
        if percent_match:
            self.queue.put(("progress", int(percent_match.group(1))))
        elif text.strip() and "Retrieving" not in text and "Downloading" not in text:
            self.queue.put(("status", text.strip())) 
    def flush(self): pass

class LauncherApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw() 

        # --- GIAO DIỆN SPLASH SCREEN ---
        self.splash = tk.Toplevel(self.root)
        self.splash.title("WGZ Launcher")
        self.splash.overrideredirect(True) 
        
        width = 350
        height = 230 
        center_window(self.splash, width, height)

        try:
            sv_ttk.set_theme("dark")
        except: pass

        style = ttk.Style()
        style.configure("Splash.TFrame", background="#2b2b2b")
        style.configure("Splash.TLabel", background="#2b2b2b", foreground="white", font=("Segoe UI", 10))
        style.configure("Splash.Header.TLabel", background="#2b2b2b", foreground="white", font=("Segoe UI", 14, "bold"))

        self.main_frame = ttk.Frame(self.splash, style="Splash.TFrame", borderwidth=1, relief="solid")
        self.main_frame.pack(fill="both", expand=True)

        ttk.Label(self.main_frame, text="WGZ Game Updater", style="Splash.Header.TLabel").pack(pady=(20, 10))

        try:
            logo_path = resource_path("logo.png")
            if os.path.exists(logo_path):
                img = Image.open(logo_path).resize((50, 50), Image.Resampling.LANCZOS)
                self.logo_tk = ImageTk.PhotoImage(img)
                ttk.Label(self.main_frame, image=self.logo_tk, style="Splash.TLabel").pack(pady=5)
        except: pass

        self.status_label = ttk.Label(self.main_frame, text="Đang khởi động core system...", style="Splash.TLabel", wraplength=320, justify="center")
        self.status_label.pack(pady=(10, 5))

        self.progress = ttk.Progressbar(self.main_frame, style="Splash.Horizontal.TProgressbar", orient="horizontal", length=280, mode="determinate")
        self.progress.pack(pady=(5, 15))

        self.queue = queue.Queue()
        threading.Thread(target=self.run_logic_thread, daemon=True).start()
        self.process_queue()

    def process_queue(self):
        try:
            while True:
                msg_type, msg_value = self.queue.get_nowait()
                if msg_type == "status":
                    self.status_label.config(text=msg_value, foreground="white")
                elif msg_type == "error":
                    self.status_label.config(text=msg_value, foreground="#ff5555")
                elif msg_type == "progress":
                    self.progress["value"] = msg_value
                    self.status_label.config(text=f"Đang tải xuống... {msg_value}%")
                elif msg_type == "launch":
                    self.launch_main_app_logic()
                elif msg_type == "close":
                    self.root.destroy()
                    sys.exit(0)
        except queue.Empty:
            pass
        self.root.after(100, self.process_queue)

    def get_local_version(self):
        # Đọc version từ INSTALL_DIR thay vì os.getcwd()
        ver_path = os.path.join(INSTALL_DIR, APP_DIR_NAME, VERSION_FILE)
        if os.path.exists(ver_path):
            try:
                with open(ver_path, 'r') as f: return f.read().strip()
            except: return "0.0.0"
        return "0.0.0"

    def set_local_version(self, ver_str):
        # Ghi version vào INSTALL_DIR
        app_dir = os.path.join(INSTALL_DIR, APP_DIR_NAME)
        if not os.path.exists(app_dir): os.makedirs(app_dir, exist_ok=True)
        with open(os.path.join(app_dir, VERSION_FILE), 'w') as f: f.write(ver_str)

    def run_logic_thread(self):
        try:
            # 1. TẠO THƯ MỤC NẾU CHƯA CÓ
            if not os.path.exists(INSTALL_DIR):
                os.makedirs(INSTALL_DIR, exist_ok=True)

            # 2. CHECK VERSION
            self.queue.put(("status", "Đang kiểm tra phiên bản..."))
            self.queue.put(("progress", 10)) 
            
            try:
                resp = requests.get(GITHUB_JSON_URL + f"?t={int(time.time())}", timeout=5)
                resp.raise_for_status()
                data = resp.json()
                
                updater_info = data.get("updater", {})
                remote_version = updater_info.get("latest_version", "0.0.0")
                
                download_url = updater_info.get("base_url")
                if not download_url:
                    download_url = updater_info.get("download_url")
                
            except Exception as e:
                self.queue.put(("error", "Lỗi mạng. Thử chạy Offline..."))
                time.sleep(1)
                self.queue.put(("launch", None))
                return

            local_version = self.get_local_version()
            # Đường dẫn file exe trong thư mục INSTALL_DIR
            main_exe_path = os.path.join(INSTALL_DIR, APP_DIR_NAME, MAIN_EXE_NAME)

            # Logic cập nhật
            if version.parse(remote_version) > version.parse(local_version) or not os.path.exists(main_exe_path):
                if not download_url:
                    self.queue.put(("error", "Lỗi: Không tìm thấy link tải."))
                    time.sleep(3)
                    self.queue.put(("close", None))
                    return
                
                # --- TẢI BẰNG GDOWN ---
                self.queue.put(("status", "Đang kết nối Google Drive..."))
                
                temp_zip = os.path.join(os.environ['TEMP'], "wgz_base_update.zip")
                if os.path.exists(temp_zip):
                    try: os.remove(temp_zip)
                    except: pass

                original_stderr = sys.stderr
                sys.stderr = QueueIO(self.queue)
                
                try:
                    output = gdown.download(download_url, temp_zip, quiet=False, fuzzy=True, resume=True)
                except Exception as e:
                    sys.stderr = original_stderr
                    raise e
                
                sys.stderr = original_stderr

                if not os.path.exists(temp_zip):
                    raise Exception("Tải thất bại.")

                # --- GIẢI NÉN VÀO INSTALL_DIR ---
                self.queue.put(("status", "Đang giải nén dữ liệu..."))
                self.queue.put(("progress", 100))
                
                # Nơi giải nén là INSTALL_DIR (Ví dụ: AppData/Local/WGZ_Game_Launcher)
                extract_path = INSTALL_DIR
                app_path = os.path.join(INSTALL_DIR, APP_DIR_NAME)
                
                # Xóa folder cũ để cài mới sạch sẽ
                if os.path.exists(app_path):
                    try: shutil.rmtree(app_path)
                    except: pass 

                with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)

                self.set_local_version(remote_version)
                
                try: os.remove(temp_zip)
                except: pass
                
                self.queue.put(("status", "Cập nhật hoàn tất!"))
                time.sleep(0.5)

            self.queue.put(("launch", None))

        except Exception as e:
            sys.stderr = sys.__stderr__ 
            self.queue.put(("error", f"Lỗi: {e}"))
            time.sleep(5)
            self.queue.put(("close", None))

    def launch_main_app_logic(self):
        # Trỏ vào file exe trong INSTALL_DIR
        exe_path = os.path.join(INSTALL_DIR, APP_DIR_NAME, MAIN_EXE_NAME)
        
        if os.path.exists(exe_path):
            self.status_label.config(text="Đang tải thư viện...", foreground="white")
            self.root.update()
            time.sleep(0.5)
            try:
                # Chạy App chính từ thư mục của nó
                subprocess.Popen([exe_path], cwd=os.path.dirname(exe_path))
                self.root.destroy()
                sys.exit(0)
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể khởi động file:\n{e}")
                self.root.destroy()
        else:
            self.status_label.config(text="Lỗi: Không tìm thấy file App!", foreground="#ff5555")
            messagebox.showerror("Lỗi", f"Không tìm thấy file tại:\n{exe_path}")
            self.root.destroy()

if __name__ == "__main__":
    app = LauncherApp()
    app.root.mainloop()