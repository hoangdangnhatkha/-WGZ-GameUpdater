# Đây là file updater.py (Phiên bản UI Tkinter + Theme sv_ttk + gdown)
import sys
import os
import time
import subprocess
import shutil
import gdown       # <-- Dùng gdown
import re          # <-- Thêm re
import threading
import queue
import tkinter as tk
import tkinter.ttk as ttk
import pywinstyles
import sv_ttk

# Build bằng: 
# pyinstaller --onefile --windowed --noconsole --add-data "C:\Path\To\sv_ttk:sv_ttk" --add-data "C:\Path\To\pywinstyles:pywinstyles" --hidden-import=gdown updater.py

# --- HÀM ÁP DỤNG THEME CHO TITLE BAR ---
def apply_theme_to_titlebar(root_window):
    current_theme = sv_ttk.get_theme()
    version = sys.getwindowsversion()
    if version.major >= 10:
        if version.build >= 22000:
            color = "#1c1c1c" if current_theme == "dark" else "#fafafa"
            try: pywinstyles.change_header_color(root_window, color)
            except Exception as e: print(f"Lỗi pywinstyles (Win11): {e}")
        else:
            try: pywinstyles.apply_style(root_window, current_theme)
            except Exception as e: print(f"Lỗi pywinstyles (Win10): {e}")
    else: print("Warning: Title bar theming only supported on Windows 10/11.")
# --- HẾT ---

# --- LỚP QueueIO (Copy từ app chính) ---
class QueueIO:
    def __init__(self, q):
        self.queue = q
    
    def write(self, text):
        progress_data = {}
        # Tìm % (ví dụ: " 35%")
        percent_match = re.search(r'(\d+)\%', text)
        if percent_match:
            progress_data["percent"] = int(percent_match.group(1))

        # Tìm tốc độ (ví dụ: "1.25MB/s")
        speed_match = re.search(r'([\d\.]+\s*[kKMG]?B/s)', text)
        if speed_match:
            progress_data["speed"] = speed_match.group(1).strip()
            
        # Tìm ETA (ví dụ: "<00:15")
        eta_match = re.search(r'<([\d:]+)', text)
        if eta_match:
            progress_data["eta"] = eta_match.group(1)

        if "percent" in progress_data:
            # Chỉ gửi message nếu tìm thấy %
            self.queue.put(("progress", progress_data))
        elif text.strip() and "---" not in text and "Bắt đầu" not in text and "Tải xong" not in text:
            # Gửi các log khác nếu cần
            self.queue.put(("status", text.strip()))
            
    def flush(self):
        pass
# --- HẾT LỚP ---

class UpdaterApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Đang Cập Nhật...")
        self.root.geometry("450x140") # Tăng kích thước
        self.root.resizable(False, False)
        
        try:
            sv_ttk.set_theme("dark")
            apply_theme_to_titlebar(self.root)
        except Exception as e:
            print(f"Lỗi khi set theme: {e}")

        # Thêm style cho progressbar màu đỏ khi lỗi

        self.queue = queue.Queue()
        self.create_widgets()

        # (CODE MỚI ĐÃ SỬA)
        # Sửa lại logic kiểm tra argv
        if len(sys.argv) < 3:
            self.update_ui("error", "Lỗi: Hãy chạy file GameUpdater.exe để update", 0)
            self.root.after(10000, self.root.destroy)
            # Không cần 'return' vì code còn lại đã ở trong 'else'
        else:
            # Dùng code khi build
            self.download_url = sys.argv[1]
            self.main_app_path = sys.argv[2]

            # Kiểm tra link (ĐÃ DI CHUYỂN VÀO TRONG 'ELSE')
            if "drive.google.com" not in self.download_url:
                    self.update_ui("error", "Lỗi Config: URL không phải link Google Drive.", 0)
                    self.root.after(10000, self.root.destroy)
            else:
                # Khởi động (ĐÃ DI CHUYỂN VÀO TRONG 'ELSE')
                self.start_worker(self.download_url, self.main_app_path)
                self.process_queue()
        # --- HẾT SỬA ---


    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.status_label = ttk.Label(main_frame, text="Đang khởi tạo...", font=("Segoe UI", 10))
        self.status_label.pack(fill=tk.X, pady=(5, 10))
        
        self.progress_bar = ttk.Progressbar(main_frame, orient="horizontal", length=100, mode="determinate")
        self.progress_bar.pack(fill=tk.X, expand=True, ipady=4)
        
        # Thêm các nhãn cho tốc độ và ETA
        labels_frame = ttk.Frame(main_frame)
        labels_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.speed_label = ttk.Label(labels_frame, text="", style="secondary.TLabel", anchor=tk.W)
        self.speed_label.pack(side=tk.LEFT)
        
        self.eta_label = ttk.Label(labels_frame, text="", style="secondary.TLabel", anchor=tk.E)
        self.eta_label.pack(side=tk.RIGHT)

    def start_worker(self, url, path):
        threading.Thread(target=main_logic, args=(self.queue, url, path), daemon=True).start()

    def process_queue(self):
        """Xử lý tin nhắn từ thread nền."""
        try:
            msg_type, msg_value = self.queue.get_nowait()
            
            if msg_type == "status":
                self.update_ui("status", msg_value, None)
            
            elif msg_type == "progress":
                # msg_value là dictionary từ QueueIO
                percent = msg_value.get("percent")
                speed = msg_value.get("speed", "")
                eta = msg_value.get("eta", "")
                
                status_text = f"Đang tải... {percent}%"
                self.speed_label.config(text=speed)
                self.eta_label.config(text=f"ETA: {eta}")
                self.update_ui("status", status_text, percent)
            
            elif msg_type == "error":
                self.update_ui("error", msg_value, None)
                self.speed_label.config(text="")
                self.eta_label.config(text="")
                self.root.after(10000, self.root.destroy)
                return
                
            elif msg_type == "close":
                self.update_ui("status", msg_value, 100)
                self.speed_label.config(text="Hoàn thành!")
                self.eta_label.config(text="")
                self.root.after(3000, self.root.destroy)
                return

        except queue.Empty:
            pass
            
        self.root.after(100, self.process_queue)

    def update_ui(self, type_name, status_text, percent_val):
        self.status_label.config(text=status_text)
        if percent_val is not None:
            self.progress_bar["value"] = percent_val
            


# --- Hàm main (logic chính của updater, chạy trong thread) ---
def main_logic(queue_instance, download_url, main_app_path):
    
    # Lưu lại stderr gốc
    original_stderr = sys.stderr 
    
    try:
        queue_instance.put(("status", "Đang đợi ứng dụng chính đóng..."))
        time.sleep(3) # Tăng thời gian chờ
        
        new_app_path = main_app_path + ".new"
        old_app_path_temp = main_app_path + ".old"

        # Dọn dẹp file tạm cũ
        try:
            if os.path.exists(new_app_path): os.remove(new_app_path)
            if os.path.exists(old_app_path_temp): os.remove(old_app_path_temp)
        except Exception as cleanup_e:
            queue_instance.put(("status", f"Cảnh báo: Không thể dọn dẹp file tạm: {cleanup_e}"))

        # --- TẢI FILE BẰNG GDOWN ---
        queue_instance.put(("status", "Bắt đầu tải..."))
        
        # 1. Cướp stderr
        sys.stderr = QueueIO(queue_instance)
        
        # 2. Chạy gdown.download
        # (Nó sẽ in tiến trình ra sys.stderr, bị QueueIO bắt lại)
        gdown.download(download_url, new_app_path, quiet=False, fuzzy=True)
        
        # 3. Trả lại stderr
        sys.stderr = original_stderr
        queue_instance.put(("progress", {"percent": 100, "speed": "", "eta": ""}))
        queue_instance.put(("status", "Tải xong!"))
        # --- HẾT PHẦN GDOWN ---
            
        # Thay thế file cũ
        queue_instance.put(("status", f"Đang thay thế {os.path.basename(main_app_path)}..."))
        max_retries = 5
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                if os.path.exists(main_app_path):
                    queue_instance.put(("status", f"Lần thử {attempt + 1}: Đổi tên file cũ..."))
                    shutil.move(main_app_path, old_app_path_temp)
                    time.sleep(0.5)

                queue_instance.put(("status", f"Lần thử {attempt + 1}: Đổi tên file mới..."))
                shutil.move(new_app_path, main_app_path)
                
                queue_instance.put(("status", "Cập nhật thành công!"))

                try:
                    if os.path.exists(old_app_path_temp):
                        os.remove(old_app_path_temp)
                except Exception: pass
                
                break 
                
            except (PermissionError, OSError) as e:
                queue_instance.put(("status", f"Lần thử {attempt + 1}/{max_retries}: Vẫn bị khóa ({e}). Đang chờ..."))
                try:
                    if os.path.exists(old_app_path_temp) and not os.path.exists(main_app_path):
                        shutil.move(old_app_path_temp, main_app_path) 
                except Exception: pass
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise e
            except Exception as e:
                raise e
        
        # Chạy lại ứng dụng chính
        queue_instance.put(("status", "Đang khởi động lại ứng dụng..."))
        subprocess.Popen([main_app_path])
        queue_instance.put(("close", "Hoàn thành!"))
        
    except Exception as e:
        sys.stderr = original_stderr # Đảm bảo trả lại stderr nếu có lỗi
        queue_instance.put(("error", f"LỖI: {e}\nVui lòng tải thủ công."))

if __name__ == "__main__":
    app = UpdaterApp()
    app.root.mainloop()