import tkinter as tk
from tkinter import ttk, messagebox
import sv_ttk
import requests
import zipfile
import os
import sys
import threading
import shutil
import subprocess
import time
import ctypes
from packaging import version
from PIL import Image, ImageTk

# --- CẤU HÌNH ---
# URL file JSON chứa thông tin version (Dùng chung file JSON với App chính)
GITHUB_JSON_URL = "https://raw.githubusercontent.com/hoangdangnhatkha/-WGZ-GameUpdater/refs/heads/main/CapNhatNightReignMod.json"

# Tên thư mục chứa App chính (Khi giải nén ra sẽ nằm trong folder này)
APP_DIR_NAME = "GameUpdater" 

# Tên file EXE chính cần chạy
MAIN_EXE_NAME = "GameUpdater.exe"

# Tên file lưu version hiện tại (nằm trong thư mục App)
VERSION_FILE = "version.txt"

def resource_path(relative_path):
    """Lấy đường dẫn tài nguyên (cho PyInstaller --onefile)"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def center_window(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    window.geometry(f'{width}x{height}+{x}+{y}')

class LauncherApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw() # Ẩn cửa sổ gốc

        # --- GIAO DIỆN SPLASH SCREEN ---
        self.splash = tk.Toplevel(self.root)
        self.splash.title("WGZ Launcher")
        self.splash.overrideredirect(True) # Mất viền
        center_window(self.splash, 400, 250)
        
        # Style
        sv_ttk.set_theme("dark")
        
        # Frame chính có viền
        main_frame = ttk.Frame(self.splash, style="Card.TFrame")
        main_frame.pack(fill="both", expand=True, padx=1, pady=1) # Tạo viền giả

        # Logo
        try:
            logo_path = resource_path("logo.png")
            if os.path.exists(logo_path):
                img = Image.open(logo_path).resize((80, 80), Image.Resampling.LANCZOS)
                self.logo_tk = ImageTk.PhotoImage(img)
                ttk.Label(main_frame, image=self.logo_tk).pack(pady=(20, 10))
        except: pass

        ttk.Label(main_frame, text="WGZ GAME UPDATER", font=("Segoe UI", 14, "bold")).pack()
        
        self.status_label = ttk.Label(main_frame, text="Đang kiểm tra phiên bản...", font=("Segoe UI", 10), foreground="#cccccc")
        self.status_label.pack(pady=(20, 5))

        self.progress = ttk.Progressbar(main_frame, orient="horizontal", length=300, mode="indeterminate")
        self.progress.pack(pady=10)
        self.progress.start(10)

        # Chạy logic trong luồng riêng
        threading.Thread(target=self.check_and_update, daemon=True).start()

    def update_status(self, text, is_error=False):
        color = "#ff5555" if is_error else "#cccccc"
        self.status_label.config(text=text, foreground=color)

    def get_local_version(self):
        """Đọc version từ file version.txt trong thư mục App"""
        ver_path = os.path.join(os.getcwd(), APP_DIR_NAME, VERSION_FILE)
        if os.path.exists(ver_path):
            try:
                with open(ver_path, 'r') as f:
                    return f.read().strip()
            except: return "0.0.0"
        return "0.0.0"

    def set_local_version(self, ver_str):
        """Ghi version mới vào file"""
        app_dir = os.path.join(os.getcwd(), APP_DIR_NAME)
        if not os.path.exists(app_dir):
            os.makedirs(app_dir)
        ver_path = os.path.join(app_dir, VERSION_FILE)
        with open(ver_path, 'w') as f:
            f.write(ver_str)

    def download_and_extract(self, url, target_version):
        """Tải ZIP và giải nén (có progress bar)"""
        try:
            self.update_status("Đang tải bản cập nhật mới...")
            self.progress.stop()
            self.progress.config(mode="determinate", value=0)

            response = requests.get(url, stream=True, timeout=15)
            total_size = int(response.headers.get('content-length', 0))
            
            temp_zip = os.path.join(os.environ['TEMP'], "wgz_update.zip")
            
            downloaded = 0
            with open(temp_zip, 'wb') as f:
                for data in response.iter_content(chunk_size=4096):
                    downloaded += len(data)
                    f.write(data)
                    if total_size > 0:
                        percent = int((downloaded / total_size) * 100)
                        self.progress['value'] = percent
                        self.root.update_idletasks() # Cập nhật UI

            self.update_status("Đang giải nén và cài đặt...")
            self.progress.config(mode="indeterminate")
            self.progress.start(10)

            # Xử lý giải nén
            extract_path = os.path.join(os.getcwd()) # Giải nén ngay tại thư mục gốc
            
            # Nếu thư mục App đã tồn tại, xóa nó đi để cài mới (tránh file rác)
            app_path = os.path.join(os.getcwd(), APP_DIR_NAME)
            if os.path.exists(app_path):
                try:
                    shutil.rmtree(app_path)
                except Exception as e:
                    self.update_status(f"Lỗi: Không thể xóa bản cũ. Hãy tắt App trước!", True)
                    time.sleep(3)
                    return False

            with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                zip_ref.extractall(extract_path)

            # Ghi version mới
            self.set_local_version(target_version)
            
            # Dọn dẹp
            try: os.remove(temp_zip)
            except: pass
            
            return True

        except Exception as e:
            self.update_status(f"Lỗi update: {e}", True)
            print(e)
            time.sleep(3)
            return False

    def check_and_update(self):
        try:
            # 1. Kiểm tra mạng & Lấy thông tin từ GitHub
            try:
                resp = requests.get(GITHUB_JSON_URL + f"?t={int(time.time())}", timeout=5)
                resp.raise_for_status()
                data = resp.json()
                
                # Cấu trúc JSON mong đợi:
                # { "updater": { "latest_version": "1.3.2", "download_url": "link_zip_onedir" } }
                updater_info = data.get("updater", {})
                remote_version = updater_info.get("latest_version", "0.0.0")
                download_url = updater_info.get("base_url")
                
            except Exception as e:
                print(f"Lỗi mạng: {e}")
                self.update_status("Không thể kết nối Server. Chạy bản Offline...", True)
                time.sleep(1)
                self.launch_main_app()
                return

            # 2. So sánh version
            local_version = self.get_local_version()
            print(f"Local: {local_version} | Remote: {remote_version}")

            if version.parse(remote_version) > version.parse(local_version) or not os.path.exists(os.path.join(os.getcwd(), APP_DIR_NAME, MAIN_EXE_NAME)):
                if not download_url:
                    self.update_status("Lỗi: Không tìm thấy link tải.", True)
                    time.sleep(2)
                else:
                    success = self.download_and_extract(download_url, remote_version)
                    if not success:
                        # Nếu update thất bại nhưng có app cũ, vẫn chạy app cũ
                        self.launch_main_app()
                        return
            else:
                self.update_status("Phiên bản đã mới nhất.")
                time.sleep(0.5)

            # 3. Chạy App chính
            self.launch_main_app()

        except Exception as e:
            self.update_status(f"Lỗi không xác định: {e}", True)
            time.sleep(3)
            self.root.destroy()

    def launch_main_app(self):
        exe_path = os.path.join(os.getcwd(), APP_DIR_NAME, MAIN_EXE_NAME)
        
        if os.path.exists(exe_path):
            self.update_status("Đang khởi động App chính...")
            time.sleep(0.5)
            try:
                # Chạy App chính và đóng Launcher
                subprocess.Popen([exe_path], cwd=os.path.dirname(exe_path))
                self.root.destroy()
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể khởi động file:\n{e}")
                self.root.destroy()
        else:
            self.update_status("Lỗi: Không tìm thấy file App chính!", True)
            messagebox.showerror("Lỗi", f"Không tìm thấy file: {exe_path}\nVui lòng kiểm tra lại đường dẫn hoặc internet.")
            self.root.destroy()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = LauncherApp()
    app.run()