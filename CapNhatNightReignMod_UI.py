# Save this file as 'CapNhatNightReignMod_Ui.py'
import gdown
import zipfile
import os
import shutil
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
import tkinter.ttk as ttk  # Đã import ttk
import threading
import queue
import re
import requests
import json
import rarfile
from PIL import Image, ImageTk
import pywinstyles
import sv_ttk  # <-- THÊM DÒNG NÀY

# --- Hàm để xử lý đường dẫn file khi đóng gói ---
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- MỚI: Hàm tải config từ Google Drive ---
def load_config_from_drive():
    # SỬA: Đã cập nhật URL của file JSON
    json_url = "https://raw.githubusercontent.com/hoangdangnhatkha/WGZGameUpdater/main/CapNhatNightReignMod.json"
    
    try:
        print("Đang tải config từ Google Drive...")
        response = requests.get(json_url, timeout=5) 
        response.raise_for_status()
        config_data = response.json()
        print("Tải config thành công.")
        return config_data
    except Exception as e:
        print(f"Lỗi khi tải config: {e}. Sẽ dùng link dự phòng.")
        return None 

# --- Configuration (SỬA) ---
# 1. Đặt các link dự phòng (hardcoded)
fallback_options = {
    "Tải Full Mod": {
        "url": "https://drive.google.com/uc?id=1Byam38jfTS5TJVNTCaebQpMmALXjPsl2", 
        "version": "v? (Dự phòng)",
        "type": "zip",
        "password": None,
        "delete_before_extract": []
    },
    "Cập Nhật Mod": {
        "url": "https://drive.google.com/uc?id=1f9rT20EHRoF4dfc19IcC3ykhwNmUPis_", 
        "version": "v? (Dự phòng)",
        "type": "zip",
        "password": None,
        "delete_before_extract": []
    },
    "Tải/Cập Nhật Seamless Coop": {
        "url": "https://drive.google.com/uc?id=1182Ju68pjG9LfPTgLaeME6lHPk6aeIEe", 
        "version": "v? (Dự phòng)",
        "type": "zip",
        "password": None,
        "delete_before_extract": []
    }
}

# 2. KHÔNG tải config ở đây nữa.
download_options = {} # Khởi tạo rỗng
# --- Hết phần sửa ---

# --- Config file setup ---
APP_NAME = "NightreignModUpdater"
appdata_path = os.getenv('APPDATA')
config_folder = os.path.join(appdata_path, APP_NAME)
config_file_path = os.path.join(config_folder, 'settings.json') 

# --- Logic cho việc lưu/tải file config local (settings.json) ---
def load_local_config():
    try:
        os.makedirs(config_folder, exist_ok=True)
        with open(config_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"destination_folder": "", "installed_versions": {}}

def save_local_config(config_data):
    try:
        os.makedirs(config_folder, exist_ok=True)
        with open(config_file_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4)
    except Exception as e:
        print(f"Cảnh báo: Không thể lưu config local: {e}")

local_config = load_local_config() 

# --- Thiết lập "bắt" tiến trình ---
progress_queue = queue.Queue()
original_stderr = sys.stderr

class QueueIO:
    # (Code của class QueueIO không đổi)
    def __init__(self, q):
        self.queue = q
    def write(self, text):
        progress_data = {}
        percent_match = re.search(r'(\d+)%', text)
        if percent_match:
            progress_data["percent"] = int(percent_match.group(1))
        speed_match = re.search(r'([\d\.]+\s*[kKMG]?B/s)', text)
        if speed_match:
            progress_data["speed"] = speed_match.group(1).strip()
        eta_match = re.search(r'<([\d:]+)', text)
        if eta_match:
            progress_data["eta"] = eta_match.group(1)
        
        if "percent" in progress_data:
            self.queue.put(("progress", progress_data))
        elif text.strip():
            self.queue.put(("status", text.strip()))
    def flush(self):
        pass

# --- Logic chính (SỬA LỖI [Errno 22]) ---
def download_and_extract_logic():
    global local_config
    
    progress_queue.put(("status", "DISABLE_BUTTONS"))
    
    selected_key = selected_option.get()
    option_label.config(text="Đang " + selected_key, foreground="white")
    if not selected_key:
        progress_queue.put(("status", "Lỗi: Vui lòng chọn một gói tải."))
        progress_queue.put(("status", "ENABLE_BUTTONS"))
        return
    
    selected_option_data = download_options[selected_key]
    file_url = selected_option_data["url"]
    print(f"Downloading from: {file_url}")
    version = selected_option_data["version"]
    file_type = selected_option_data.get("type", "zip") 
    password = selected_option_data.get("password", None)
    delete_list = selected_option_data.get("delete_before_extract", [])
    
    destination_folder = path_entry.get()
    
    if not destination_folder or not os.path.isdir(destination_folder):
        progress_queue.put(("status", "Lỗi: Đường dẫn không hợp lệ."))
        progress_queue.put(("status", "ENABLE_BUTTONS"))
        return
        
    local_config['destination_folder'] = destination_folder
    save_local_config(local_config)
    
    sys.stderr = QueueIO(progress_queue)

    try:
        if file_type == "exe":
            # --- XỬ LÝ EXE ---
            sanitized_key = re.sub(r'[\\/*?:"<>|]', "", selected_key)
            sanitized_version = re.sub(r'[\\/*?:"<>|]', "", version)
            
            file_name = f"{sanitized_key}_{sanitized_version}.exe"
            target_exe_path = os.path.join(destination_folder, file_name) 

            if os.path.exists(target_exe_path):
                progress_queue.put(("status", "File đã tồn tại. Đang mở..."))
                os.startfile(target_exe_path)
            else:
                progress_queue.put(("status", "Bắt đầu tải file..."))
                gdown.download(file_url, target_exe_path, quiet=False)
                progress_queue.put(("status", "Đã tải xong! Đang mở file..."))
                os.startfile(target_exe_path)
        
        elif file_type == "zip" or file_type == "rar":
            # --- XỬ LÝ ZIP HOẶC RAR ---
            
            temp_archive_path = os.path.join(os.environ['TEMP'], f"my_temp_download.{file_type}")
            
            if os.path.exists(temp_archive_path):
                os.remove(temp_archive_path)
                
            progress_queue.put(("status", "Bắt đầu tải file..."))
            gdown.download(file_url, temp_archive_path, quiet=False) 

            if delete_list:
                progress_queue.put(("status", "Đang dọn dẹp file cũ..."))
                for item_name in delete_list:
                    item_path = os.path.join(destination_folder, item_name)
                    try:
                        if os.path.exists(item_path):
                            if os.path.isfile(item_path) or os.path.islink(item_path):
                                os.remove(item_path)
                            elif os.path.isdir(item_path):
                                shutil.rmtree(item_path)
                        else:
                            print(f"Bỏ qua (không tìm thấy): {item_path}")
                    except Exception as e:
                        print(f"Lỗi khi xóa {item_path}: {e}")
                        progress_queue.put(("status", f"Lỗi khi dọn dẹp: {e}"))
            
            progress_queue.put(("status", "Đã tải xong! Đang giải nén..."))
            
            temp_dir = os.path.join(destination_folder, "temp_extraction_92837")
            os.makedirs(temp_dir, exist_ok=True)

            if file_type == "zip":
                pwd_bytes = bytes(password, 'utf-8') if password else None
                with zipfile.ZipFile(temp_archive_path) as z:
                    z.extractall(temp_dir, pwd=pwd_bytes)
            elif file_type == "rar":
                with rarfile.RarFile(temp_archive_path) as r:
                    r.extractall(temp_dir, pwd=password)
            
            shutil.copytree(temp_dir, destination_folder, dirs_exist_ok=True)
            shutil.rmtree(temp_dir)
            
            if os.path.exists(temp_archive_path):
                os.remove(temp_archive_path)
        
        # --- CẬP NHẬT CHUNG ---
        option_label.config(text="Đã Hoàn Thành " + selected_key, foreground="green")
        progress_queue.put(("status", "Cài đặt/Chạy thành công!"))

        new_version = download_options[selected_key]['version']
        if 'installed_versions' not in local_config:
            local_config['installed_versions'] = {}
        local_config['installed_versions'][selected_key] = new_version
        save_local_config(local_config)
        
        update_radio_buttons_text()

    except Exception as e:
        if "Bad password" in str(e) or "NeedPassword" in str(e):
            progress_queue.put(("status", "Lỗi: Sai mật khẩu!"))
        else:
            progress_queue.put(("status", f"Lỗi không xác định: {e}"))
        print(f"Lỗi: {e}") 

    finally:
        sys.stderr = original_stderr
        progress_queue.put(("status", "ENABLE_BUTTONS"))


        
# --- Các hàm cho Nút bấm ---
def start_download_thread():
    style = ttk.Style()
    style.configure("Green.TRadiobutton", foreground="green")
    style.configure("Red.TRadiobutton", foreground="red")
    progress_bar['value'] = 0
    status_label.config(text="Hãy chọn đường dẫn và bấm bắt đầu.", foreground="green")
    speed_label.config(text="")
    eta_label.config(text="")
    option_label.config(text="GG", foreground="black")
    
    root.after(100, process_queue)
    threading.Thread(target=download_and_extract_logic, daemon=True).start()

def browse_for_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        path_entry.delete(0, tk.END)
        path_entry.insert(0, folder_selected)

# --- Hàm xử lý queue ---
def process_queue():
    global download_options, local_config
    try:
        message_type, message_value = progress_queue.get_nowait()
        
        if message_type == "config_loaded":
            download_options = message_value 
            
            progress_bar.stop()
            progress_bar.config(mode="determinate")
            progress_bar['value'] = 0
            
            start_button.config(state=tk.NORMAL)
            browse_button.config(state=tk.NORMAL)
            
            update_radio_buttons_text() 
            
            saved_path = local_config.get("destination_folder", "")
            if saved_path:
                path_entry.insert(0, saved_path)
            
            status_label.config(text="Hãy chọn đường dẫn và bấm bắt đầu.", foreground="white")
            return 

        elif message_type == "status":
            if message_value == "DISABLE_BUTTONS":
                start_button.config(state=tk.DISABLED)
                browse_button.config(state=tk.DISABLED)
            elif message_value == "ENABLE_BUTTONS":
                start_button.config(state=tk.NORMAL)
                browse_button.config(state=tk.NORMAL)
                if "thành công" not in status_label.cget("text"):
                    status_label.config(text="Hãy chọn đường dẫn và bấm bắt đầu.", foreground="black")
                    progress_bar['value'] = 0
                speed_label.config(text="")
                eta_label.config(text="")
                return 
            elif "Lỗi" in message_value:
                status_label.config(text=message_value, foreground="red")
                option_label.config(text="Thất bại", foreground="red") 
                progress_bar['value'] = 0
                speed_label.config(text="")
                eta_label.config(text="")
            elif "thành công" in message_value:
                status_label.config(text=message_value, foreground="green")
                progress_bar['value'] = 100
                speed_label.config(text="Hoàn thành!")
                eta_label.config(text="")
            else:
                status_label.config(text=message_value, foreground="white")
        
        elif message_type == "progress":
            progress_data = message_value
            if "percent" in progress_data:
                percent = progress_data["percent"]
                progress_bar['value'] = percent
                status_label.config(text=f"Đang tải: {percent}%", foreground="white")
            if "speed" in progress_data:
                speed_label.config(text=progress_data["speed"])
            if "eta" in progress_data:
                eta_label.config(text=f"ETA: {progress_data['eta']}")

    except queue.Empty:
        pass
    
    root.after(100, process_queue)

# --- Hàm xử lý khi bấm nút X ---
def on_closing():
    if start_button['state'] == tk.DISABLED:
        if messagebox.askyesno("Xác nhận thoát", "Đang tải file. Bạn có chắc chắn muốn thoát? \n (Việc tải sẽ bị hủy và phải tải lại từ đầu)"):
            root.destroy()
    else:
        root.destroy()


def apply_theme_to_titlebar(root):
    """Applies dark/light theme to the Windows title bar."""
    # Ensure sv_ttk theme is applied first for get_theme() to work
    current_theme = sv_ttk.get_theme() # Get current theme ('dark' or 'light')
    
    # Check Windows version (requires sys module)
    version = sys.getwindowsversion()

    if version.major >= 10: # Works on Windows 10 and 11
        if version.build >= 22000: # Windows 11 specific API for background color
             # Use dark grey for dark theme, light grey for light theme
            color = "#1c1c1c" if current_theme == "dark" else "#fafafa"
            pywinstyles.change_header_color(root, color)
        else: # Windows 10 generic dark/light mode API
            pywinstyles.apply_style(root, current_theme) # Apply 'dark' or 'light'
    else:
        print("Warning: Title bar theming only supported on Windows 10/11.")
# --- Cài đặt cửa sổ Giao diện (UI) (SỬA) ---
root = tk.Tk()

# --- THÊM DÒNG NÀY ĐỂ KÍCH HOẠT THEME ---
# Bạn có thể đổi "dark" thành "light"

root.title("")
root.geometry("700x600") 

try:
    rarfile.UNRAR_TOOL = resource_path("UnRAR.exe")
except Exception as e:
    print(f"Lỗi nghiêm trọng: Không tìm thấy UnRAR.exe đã đóng gói: {e}")

try:
    icon_path = resource_path("logo.ico")
    root.iconbitmap(icon_path)
except Exception as e:
    print(f"Lỗi khi tải icon: {e}")

# SỬA: Đổi tk.Frame sang ttk.Frame
notebook = ttk.Notebook(root, padding=(10, 10))
notebook.pack(expand=True, fill="both")
main_tab_frame = ttk.Frame(notebook)
second_tab_frame = ttk.Frame(notebook)
notebook.add(main_tab_frame, text="Tải/Cập Nhật Game")
notebook.add(second_tab_frame, text=" Upload ")
# --- Thêm logo ---
try:
    # image_path = resource_path("logo.jpg")
    image_path = resource_path(r"C:\Users\Dang\Desktop\Exe File\[WGZ]GameUpdaterProject\WGZGameUpdater\logo.png")
    my_image = Image.open(image_path)
    my_image = my_image.resize((150, 150), Image.Resampling.LANCZOS)
    tk_image = ImageTk.PhotoImage(my_image)
    # Ảnh Label dùng tk.Label vẫn ổn, nhưng ttk.Label cũng được
    image_label = ttk.Label(main_tab_frame, image=tk_image, anchor=tk.CENTER)
    image_label.pack(pady=(0, 10)) 
    root.tk_image = tk_image
except Exception as e:
    print(f"Lỗi khi tải ảnh (bỏ qua): {e}")

# --- Khung chứa các lựa chọn ---
# SỬA: Đổi sang ttk.LabelFrame
options_frame = ttk.LabelFrame(main_tab_frame, text="Bro muốn làm gì?", padding=(10, 5))
options_frame.pack(fill=tk.X, pady=5)
selected_option = tk.StringVar()

radio_buttons = [] # Biến global

def update_radio_buttons_text():
    """Hàm này tạo/cập nhật text của các radio button VÀ THÊM NHÃN 'NEW!' VÀ ÁP DỤNG MÀU."""
    global local_config, radio_buttons
    local_config = load_local_config() 
    
    # Xóa các widget cũ bên trong options_frame
    for widget in options_frame.winfo_children():
        widget.destroy()
    radio_buttons = [] # Reset list radio buttons

    # Tạo style cho nhãn "NEW!" màu đỏ VÀ text màu xanh lá
    style = ttk.Style()
    style.configure("New.TLabel", foreground="red", font=('TkDefaultFont', 9, 'bold')) # Đỏ và đậm
    # Đảm bảo style Green được định nghĩa (nó sẽ ghi đè nếu đã tồn tại)
    style.configure("Green.TRadiobutton", foreground="green") 
    
    for (key, data) in download_options.items():
        online_version = data['version']
        installed_version = local_config.get("installed_versions", {}).get(key, "Chưa cài đặt")
        
        # Tạo một Frame cho mỗi hàng (option)
        row_frame = ttk.Frame(options_frame)
        row_frame.pack(fill=tk.X, pady=1) # Thêm padding nhỏ giữa các hàng

        button_text = f"{key} "
        button_style = "TRadiobutton" # Style mặc định
        is_new = False # Cờ để biết có cần thêm "NEW!" không

        if online_version == installed_version:
            button_text += f"({online_version}) - Đã cài đặt"
            button_style = "Green.TRadiobutton" # SỬA: Gán style xanh lá
        else:
            button_text += f"(Mới: {online_version} | Hiện tại: {installed_version})"
            # Không cần gán style đỏ cho radio button, chỉ cho nhãn NEW!
            is_new = True # Đánh dấu là mới

        # Tạo Radiobutton VỚI STYLE ĐÚNG
        rb = ttk.Radiobutton(row_frame, # Đặt vào row_frame
                       text=button_text,
                       variable=selected_option, 
                       value=key,
                       style=button_style # SỬA: Áp dụng style ở đây
                       )
        rb.pack(side=tk.LEFT) # Đặt radio button bên trái
        radio_buttons.append(rb) 

        # Thêm nhãn "NEW!" nếu cần
        if is_new:
            new_label = ttk.Label(row_frame, text="NEW!", style="New.TLabel", foreground="red")
            new_label.pack(side=tk.LEFT, padx=(5, 0)) # Đặt bên cạnh radio button

    # Chọn mặc định lựa chọn đầu tiên
    if radio_buttons: 
        first_option_key = list(download_options.keys())[0]
        selected_option.set(first_option_key)

# --- Hàng cho đường dẫn ---
# SỬA: Đổi sang ttk
path_frame = ttk.Frame(main_tab_frame)
path_frame.pack(fill=tk.X)
path_label = ttk.Label(path_frame, text="Đường dẫn folder mod:")
path_label.pack(side=tk.LEFT, padx=(0, 5))
path_entry = ttk.Entry(path_frame)
path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

# --- Hàng cho các nút bấm ---
# SỬA: Đổi sang ttk
button_frame = ttk.Frame(main_tab_frame)
button_frame.pack(pady=10)
browse_button = ttk.Button(button_frame, text="Tìm đường dẫn...", command=browse_for_folder)
browse_button.pack(side=tk.LEFT, padx=5)
# Thêm style 'Accent' cho nút quan trọng nhất
start_button = ttk.Button(button_frame, text="Bắt đầu Cài đặt", command=start_download_thread, style="Accent.TButton")
start_button.pack(side=tk.LEFT, padx=5)

# --- Hàng cho trạng thái và credit ---
# SỬA: Đổi sang ttk
path_label_credit = ttk.Label(main_tab_frame, text="by Mr-Mime", style="secondary.TLabel") # Style chữ nhỏ/xám
path_label_credit.pack(side=tk.BOTTOM, pady=(0, 5)) 

option_label = ttk.Label(main_tab_frame, text = "GG", anchor=tk.W)
option_label.pack(side=tk.BOTTOM, pady=(0, 5)) 
progress_bar = ttk.Progressbar(main_tab_frame, orient="horizontal", length=100, mode="indeterminate")
progress_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0)) 

status_frame = ttk.Frame(main_tab_frame)
status_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))
status_label = ttk.Label(status_frame, text="Hãy chọn đường dẫn và bấm bắt đầu.", anchor=tk.W)
status_label.pack(side=tk.LEFT, fill=tk.X, expand=True) 
eta_label = ttk.Label(status_frame, text="", style="secondary.TLabel", anchor=tk.E, width=8)
eta_label.pack(side=tk.RIGHT, padx=(5,0))
speed_label = ttk.Label(status_frame, text="", style="secondary.TLabel", anchor=tk.E, width=12)
speed_label.pack(side=tk.RIGHT)
# --- Hết phần sửa ---

# --- SỬA: Hàm cho luồng tải config ---
def load_config_thread():
    """Tải config và gửi vào queue."""
    global fallback_options
    config = load_config_from_drive()
    if config:
        progress_queue.put(("config_loaded", config))
    else:
        progress_queue.put(("config_loaded", fallback_options))

# --- Chạy ứng dụng ---
root.protocol("WM_DELETE_WINDOW", on_closing)

# Bắt đầu UI ở trạng thái loading
status_label.config(text="Đang tải config phiên bản...", foreground="blue")
progress_bar.start(10) # Bắt đầu animation loading
start_button.config(state=tk.DISABLED)
browse_button.config(state=tk.DISABLED)

# Bắt đầu vòng lặp process_queue
root.after(100, process_queue) 
# Bắt đầu luồng tải config
threading.Thread(target=load_config_thread, daemon=True).start()
sv_ttk.set_theme("dark")
# --- HẾT ---
apply_theme_to_titlebar(root)
# Bắt đầu vòng lặp chính của UI
root.mainloop()