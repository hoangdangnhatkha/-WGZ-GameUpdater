# Save this file as 'CapNhatNightReignMod_Ui.py'
import gdown
import zipfile
import os
import shutil
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog # Added simpledialog
import tkinter.ttk as ttk
import threading
import queue
import re
import requests
import json
import rarfile
from PIL import Image, ImageTk
import pywinstyles
import sv_ttk
# --- THÊM IMPORT CHO GITHUB ---
import github
from github import Github, InputGitAuthor, GithubException
import base64
import time
# --- HẾT ---

# --- Hàm để xử lý đường dẫn file khi đóng gói ---
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- Hàm tải config từ GitHub ---
def load_config_from_github(): # Đổi tên hàm cho rõ
    json_url = "https://raw.githubusercontent.com/hoangdangnhatkha/WGZGameUpdater/refs/heads/main/CapNhatNightReignMod.json"
    cache_buster = f"?_={int(time.time())}" # Thêm timestamp hiện tại
    full_url = json_url + cache_buster
    try:
        print(f"Đang tải config từ GitHub: {full_url}")
        response = requests.get(full_url, timeout=10)
        response.raise_for_status()
        config_data = response.json()
        print("Tải config thành công.")
        return config_data
    except requests.exceptions.Timeout:
        print(f"Lỗi khi tải config: Timeout. Sẽ dùng link dự phòng.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Lỗi mạng khi tải config: {e}. Sẽ dùng link dự phòng.")
        return None
    except json.JSONDecodeError as e:
         print(f"Lỗi đọc JSON config: {e}. Sẽ dùng link dự phòng.")
         return None
    except Exception as e:
        print(f"Lỗi không xác định khi tải config: {e}. Sẽ dùng link dự phòng.")
        return None

# --- Configuration ---
fallback_options = {
    "Tải Full Mod": {
        "url": "https://drive.google.com/uc?id=1Byam38jfTS5TJVNTCaebQpMmALXjPsl2",
        "version": "v? (Dự phòng)", "type": "zip", "password": None, "delete_before_extract": []
    },
    "Cập Nhật Mod": {
        "url": "https://drive.google.com/uc?id=1f9rT20EHRoF4dfc19IcC3ykhwNmUPis_",
        "version": "v? (Dự phòng)", "type": "zip", "password": None, "delete_before_extract": []
    },
    "Tải/Cập Nhật Seamless Coop": {
        "url": "https://drive.google.com/uc?id=1182Ju68pjG9LfPTgLaeME6lHPk6aeIEe",
        "version": "v? (Dự phòng)", "type": "zip", "password": None, "delete_before_extract": []
    },
    "Tải/Cập Nhật Seamless Coop": {
        "url": "https://drive.google.com/uc?id=1182Ju68pjG9LfPTgLaeME6lHPk6aeIEe",
        "version": "v? (Dự phòng)", "type": "zip", "password": None, "delete_before_extract": []
    }
    
}
download_options = {}

# --- THÊM CONFIG GITHUB ---
GITHUB_REPO_OWNER = "hoangdangnhatkha"
GITHUB_REPO_NAME = "WGZGameUpdater"
GITHUB_FILE_PATH = "CapNhatNightReignMod.json"
GITHUB_BRANCH = "main"
GITHUB_TOKEN_FILE = r"C:\Users\Dang\Desktop\Exe File\[WGZ]GameUpdaterProject\WGZGameUpdater\github_token.txt"
# --- HẾT ---

# --- Config file setup ---
APP_NAME = "NightreignModUpdater"
appdata_path = os.getenv('APPDATA')
config_folder = os.path.join(appdata_path, APP_NAME)
config_file_path = os.path.join(config_folder, 'settings.json')

# --- Logic cho việc lưu/tải file config local ---
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

# --- THÊM CÁC HÀM GITHUB ---
def get_github_token():
    """Đọc token từ file local."""
    try:
        token_path = resource_path(GITHUB_TOKEN_FILE)
        with open(token_path, 'r') as f:
            token = f.read().strip()
            if not token:
                 messagebox.showerror("Lỗi Token", f"File '{GITHUB_TOKEN_FILE}' rỗng.")
                 return None
            return token
    except FileNotFoundError:
        messagebox.showerror("Lỗi Token", f"Không tìm thấy file '{GITHUB_TOKEN_FILE}'. Vui lòng tạo file này và dán Personal Access Token vào.")
        return None
    except Exception as e:
         messagebox.showerror("Lỗi Token", f"Không thể đọc token: {e}")
         return None

def get_github_repo():
    """Kết nối GitHub và trả về đối tượng repo."""
    token = get_github_token()
    if not token:
        return None
    
    try:
        auth = github.Auth.Token(token)
        g = github.Github(auth=auth)
        user = g.get_user(GITHUB_REPO_OWNER)
        repo = user.get_repo(GITHUB_REPO_NAME)
        print("Kết nối GitHub repo thành công.")
        return repo
    except GithubException as e:
        messagebox.showerror("Lỗi GitHub", f"Không thể kết nối hoặc tìm repo:\n{e.data.get('message', str(e))}")
        return None
    except Exception as e:
         messagebox.showerror("Lỗi GitHub", f"Lỗi không xác định khi kết nối GitHub: {e}")
         return None

# Helper to format JSON nicely
def format_json_for_display(json_string):
    """Tries to format a JSON string with indentation."""
    try:
        parsed = json.loads(json_string)
        return json.dumps(parsed, indent=4, ensure_ascii=False)
    except json.JSONDecodeError:
        return json_string # Return original if invalid

def load_json_from_github_api(repo): # Đổi tên để tránh trùng lặp
    """Tải nội dung JSON và SHA từ GitHub API."""
    if not repo: return None, None
    print(f"Đang tải {GITHUB_FILE_PATH} từ repo...")
    try:
        contents = repo.get_contents(GITHUB_FILE_PATH, ref=GITHUB_BRANCH)
        content_str = base64.b64decode(contents.content).decode('utf-8')
        print(f"Tải thành công. SHA: {contents.sha}")
        return content_str, contents.sha # Trả về string và SHA
    except GithubException as e:
        if e.status == 404:
            messagebox.showerror("Lỗi GitHub", f"Không tìm thấy file '{GITHUB_FILE_PATH}' trên nhánh '{GITHUB_BRANCH}'.")
        else:
            messagebox.showerror("Lỗi GitHub", f"Không thể tải file JSON từ GitHub:\n{e.data.get('message', str(e))}")
        return None, None
    except Exception as e:
         messagebox.showerror("Lỗi GitHub", f"Lỗi không xác định khi tải JSON: {e}")
         return None, None

def upload_json_to_github(repo, config_dict_to_upload, current_sha): # Takes dictionary now
    """Uploads the updated config dictionary to GitHub."""
    if not repo: return False, None # Return success status and new SHA

    # Convert dict to formatted JSON string for upload
    json_string_to_upload = json.dumps(config_dict_to_upload, indent=4, ensure_ascii=False)

    print(f"Chuẩn bị upload lên {GITHUB_FILE_PATH} với SHA: {current_sha}")
    try:
        commit_message = f"Update {GITHUB_FILE_PATH} via Updater Tool"

        # Check if content actually changed (comparing objects)
        current_content_str, _ = load_json_from_github_api(repo)
        needs_upload = True
        if current_content_str:
            try:
                current_obj = json.loads(current_content_str)
                if current_obj == config_dict_to_upload:
                    messagebox.showinfo("Thông báo", "Nội dung config không thay đổi. Bỏ qua upload.")
                    needs_upload = False
                    # Return True and the original SHA since nothing changed
                    return True, current_sha
            except json.JSONDecodeError:
                pass # If current file is invalid, proceed with upload

        if needs_upload:
            update_result = repo.update_file(
                path=GITHUB_FILE_PATH,
                message=commit_message,
                content=json_string_to_upload,
                sha=current_sha,
                branch=GITHUB_BRANCH,
            )
            new_sha = update_result['commit'].sha # Get SHA of the commit containing the update
            print(f"Update result: {update_result}")
            print(f"New commit SHA: {new_sha}")
             # After successful update, get the new SHA of the *file blob* itself
            try:
                 updated_contents = repo.get_contents(GITHUB_FILE_PATH, ref=GITHUB_BRANCH)
                 new_file_sha = updated_contents.sha
                 print(f"New file SHA: {new_file_sha}")
                 messagebox.showinfo("Thành công", "Đã cập nhật file JSON lên database thành công!")
                 return True, new_file_sha # Return success and the new file SHA
            except Exception as sha_error:
                 print(f"Lỗi khi lấy SHA mới của file sau update: {sha_error}")
                 messagebox.showinfo("Thành công", "Đã cập nhật file JSON lên Database! (Không thể lấy SHA mới)")
                 return True, None # Indicate success but SHA is unknown

    except GithubException as e:
        if e.status == 409:
             messagebox.showerror("Lỗi GitHub Upload (409)", "File trên GitHub đã bị thay đổi kể từ lần bạn tải về.\nVui lòng 'Tải Config (Làm mới)' để lấy phiên bản mới nhất trước khi upload.")
        else:
            messagebox.showerror("Lỗi GitHub Upload", f"Không thể cập nhật file:\n{e.data.get('message', str(e))}")
        return False, None
    except Exception as e:
         messagebox.showerror("Lỗi GitHub Upload", f"Lỗi không xác định khi upload: {e}")
         return False, None
# --- Hết hàm GitHub ---

# --- Thiết lập "bắt" tiến trình ---
progress_queue = queue.Queue()
original_stderr = sys.stderr

class QueueIO:
    # (Code QueueIO không đổi)
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

# --- Logic chính (Download/Extract) ---
def download_and_extract_logic():
    # (Code hàm này không đổi so với phiên bản trước)
    global local_config

    progress_queue.put(("status", "DISABLE_BUTTONS"))

    selected_key = selected_option.get()
    option_label.configure(text="Đang " + selected_key, style="White.TLabel")

    if not selected_key:
        progress_queue.put(("status", "Lỗi: Vui lòng chọn một gói tải."))
        progress_queue.put(("status", "ENABLE_BUTTONS"))
        return

    selected_option_data = download_options[selected_key]
    file_url = selected_option_data["url"]
    print(f"Downloading from: {file_url}") # Debug print
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

    temp_archive_path = None # Khởi tạo

    try:
        if file_type == "exe":
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
            temp_archive_path = os.path.join(os.environ['TEMP'], f"my_temp_download.{file_type}")

            if os.path.exists(temp_archive_path):
                try: os.remove(temp_archive_path)
                except OSError as e: print(f"Cảnh báo: Không thể xóa file tạm cũ {temp_archive_path}: {e}")

            progress_queue.put(("status", "Bắt đầu tải file..."))
            gdown.download(file_url, temp_archive_path, quiet=False)

            if delete_list:
                progress_queue.put(("status", "Đang dọn dẹp file cũ..."))
                # (Code dọn dẹp không đổi)
                for item_name in delete_list:
                    item_path = os.path.join(destination_folder, item_name)
                    try:
                        if os.path.exists(item_path):
                            if os.path.isfile(item_path) or os.path.islink(item_path): os.remove(item_path)
                            elif os.path.isdir(item_path): shutil.rmtree(item_path)
                    except Exception as e:
                        print(f"Lỗi khi xóa {item_path}: {e}")
                        progress_queue.put(("status", f"Lỗi khi dọn dẹp: {e}"))

            progress_queue.put(("status", "Đã tải xong! Đang giải nén..."))

            temp_dir = os.path.join(destination_folder, "temp_extraction_92837")
            if os.path.isdir(temp_dir): shutil.rmtree(temp_dir)
            os.makedirs(temp_dir, exist_ok=True)

            archive_object = None
            if file_type == "zip":
                pwd_bytes = bytes(password, 'utf-8') if password else None
                archive_object = zipfile.ZipFile(temp_archive_path)
                archive_object.extractall(temp_dir, pwd=pwd_bytes)
            elif file_type == "rar":
                archive_object = rarfile.RarFile(temp_archive_path)
                archive_object.extractall(temp_dir, pwd=password)

            if archive_object: archive_object.close()

            shutil.copytree(temp_dir, destination_folder, dirs_exist_ok=True)
            shutil.rmtree(temp_dir)

            if temp_archive_path and os.path.exists(temp_archive_path):
                 try: os.remove(temp_archive_path)
                 except OSError as e: print(f"Cảnh báo: Không thể xóa file tạm {temp_archive_path} sau khi thành công: {e}")

        option_label.configure(text="Đã Hoàn Thành " + selected_key, style="Green.TLabel")
        progress_queue.put(("status", "Cài đặt/Chạy thành công!"))

        new_version = download_options[selected_key]['version']
        if 'installed_versions' not in local_config: local_config['installed_versions'] = {}
        local_config['installed_versions'][selected_key] = new_version
        save_local_config(local_config)

        update_radio_buttons_text()

    except Exception as e:
        if "Bad password" in str(e) or "NeedPassword" in str(e):
            progress_queue.put(("status", "Lỗi: Sai mật khẩu!"))
        else:
            progress_queue.put(("status", f"Lỗi không xác định: {e}"))
        print(f"Lỗi trong try: {e}")

    finally:
        sys.stderr = original_stderr
        progress_queue.put(("status", "ENABLE_BUTTONS"))


# --- Các hàm cho Nút bấm ---
def start_download_thread():
    # (Code hàm này không đổi)
    progress_bar['value'] = 0
    status_label.configure(text="Hãy chọn đường dẫn và bấm bắt đầu.", style="White.TLabel")
    speed_label.config(text="")
    eta_label.config(text="")
    option_label.configure(text="GG", style="White.TLabel")

    root.after(100, process_queue)
    threading.Thread(target=download_and_extract_logic, daemon=True).start()

def browse_for_folder():
    # (Code hàm này không đổi)
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        path_entry.delete(0, tk.END)
        path_entry.insert(0, folder_selected)

# --- Hàm xử lý queue ---
def process_queue():
    # (Code hàm này không đổi)
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
            status_label.configure(text="Hãy chọn đường dẫn và bấm bắt đầu.", style="White.TLabel")
            return

        elif message_type == "status":
            if message_value == "DISABLE_BUTTONS":
                start_button.config(state=tk.DISABLED)
                browse_button.config(state=tk.DISABLED)
            elif message_value == "ENABLE_BUTTONS":
                start_button.config(state=tk.NORMAL)
                browse_button.config(state=tk.NORMAL)
                current_status_text = status_label.cget("text")
                if "thành công" not in current_status_text and "Lỗi" not in current_status_text and "Sai mật khẩu" not in current_status_text:
                    status_label.configure(text="Hãy chọn đường dẫn và bấm bắt đầu.", style="White.TLabel")
                    progress_bar['value'] = 0
                speed_label.config(text="")
                eta_label.config(text="")
                return
            elif "Lỗi" in message_value or "Sai mật khẩu" in message_value:
                status_label.configure(text=message_value, style="Red.TLabel")
                option_label.configure(text="Thất bại", style="Red.TLabel")
                progress_bar['value'] = 0
                speed_label.config(text="")
                eta_label.config(text="")
            elif "thành công" in message_value:
                status_label.configure(text=message_value, style="Green.TLabel")
                progress_bar['value'] = 100
                speed_label.config(text="Hoàn thành!")
                eta_label.config(text="")
            else:
                status_label.configure(text=message_value, style="White.TLabel")

        elif message_type == "progress":
            progress_data = message_value
            if "percent" in progress_data:
                percent = progress_data["percent"]
                progress_bar['value'] = percent
                status_label.configure(text=f"Đang tải: {percent}%", style="White.TLabel")
            if "speed" in progress_data:
                speed_label.config(text=progress_data["speed"])
            if "eta" in progress_data:
                eta_label.config(text=f"ETA: {progress_data['eta']}")

    except queue.Empty:
        pass

    root.after(100, process_queue)

# --- Hàm xử lý khi bấm nút X ---
# --- Hàm xử lý khi bấm nút X ---
def on_closing():
    # Kiểm tra xem có đang tải file không (dựa vào trạng thái nút)
    print(start_button.instate(['disabled']))
    if start_button.instate(['disabled']): # <--- Kiểm tra ở đây
        # Nếu đang tải, hỏi xác nhận
        if messagebox.askyesno("Xác nhận thoát", "Đm dang tải file. m có chắc chắn muốn thoát? \n (Việc tải sẽ bị hủy và phải tải lại từ đầu)"):
            # Nếu người dùng chọn "Yes", thoát chương trình
            root.destroy()
        # else: (Nếu chọn "No", không làm gì cả, cửa sổ tiếp tục)
    else:
        # Nếu không đang tải, thoát luôn
        root.destroy()

# --- Hàm áp dụng theme cho title bar ---
def apply_theme_to_titlebar(root_window):
    # (Code hàm này không đổi)
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

# --- Cài đặt cửa sổ Giao diện (UI) ---
root = tk.Tk()
sv_ttk.set_theme("dark")
apply_theme_to_titlebar(root)
root.title("[WGZ] Game Updater")
root.geometry("800x800") # Giữ nguyên kích thước
root.minsize(800, 550)
# --- Định nghĩa Style ---
style = ttk.Style()
style.configure("Red.TLabel", foreground="red")
style.configure("Green.TLabel", foreground="green")
style.configure("White.TLabel", foreground="white") # Cho theme tối
style.configure("New.TLabel", foreground="red", font=('TkDefaultFont', 9, 'bold'))
style.configure("Green.TRadiobutton", foreground="green")

try: rarfile.UNRAR_TOOL = resource_path("UnRAR.exe")
except Exception as e: print(f"Lỗi nghiêm trọng: Không tìm thấy UnRAR.exe đã đóng gói: {e}")
try:
    icon_path = resource_path("logo.ico")
    root.iconbitmap(icon_path)
except Exception as e: 
    print(f"Lỗi khi tải icon: {e}")
    icon_path = resource_path(r"C:\Users\Dang\Desktop\Exe File\[WGZ]GameUpdaterProject\WGZGameUpdater\logo.ico")
    root.iconbitmap(icon_path)

# --- Tạo Notebook và Tab 1 ---
notebook = ttk.Notebook(root, padding=(15, 15))
notebook.pack(expand=True, fill="both")
main_tab_frame = ttk.Frame(notebook, padding=(10, 10))
notebook.add(main_tab_frame, text=" Tải/Cập Nhật Game ")

# --- Nội dung Tab 1 ---
# (Code nội dung Tab 1 không đổi)
try:
    image_path = resource_path("logo.png")
    my_image = Image.open(image_path)
    my_image = my_image.resize((150, 150), Image.Resampling.LANCZOS)
    tk_image = ImageTk.PhotoImage(my_image)
    image_label = ttk.Label(main_tab_frame, image=tk_image, anchor=tk.CENTER)
    image_label.pack(pady=(10, 15))
    root.tk_image = tk_image
except Exception as e: 
    print(f"Lỗi khi tải ảnh (bỏ qua): {e}")
    image_path = resource_path(r"C:\Users\Dang\Desktop\Exe File\[WGZ]GameUpdaterProject\WGZGameUpdater\logo.png")
    my_image = Image.open(image_path)
    my_image = my_image.resize((150, 150), Image.Resampling.LANCZOS)
    tk_image = ImageTk.PhotoImage(my_image)
    image_label = ttk.Label(main_tab_frame, image=tk_image, anchor=tk.CENTER)
    image_label.pack(pady=(10, 15))
    root.tk_image = tk_image

# 1. Tạo options_frame (LabelFrame) làm frame host CỐ ĐỊNH
# Frame này sẽ có chiều cao CỐ ĐỊNH và chứa cả canvas lẫn scrollbar
options_frame = ttk.LabelFrame(main_tab_frame, text="Bro muốn làm gì?", padding=(5, 5), height=250)
options_frame.pack(fill=tk.X, expand=False, pady=10, padx=(10, 0))
options_frame.pack_propagate(False) # RẤT QUAN TRỌNG: Giữ chiều cao cố định

# 2. Tạo Scrollbar BÊN TRONG options_frame
scrollbar = ttk.Scrollbar(options_frame, orient="vertical")
# Pack scrollbar BÊN PHẢI. Thêm padding nhỏ để không dính viền
scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=(0, 2), padx=(0, 2)) 

# 3. Tạo Canvas BÊN TRONG options_frame
canvas = tk.Canvas(options_frame, borderwidth=0, highlightthickness=0, yscrollcommand=scrollbar.set)
# Pack canvas vào không gian còn lại
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# 4. Liên kết scrollbar với canvas (làm ở bước 3 rồi)
scrollbar.config(command=canvas.yview)

# 5. Tạo content_frame (Frame MỚI) BÊN TRONG Canvas
# Đây là frame sẽ chứa các radio button
# Nó thay thế vai trò của options_frame cũ
content_frame = ttk.Frame(canvas, padding=(10, 5)) # Bạn có thể chỉnh padding ở đây

# 6. Đặt content_frame vào trong canvas
canvas_window_id = canvas.create_window((0, 0), window=content_frame, anchor="nw")

# --- Các hàm Helper cho việc cuộn ---

def on_content_frame_configure(event):
    """Cập nhật scroll region của canvas khi kích thước options_frame thay đổi."""
    canvas.configure(scrollregion=canvas.bbox("all"))

def on_canvas_configure(event):
    """Đảm bảo options_frame luôn fill chiều rộng của canvas."""
    # Trừ đi một chút để tránh thanh cuộn ngang không cần thiết
    canvas.itemconfig(canvas_window_id, width=event.width - 4)

def on_mouse_wheel(event):
    """Cho phép cuộn bằng bánh xe chuột trên các hệ điều hành."""
    scroll_amount = 0
    if sys.platform == "win32":
        scroll_amount = int(-1 * (event.delta / 120))
    elif sys.platform == "darwin": # macOS
        scroll_amount = event.delta
    else: # Linux
        if event.num == 4:
            scroll_amount = -1
        elif event.num == 5:
            scroll_amount = 1
    
    canvas.yview_scroll(scroll_amount, "units")

# 7. Bind (gắn) các sự kiện
# Khi content_frame thay đổi (thêm radio), cập nhật scrollregion
content_frame.bind("<Configure>", on_content_frame_configure) # <-- ĐỔI TÊN FRAME VÀ HÀM
# Khi canvas thay đổi (resize cửa sổ), chỉnh lại chiều rộng của content_frame
canvas.bind("<Configure>", on_canvas_configure)
# Bind mousewheel để cuộn (áp dụng cho canvas và frame bên trong)
canvas.bind("<MouseWheel>", on_mouse_wheel)
content_frame.bind("<MouseWheel>", on_mouse_wheel) # <-- ĐỔI TÊN FRAME
# Cho Linux
canvas.bind("<Button-4>", on_mouse_wheel)
canvas.bind("<Button-5>", on_mouse_wheel)
content_frame.bind("<Button-4>", on_mouse_wheel) # <-- ĐỔI TÊN FRAME
content_frame.bind("<Button-5>", on_mouse_wheel)
selected_option = tk.StringVar()
radio_buttons = []

def update_radio_buttons_text():
    # (Code hàm này không đổi)
    global local_config, radio_buttons
    local_config = load_local_config()
    for widget in content_frame.winfo_children(): widget.destroy()
    radio_buttons = []

    style = ttk.Style() # Lấy style object
    style.configure("New.TLabel", foreground="red", font=('TkDefaultFont', 9, 'bold'))
    style.configure("Green.TRadiobutton", foreground="green")

    for (key, data) in download_options.items():
        online_version = data['version']
        installed_version = local_config.get("installed_versions", {}).get(key, "Chưa cài đặt")
        row_frame = ttk.Frame(content_frame)
        row_frame.pack(fill=tk.X, pady=1)
        button_text = f"{key} "
        button_style = "TRadiobutton"
        is_new = False
        if online_version == installed_version:
            button_text += f"({online_version}) - Đã cài đặt"
            button_style = "Green.TRadiobutton"
        else:
            button_text += f" - Hãy cập nhật phiên bản mới nhất ({online_version})"
            is_new = True
        rb = ttk.Radiobutton(row_frame, text=button_text, variable=selected_option, value=key, style=button_style)
        rb.pack(side=tk.LEFT)
        radio_buttons.append(rb)

        row_frame.bind("<MouseWheel>", on_mouse_wheel)
        rb.bind("<MouseWheel>", on_mouse_wheel)
        # Cho Linux
        row_frame.bind("<Button-4>", on_mouse_wheel)
        rb.bind("<Button-4>", on_mouse_wheel)
        row_frame.bind("<Button-5>", on_mouse_wheel)
        rb.bind("<Button-5>", on_mouse_wheel)
        if is_new:
            new_label = ttk.Label(row_frame, text="NEW!", style="New.TLabel")
            new_label.pack(side=tk.LEFT, padx=(5, 0))

            new_label.bind("<MouseWheel>", on_mouse_wheel)
            new_label.bind("<Button-4>", on_mouse_wheel)
            new_label.bind("<Button-5>", on_mouse_wheel)
    if radio_buttons:
        first_option_key = list(download_options.keys())[0]
        selected_option.set(first_option_key)

path_frame = ttk.Frame(main_tab_frame)
path_frame.pack(fill=tk.X, pady=(5, 10))
path_label = ttk.Label(path_frame, text="Đường dẫn folder mod:")
path_label.pack(side=tk.LEFT, padx=(0, 10))
path_entry = ttk.Entry(path_frame)
path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

button_frame = ttk.Frame(main_tab_frame)
button_frame.pack(pady=15)
browse_button = ttk.Button(button_frame, text="Tìm đường dẫn...", command=browse_for_folder)
browse_button.pack(side=tk.LEFT, padx=10)
start_button = ttk.Button(button_frame, text="Bắt đầu Cài đặt", command=start_download_thread, style="Accent.TButton")
start_button.pack(side=tk.LEFT, padx=10)

path_label_credit = ttk.Label(main_tab_frame, text="by Mr-Mime", style="secondary.TLabel")
path_label_credit.pack(side=tk.BOTTOM, pady=(5, 5))
option_label = ttk.Label(main_tab_frame, text = "GG", anchor=tk.W, style="White.TLabel")
option_label.pack(side=tk.BOTTOM, pady=(5, 5))
progress_bar = ttk.Progressbar(main_tab_frame, orient="horizontal", length=100, mode="indeterminate")
progress_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 5))
status_frame = ttk.Frame(main_tab_frame)
status_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 5))
status_label = ttk.Label(status_frame, text="Hãy chọn đường dẫn và bấm bắt đầu.", anchor=tk.W, style="White.TLabel")
status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
eta_label = ttk.Label(status_frame, text="", style="secondary.TLabel", anchor=tk.E, width=8)
eta_label.pack(side=tk.RIGHT, padx=(10,0))
speed_label = ttk.Label(status_frame, text="", style="secondary.TLabel", anchor=tk.E, width=12)
speed_label.pack(side=tk.RIGHT)
# --- Hết Nội dung Tab 1 ---

# --- SỬA: Tạo UI cho Tab 2 ("Upload Config") ---
second_tab_frame = ttk.Frame(notebook, padding=(10, 10))
notebook.add(second_tab_frame, text="Thêm/Xóa Option Tải")

# --- Variables ---
current_config_data = {} # Dictionary để giữ config đang sửa
current_github_sha = None # SHA của file đã tải từ GitHub

# --- Frames ---
top_button_frame = ttk.Frame(second_tab_frame)
top_button_frame.pack(fill=tk.X, pady=(0, 10))
middle_frame = ttk.Frame(second_tab_frame)
middle_frame.pack(fill=tk.BOTH, expand=True)
tree_frame = ttk.Frame(middle_frame)
tree_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
edit_form_frame = ttk.LabelFrame(middle_frame, text="Thêm/Sửa Option", padding=(10, 5))
edit_form_frame.pack(side=tk.RIGHT, fill=tk.Y)
bottom_status_frame = ttk.Frame(second_tab_frame)
bottom_status_frame.pack(fill=tk.X, pady=(10, 0))

# --- Treeview Setup ---
tree_scrollbar = ttk.Scrollbar(tree_frame)
tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
cols = ("Option Name", "Version", "Type")
options_treeview = ttk.Treeview(tree_frame, columns=cols, show='headings', yscrollcommand=tree_scrollbar.set, height=15)
options_treeview.pack(expand=True, fill=tk.BOTH)
tree_scrollbar.config(command=options_treeview.yview)
for col in cols:
    options_treeview.heading(col, text=col)
    options_treeview.column(col, width=100, anchor=tk.W)
options_treeview.column("Option Name", width=180)

# --- Edit Form Setup ---
form_widgets = {}
def create_form_row(parent, label_text, widget_type="Entry", options=None):
    row = ttk.Frame(parent)
    row.pack(fill=tk.X, pady=2)
    label = ttk.Label(row, text=label_text, width=15, anchor=tk.W)
    label.pack(side=tk.LEFT)
    if widget_type == "Entry": widget = ttk.Entry(row)
    elif widget_type == "Combobox":
        widget = ttk.Combobox(row, values=options, state="readonly")
        if options: widget.set(options[0])
    elif widget_type == "Text":
        widget = tk.Text(row, height=3, width=20, wrap="word", relief=tk.SUNKEN, borderwidth=1) # Dùng tk.Text
        txt_scroll = ttk.Scrollbar(row, orient="vertical", command=widget.yview)
        widget['yscrollcommand'] = txt_scroll.set
        txt_scroll.pack(side=tk.RIGHT, fill=tk.Y) # Pack scrollbar trước
    widget.pack(side=tk.LEFT, expand=True, fill=tk.X) # Pack widget sau
    form_widgets[label_text] = widget
    return widget

create_form_row(edit_form_frame, "Option Name:")
create_form_row(edit_form_frame, "URL:")
create_form_row(edit_form_frame, "Version:")
create_form_row(edit_form_frame, "Type:", widget_type="Combobox", options=["zip", "rar", "exe"])
create_form_row(edit_form_frame, "Password:")
create_form_row(edit_form_frame, "Delete List:", widget_type="Text")
delete_help = ttk.Label(edit_form_frame, text="(Nhập file/folder, mỗi cái một dòng)", style="secondary.TLabel")
delete_help.pack(fill=tk.X)

form_button_frame = ttk.Frame(edit_form_frame)
form_button_frame.pack(pady=10)
add_update_button = ttk.Button(form_button_frame, text="Thêm / Cập nhật", style="Accent.TButton")
add_update_button.pack(side=tk.LEFT, padx=5)
clear_button = ttk.Button(form_button_frame, text="Xóa Hết")
clear_button.pack(side=tk.LEFT, padx=5)

# --- Bottom Status ---
upload_status_label = ttk.Label(bottom_status_frame, text="Tải Config để bắt đầu")
upload_status_label.pack(side=tk.LEFT)

# --- Treeview Functions ---
def populate_treeview():
    options_treeview.delete(*options_treeview.get_children())
    if not current_config_data: return
    for key, data in current_config_data.items():
        options_treeview.insert("", tk.END, iid=key, values=(
            key, data.get("version", ""), data.get("type", "zip")
        ))

def on_treeview_select(event):
    """Fills the form when an item in the treeview is selected."""
    selected_items = options_treeview.selection()
    if not selected_items:
        clear_form() # Clear form if selection is removed
        return

    selected_key = selected_items[0] # Get the item ID (which is the option key)
    if selected_key in current_config_data:
        data = current_config_data[selected_key]
        form_widgets["Option Name:"].delete(0, tk.END)
        form_widgets["Option Name:"].insert(0, selected_key)

        # --- SỬA LOGIC HIỂN THỊ URL ---
        url_entry = form_widgets["URL:"]
        url_entry.delete(0, tk.END)
        stored_url = data.get("url", "")
        # Check if it's a Google Drive direct link
        gdrive_prefix = "https://drive.google.com/uc?id="
        if stored_url.startswith(gdrive_prefix):
            # Extract and display only the ID
            file_id = stored_url[len(gdrive_prefix):]
            url_entry.insert(0, file_id)
        else:
            # Display the full URL if it's not a GDrive link
            url_entry.insert(0, stored_url)
        # --- HẾT SỬA ---

        form_widgets["Version:"].delete(0, tk.END)
        form_widgets["Version:"].insert(0, data.get("version", ""))
        form_widgets["Type:"].set(data.get("type", "zip"))
        form_widgets["Password:"].delete(0, tk.END)
        form_widgets["Password:"].insert(0, data.get("password", "") or "") # Insert empty string if None/null

        delete_list_widget = form_widgets["Delete List:"]
        delete_list_widget.config(state=tk.NORMAL) # Allow editing
        delete_list_widget.delete("1.0", tk.END)
        delete_items = data.get("delete_before_extract", [])
        if delete_items:
            delete_list_widget.insert("1.0", "\n".join(delete_items))

options_treeview.bind('<<TreeviewSelect>>', on_treeview_select)

# --- Form Button Functions ---
def clear_form():
    form_widgets["Option Name:"].delete(0, tk.END)
    form_widgets["URL:"].delete(0, tk.END)
    form_widgets["Version:"].delete(0, tk.END)
    form_widgets["Type:"].set("zip")
    form_widgets["Password:"].delete(0, tk.END)
    form_widgets["Delete List:"].config(state=tk.NORMAL)
    form_widgets["Delete List:"].delete("1.0", tk.END)
    options_treeview.selection_remove(options_treeview.selection())

def action_add_update_option():
    """Adds or updates an option in the current_config_data dictionary."""
    global current_config_data
    option_name = form_widgets["Option Name:"].get().strip()
    if not option_name:
        messagebox.showwarning("Thiếu tên", "Vui lòng nhập 'Option Name'.")
        return

    # --- SỬA LOGIC XỬ LÝ URL INPUT ---
    url_input = form_widgets["URL:"].get().strip()
    final_url = url_input # Assume it's a full URL initially

    # Check if input looks like just a Google Drive ID (basic check)
    # Simple check: no slashes, no colons, likely alphanumeric with maybe _-
    if url_input and "/" not in url_input and ":" not in url_input and "drive.google.com" not in url_input:
        # Assume it's an ID, construct the full URL
        final_url = f"https://drive.google.com/uc?id={url_input}"
        print(f"Detected ID, constructed URL: {final_url}") # Debug print
    # --- HẾT SỬA ---

    version = form_widgets["Version:"].get().strip()
    option_type = form_widgets["Type:"].get()
    password = form_widgets["Password:"].get().strip()
    delete_list_raw = form_widgets["Delete List:"].get("1.0", tk.END).strip()
    delete_list = [line.strip() for line in delete_list_raw.splitlines() if line.strip()]

    # Create the data object using final_url
    new_data = {
        "url": final_url, # Use the potentially constructed URL
        "version": version,
        "type": option_type,
        "password": password if password else None, # Store empty as None (JSON null)
        "delete_before_extract": delete_list
    }

    current_config_data[option_name] = new_data

    populate_treeview() # Refresh the treeview
    # Select the added/updated item
    options_treeview.selection_set(option_name)
    options_treeview.focus(option_name) # Scroll to it
    upload_status_label.config(text=f"'{option_name}' đã được thêm/cập nhật cục bộ.", style="White.TLabel")

def action_delete_option():
    global current_config_data
    selected_items = options_treeview.selection()
    if not selected_items:
        messagebox.showwarning("Chưa chọn", "Vui lòng chọn một option trong danh sách để xóa.")
        return
    selected_key = selected_items[0]
    if messagebox.askyesno("Xác nhận xóa", f"Bạn có chắc chắn muốn xóa option '{selected_key}'?"):
        if selected_key in current_config_data:
            del current_config_data[selected_key]
            populate_treeview()
            clear_form()
            upload_status_label.config(text=f"'{selected_key}' đã được xóa cục bộ.", style="Red.TLabel") # Dùng style
        else: messagebox.showerror("Lỗi", "Option đã chọn không còn tồn tại?")

add_update_button.config(command=action_add_update_option)
clear_button.config(command=clear_form)

# --- Top Button Functions ---
def action_load_from_github_wrapper():
    global current_config_data, current_github_sha
    upload_status_label.config(text="Đang tải từ GitHub...", style="White.TLabel") # Dùng style
    root.update_idletasks()
    repo = get_github_repo()
    if not repo:
        upload_status_label.config(text="Lỗi kết nối repo.", style="Red.TLabel") # Dùng style
        return

    json_content, sha = load_json_from_github_api(repo)
    if json_content is not None and sha is not None:
        try:
            current_config_data = json.loads(json_content)
            current_github_sha = sha
            populate_treeview()
            clear_form()
            upload_status_label.config(text="Đã tải config từ database", style="Green.TLabel") # Dùng style
        except json.JSONDecodeError:
             messagebox.showerror("Lỗi JSON", "File JSON tải về từ GitHub không hợp lệ.")
             upload_status_label.config(text="Lỗi đọc JSON từ GitHub.", style="Red.TLabel")
             current_config_data = {}; current_github_sha = None; populate_treeview()
        except Exception as e:
             messagebox.showerror("Lỗi", f"Lỗi không xác định khi xử lý JSON: {e}")
             upload_status_label.config(text="Lỗi xử lý JSON.", style="Red.TLabel")
    else:
        upload_status_label.config(text="Tải JSON từ GitHub thất bại.", style="Red.TLabel")
        current_config_data = {}; current_github_sha = None; populate_treeview()

def action_upload_to_github_wrapper():
    global current_github_sha
    if not current_config_data:
         messagebox.showwarning("Chưa có dữ liệu", "Không có dữ liệu config để upload.")
         return
    if current_github_sha is None:
        messagebox.showwarning("Thiếu SHA", "Vui lòng 'Tải Config' trước khi upload.")
        return
    repo = get_github_repo()
    if not repo: return
    if messagebox.askyesno("Xác nhận Cập Nhật", "Bạn có chắc chắn muốn ghi đè file config bằng dữ liệu hiện tại?"):
        entered_pin = simpledialog.askstring("Xác nhận PIN", "Nhập mã PIN quản trị:", show='*')
        correct_pin = "2408" # Mã PIN cứng

        if entered_pin != correct_pin:
            messagebox.showerror("Sai PIN", "Mã PIN không chính xác. Đã hủy upload.")
            return # Dừng nếu PIN sai
        upload_status_label.config(text="Đang upload lên GitHub...", style="White.TLabel")
        root.update_idletasks()
        success, new_sha = upload_json_to_github(repo, current_config_data, current_github_sha)
        if success:
            if new_sha:
                 current_github_sha = new_sha
                 upload_status_label.config(text="Upload thành công!", style="Green.TLabel")
            else:
                 current_github_sha = None
                 upload_status_label.config(text="Upload thành công! (Nên tải lại config)", style="White.TLabel") # Dùng style
        else:
            upload_status_label.config(text="Upload thất bại.", style="Red.TLabel") # Dùng style

# --- Create Top Buttons ---
load_button_top = ttk.Button(top_button_frame, text="Tải Config (Làm mới)", command=action_load_from_github_wrapper)
load_button_top.pack(side=tk.LEFT, padx=5)
delete_button_top = ttk.Button(top_button_frame, text="Xóa Option Đã Chọn", command=action_delete_option)
delete_button_top.pack(side=tk.LEFT, padx=5)
upload_button_top = ttk.Button(top_button_frame, text="Lưu Config", command=action_upload_to_github_wrapper, style="Accent.TButton")
upload_button_top.pack(side=tk.LEFT, padx=5)
# --- Hết phần sửa cho Tab 2 ---

# --- Hàm cho luồng tải config ban đầu ---
def load_config_thread():
    """Tải config và gửi vào queue."""
    global fallback_options
    config = load_config_from_github()
    if config:
        progress_queue.put(("config_loaded", config))
    else:
        progress_queue.put(("config_loaded", fallback_options))

# --- Chạy ứng dụng ---
root.protocol("WM_DELETE_WINDOW", on_closing)
status_label.configure(text="Đang tải config phiên bản...", style="White.TLabel")
progress_bar.start(10)
start_button.config(state=tk.DISABLED)
browse_button.config(state=tk.DISABLED)
root.after(100, process_queue)
threading.Thread(target=load_config_thread, daemon=True).start()
root.mainloop()