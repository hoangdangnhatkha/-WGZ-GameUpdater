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

from tkinterdnd2 import DND_FILES, TkinterDnD
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

import httplib2 
from google_auth_httplib2 import AuthorizedHttp

import webbrowser
from packaging import version
import subprocess
# --- HẾT ---
CURRENT_VERSION = "1.1"
# --- Hàm để xử lý đường dẫn file khi đóng gói ---
def resource_path(relative_path):
    """ Lấy đường dẫn tuyệt đối, hoạt động cho cả .py và .exe """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def format_bytes(size_in_bytes):
    """Chuyển đổi bytes thành KB, MB, GB..."""
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:3.1f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:3.1f} PB" # Just in case

def format_time(seconds):
    """Chuyển đổi giây thành HH:MM:SS."""
    try:
        seconds = int(seconds)
        if seconds < 0: return "00:00"
        
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        else:
            return f"{m:02d}:{s:02d}"
    except:
        return "--:--"
    
def check_for_updates(config_data):
    """So sánh phiên bản hiện tại với phiên bản trên GitHub."""
    try:
        updater_info = config_data.get("updater")
        if not updater_info: return

        latest_version_str = updater_info.get("latest_version")
        if not latest_version_str: return

        # So sánh phiên bản
        if version.parse(latest_version_str) > version.parse(CURRENT_VERSION):
            print(f"Phát hiện phiên bản mới: {latest_version_str}")

            notes = updater_info.get("release_notes", "Không có ghi chú.")
            url = updater_info.get("download_url") # Phải có URL trực tiếp

            if not url:
                print("Lỗi config: 'download_url' bị thiếu trong mục 'updater'.")
                return

            message = (
                f"Đã có phiên bản mới: {latest_version_str}!\n"
                f"(Bạn đang dùng: {CURRENT_VERSION})\n\n"
                f"Ghi chú:\n{notes}\n\n"
                "Bạn có muốn tự động cập nhật ngay bây giờ?"
            )

            # Hiển thị thông báo (an toàn vì đang chạy trong process_queue)
            if messagebox.askyesno("Có Cập Nhật Mới!", message):
                try:
                    updater_exe_path = resource_path("updater.exe") 
                    main_app_path = sys.executable # Đường dẫn đến file .exe chính

                    if not os.path.exists(updater_exe_path):
                        raise FileNotFoundError("Không tìm thấy file 'updater.exe'.")

                    print("Bắt đầu chạy updater...")

                    # Chạy updater.exe và truyền (1) URL và (2) Đường dẫn app chính
                    subprocess.Popen([updater_exe_path, url, main_app_path])

                    # Đóng ứng dụng chính
                    root.destroy()

                except Exception as e:
                    messagebox.showerror("Lỗi Cập Nhật", f"Không thể chạy updater: {e}\nSẽ mở link tải thủ công.")
                    webbrowser.open_new_tab(url)
        else:
            print("Ứng dụng đã ở phiên bản mới nhất.")

    except Exception as e:
        print(f"Lỗi khi kiểm tra cập nhật: {e}")
# --- Hàm tải config từ GitHub ---
def load_config_from_github(): # Đổi tên hàm cho rõ
    json_url = "https://raw.githubusercontent.com/hoangdangnhatkha/-WGZ-GameUpdater/refs/heads/main/CapNhatNightReignMod.json"
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
GITHUB_REPO_NAME = "-WGZ-GameUpdater"
GITHUB_FILE_PATH = "CapNhatNightReignMod.json"
GITHUB_BRANCH = "main"
GITHUB_TOKEN_FILE = "github_token.txt"
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

# --- Hết hàm GitHub ---

# --- THÊM CÁC HÀM XỬ LÝ GOOGLE DRIVE ---

# Biến này sẽ lưu trữ dịch vụ Google Drive sau khi đăng nhập
drive_service = None
# Phạm vi (quyền) mà chúng ta yêu cầu: chỉ upload file
SCOPES = ['https://www.googleapis.com/auth/drive']

GOOGLE_DRIVE_FOLDER_ID = "1lO7qc485mhdLpirFgyhqMGKXAQvHoQYA"

def authenticate_google_drive():
    """Xác thực với Google Drive và trả về đối tượng service."""
    global drive_service
    creds = None
    
    # File token.json lưu trữ thông tin đăng nhập của người dùng.
    # Nó được tạo tự động sau lần đăng nhập đầu tiên.
    token_path = resource_path('token.json')
    creds_path = resource_path('credentials.json') # File bạn tải ở Bước 2
    
    if not os.path.exists(creds_path):
        messagebox.showerror("Lỗi Thiết Lập", "Không tìm thấy file 'credentials.json'.\nVui lòng làm theo Bước 2 trong hướng dẫn.")
        return None

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    # Nếu chưa có (hoặc đã hết hạn), yêu cầu người dùng đăng nhập lại
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Lỗi khi làm mới token: {e}")
                creds = None # Buộc đăng nhập lại
        else:
            try:
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                creds = flow.run_local_server(port=0)
            except Exception as e:
                messagebox.showerror("Lỗi Đăng Nhập", f"Không thể lấy thông tin xác thực: {e}")
                return None
        
        # Lưu thông tin đăng nhập cho lần chạy sau
        try:
            with open(token_path, 'w') as token_file:
                token_file.write(creds.to_json())
        except Exception as e:
            print(f"Không thể lưu token: {e}")
            
    try:
    # --- SỬA: THÊM TIMEOUT CHO TẤT CẢ YÊU CẦU API ---
    # 1. Tạo một http client từ credentials, set timeout là 15 giây

    # 2. Xây dựng service với http client đã có timeout
    
        service = build('drive', 'v3', credentials=creds)
    # --- HẾT SỬA ---

        drive_service = service # Lưu vào biến toàn cục
        return service
    except HttpError as error:
        messagebox.showerror("Lỗi API", f"Lỗi khi xây dựng dịch vụ Drive: {error}")
        drive_service = None
    return None

def upload_file_logic(file_path, status_listbox):
    """Hàm logic để upload file (chạy trong thread), CÓ THEO DÕI TIẾN TRÌNH."""
    global drive_service
    if not drive_service:
        status_listbox.insert(tk.END, f"LỖI: Chưa đăng nhập Google Drive.")
        status_listbox.itemconfig(tk.END, {'fg': 'red'})
        return
        
    if GOOGLE_DRIVE_FOLDER_ID == "YOUR_FOLDER_ID_GOES_HERE":
         status_listbox.insert(tk.END, f"LỖI: Vui lòng sửa GOOGLE_DRIVE_FOLDER_ID trong code.")
         status_listbox.itemconfig(tk.END, {'fg': 'red'})
         return

    file_name = os.path.basename(file_path)
    
    try:
        # 0. Gửi tin nhắn reset tiến trình
        progress_queue.put(("drive_upload_progress", {
            "percent": 0, "status_text": f"Đang tìm {file_name}...", 
            "speed_text": "", "eta_text": ""
        }))
        
        file_size = os.path.getsize(file_path) # Lấy kích thước file để tính %

        # 1. Tìm file đã tồn tại
        status_listbox.insert(tk.END, f"Đang tìm {file_name} trong folder...")
        status_listbox.see(tk.END)
        
        query = f"name = '{file_name}' and '{GOOGLE_DRIVE_FOLDER_ID}' in parents and trashed = false"
        response = drive_service.files().list(
            q=query, spaces='drive', fields='files(id, name)'
        ).execute()
        files = response.get('files', [])
        
        # 2. Chuẩn bị media body và request
        # Đặt chunksize (ví dụ 1MB), rất quan trọng cho resumable upload
        media = MediaFileUpload(file_path, chunksize=1024*1024, resumable=True)
        request = None
        
        if files:
            # 2a. NẾU TÌM THẤY: Chuẩn bị request Cập nhật
            existing_file_id = files[0].get('id')
            status_listbox.insert(tk.END, f"Tìm thấy. Đang cập nhật {file_name}...")
            request = drive_service.files().update(
                fileId=existing_file_id,
                media_body=media,
                fields='id'
            )
        else:
            # 2b. NẾU KHÔNG TÌM THẤY: Chuẩn bị request Tạo mới
            status_listbox.insert(tk.END, f"Không tìm thấy. Đang tạo mới {file_name}...")
            file_metadata = {'name': file_name, 'parents': [GOOGLE_DRIVE_FOLDER_ID]}
            request = drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            )
        
        status_listbox.see(tk.END)

        # 3. Thực thi upload bằng vòng lặp next_chunk()
        response = None
        start_time = time.time()
        
        while response is None:
            # status: chứa tiến trình; response: chứa kết quả khi hoàn thành
            status, response = request.next_chunk()
            
            if status:
                bytes_uploaded = status.resumable_progress
                percent = int(status.progress() * 100)
                
                elapsed_time = time.time() - start_time
                speed_bps = (bytes_uploaded / elapsed_time) if elapsed_time > 0 else 0
                
                remaining_bytes = file_size - bytes_uploaded
                eta_seconds = (remaining_bytes / speed_bps) if speed_bps > 0 else 0
                
                # Gửi tiến trình về queue
                progress_queue.put(("drive_upload_progress", {
                    "percent": percent,
                    "status_text": f"Đang upload: {percent}%",
                    "speed_text": f"{format_bytes(speed_bps)}/s",
                    "eta_text": f"ETA: {format_time(eta_seconds)}"
                }))

        # 4. Xử lý khi hoàn thành
        if response:
            action_text = "cập nhật" if files else "upload mới"
            status_listbox.insert(tk.END, f"THÀNH CÔNG: Đã {action_text} {file_name}.")
            status_listbox.itemconfig(tk.END, {'fg': 'green'})
            progress_queue.put(("refresh_drive_list", None)) # Yêu cầu refresh list

    except HttpError as error:
        status_listbox.insert(tk.END, f"LỖI: {error} khi xử lý {file_name}.")
        status_listbox.itemconfig(tk.END, {'fg': 'red'})
    except Exception as e:
        # Bắt các lỗi mạng (như SSL, timeout)
        status_listbox.insert(tk.END, f"LỖI KHÁC: {e} khi xử lý {file_name}.")
        status_listbox.itemconfig(tk.END, {'fg': 'red'})
    finally:
        # 5. Gửi tin nhắn reset (bất kể thành công hay thất bại)
        progress_queue.put(("drive_upload_progress", {
            "percent": 0, "status_text": "Sẵn sàng.", "speed_text": "", "eta_text": ""
        }))
        status_listbox.see(tk.END)

# --- HẾT HÀM GOOGLE DRIVE ---

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
            check_for_updates(message_value)
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
        
        elif message_type == "drive_data_updated": # <-- ĐỔI TÊN TIN NHẮN
            drive_refresh_button.config(state=tk.NORMAL)

            # --- THÊM MỚI: Xử lý dữ liệu QUOTA ---
            quota = message_value.get("quota")
            if quota and 'limit' in quota and 'usage' in quota:
                try:
                    # Dùng hàm format_bytes() đã có
                    usage_str = format_bytes(int(quota['usage']))
                    limit_str = format_bytes(int(quota['limit']))
                    drive_storage_label.config(text=f"Dung lượng Drive: {usage_str} / {limit_str}")
                except Exception as e:
                    print(f"Lỗi format dung lượng: {e}")
                    drive_storage_label.config(text="Dung lượng Drive: Lỗi")
            else:
                drive_storage_label.config(text="Dung lượng Drive: Không thể tải")
            # --- HẾT THÊM MỚI ---

            # --- Code cũ: Xử lý danh sách FILES ---
            # Xóa tất cả icon cũ
            for widget in drive_icon_content_frame.winfo_children():
                widget.destroy()

            files = message_value.get("files", []) # Lấy 'files' từ dict

            # (Toàn bộ code còn lại để tạo lưới icon...
            # ... từ "icon_zip = root.drive_icon_zip" ...
            # ... đến "empty_label.pack()" ...
            # ... là GIỮ NGUYÊN KHÔNG ĐỔI)

            # Lấy các icon đã tải
            icon_zip = root.drive_icon_zip
            icon_exe = root.drive_icon_exe
            icon_rar = root.drive_icon_rar
            icon_file = root.drive_icon_unknown

            # Định nghĩa layout lưới (ví dụ: 6 cột)
            MAX_COLS = 8
            current_row = 0
            current_col = 0

            if files:
                for file in files:
                    file_name = file.get("name")
                    file_id = file.get("id")

                    # 1. Chọn icon dựa trên tên file
                    icon_to_use = icon_file # Mặc định
                    if file_name.endswith(".zip"):
                        icon_to_use = icon_zip
                    elif file_name.endswith(".rar"):
                        icon_to_use = icon_rar
                    elif file_name.endswith(".exe"):
                        icon_to_use = icon_exe

                    # 2. Tạo 'mini-frame' cho item này
                    item_frame = ttk.Frame(drive_icon_content_frame, style="Card.TFrame") # Dùng style 'Card'
                    item_frame.grid(row=current_row, column=current_col, padx=10, pady=10, sticky='n')

                    # 3. Tạo Icon Label
                    icon_label = ttk.Label(item_frame, image=icon_to_use)
                    icon_label.pack(side=tk.TOP, pady=(5, 0))

                    # 4. Tạo Name Label (tự động xuống dòng)
                    name_label = ttk.Label(item_frame, text=file_name, anchor=tk.CENTER, wraplength=80) 
                    name_label.pack(side=tk.TOP, fill=tk.X, expand=True, pady=(5, 5))
                    # --- 5. Gắn sự kiện Click chuột trái ---
                    def create_click_lambda(frame):
                        return lambda e: on_drive_item_click(e, frame)

                    click_func = create_click_lambda(item_frame)
                    item_frame.bind("<Button-1>", click_func)
                    icon_label.bind("<Button-1>", click_func)
                    name_label.bind("<Button-1>", click_func)
                    # --- HẾT THÊM MỚI ---


                    # --- 6. Thêm menu chuột phải (Copy Name, ID, Delete) --- 

                    # Hàm helper chung cho việc copy
                    def copy_to_clipboard(text_to_copy, type_name):
                        root.clipboard_clear()
                        root.clipboard_append(text_to_copy)
                        print(f"Đã copy {type_name}: {text_to_copy}")

                    # Hàm helper tạo lambda
                    def create_copy_lambda(text, t_name):
                        return lambda: copy_to_clipboard(text, t_name)

                    # Hàm helper tạo lambda cho Xóa
                    def create_delete_lambda(fid, fname):
                        # Hàm này sẽ gọi thread xóa
                        def start_delete_thread():
                            threading.Thread(target=action_delete_drive_file_thread, args=(fid, fname), daemon=True).start()
                        return start_delete_thread

                    context_menu = tk.Menu(item_frame, tearoff=0)

                    # Thêm 2 lệnh copy
                    context_menu.add_command(label="Copy Tên File", command=create_copy_lambda(file_name, "Tên File"))
                    context_menu.add_command(label="Copy File ID", command=create_copy_lambda(file_id, "File ID"))

                    context_menu.add_separator()

                    # Thêm lệnh Xóa
                    context_menu.add_command(label="Xóa File...", command=create_delete_lambda(file_id, file_name))

                    # Hàm hiển thị menu (không đổi)
                    def create_show_menu_lambda(menu):
                        return lambda e: menu.post(e.x_root, e.y_root)

                    show_menu_func = create_show_menu_lambda(context_menu)

                    # Gắn sự kiện chuột phải cho tất cả các phần (không đổi)
                    item_frame.bind("<Button-3>", show_menu_func)
                    icon_label.bind("<Button-3>", show_menu_func)
                    name_label.bind("<Button-3>", show_menu_func)
                    # --- Hết phần menu ---

                    # 6. Cập nhật vị trí lưới
                    current_col += 1
                    if current_col >= MAX_COLS:
                        current_col = 0
                        current_row += 1
            else:
                # Hiển thị nếu list rỗng
                empty_label = ttk.Label(drive_icon_content_frame, text="(Folder rỗng hoặc có lỗi)")
                empty_label.pack()

    # --- THÊM MỚI: XỬ LÝ YÊU CẦU REFRESH TỪ THREAD KHÁC ---
        elif message_type == "refresh_drive_list":
            action_refresh_drive_list()
        
        elif message_type == "drive_upload_progress":
            data = message_value
            drive_upload_progressbar['value'] = data.get('percent', 0)
            drive_upload_status_label.config(text=data.get('status_text', '...'))
            drive_upload_speed_label.config(text=data.get('speed_text', ''))
            drive_upload_eta_label.config(text=data.get('eta_text', ''))

        # --- THÊM MỚI: XỬ LÝ LOG CHO TAB 3 ---
        elif message_type == "drive_log":
            upload_status_listbox.insert(tk.END, message_value)
            upload_status_listbox.see(tk.END) # Cuộn xuống
    # --- HẾT THÊM MỚI ---
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
root = TkinterDnD.Tk()
sv_ttk.set_theme("dark")
apply_theme_to_titlebar(root)
root.title("[WGZ] Game Updater")
root.geometry("800x900") # Giữ nguyên kích thước
root.minsize(800, 550)
root.resizable(False,False)
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
    root.iconbitmap(default=icon_path)
except Exception as e: 
    print(f"Lỗi khi tải icon: {e}")

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

# --- THÊM MỚI: Tải các icon file chung ---
def load_drive_icon(filename, size=(32, 32)):
    """Hàm helper để tải và resize icon, trả về None nếu lỗi."""
    try:
        icon_path = resource_path(filename)
        icon_img = Image.open(icon_path).resize(size, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(icon_img)
    except Exception as e:
        print(f"Lỗi tải {filename} (bỏ qua): {e}")
        return None

# Lưu vào root để không bị garbage-collected
root.drive_icon_zip = load_drive_icon("zip_icon.png")
root.drive_icon_exe = load_drive_icon("exe_icon.png")
root.drive_icon_rar = load_drive_icon("rar_icon.png")
root.drive_icon_unknown = load_drive_icon("unknown_icon.png")
# --- HẾT THÊM MỚI ---

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
        if key == "updater":
            continue
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

path_label_credit = ttk.Label(main_tab_frame, text="by Mr-Mime 2025", style="secondary.TLabel")
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
        if key == "updater":
            continue
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
    if option_name.lower() == "updater":
        messagebox.showerror("Tên Bị Cấm", "Bạn không thể đặt tên 'updater'")
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

upload_button_top.pack(side=tk.LEFT, padx=5)
# --- Hết phần sửa cho Tab 2 ---


# --- BẮT ĐẦU CODE CHO TAB 3 ("Upload Lên Drive") ---
third_tab_frame = ttk.Frame(notebook, padding=(10, 10))
notebook.add(third_tab_frame, text=" Upload Lên Drive ")

drive_storage_label = ttk.Label(third_tab_frame, text="Dung lượng Drive: Đang tải...", style="secondary.TLabel", anchor=tk.W)
# --- Các biến và hàm cho Tab 3 ---
# Biến này sẽ lưu danh sách các đường dẫn file đã kéo vào
files_to_upload_list = []

def handle_drop_enter(event):
    # Thay đổi giao diện khi chuột kéo file vào
    drop_target_listbox.config(background="lightblue")
    
def handle_drop_leave(event):
    # Trả lại giao diện cũ
    drop_target_listbox.config(background=style.lookup("TListbox", "background"))

def handle_drop(event):
    # Xử lý khi người dùng thả file
    handle_drop_leave(event) # Trả lại màu nền
    # event.data chứa một chuỗi các đường dẫn file
    # Chúng có thể được bọc trong dấu {} nếu chứa dấu cách
    
    # Xóa danh sách cũ
    files_to_upload_list.clear()
    drop_target_listbox.delete(0, tk.END)
    
    # Phân tích chuỗi file paths (hơi phức tạp)
    raw_paths = root.tk.splitlist(event.data)
    
    for file_path in raw_paths:
        if os.path.exists(file_path) and os.path.isfile(file_path): # Chỉ chấp nhận file
            files_to_upload_list.append(file_path)
            drop_target_listbox.insert(tk.END, os.path.basename(file_path))
        else:
            print(f"Bỏ qua: {file_path} (không phải file hoặc không tồn tại)")
    
    upload_files_button.config(state=tk.NORMAL) # Bật nút upload

def action_drive_login():
    entered_pin = simpledialog.askstring("Xác nhận PIN", "Nhập mã PIN quản trị:", show='*')
    correct_pin = "2408" # Mã PIN cứng

    if entered_pin != correct_pin:
        messagebox.showerror("Sai PIN", "Mã PIN không chính xác. Đã hủy upload.")
        return # Dừng nếu PIN sai
    # Gọi hàm xác thực
    drive_auth_button.config(text="Đang đăng nhập...", state=tk.DISABLED)
    root.update_idletasks()
    
    service = authenticate_google_drive() # Hàm này chúng ta đã thêm ở Bước 4
    
    if service:
        drive_auth_button.config(text="Đã đăng nhập Google Drive", style="Green.TButton")
        # Kiểm tra xem có file chờ upload không
        if files_to_upload_list:
            upload_files_button.config(state=tk.NORMAL)
        action_refresh_drive_list()
    else:
        drive_auth_button.config(text="Đăng nhập Google Drive", state=tk.NORMAL)

def action_start_upload_all():
    # Bắt đầu upload tất cả các file trong danh sách
    if not drive_service:
        messagebox.showwarning("Chưa Đăng Nhập", "Vui lòng đăng nhập Google Drive trước.")
        return
        
    if not files_to_upload_list:
        messagebox.showinfo("Không có file", "Vui lòng kéo file vào ô bên trên trước.")
        return

    # Xóa log cũ
    upload_status_listbox.delete(0, tk.END)
    
    # Vô hiệu hóa nút để tránh bấm nhiều lần
    upload_files_button.config(state=tk.DISABLED)
    drive_auth_button.config(state=tk.DISABLED)

    # Chạy upload trong thread để không treo UI
    def upload_all_thread():
        for file_path in files_to_upload_list:
            # Chúng ta gọi hàm logic trực tiếp
            # (Hoặc có thể tạo thread riêng cho từng file)
            upload_file_logic(file_path, upload_status_listbox)
        
        # Khi xong, bật lại nút
        upload_status_listbox.insert(tk.END, "--- HOÀN THÀNH TẤT CẢ ---")
        upload_status_listbox.see(tk.END)
        upload_files_button.config(state=tk.NORMAL)
        drive_auth_button.config(state=tk.NORMAL)

    threading.Thread(target=upload_all_thread, daemon=True).start()

def action_clear_upload_list():
    files_to_upload_list.clear()
    drop_target_listbox.delete(0, tk.END)
    upload_status_listbox.delete(0, tk.END)
    upload_files_button.config(state=tk.DISABLED)

def action_refresh_drive_list():
    """Bọc hàm tải danh sách file vào một thread (an toàn cho UI)."""
    drive_refresh_button.config(state=tk.DISABLED) # Tắt nút

    # --- SỬA LỖI: Xóa item khỏi FRAME LƯỚI, không phải TREEVIEW ---
    # Xóa list cũ và hiện loading
    for widget in drive_icon_content_frame.winfo_children():
        widget.destroy()

    loading_label = ttk.Label(drive_icon_content_frame, text="Đang tải, vui lòng chờ...")
    loading_label.pack(pady=10)
    # --- HẾT SỬA ---

    # Bắt đầu thread để tải
    root.after(100, process_queue)
    threading.Thread(target=refresh_drive_file_list_thread, daemon=True).start()

def refresh_drive_file_list_thread():
    """(Chạy trong thread) Lấy danh sách file VÀ dung lượng từ Drive."""
    global drive_service
    if not drive_service:
        progress_queue.put(("status", "Lỗi: Vui lòng đăng nhập Drive trước."))
        progress_queue.put(("drive_data_updated", {"files": [], "quota": None})) # Gửi dữ liệu rỗng
        return

    if GOOGLE_DRIVE_FOLDER_ID == "YOUR_FOLDER_ID_GOES_HERE":
        progress_queue.put(("status", "Lỗi: GOOGLE_DRIVE_FOLDER_ID chưa được set."))
        progress_queue.put(("drive_data_updated", {"files": [], "quota": None})) # Gửi dữ liệu rỗng
        return

    try:
        # 1. Lấy danh sách file (như cũ)
        query = f"'{GOOGLE_DRIVE_FOLDER_ID}' in parents and trashed = false"
        response_files = drive_service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)',
            orderBy='name' # Sắp xếp theo tên
        ).execute()
        files = response_files.get('files', [])

        # 2. THÊM MỚI: Lấy thông tin dung lượng
        quota_data = drive_service.about().get(fields='storageQuota').execute()
        quota = quota_data.get('storageQuota', {})

        # 3. Gửi cả hai về queue
        progress_queue.put(("drive_data_updated", {"files": files, "quota": quota}))

    except HttpError as error:
        progress_queue.put(("status", f"Lỗi khi tải dữ liệu Drive: {error}"))
        progress_queue.put(("drive_data_updated", {"files": [], "quota": None})) # Gửi rỗng
    except Exception as e:
        progress_queue.put(("status", f"Lỗi: {e}"))
        progress_queue.put(("drive_data_updated", {"files": [], "quota": None})) # Gửi rỗng

def action_delete_drive_file_thread(file_id, file_name):
    """(Chạy trong thread) Xóa file khỏi Google Drive."""
    global drive_service
    if not drive_service:
        messagebox.showerror("Lỗi", "Chưa đăng nhập Google Drive.")
        return

    # 1. Xác nhận
    if not messagebox.askyesno("Xác nhận Xóa", f"Bạn có chắc chắn muốn XÓA VĨNH VIỄN file này khỏi Google Drive không?\n\nFile: {file_name}"):
        progress_queue.put(("drive_log", "Đã hủy thao tác xóa."))
        return # Hủy

    # 2. Gửi trạng thái
    progress_queue.put(("drive_log", f"Đang xóa {file_name}..."))

    try:
        # 3. Thực thi
        drive_service.files().delete(fileId=file_id).execute()

        # 4. Báo thành công và Yêu cầu Refresh
        progress_queue.put(("drive_log", f"Đã xóa {file_name} thành công."))
        progress_queue.put(("refresh_drive_list", None)) # <-- Yêu cầu tải lại lưới

    except HttpError as error:
        messagebox.showerror("Lỗi Xóa", f"Lỗi khi xóa file: {error}")
        progress_queue.put(("drive_log", f"Lỗi khi xóa {file_name}."))
    except Exception as e:
        messagebox.showerror("Lỗi Xóa", f"Lỗi không xác định: {e}")
        progress_queue.put(("drive_log", f"Lỗi khi xóa {file_name}."))
# --- Giao diện cho Tab 3 ---



# Frame trên cho các nút
drive_button_frame = ttk.Frame(third_tab_frame)
drive_button_frame.pack(fill=tk.X, pady=5)

drive_auth_button = ttk.Button(drive_button_frame, text="Đăng nhập Google Drive", command=action_drive_login, style="Accent.TButton")
drive_auth_button.pack(side=tk.LEFT, padx=5)

upload_files_button = ttk.Button(drive_button_frame, text="Upload Tất Cả File", command=action_start_upload_all, style="Accent.TButton", state=tk.DISABLED)
upload_files_button.pack(side=tk.LEFT, padx=5)

clear_upload_list_button = ttk.Button(drive_button_frame, text="Xóa Danh Sách Upload", command=action_clear_upload_list)
clear_upload_list_button.pack(side=tk.LEFT, padx=5)

drive_refresh_button = ttk.Button(drive_button_frame, text="Tải Danh Sách File", command=action_refresh_drive_list) # Sẽ định nghĩa hàm này sau
drive_refresh_button.pack(side=tk.LEFT, padx=5)

g_selected_drive_item_frame = None # Biến theo dõi item đang được chọn

def on_drive_item_click(event, clicked_frame):
    """Xử lý khi click chuột trái vào một item trong lưới."""
    global g_selected_drive_item_frame

    # 1. Bỏ chọn item cũ (nếu có)
    if g_selected_drive_item_frame and g_selected_drive_item_frame != clicked_frame:
        try:
            # Trả về style mặc định 'Card.TFrame'
            g_selected_drive_item_frame.config(style="Card.TFrame")
        except Exception as e:
            print(f"Lỗi bỏ chọn item: {e}")

    # 2. Chọn item mới
    try:
        # Đặt style mới là "Accent.TFrame" (màu xanh accent)
        clicked_frame.config(style="Accent.TFrame") 
        g_selected_drive_item_frame = clicked_frame
    except Exception as e:
        print(f"Lỗi chọn item: {e}")
# --- HẾT THÊM MỚI ---

# Frame cho ô kéo thả
drop_target_frame = ttk.LabelFrame(third_tab_frame, text="Kéo file vào đây để upload", padding=(10, 10))
drop_target_frame.pack(fill=tk.BOTH, expand=True, pady=5)

drop_target_listbox = tk.Listbox(drop_target_frame, height=10, selectmode=tk.EXTENDED)
drop_target_listbox.pack(fill=tk.BOTH, expand=True)

# Đăng ký sự kiện kéo-thả
drop_target_listbox.drop_target_register(DND_FILES)
drop_target_listbox.dnd_bind('<<DropEnter>>', handle_drop_enter)
drop_target_listbox.dnd_bind('<<DropLeave>>', handle_drop_leave)
drop_target_listbox.dnd_bind('<<Drop>>', handle_drop)

drive_storage_label.pack(fill=tk.X, pady=(10, 2), padx=(5,0))
# --- THAY THẾ: Tạo giao diện lưới (grid) có thể cuộn ---
drive_list_frame = ttk.LabelFrame(third_tab_frame, text="File hiện có trên Drive", padding=(5, 5))
drive_list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

# 1. Tạo Canvas và Scrollbar
drive_canvas = tk.Canvas(drive_list_frame, borderwidth=0, highlightthickness=0)
drive_scrollbar = ttk.Scrollbar(drive_list_frame, orient="vertical", command=drive_canvas.yview)
drive_canvas.configure(yscrollcommand=drive_scrollbar.set)

drive_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
drive_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# 2. Tạo Frame nội dung BÊN TRONG Canvas
# Frame này sẽ chứa các icon
drive_icon_content_frame = ttk.Frame(drive_canvas, padding=(5, 5))

# 3. Đặt Frame nội dung vào Canvas
drive_canvas_window_id = drive_canvas.create_window((0, 0), window=drive_icon_content_frame, anchor="nw")

# --- Các hàm helper cho việc cuộn (Tương tự Tab 1) ---
def on_drive_content_frame_configure(event):
    """Cập nhật scroll region của canvas."""
    drive_canvas.configure(scrollregion=drive_canvas.bbox("all"))

def on_drive_canvas_configure(event):
    """Đảm bảo frame nội dung luôn fill chiều rộng của canvas."""
    drive_canvas.itemconfig(drive_canvas_window_id, width=event.width - 4)

# 4. Bind (gắn) các sự kiện cuộn
drive_icon_content_frame.bind("<Configure>", on_drive_content_frame_configure)
drive_canvas.bind("<Configure>", on_drive_canvas_configure)

# Gắn sự kiện cuộn chuột cho tất cả
drive_canvas.bind_all("<MouseWheel>", on_mouse_wheel) # Dùng on_mouse_wheel chung
drive_canvas.bind_all("<Button-4>", on_mouse_wheel)
drive_canvas.bind_all("<Button-5>", on_mouse_wheel)
# --- HẾT THAY THẾ ---
# --- HẾT THÊM MỚI ---
# Frame cho log trạng thái
upload_status_frame = ttk.LabelFrame(third_tab_frame, text="Trạng thái Upload", padding=(10, 10))
upload_status_frame.pack(fill=tk.X, expand=False, pady=5)

# --- THÊM MỚI: Thanh Progress Bar và Nhãn (Giống Tab 1) ---
drive_upload_progressbar = ttk.Progressbar(upload_status_frame, orient="horizontal", length=100, mode="determinate")
drive_upload_progressbar.pack(fill=tk.X, pady=(0, 5))

drive_upload_labels_frame = ttk.Frame(upload_status_frame)
drive_upload_labels_frame.pack(fill=tk.X)

drive_upload_status_label = ttk.Label(drive_upload_labels_frame, text="Sẵn sàng upload...", anchor=tk.W, style="White.TLabel")
drive_upload_status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

drive_upload_eta_label = ttk.Label(drive_upload_labels_frame, text="", style="secondary.TLabel", anchor=tk.E, width=8)
drive_upload_eta_label.pack(side=tk.RIGHT, padx=(10,0))

drive_upload_speed_label = ttk.Label(drive_upload_labels_frame, text="", style="secondary.TLabel", anchor=tk.E, width=12)
drive_upload_speed_label.pack(side=tk.RIGHT)
# --- HẾT THÊM MỚI ---

# Log listbox (nằm bên dưới)
status_listbox_scrollbar = ttk.Scrollbar(upload_status_frame, orient="vertical")
upload_status_listbox = tk.Listbox(upload_status_frame, height=8, yscrollcommand=status_listbox_scrollbar.set) # Giảm chiều cao
status_listbox_scrollbar.config(command=upload_status_listbox.yview)

status_listbox_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=(5,0))
upload_status_listbox.pack(fill=tk.BOTH, expand=True, pady=(5,0))

# --- HẾT CODE CHO TAB 3 ---
# --- BẮT ĐẦU CODE CHO TAB 4 ("Credit") ---
fourth_tab_frame = ttk.Frame(notebook, padding=(20, 20)) # Increased padding
notebook.add(fourth_tab_frame, text=" Credit ")

# Add content to the Credit tab
credit_title_label = ttk.Label(
    fourth_tab_frame,
    text="WGZ Game Updater",
    font=("Segoe UI", 16, "bold"), # Larger, bold font
    anchor=tk.CENTER
)
credit_title_label.pack(pady=(10, 20), fill=tk.X)

credit_author_label = ttk.Label(
    fourth_tab_frame,
    text="Phát triển bởi: Mr-Mime (hoangdangnhatkha)",
    anchor=tk.CENTER
)
credit_author_label.pack(pady=5, fill=tk.X)

credit_github_label = ttk.Label(
    fourth_tab_frame,
    text="GitHub: https://github.com/hoangdangnhatkha",
    style="Link.TLabel", # Requires Link.TLabel style definition (optional)
    cursor="hand2",       # Make it look clickable
    anchor=tk.CENTER
)
credit_github_label.pack(pady=5, fill=tk.X)

# Function to open the link
def open_github(event):
    webbrowser.open_new_tab("https://github.com/hoangdangnhatkha/-WGZ-GameUpdater")

# Bind click event to open the link
credit_github_label.bind("<Button-1>", open_github)

# Optional: Add more labels for libraries used, special thanks, etc.
credit_thanks_label = ttk.Label(
    fourth_tab_frame,
    text="\n\nChỉ dành cho việc tải, upload và chia sẽ game của Discord WIBU's Gaming Zone",
    style="secondary.TLabel",
    anchor=tk.CENTER
)
credit_thanks_label.pack(pady=(20, 5), fill=tk.X)
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