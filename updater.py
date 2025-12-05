# Save this file as 'updater.py'
import sys
import os
import time
import subprocess
import shutil
import zipfile
import threading
import queue
import tkinter as tk
import tkinter.ttk as ttk
import re
import gdown

# --- CẤU HÌNH GIAO DIỆN (THEME) ---
import pywinstyles
import sv_ttk

def apply_theme_to_titlebar(root_window):
    current_theme = sv_ttk.get_theme()
    version = sys.getwindowsversion()
    if version.major >= 10:
        if version.build >= 22000:
            color = "#1c1c1c" if current_theme == "dark" else "#fafafa"
            try: pywinstyles.change_header_color(root_window, color)
            except: pass
        else:
            try: pywinstyles.apply_style(root_window, current_theme)
            except: pass

class QueueIO:
    def __init__(self, q):
        self.queue = q
    def write(self, text):
        progress_data = {}
        percent_match = re.search(r'(\d+)\%', text)
        if percent_match:
            progress_data["percent"] = int(percent_match.group(1))
        if "percent" in progress_data:
            self.queue.put(("progress", progress_data))
        elif text.strip() and "Retrieving" not in text:
            self.queue.put(("status", text.strip()))
    def flush(self): pass

class UpdaterApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Đang Cập Nhật Hệ Thống...")
        self.root.geometry("450x150")
        self.root.resizable(False, False)
        
        try:
            sv_ttk.set_theme("dark")
            apply_theme_to_titlebar(self.root)
        except: pass

        self.queue = queue.Queue()
        self.create_widgets()

        # --- NHẬN THAM SỐ TỪ APP CHÍNH ---
        # sys.argv[1]: Link tải (Google Drive URL)
        # sys.argv[2]: Đường dẫn thư mục cài đặt (Install Folder)
        # sys.argv[3]: Tên file EXE chính để mở lại sau khi xong
        
        if len(sys.argv) < 4:
            self.update_ui("error", "Lỗi: Thiếu tham số cập nhật.", 0)
            # Chế độ Debug (nếu chạy thủ công)
            # self.start_worker("LINK_TEST", r"C:\Path\To\Install", "Game.exe")
        else:
            dl_url = sys.argv[1]
            install_dir = sys.argv[2]
            exe_name = sys.argv[3]
            self.start_worker(dl_url, install_dir, exe_name)
            self.process_queue()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.status_label = ttk.Label(main_frame, text="Đang khởi tạo...", font=("Segoe UI", 10))
        self.status_label.pack(fill=tk.X, pady=(5, 10))
        
        self.progress_bar = ttk.Progressbar(main_frame, orient="horizontal", length=100, mode="determinate")
        self.progress_bar.pack(fill=tk.X, expand=True, ipady=4)

    def start_worker(self, url, path, exe_name):
        threading.Thread(target=update_logic, args=(self.queue, url, path, exe_name), daemon=True).start()

    def process_queue(self):
        try:
            msg_type, msg_value = self.queue.get_nowait()
            if msg_type == "status":
                self.status_label.config(text=msg_value)
            elif msg_type == "progress":
                self.progress_bar["value"] = msg_value.get("percent", 0)
                self.status_label.config(text=f"Đang tải... {msg_value.get('percent')}%")
            elif msg_type == "close":
                self.root.destroy()
                sys.exit(0)
            elif msg_type == "error":
                self.status_label.config(text=msg_value, foreground="red")
        except queue.Empty:
            pass
        self.root.after(100, self.process_queue)

    def update_ui(self, type_name, text, val):
        self.status_label.config(text=text)

def update_logic(queue_instance, download_url, install_folder, main_exe_name):
    original_stderr = sys.stderr
    temp_zip_path = os.path.join(os.environ['TEMP'], "update_package.zip")
    
    try:
        queue_instance.put(("status", "Đang chờ ứng dụng chính đóng hẳn..."))
        time.sleep(2) # Chờ app chính tắt

        # 1. TẢI FILE ZIP
        queue_instance.put(("status", "Đang tải bản cập nhật (ZIP)..."))
        sys.stderr = QueueIO(queue_instance) # Bắt log gdown
        
        if os.path.exists(temp_zip_path): os.remove(temp_zip_path)
        gdown.download(download_url, temp_zip_path, quiet=False, fuzzy=True)
        
        sys.stderr = original_stderr # Trả lại stderr

        if not os.path.exists(temp_zip_path):
            raise Exception("Tải thất bại (Không thấy file).")

        # 2. XÓA THƯ MỤC NỘI BỘ CŨ (_internal)
        # Đây là nơi chứa thư viện Python nặng nề, cần xóa sạch để tránh xung đột
        internal_dir = os.path.join(install_folder, "_internal")
        if os.path.exists(internal_dir):
            queue_instance.put(("status", "Đang dọn dẹp phiên bản cũ..."))
            try:
                shutil.rmtree(internal_dir)
            except Exception as e:
                print(f"Không xóa được _internal: {e}") 
                # Vẫn tiếp tục, unzip sẽ ghi đè

        # 3. GIẢI NÉN
        queue_instance.put(("status", "Đang giải nén phiên bản mới..."))
        queue_instance.put(("progress", {"percent": 50})) # Fake progress cho giải nén
        
        with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
            zip_ref.extractall(install_folder)

        queue_instance.put(("progress", {"percent": 100}))
        queue_instance.put(("status", "Cập nhật hoàn tất!"))
        time.sleep(1)

        # 4. MỞ LẠI APP CHÍNH
        exe_path = os.path.join(install_folder, main_exe_name)
        if os.path.exists(exe_path):
            subprocess.Popen([exe_path])
        else:
            queue_instance.put(("error", f"Không tìm thấy file: {main_exe_name}"))
            time.sleep(3)

        # 5. DỌN DẸP
        try: os.remove(temp_zip_path)
        except: pass
        
        queue_instance.put(("close", None))

    except Exception as e:
        sys.stderr = original_stderr
        queue_instance.put(("error", f"LỖI: {e}"))
        time.sleep(5) # Để người dùng kịp đọc lỗi

if __name__ == "__main__":
    app = UpdaterApp()
    app.root.mainloop()