# Save this file as 'CapNhatNightReignMod_Ui.py'
import sys
import os
if sys.platform == "win32":
    class NullWriter:
        def write(self, data): pass
        def flush(self): pass
        def fileno(self): return -1
        def reconfigure(self, *args, **kwargs): pass
    # Gán đè ngay lập tức nếu chúng không tồn tại (chế độ --windowed)
    if sys.stdin is None: sys.stdin = NullWriter()
    if sys.stdout is None: sys.stdout = NullWriter()
    if sys.stderr is None: sys.stderr = NullWriter()
import tkinter as tk
import tkinter.ttk as ttk
from PIL import Image, ImageTk
from tkinterdnd2 import DND_FILES, TkinterDnD
import ctypes
import io
import platform
import shutil
import zipfile
import pyperclip
import threading
import webview
import queue
import gdown



from google.auth.transport.requests import AuthorizedSession
from tkinter import filedialog, messagebox, simpledialog # Added simpledialog
import pyautogui
import pygetwindow as gw
import re
import io
import requests
import json
import rarfile
import winreg
import winshell  # <-- THÊM MỚI
import glob
import pythoncom
import pywinstyles
import sv_ttk
import hashlib
# --- THÊM IMPORT CHO GITHUB ---
import github
from github import Github, InputGitAuthor, GithubException
import base64
import time
import math
import multiprocessing
from datetime import datetime
import concurrent.futures
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload, MediaIoBaseUpload
from PIL import Image, ImageTk, ImageGrab, ImageDraw
import random # Đảm bảo đã có random
import httplib2 
from google_auth_httplib2 import AuthorizedHttp
import webbrowser
from packaging import version
import subprocess
import winsound

if sys.platform.startswith('win'):
    import io
    if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

if sys.platform == "win32":
    class NullWriter:
        def write(self, data): pass
        def flush(self): pass
        
    if sys.stdin is None:
        sys.stdin = NullWriter()
    if sys.stdout is None:
        sys.stdout = NullWriter()
    if sys.stderr is None:
        sys.stderr = NullWriter()

global root
root = None

def enforce_admin_rights():
    """
    Kiểm tra và yêu cầu quyền Admin.
    Phiên bản Safe-Unicode: Chống crash khi đường dẫn có Tiếng Việt.
    """
    try:
        # Kiểm tra quyền Admin
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        except:
            is_admin = False

        if is_admin:
            # Đã là admin -> Chạy tiếp
            return True
        else:
            # Chưa là admin -> Yêu cầu quyền
            
            # Lấy đường dẫn file thực thi (EXE hoặc PY)
            executable = sys.executable
            
            if getattr(sys, 'frozen', False):
                # Trường hợp chạy file .EXE
                # Chúng ta dùng chính file exe làm target
                target_exe = sys.executable
                params = "" # Không cần tham số phụ cho exe
                
                # Lấy thư mục làm việc (quan trọng để load file config)
                cwd = os.path.dirname(target_exe)
            else:
                # Trường hợp chạy file .PY (Dev)
                target_exe = sys.executable
                # Lấy đường dẫn script tuyệt đối
                script_path = os.path.abspath(sys.argv[0])
                # Bọc đường dẫn trong ngoặc kép để tránh lỗi khoảng trắng
                params = f'"{script_path}"'
                cwd = os.path.dirname(script_path)

            print("Dang yeu cau quyen Admin (Re-launching)...")
            
            # Sử dụng ShellExecuteW (W = Wide String = Hỗ trợ Unicode/Tiếng Việt)
            ret = ctypes.windll.shell32.ShellExecuteW(
                None, 
                "runas", 
                target_exe, 
                params, 
                cwd, 
                1
            )
            
            # Nếu người dùng bấm Yes (ret > 32), thoát app cũ
            # Nếu bấm No hoặc lỗi, ret <= 32
            if int(ret) > 32:
                sys.exit(0)
            else:
                # Người dùng bấm No hoặc lỗi
                return False
            
    except Exception as e:
        # Dùng try-except khi print lỗi để tránh crash chồng crash
        try:
            print(f"Loi khi xin quyen Admin: {e}")
        except:
            pass # Nếu print cũng lỗi thì bỏ qua luôn
        
        # Hiện popup báo lỗi (dùng tiếng Việt không dấu hoặc tiếng Anh để an toàn)
        try:
            ctypes.windll.user32.MessageBoxW(0, f"Khong the lay quyen Admin:\n{e}", "Loi Quyen", 0x10)
        except: pass
        
        return False

ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002
ABOVE_NORMAL_PRIORITY_CLASS = 0x00008000

def prevent_system_sleep_and_boost_priority():
    """
    1. Ngăn Windows tự ngủ khi đang tải.
    2. Tăng mức ưu tiên CPU để không bị bóp hiệu năng khi Minimize.
    """
    try:
        # --- 1. CẤM NGỦ (Keep Awake) ---
        # Báo cho Windows biết thread này đang làm việc quan trọng
        # ES_SYSTEM_REQUIRED: Máy không được Sleep
        # ES_DISPLAY_REQUIRED: Màn hình không được tắt (Tùy chọn, có thể bỏ nếu muốn tắt màn)
        ctypes.windll.kernel32.SetThreadExecutionState(
            ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
        )
        print("System Power: Đã bật chế độ 'Không Ngủ'.")

        # --- 2. TĂNG ƯU TIÊN (Boost Priority) ---
        # Lấy Process ID hiện tại
        app_process = ctypes.windll.kernel32.GetCurrentProcess()
        
        # Đặt mức ưu tiên là ABOVE_NORMAL (Cao hơn bình thường một chút)
        # Lưu ý: Không nên dùng HIGH_PRIORITY vì có thể làm đơ chuột máy tính yếu.
        ctypes.windll.kernel32.SetPriorityClass(app_process, ABOVE_NORMAL_PRIORITY_CLASS)
        
        print("System Priority: Đã tăng mức ưu tiên lên 'Above Normal'.")
        
    except Exception as e:
        print(f"Không thể set quyền ưu tiên: {e}")




def center_window_on_screen(window, width, height):
    """Tính toán và đặt Toplevel (cửa sổ con) vào giữa màn hình."""
    try:
        # Lấy kích thước màn hình
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()

        # Tính toán vị trí x, y để căn giữa
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)

        # Đặt kích thước VÀ vị trí cho cửa sổ
        window.geometry(f'{width}x{height}+{x}+{y}')
    except Exception as e:
        print(f"Lỗi khi căn giữa cửa sổ: {e}")
        # Fallback: nếu lỗi, chỉ đặt kích thước
        window.geometry(f'{width}x{height}')

def _show_custom_dialog(title, message, dialog_type="info", parent=None):
    """
    Hàm lõi để hiển thị popup tùy chỉnh.
    """
    # Use the passed parent, or the global root, or create a hidden temporary root if needed
    current_parent = parent if parent else root
    
    if current_parent is None:
        print("Error: Dialog called before root window created.")
        return None

    # 1. Biến lưu kết quả
    result = [None]
    
    # 2. Tạo cửa sổ
    dlg = tk.Toplevel(current_parent)
    dlg.title(title)
    
    # Kích thước & Căn giữa
    w, h = 400, 250 # Kích thước mặc định rộng hơn xíu cho đẹp
    center_window_on_screen(dlg, w, h)
    
    dlg.transient(parent if parent else root)
    dlg.grab_set()
    dlg.resizable(False, False)
    
    # Áp dụng Theme cho Titlebar
    dlg.after(10, lambda: apply_theme_to_titlebar(dlg))

    # 3. UI Nội dung
    main_frame = ttk.Frame(dlg, padding=20)
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Icon giả lập bằng Text (Hoặc bạn có thể load ảnh nếu muốn)
    icon_text = "ℹ️"
    icon_color = "white"
    
    if dialog_type == "error": 
        icon_text = "❌"
        icon_color = "#ff4d4d" # Đỏ
    elif dialog_type == "warning":
        icon_text = "⚠️"
        icon_color = "#ffcc00" # Vàng
    elif dialog_type == "yesno":
        icon_text = "❓"
        icon_color = "#4a90e2" # Xanh

    # Header (Icon + Title rút gọn hoặc Loại)
    header_frame = ttk.Frame(main_frame)
    header_frame.pack(fill=tk.X, pady=(0, 10))
    
    lbl_icon = tk.Label(header_frame, text=icon_text, font=("Segoe UI", 20), bg=style.lookup("TFrame", "background"), fg=icon_color)
    lbl_icon.pack(side=tk.LEFT, padx=(0, 10))
    
    # Nội dung tin nhắn
    lbl_msg = ttk.Label(
        main_frame, 
        text=message, 
        wraplength=350, 
        justify=tk.LEFT, 
        font=("Segoe UI", 10)
    )
    lbl_msg.pack(fill=tk.BOTH, expand=True)

    # 4. Nút bấm
    btn_frame = ttk.Frame(dlg, padding=10)
    btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

    def on_close(res):
        result[0] = res
        dlg.destroy()

    # Cấu hình nút theo loại dialog
    if dialog_type == "yesno":
        # Nút YES (Accent)
        btn_yes = ttk.Button(btn_frame, text="Có (Yes)", style="Accent.TButton", command=lambda: on_close(True))
        btn_yes.pack(side=tk.RIGHT, padx=5)
        # Nút NO (Thường)
        btn_no = ttk.Button(btn_frame, text="Không (No)", command=lambda: on_close(False))
        btn_no.pack(side=tk.RIGHT, padx=5)
        
    elif dialog_type == "error":
        # Nút Đóng (Danger hoặc Accent tùy ý, ở đây dùng Danger cho lỗi)
        btn_ok = ttk.Button(btn_frame, text="Đóng", style="Danger.TButton", command=lambda: on_close(None))
        btn_ok.pack(side=tk.RIGHT)
        
    else: # info, warning
        # Nút OK (Accent)
        btn_ok = ttk.Button(btn_frame, text="OK", style="Accent.TButton", command=lambda: on_close(None))
        btn_ok.pack(side=tk.RIGHT)

    # Xử lý phím Enter/Esc
    dlg.bind("<Return>", lambda e: on_close(True if dialog_type == "yesno" else None))
    dlg.bind("<Escape>", lambda e: on_close(False if dialog_type == "yesno" else None))

    # Chờ người dùng đóng
    root.wait_window(dlg)
    return result[0]

# --- CÁC HÀM WRAPPER (Dùng để thay thế messagebox) ---

def custom_showinfo(title, message, parent=None):
    _show_custom_dialog(title, message, "info", parent)

def custom_showwarning(title, message, parent=None):
    _show_custom_dialog(title, message, "warning", parent)

def custom_showerror(title, message, parent=None):
    _show_custom_dialog(title, message, "error", parent)

def custom_askyesno(title, message, parent=None):
    return _show_custom_dialog(title, message, "yesno", parent)

def custom_askstring(title, prompt, parent=None, show=None, initialvalue=None):
    current_parent = parent if parent else root
    if current_parent is None: return None

    # 1. Biến lưu kết quả
    result = [None]
    
    # 2. Tạo cửa sổ
    dlg = tk.Toplevel(current_parent)
    dlg.title(title)
    
    # Kích thước & Căn giữa
    w, h = 400, 210
    center_window_on_screen(dlg, w, h)
    
    dlg.transient(parent if parent else root)
    dlg.grab_set()
    dlg.resizable(False, False)
    
    # --- ÁP DỤNG THEME CHO TITLEBAR ---
    dlg.after(10, lambda: apply_theme_to_titlebar(dlg))
    # ----------------------------------

    # 3. UI Nội dung
    main_frame = ttk.Frame(dlg, padding=20)
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Label câu hỏi
    lbl_prompt = ttk.Label(main_frame, text=prompt, wraplength=360, justify=tk.LEFT)
    lbl_prompt.pack(fill=tk.X, pady=(0, 10))

    # Ô nhập liệu (Entry)
    entry = ttk.Entry(main_frame)
    
    # Xử lý hiển thị mật khẩu (dấu *)
    if show:
        entry.config(show=show)
        
    # Giá trị mặc định
    if initialvalue:
        entry.insert(0, initialvalue)
        
    entry.pack(fill=tk.X, pady=(0, 10))
    entry.focus_force() # Focus ngay vào ô nhập

    # 4. Nút bấm
    btn_frame = ttk.Frame(dlg, padding=10)
    btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

    def on_ok():
        val = entry.get()
        result[0] = val # Lưu kết quả
        dlg.destroy()

    def on_cancel():
        result[0] = None # Hủy bỏ
        dlg.destroy()

    # Nút OK (Accent)
    btn_ok = ttk.Button(btn_frame, text="OK", style="Accent.TButton", command=on_ok)
    btn_ok.pack(side=tk.RIGHT, padx=5)

    # Nút Cancel
    btn_cancel = ttk.Button(btn_frame, text="Hủy (Cancel)", command=on_cancel)
    btn_cancel.pack(side=tk.RIGHT, padx=5)

    # Phím tắt
    dlg.bind("<Return>", lambda e: on_ok())
    dlg.bind("<Escape>", lambda e: on_cancel())

    # Chờ đóng cửa sổ
    root.wait_window(dlg)
    
    return result[0]

def resource_path(relative_path):
    """ Lấy đường dẫn tuyệt đối, hoạt động cho cả .py và .exe """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)
# Thử tải logo cho splash (nếu lỗi thì bỏ qua)

g_translator_process = None # Lưu trữ tiến trình đang chạy

def start_translator_service():
    """Khởi động GameTranslator (Có gắn Job Object để tự sát khi App chính tắt)."""
    global g_translator_process
    
    if g_translator_process and g_translator_process.poll() is None:
        print("Magic Translator đang chạy.")
        return

    # 1. Xác định file (như cũ)
    is_frozen = getattr(sys, 'frozen', False)
    script_name = "GameTranslator.exe" if is_frozen else "GameTranslator.py"

    if is_frozen:
        source_path = os.path.join(sys._MEIPASS, script_name)
    else:
        source_path = os.path.join(os.getcwd(), script_name)

    if not os.path.exists(source_path):
        print(f"Lỗi: Không tìm thấy {source_path}")
        return

    try:
        print(f"Đang khởi động Translator...")
        
        # 2. Chạy tiến trình
        if is_frozen:
            g_translator_process = subprocess.Popen(
                [source_path], 
                creationflags=0x08000000,
                cwd=os.path.dirname(source_path)
            )
        else:
            g_translator_process = subprocess.Popen(
                [sys.executable, source_path],
                creationflags=0x08000000
            )

        # --- [MỚI] GẮN JOB OBJECT (CHỈ WINDOWS) ---
        # Cơ chế này ép buộc Windows: "Nếu App Cha chết, hãy giết ngay App Con"
        try:
            import ctypes
            from ctypes import wintypes
            
            # Tạo Job
            job_handle = ctypes.windll.kernel32.CreateJobObjectW(None, None)
            
            # Cấu hình: JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE (0x2000)
            # Khi handle của Job bị đóng (do App cha tắt), mọi process trong Job sẽ bị kill.
            JOBOBJECT_EXTENDED_LIMIT_INFORMATION = 9
            class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
                _fields_ = [('LimitFlags', wintypes.DWORD),
                            ('MinimumWorkingSetSize', ctypes.c_size_t),
                            ('MaximumWorkingSetSize', ctypes.c_size_t),
                            ('ActiveProcessLimit', wintypes.DWORD),
                            ('Affinity', ctypes.c_size_t),
                            ('PriorityClass', wintypes.DWORD),
                            ('SchedulingClass', wintypes.DWORD)]

            class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
                _fields_ = [('BasicLimitInformation', JOBOBJECT_BASIC_LIMIT_INFORMATION),
                            ('IoInfo', ctypes.c_void_p), # IO_COUNTERS (bỏ qua)
                            ('ProcessMemoryLimit', ctypes.c_size_t),
                            ('JobMemoryLimit', ctypes.c_size_t),
                            ('PeakProcessMemoryUsed', ctypes.c_size_t),
                            ('PeakJobMemoryUsed', ctypes.c_size_t)]

            info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
            info.BasicLimitInformation.LimitFlags = 0x2000 # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE

            # Set thông tin cho Job
            ctypes.windll.kernel32.SetInformationJobObject(
                job_handle,
                9, # JobObjectExtendedLimitInformation
                ctypes.byref(info),
                ctypes.sizeof(info)
            )

            # Gán tiến trình con vào Job này
            ctypes.windll.kernel32.AssignProcessToJobObject(
                job_handle,
                int(g_translator_process._handle)
            )
            
            # Lưu lại handle để nó không bị Python dọn dẹp (Garbage Collection)
            # Nếu biến này mất, Job sẽ đóng và giết process ngay lập tức -> Phải lưu toàn cục
            global g_translator_job_handle
            g_translator_job_handle = job_handle
            
            print("Đã gắn Job Object (Auto-Kill) thành công.")
            
        except Exception as e:
            print(f"Không thể gắn Job Object (Không sao, dùng taskkill vẫn ổn): {e}")
        # ------------------------------------------
            
    except Exception as e:
        print(f"Lỗi khởi động Translator: {e}")

def stop_translator_service():
    """Tắt tiến trình Translator (Sử dụng TASKKILL để diệt tận gốc)."""
    global g_translator_process
    
    if g_translator_process:
        print("Đang tắt Magic Translator...")
        try:
            # Lấy PID (Process ID) của tiến trình con
            pid = g_translator_process.pid
            
            # Dùng lệnh Windows để diệt:
            # /F: Force (Bắt buộc tắt)
            # /T: Tree (Tắt cả tiến trình con cháu của nó)
            # /PID: Theo mã số
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                capture_output=True, 
                creationflags=0x08000000 # Ẩn cửa sổ CMD
            )
        except Exception as e:
            print(f"Lỗi khi kill process: {e}")
            # Fallback: Thử dùng lệnh python thường nếu taskkill lỗi
            try: g_translator_process.kill()
            except: pass
            
        g_translator_process = None

class ProgressStream(io.FileIO):
    """
    Một lớp bao bọc (Wrapper) cho file stream.
    Nó tự động báo cáo tiến trình mỗi khi dữ liệu được đọc.
    """
    def __init__(self, path, callback, *args, **kwargs):
        super().__init__(path, *args, **kwargs)
        self.callback = callback
        self.total_size = os.path.getsize(path)
        self.uploaded_so_far = 0
        self.last_callback_time = 0

    def read(self, size=-1):
        # Gọi hàm read gốc để lấy dữ liệu
        data = super().read(size)
        
        if data:
            self.uploaded_so_far += len(data)
            
            # Giới hạn cập nhật UI mỗi 0.1 giây để không làm lag App
            # (Vẫn đủ nhanh để mắt thường thấy mượt)
            current_time = time.time()
            if current_time - self.last_callback_time > 0.1 or self.uploaded_so_far == self.total_size:
                self.callback(self.uploaded_so_far, self.total_size)
                self.last_callback_time = current_time
                
        return data
    
# --- THÊM MỚI: LỚP ĐẢM BẢO CHẠY 1 LẦN (SINGLETON) ---
class SingleInstance:
    """Sử dụng Mutex của Windows để đảm bảo chỉ có 1 instance của app chạy."""
    def __init__(self, mutex_name_bytes):
        self.mutex_name = mutex_name_bytes
        self.mutex = None
        ERROR_ALREADY_EXISTS = 183
        
        # 1. Tạo một mutex với tên duy nhất
        self.mutex = ctypes.windll.kernel32.CreateMutexA(
            None,           # Security attributes
            1,              # bInitialOwner
            self.mutex_name # Tên
        )
        
        # 2. Kiểm tra lỗi
        last_error = ctypes.windll.kernel32.GetLastError()
        
        # 3. Nếu lỗi "Đã Tồn Tại", thoát app
        if last_error == ERROR_ALREADY_EXISTS:
            print("Phát hiện app đã chạy. Thoát instance mới.")
            sys.exit(0)
    
    def __del__(self):
        # Hàm hủy an toàn: Bọc trong try-except và kiểm tra thư viện
        try:
            # Chỉ gọi lệnh nếu ctypes vẫn còn tồn tại (chưa bị Python dọn dẹp)
            if self.mutex and 'ctypes' in globals() and ctypes:
                ctypes.windll.kernel32.CloseHandle(self.mutex)
        except Exception:
            # Bỏ qua mọi lỗi khi tắt app (vì Windows sẽ tự dọn dẹp sau đó)
            pass



scan_loading_window = None
g_secret_click_count = 0
g_current_game_name = None
g_game_search_entry = None
g_game_grid_container = None
g_all_mods_flat = {}
g_game_themes = {}
global g_mod_buttons
g_mod_buttons = {}
global g_current_selected_key
g_current_selected_key = None
CURRENT_VERSION = "1.3.1"
EXPECTED_UPDATER_HASH = "6F5E4FDB65D1BFFE174DE56908614C44EB5C87D5178AF1BEE99931B05140D79D"
GIF_URL = "https://media3.giphy.com/media/v1.Y2lkPTZjMDliOTUyNmQ4bGtzOW15aDhqcGYzbmx2bjVwdzBxMzNtcDB6aG9oZDBpejdpcyZlcD12MV9zdGlja2Vyc19zZWFyY2gmY3Q9cw/MZ7yrimhG3DThJqHjl/200w.gif"
ROCKET_GIF_URL = "https://media.tenor.com/ike6N7DwCa0AAAAM/%D8%B1%D9%8A%D8%A7%D9%84-%D9%85%D8%AF%D8%B1%D9%8A%D8%AF.gif"
g_rocket_frames = []
g_rocket_raw_data = None
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1439922562422411387/dL6kx7UA7gde-gh4ChiVs_tw5M3XY9NVyDzergGTEQLnaPkRde65ymnrwtWo9bktoIxS"
SHARINGAN_GIF_URL = "https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/f99cb04a-9bec-4af9-b6fd-74056aa8c204/dfmjhu4-2acb26b5-b9be-4384-81dd-9da6e6cfe711.gif?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1cm46YXBwOjdlMGQxODg5ODIyNjQzNzNhNWYwZDQxNWVhMGQyNmUwIiwiaXNzIjoidXJuOmFwcDo3ZTBkMTg4OTgyMjY0MzczYTVmMGQ0MTVlYTBkMjZlMCIsIm9iaiI6W1t7InBhdGgiOiIvZi9mOTljYjA0YS05YmVjLTRhZjktYjZmZC03NDA1NmFhOGMyMDQvZGZtamh1NC0yYWNiMjZiNS1iOWJlLTQzODQtODFkZC05ZGE2ZTZjZmU3MTEuZ2lmIn1dXSwiYXVkIjpbInVybjpzZXJ2aWNlOmZpbGUuZG93bmxvYWQiXX0.TiTaTm-v-Z_zw6Q3OQPFUSLdKQlVjWYMkIMEdwBQza8"
CRACKED_GLASS_URL = "https://www.pngmart.com/files/19/Broken-Glass-Cracks-Transparent-PNG.png"
UPLOAD_CHUNK_SIZE = 100 * 1024 * 1024
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
    
# --- THÊM MỚI: LỚP HELPER ĐỂ TẠO TOOLTIP ---
class CreateToolTip(object):
    """
    Tạo một tooltip (chú thích) cho một widget.
    """
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.tooltip_window = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(500, self.showtip) # Chờ 500ms

    def unschedule(self):
        id = getattr(self, 'id', None)
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        
        # Tạo cửa sổ Toplevel
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True) # Xóa title bar
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(self.tooltip_window, text=self.text, justify='left',
                         background="#2b2b2b", foreground="white", relief='solid', borderwidth=1,
                         font=("Segoe UI", 9))
        label.pack(ipadx=4, ipady=4)

    def hidetip(self):
        tw = self.tooltip_window
        self.tooltip_window = None
        if tw:
            tw.destroy()


def check_for_updates(config_data):
    """
    So sánh phiên bản hiện tại, HIỂN THỊ POPUP VÀ BẮT BUỘC CẬP NHẬT.
    Trả về True nếu tìm thấy update, False nếu không.
    """
    try:
        updater_info = config_data.get("updater")
        if not updater_info: return False

        latest_version_str = updater_info.get("latest_version")
        if not latest_version_str: return False

        # So sánh phiên bản
        if version.parse(latest_version_str) > version.parse(CURRENT_VERSION):
            print(f"Phát hiện phiên bản mới: {latest_version_str}")

            notes = updater_info.get("release_notes", "Không có ghi chú.")
            url = updater_info.get("download_url") 

            if not url:
                print("Lỗi config: 'download_url' bị thiếu.")
                return False

            # --- SỬA: Thay đổi nội dung tin nhắn thành tin nhắn BẮT BUỘC ---
            message = (
                f"Đã có phiên bản mới: {latest_version_str}!\n"
                f"(Bạn đang dùng: {CURRENT_VERSION})\n\n"
                f"Ghi chú:\n{notes}\n\n"
                "Đây là bản cập nhật bắt buộc. Ứng dụng sẽ tự động cập nhật ngay bây giờ."
            )

            # --- SỬA: Thay 'custom_askyesno' bằng 'custom_showwarning' ---
            # Người dùng chỉ có thể bấm "OK"
            custom_showwarning("Chuẩn Bị Cập Nhật!", message)
            
            # --- SỬA: Xóa 'if' - Chạy logic cập nhật ngay lập tức ---
            try:
                main_app_path = sys.executable
                main_app_dir = os.path.dirname(main_app_path)
                updater_exe_path = os.path.join(main_app_dir, "updater.exe") 

                if not os.path.exists(updater_exe_path):
                    raise FileNotFoundError("Không tìm thấy file 'updater.exe'.")

                print("Đang xác thực file updater.exe...")
                is_valid, reason = verify_file_hash(updater_exe_path, EXPECTED_UPDATER_HASH)

                if not is_valid:
                    custom_showerror("Lỗi An Ninh", f"Không thể chạy trình cập nhật. Lý do: {reason}.")
                    webbrowser.open_new_tab(url)
                    return True # Vẫn trả về True vì đã tìm thấy

                print("Xác thực thành công. Bắt đầu chạy updater...")
                # (Chúng ta chạy updater và thoát ngay)
                subprocess.Popen([updater_exe_path, url, main_app_path])
                root.destroy()

            except Exception as e:
                # Nếu có lỗi khi chạy updater, mở link tải thủ công
                custom_showerror("Lỗi Cập Nhật", f"Không thể chạy updater: {e}\nSẽ mở link tải thủ công.")
                webbrowser.open_new_tab(url)
            
            return True # Đã tìm thấy update
            # --- HẾT SỬA ---

        else:
            print("Ứng dụng đã ở phiên bản mới nhất.")
            return False # Không tìm thấy update

    except Exception as e:
        print(f"Lỗi khi kiểm tra cập nhật: {e}")
        return False

def verify_file_hash(file_path, expected_hash):
    """Tính hash SHA-256 của file và so sánh với hash mong đợi."""
    if not os.path.exists(file_path):
        return False, "File không tồn tại"

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Đọc file theo từng khối để tránh tốn RAM
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        # Lấy hash đã tính (dạng chữ thường)
        calculated_hash = sha256_hash.hexdigest().lower()

        if calculated_hash == expected_hash.lower():
            return True, "Hash hợp lệ"
        else:
            print(f"CẢNH BÁO HASH: Hash mong đợi: {expected_hash.lower()}")
            print(f"CẢNH BÁO HASH: Hash tính được: {calculated_hash}")
            return False, "Hash không khớp (file giả mạo hoặc bị hỏng)"

    except Exception as e:
        print(f"Lỗi khi tính hash: {e}")
        return False, f"Lỗi đọc file: {e}"

# --- THÊM MỚI: HÀM TRÍCH XUẤT ID TỪ URL ---

def action_manual_check_for_updates():
    """(Nút bấm) Vô hiệu hóa nút và bắt đầu thread kiểm tra."""
    # Chắc chắn rằng nút tồn tại trước khi cấu hình
    if 'update_app_button' in globals():
        update_app_button.config(state=tk.DISABLED, text="Đang kiểm tra...")
    threading.Thread(target=manual_check_thread, daemon=True).start()

def manual_check_thread():
    """(Thread ngầm) Tải config và gửi về queue để xử lý."""
    try:
        config = load_config_from_github()
        progress_queue.put(("manual_update_check", config))
    except Exception as e:
        progress_queue.put(("manual_update_check_failed", str(e)))
# --- HẾT THÊM MỚI ---

def extract_gdrive_id_from_url(url):
    """Trích xuất File ID từ link Google Drive (uc?id=...)"""
    if not isinstance(url, str):
        return None
    # Tìm chuỗi ký tự sau 'id='
    match = re.search(r'id=([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1)

    # Nếu không tìm thấy, có thể người dùng đã nhập ID trực tiếp (như trong Tab 2)
    # Chúng ta kiểm tra xem nó có "trông giống" một ID không
    if "drive.google.com" not in url and "/" not in url and len(url) > 20:
        return url

    return None
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
g_cache_dir = os.path.join(config_folder, "img_cache")

def is_folder_excluded_from_defender(folder_path):
    """
    Kiểm tra xem folder_path (hoặc folder cha của nó) có nằm trong
    Exclusion List của Windows Defender không.
    YÊU CẦU: App phải chạy với quyền Admin.
    """
    import subprocess
    
    folder_path = os.path.abspath(folder_path).lower()
    
    try:
        # Lệnh PowerShell để lấy danh sách ExclusionPath
        cmd = ["powershell", "-NoProfile", "-Command", "Get-MpPreference | Select-Object -ExpandProperty ExclusionPath"]
        
        # Chạy lệnh và ẩn cửa sổ console (0x08000000)
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            creationflags=0x08000000,
            encoding='utf-8', # Hoặc 'cp437' nếu lỗi font
            errors='ignore'
        )
        
        if process.returncode != 0:
            print("Không thể đọc Defender Preference (Có thể thiếu quyền Admin).")
            return False

        # Lấy danh sách các đường dẫn đã loại trừ
        excluded_paths = process.stdout.strip().splitlines()
        
        # Chuẩn hóa và so sánh
        for excluded in excluded_paths:
            if not excluded.strip(): continue
            
            clean_excluded = os.path.abspath(excluded.strip()).lower()
            
            # Logic kiểm tra:
            # 1. Nếu folder đích CHÍNH LÀ folder loại trừ
            # 2. Hoặc folder đích nằm BÊN TRONG một folder loại trừ
            # (Dùng startswith để kiểm tra folder con)
            if folder_path == clean_excluded or folder_path.startswith(clean_excluded + os.sep):
                print(f"Phát hiện Exclusion hợp lệ: {clean_excluded}")
                return True
                
        return False

    except Exception as e:
        print(f"Lỗi khi kiểm tra Defender: {e}")
        return False

# --- Logic cho việc lưu/tải file config local ---
def load_local_config():
    """Tải config local (đã nâng cấp lên game_paths)."""
    try:
        os.makedirs(config_folder, exist_ok=True)
        os.makedirs(g_cache_dir, exist_ok=True)
        with open(config_file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            if "auto_start_translator" not in config:
                config["auto_start_translator"] = False
            # --- LOGIC NÂNG CẤP ---
            if "game_paths" not in config:
                config["game_paths"] = {}

            if "last_used_folder" not in config:
                # Thử migrate (di chuyển) từ key cũ
                config["last_used_folder"] = config.get("destination_folder", "")

            # Xóa key cũ (nếu có) để dọn dẹp
            config.pop("destination_folder", None)
            # --- HẾT LOGIC NÂNG CẤP ---

            # Đặt giá trị mặc định nếu thiếu
            if "installed_versions" not in config:
                config["installed_versions"] = {}
            if "backup_enabled" not in config:
                config["backup_enabled"] = False
            if "secret_exe_id" not in config:
                config["secret_exe_id"] = ""
            if "secret_zip_id" not in config:
                config["secret_zip_id"] = ""
            if "steam_path" not in config:
                config["steam_path"] = ""
            if "riot_path" not in config:
                config["riot_path"] = ""
            if "custom_games" not in config:
                config["custom_games"] = {}
            # [THÊM DÒNG NÀY] Lưu trữ ảnh thay thế cho game server
            if "theme_overrides" not in config:
                config["theme_overrides"] = {}
            if "display_name_overrides" not in config:
                config["display_name_overrides"] = {}

            return config
    except (FileNotFoundError, json.JSONDecodeError):
        # Trả về config mặc định (đã nâng cấp)
        return {
            "game_paths": {}, "installed_versions": {}, "backup_enabled": False, 
            "secret_exe_id": "", "secret_zip_id": "", "steam_path": "", "riot_path": "",
            "last_used_folder": "", # Thêm key mới
            "game_launchers": {}
        }

def save_local_config(config_data):
    try:
        os.makedirs(config_folder, exist_ok=True)
        with open(config_file_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4)
    except Exception as e:
        print(f"Cảnh báo: Không thể lưu config local: {e}")

def find_steam_path():
    """Quét Registry để tìm steam.exe."""
    try:
        # 1. Thử tìm key 64-bit
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")
    except FileNotFoundError:
        try:
            # 2. Nếu không thấy, thử key 32-bit
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam")
        except FileNotFoundError:
            print("Không tìm thấy Steam trong Registry.")
            return None
    
    try:
        # 3. Lấy giá trị 'InstallPath'
        install_path, _ = winreg.QueryValueEx(key, "InstallPath")
        exe_path = os.path.join(install_path, "steam.exe")
        
        if os.path.exists(exe_path):
            print(f"Đã tự động tìm thấy Steam: {exe_path}")
            return exe_path
        else:
            print("Tìm thấy InstallPath của Steam nhưng không thấy steam.exe.")
            return None
    except Exception as e:
        print(f"Lỗi khi đọc giá trị Registry của Steam: {e}")
        return None
    finally:
        winreg.CloseKey(key)

def find_shortcut_target(search_dir, shortcut_name):
    """
    (Hàm helper) Tìm đệ quy trong một thư mục cho một shortcut 
    và trả về đường dẫn .exe nếu nó trỏ đến RiotClientServices.exe
    """
    try:
        # Dùng os.walk để tìm đệ quy
        for root, dirs, files in os.walk(search_dir):
            for file in files:
                if file.lower() == shortcut_name.lower():
                    # Tìm thấy file shortcut (ví dụ: "Riot Client.lnk")
                    shortcut_path = os.path.join(root, file)
                    try:
                        # Dùng winshell để đọc file
                        shortcut = winshell.shortcut(shortcut_path)
                        target_path = shortcut.path # Đây là file .exe
                        
                        # KIỂM TRA QUAN TRỌNG:
                        # Đảm bảo file .exe này là file chúng ta cần
                        if target_path and os.path.basename(target_path).lower() == "riotclientservices.exe" and os.path.exists(target_path):
                            print(f"Tìm thấy shortcut tại: {shortcut_path}")
                            print(f"Shortcut trỏ đến: {target_path}")
                            return target_path
                    except Exception as e:
                        print(f"Lỗi khi đọc shortcut {shortcut_path}: {e}")
    except Exception as e:
        print(f"Lỗi khi quét thư mục {search_dir}: {e}")
    return None

def find_riot_path():
    """
    Quét Registry, file config VÀ SHORTCUT để tìm RiotClientServices.exe (Thử 5 phương pháp).
    """
    
    # --- PHƯƠNG PHÁP 1: TÌM TRONG "UNINSTALL" (Registry HKLM) ---
    try:
        key_path = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Riot Game "Riot Client"'
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
        try:
            install_location, _ = winreg.QueryValueEx(key, "InstallLocation")
            target_exe_path = os.path.join(install_location, "RiotClientServices.exe")
            if os.path.exists(target_exe_path):
                print(f"Đã tự động tìm thấy Riot (Method 1): {target_exe_path}")
                winreg.CloseKey(key)
                return target_exe_path
        except Exception: pass
        finally: winreg.CloseKey(key)
    except FileNotFoundError: print("Không tìm thấy Riot Client (Method 1). Đang thử Method 2...")
    except Exception: pass

    # --- PHƯƠNG PHÁP 2: TÌM TRONG KEY "Riot Games" (Registry HKLM) ---
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Riot Games\Riot Client")
        try:
            path_bytes, _ = winreg.QueryValueEx(key, "Path")
            install_json_path = os.path.normpath(path_bytes)
            install_folder = os.path.dirname(install_json_path)
            target_exe_path = os.path.join(install_folder, "RiotClientServices.exe")
            if os.path.exists(target_exe_path):
                print(f"Đã tự động tìm thấy Riot (Method 2): {target_exe_path}")
                winreg.CloseKey(key)
                return target_exe_path
        except Exception: pass
        finally: winreg.CloseKey(key)
    except FileNotFoundError: print("Không tìm thấy Riot Client (Method 2). Đang thử Method 3...")
    except Exception: pass

    # --- PHƯƠNG PHÁP 3: ĐỌC FILE CONFIG CỦA USER (LOCALAPPDATA) ---
    try:
        local_app_data = os.getenv('LOCALAPPDATA')
        if local_app_data:
            config_file_path = os.path.join(local_app_data, 'Riot Games', 'Riot Client', 'Data', 'RiotClientInstalls.json')
            if os.path.exists(config_file_path):
                with open(config_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    install_folder = data.get('rc_default') or data.get('rc_live')
                    if install_folder and os.path.isdir(install_folder):
                        target_exe_path = os.path.join(install_folder, "RiotClientServices.exe")
                        if os.path.exists(target_exe_path):
                            print(f"Đã tự động tìm thấy Riot (Method 3): {target_exe_path}")
                            return target_exe_path
            else: print(f"Không tìm thấy file config (Method 3) tại: {config_file_path}")
    except Exception as e: print(f"Lỗi khi thực hiện Method 3: {e}")
    print("Đang thử Method 4...")

    # --- PHƯƠNG PHÁP 4: ĐỌC FILE CONFIG TỪ PROGRAMDATA (ALL USERS) ---
    try:
        program_data = os.getenv('PROGRAMDATA')
        if program_data:
            config_file_path = os.path.join(program_data, 'Riot Games', 'RiotClientInstalls.json')
            if os.path.exists(config_file_path):
                with open(config_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    install_folder = data.get('rc_default') or data.get('rc_live')
                    if install_folder and os.path.isdir(install_folder):
                        target_exe_path = os.path.join(install_folder, "RiotClientServices.exe")
                        if os.path.exists(target_exe_path):
                            print(f"Đã tự động tìm thấy Riot (Method 4): {target_exe_path}")
                            return target_exe_path
            else: print(f"Không tìm thấy file config (Method 4) tại: {config_file_path}")
    except Exception as e: print(f"Lỗi khi thực hiện Method 4: {e}")
    print("Đang thử Method 5...")

    # --- PHƯƠNG PHÁP 5: TÌM SHORTCUT TRONG START MENU VÀ DESKTOP ---
    try:
        # Các vị trí phổ biến để tìm shortcut
        search_locations = [
            os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs'), # User Start Menu
            os.path.join(os.getenv('PROGRAMDATA'), r'Microsoft\Windows\Start Menu\Programs'), # All Users Start Menu
            os.path.join(os.getenv('USERPROFILE'), r'Desktop'), # User Desktop
            os.path.join(os.getenv('PUBLIC'), r'Desktop') # Public Desktop
        ]
        
        # Tên file shortcut (thường là thế này)
        shortcut_to_find = "Riot Client.lnk"
        
        for location in search_locations:
            print(f"Đang quét shortcut trong: {location}")
            found_path = find_shortcut_target(location, shortcut_to_find)
            if found_path:
                print(f"Đã tự động tìm thấy Riot (Method 5): {found_path}")
                return found_path
                
    except Exception as e:
        print(f"Lỗi khi thực hiện Method 5 (Tìm Shortcut): {e}")

    # --- NẾU CẢ 5 PHƯƠNG PHÁP ĐỀU THẤT BẠI ---
    print("Đã thử cả 5 phương pháp nhưng không tìm thấy Riot Client.")
    return None

def auto_find_paths_thread():
    """
    (CHẠY NGẦM) Tự động tìm Steam và Riot.
    Gửi kết quả về progress_queue để xử lý an toàn.
    """
    
    # --- SỬA LỖI: KHỞI TẠO COM TRƯỚC KHI DÙNG WINSHELL ---
    try:
        pythoncom.CoInitialize()
    except Exception as e:
        print(f"Cảnh báo: Không thể CoInitialize(): {e}")
    # --- HẾT SỬA ---

    steam_path = find_steam_path()
    if steam_path:
        progress_queue.put(("steam_path_found", steam_path))
        
    riot_path = find_riot_path()
    if riot_path:
        progress_queue.put(("riot_path_found", riot_path))

local_config = load_local_config()


# DÁN CODE NÀY ĐÈ LÊN HÀM 'launch_riot_login_thread' CŨ CỦA BẠN
# (Từ dòng 746 đến 918)

def launch_riot_login_thread(riot_client_path, username, password):
    """
    (CHẠY TRONG THREAD)
    Kiểm tra focus liên tục VÀ CHỜ FORM SẴN SÀNG trước khi gõ phím.
    """
    
    try:
        # --- BƯỚC 1 & 2: TẮT CLIENT VÀ XÓA TOKEN (Như cũ) ---
        progress_queue.put(("login_status_update", "Đang tắt Riot Client..."))
        CREATE_NO_WINDOW = 0x08000000
        subprocess.run(
            ["taskkill", "/F", "/IM", "RiotClientServices.exe"],
            capture_output=True, text=True,
            creationflags=CREATE_NO_WINDOW
        )
        subprocess.run(
            ["taskkill", "/F", "/IM", "RiotClientUx.exe"],
            capture_output=True, text=True,
            creationflags=CREATE_NO_WINDOW
        )
        
        progress_queue.put(("login_status_update", "Đang xóa token đăng nhập..."))
        try:
            local_app_data = os.getenv('LOCALAPPDATA')
            if local_app_data:
                settings_file_path = os.path.join(
                    local_app_data, 'Riot Games', 'Riot Client', 
                    'Data', 'RiotClientPrivateSettings.yaml'
                )
                if os.path.exists(settings_file_path):
                    os.remove(settings_file_path)
            else:
                 progress_queue.put(("login_status_update", "Lỗi: Không tìm thấy LOCALAPPDATA"))
        except Exception as e:
            progress_queue.put(("login_status_update", "Lỗi: Không thể xóa token."))
        
        time.sleep(2)
        
        # --- BƯỚC 3: KHỞI ĐỘNG LẠI (Như cũ) ---
        progress_queue.put(("login_status_update", "Đang khởi động Riot Client..."))
        subprocess.Popen([riot_client_path])
        
        # --- BƯỚC 4: CHỜ THÔNG MINH (Như cũ) ---
        timeout_seconds = 30
        start_time = time.time()
        riot_window = None
        
        progress_queue.put(("login_status_update", f"Đang chờ cửa sổ Riot..."))
        
        while True:
            windows = gw.getWindowsWithTitle('Riot Client')
            if windows:
                riot_window = windows[0]
                progress_queue.put(("login_status_update", "Đã tìm thấy cửa sổ!"))
                break 
            if time.time() - start_time > timeout_seconds:
                progress_queue.put(("login_status_hide", "Lỗi: Hết thời gian chờ Riot Client."))
                return 

            time.sleep(0.5)
        
        # --- BƯỚC 5: TỰ ĐỘNG HÓA (ĐÃ CẬP NHẬT) ---
        try:
            from pywinauto.application import Application
            # --- BƯỚC 5A: LƯU CLIPBOARD GỐC (Như cũ) ---
            try:
                original_clipboard = pyperclip.paste()
            except Exception as e:
                print(f"Cảnh báo: Không thể đọc clipboard: {e}")
                
            progress_queue.put(("login_status_update", "Đang focus cửa sổ (API v3)..."))
            
            try:
                hwnd = riot_window._hWnd 

                SW_RESTORE = 9 # Hiển thị lại cửa sổ đã minimize
                
                # --- VÒNG LẶP KIỂM TRA FOCUS (Như cũ) ---
                start_time = time.time()
                while True:
                    is_minimized = ctypes.windll.user32.IsIconic(hwnd)
                    
                    if is_minimized:
                        print("API: Phát hiện minimize. Đang Restore (SW_RESTORE)...")
                        ctypes.windll.user32.ShowWindow(hwnd, SW_RESTORE)
                        time.sleep(0.5) 
                    
                    print("API: Đang SetForegroundWindow...")
                    ctypes.windll.user32.SetForegroundWindow(hwnd)
                    time.sleep(0.5)
                    
                    current_focus_hwnd = ctypes.windll.user32.GetForegroundWindow()
                    
                    if hwnd == current_focus_hwnd:
                        print("API: Focus thành công! (HWND trùng khớp)")
                        break
                    
                    if time.time() - start_time > 3.0:
                        print("API CẢNH BÁO: Hết thời gian chờ focus (3s).")
                        break 
                        
                    print("API: Cửa sổ chưa focus, đang thử lại...")

            except Exception as e:
                # Fallback (Như cũ)
                print(f"Lỗi khi dùng ctypes focus: {e}. Quay lại dùng pygetwindow...")
                if riot_window.isMinimized:
                    riot_window.restore()
                else:
                    riot_window.activate()
                time.sleep(1.0)
                # Lấy lại HWND sau khi fallback
                hwnd = riot_window._hWnd 

            # --- *** BƯỚC 5B: (MỚI) CHỜ FORM LOGIN SẴN SÀNG *** ---
            try:
                progress_queue.put(("login_status_update", "Đang kết nối với UI..."))
                # 1. Kết nối pywinauto với cửa sổ Riot mà pygetwindow tìm thấy
                # (Chúng ta dùng backend="uia" vì nó hiện đại, tốt cho app như Riot)
                app = Application(backend="uia").connect(handle=riot_window._hWnd, timeout=20)
                
                # 2. Lấy đối tượng cửa sổ
                dlg = app.window(handle=riot_window._hWnd)
                
                progress_queue.put(("login_status_update", "Đang chờ form login..."))
                
                # 3. Chờ cho đến khi label "TÊN NGƯỜI DÙNG" xuất hiện (tối đa 20s)
                # (Dựa trên ảnh screenshot của bạn)
                login_label = dlg.child_window(title="TÊN NGƯỜI DÙNG", control_type="Text")
                login_label.wait('visible', timeout=20) 
                
                progress_queue.put(("login_status_update", "Form đã sẵn sàng!"))
                
            except Exception as e:
                # Nếu hết 20s mà không tìm thấy, báo lỗi và hủy
                print(f"Lỗi pywinauto: {e}")
                progress_queue.put(("login_status_hide", f"Lỗi: Hết thời gian chờ form login ({e})"))
                return

            # --- BƯỚC 5C: TỰ ĐỘNG HÓA (Đã tối ưu) ---

            # --- KIỂM TRA FOCUS (LẦN 1) ---
            # (Kiểm tra này vẫn cần thiết, đề phòng người dùng click ra ngoài)
            progress_queue.put(("login_status_update", "Kiểm tra focus API... (1/3)"))
            is_minimized_check1 = ctypes.windll.user32.IsIconic(hwnd)
            current_focus_check1 = ctypes.windll.user32.GetForegroundWindow()
            if is_minimized_check1 or current_focus_check1 != hwnd:
                raise Exception("Cửa sổ mất focus. Hủy đăng nhập. (Code 1)")
            
            # --- SỬA: DÙNG PASTE USERNAME (Như cũ) ---
            progress_queue.put(("login_status_update", "Đang gõ username..."))
            # Gõ từng phím với khoảng trễ 0.05s để đảm bảo client nhận kịp
            pyautogui.typewrite(username, interval=0.05) 
            time.sleep(0.5)
            # Chờ client xử lý 'tab' (giữ nguyên)
            pyautogui.press('tab')

            # --- KIỂM TRA FOCUS (LẦN 2) ---
            progress_queue.put(("login_status_update", "Kiểm tra focus API... (2/3)"))
            is_minimized_check2 = ctypes.windll.user32.IsIconic(hwnd)
            current_focus_check2 = ctypes.windll.user32.GetForegroundWindow()
            if is_minimized_check2 or current_focus_check2 != hwnd:
                raise Exception("Cửa sổ mất focus. Hủy đăng nhập. (Code 2)")

            # --- SỬA: DÙNG PASTE PASSWORD (Như cũ) ---
            progress_queue.put(("login_status_update", "Đang gõ password..."))
            pyautogui.typewrite(password, interval=0.05)
            
            # time.sleep(0.2) # <-- ĐÃ XÓA: Không cần thiết

            # --- KIỂM TRA FOCUS (LẦN 3) ---
            progress_queue.put(("login_status_update", "Kiểm tra focus API... (3/3)"))
            is_minimized_check3 = ctypes.windll.user32.IsIconic(hwnd)
            current_focus_check3 = ctypes.windll.user32.GetForegroundWindow()
            if is_minimized_check3 or current_focus_check3 != hwnd:
                raise Exception("Cửa sổ mất focus. Hủy đăng nhập. (Code 3)")

            pyautogui.press('enter')
            
            progress_queue.put(("login_status_update", "Hoàn tất! Đang chờ..."))
            time.sleep(3) # Giữ lại sleep 3s *SAU KHI ENTER* để chờ login

        finally:
            # === BƯỚC 5D: KHÔI PHỤC CLIPBOARD VÀ ẨN POPUP (Như cũ) ===
            try:
                pyperclip.copy(original_clipboard)
            except Exception as e:
                 print(f"Cảnh báo: Không thể khôi phục clipboard: {e}")
                 
            progress_queue.put(("login_status_hide", None))

    except Exception as e:
        # Bắt lỗi từ 'raise Exception' hoặc bất kỳ lỗi nào khác
        print(f"Lỗi không xác định trong launch_riot_login_thread: {e}")
        progress_queue.put(("login_status_hide", f"Đã hủy: {e}"))


def load_accounts_from_drive_thread():
    """
    (CHẠY NGẦM) Tải, và TỰ ĐỘNG DI CHUYỂN data cũ.
    """
    global drive_service, g_user_accounts_data, g_user_accounts_file_id
    global g_accounts_loaded

    if g_accounts_loaded:
        print("Config account đã được tải. Bỏ qua.")
        return

    if not drive_service:
        print("Lỗi: Không thể tải config account vì chưa đăng nhập Drive.")
        return

    try:
        print(f"Đang tìm file config account: {ACCOUNT_CONFIG_FILENAME}...")
        
        query = f"name = '{ACCOUNT_CONFIG_FILENAME}' and '{GOOGLE_DRIVE_FOLDER_ID}' in parents and trashed = false"
        response = drive_service.files().list(
            q=query, spaces='drive', fields='files(id, name)'
        ).execute()
        files = response.get('files', [])

        if files:
            file_info = files[0]
            g_user_accounts_file_id = file_info['id']
            print(f"Tìm thấy config: {g_user_accounts_file_id}. Đang tải nội dung...")
            
            request = drive_service.files().get_media(fileId=g_user_accounts_file_id)
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                if status:
                    print(f"Đang tải config account: {int(status.progress() * 100)}%")

            print("Tải config account hoàn tất.")
            
            try:
                # 1. Tải raw data
                raw_data = json.loads(file_content.getvalue().decode('utf-8'))
                
                # --- LOGIC DI CHUYỂN (MỚI) ---
                is_old_structure = False
                if raw_data: # Kiểm tra xem có rỗng không
                    first_key = next(iter(raw_data.keys()))
                    # Nếu key là "Steam" hoặc "Riot", đây là cấu trúc cũ
                    if first_key == "Steam" or first_key == "Riot":
                        is_old_structure = True
                
                if is_old_structure:
                    print("Phát hiện cấu trúc data cũ (theo Dịch vụ). Đang di chuyển...")
                    # 2. Gọi hàm di chuyển
                    g_user_accounts_data = migrate_data_to_game_keys(raw_data)
                    
                    # 3. Tự động lưu lại cấu trúc mới (chỉ 1 lần)
                    print("Di chuyển hoàn tất. Đang tự động lưu cấu trúc mới lên Drive...")
                    threading.Thread(target=save_accounts_to_drive_thread, daemon=True).start()
                else:
                    # Nếu cấu trúc đã đúng (key là Game), gán bình thường
                    g_user_accounts_data = raw_data
                # --- HẾT LOGIC DI CHUYỂN ---

            except json.JSONDecodeError:
                print("Lỗi: File config trên Drive bị hỏng (JSON Lỗi). Dùng dict rỗng.")
                g_user_accounts_data = {}

        else:
            # (Code tạo file mới không đổi)
            print("Không tìm thấy config. Đang tạo file mới trên Drive...")
            g_user_accounts_data = {}
            new_file_id = create_empty_account_file_on_drive()
            if new_file_id:
                g_user_accounts_file_id = new_file_id
                print(f"Đã tạo file mới với ID: {g_user_accounts_file_id}")
            else:
                print("LỖI NGHIÊM TRỌNG: Không thể tạo file config mới.")
                return

        mark_accounts_as_saved()

        g_accounts_loaded = True
        progress_queue.put(("accounts_loaded", None))

    except Exception as e:
        print(f"Lỗi nghiêm trọng khi tải/tạo config account: {e}")
        custom_showerror("Lỗi Tải Account", f"Không thể tải file config account: {e}")
        progress_queue.put(("accounts_load_failed", str(e)))

def create_empty_account_file_on_drive():
    """Tạo file JSON rỗng (nội dung "{}") trên Drive và trả về ID."""
    try:
        file_metadata = {
            'name': ACCOUNT_CONFIG_FILENAME,
            'parents': [GOOGLE_DRIVE_FOLDER_ID]
        }
        # Tạo nội dung rỗng (empty JSON object)
        empty_content = "{}"
        media = MediaFileUpload(
            io.BytesIO(empty_content.encode('utf-8')), 
            mimetype='application/json',
            resumable=False
        )
        
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        return file.get('id')
    except Exception as e:
        print(f"Lỗi khi tạo file rỗng: {e}")
        return None

def save_accounts_to_drive_thread():
    """
    (CHẠY NGẦM) Upload (ghi đè) file 'wgz_user_accounts.json'.
    (ĐÃ SỬA LỖI 200 OK)
    """
    global drive_service, g_user_accounts_data, g_user_accounts_file_id
    
    if not drive_service or not g_user_accounts_file_id:
        print("Lỗi: Không thể lưu config (chưa đăng nhập hoặc chưa có File ID)")
        progress_queue.put(("account_save_status", ("Lỗi: Chưa đăng nhập!", "Red.TLabel")))
        return

    # Gửi tin nhắn "Đang lưu..."
    progress_queue.put(("account_save_status", ("Đang lưu...", "White.TLabel")))
    
    try:
        # 1. Chuyển dict thành chuỗi JSON
        if 'g_acct_page_2_save_btn' in globals() and g_acct_page_2_save_btn:
            g_acct_page_2_save_btn.config(state=tk.DISABLED)
        json_string = json.dumps(g_user_accounts_data, indent=4, ensure_ascii=False)
        
        # 2. Chuẩn bị file media (DÙNG MediaIoBaseUpload)
        fh = io.BytesIO(json_string.encode('utf-8'))
        media = MediaIoBaseUpload(
            fh, 
            mimetype='application/json',
            resumable=True
        )
        
        # --- SỬA LỖI: DÙNG VÒNG LẶP next_chunk() THAY VÌ .execute() ---
        
        # 3. Chuẩn bị request (chỉ .update())
        request = drive_service.files().update(
            fileId=g_user_accounts_file_id,
            media_body=media,
            fields='id'
        )

        # 4. Thực thi upload bằng vòng lặp
        response = None
        while response is None:
            # status: chứa tiến trình; response: chứa kết quả khi hoàn thành
            # (Chúng ta không cần báo % ở đây, chỉ cần chạy cho đến khi xong)
            status, response = request.next_chunk()

        # 5. Xử lý khi hoàn thành
        if response:
            print(f"Đã lưu config account lên Drive (ID: {g_user_accounts_file_id})")
            # Gửi tin nhắn "Đã lưu!" và ẩn đi sau 3 giây
            progress_queue.put(("account_save_status", ("Đã lưu!", "Green.TLabel")))
            mark_accounts_as_saved()
        else:
            # Lỗi không xác định
            raise Exception("Lỗi: Upload hoàn tất nhưng không có phản hồi.")
        # --- HẾT SỬA LỖI ---
        
    except Exception as e:
        print(f"Lỗi nghiêm trọng khi lưu config account: {e}")
        progress_queue.put(("account_save_status", (f"Lỗi: {e}", "Red.TLabel")))
        if 'g_acct_page_2_save_btn' in globals() and g_acct_page_2_save_btn:
            g_acct_page_2_save_btn.config(state=tk.NORMAL)


def migrate_data_to_game_keys(old_data):
    """
    (HÀM MỚI)
    Chuyển đổi cấu trúc data từ {Service: [Accounts]} sang {Game: [Accounts]}.
    """
    print("Đang chạy logic di chuyển (migration) dữ liệu...")
    new_data = {}
    
    # Lặp qua cấu trúc cũ (ví dụ: key="Steam", accounts_list=[...])
    for service_name, accounts_list in old_data.items():
        for acc_info in accounts_list:
            # Lấy "game" (tag) đã lưu (ví dụ: "Elden Ring")
            game_tag = acc_info.get("game")
            
            # Key mới sẽ là "game_tag"
            key_to_use = game_tag
            
            if not key_to_use:
                # Nếu tài khoản không có tag "game",
                # dùng Dịch vụ (Steam/Riot) làm key dự phòng
                key_to_use = service_name
                
                # Cập nhật lại acc_info để nó tự gán game
                acc_info["game"] = service_name

            # Thêm tài khoản vào key mới
            # (ví dụ: new_data["Elden Ring"].append(acc_info))
            new_data.setdefault(key_to_use, []).append(acc_info)
            
    print(f"Di chuyển hoàn tất. Data mới có {len(new_data)} keys (games).")
    return new_data

# --- THÊM CÁC HÀM GITHUB ---
def get_github_token():
    """Đọc token từ file local."""
    try:
        token_path = resource_path(GITHUB_TOKEN_FILE)
        with open(token_path, 'r') as f:
            token = f.read().strip()
            if not token:
                 custom_showerror("Lỗi Token", f"File '{GITHUB_TOKEN_FILE}' rỗng.")
                 return None
            return token
    except FileNotFoundError:
        custom_showerror("Lỗi Token", f"Không tìm thấy file '{GITHUB_TOKEN_FILE}'. Vui lòng tạo file này và dán Personal Access Token vào.")
        return None
    except Exception as e:
         custom_showerror("Lỗi Token", f"Không thể đọc token: {e}")
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
        custom_showerror("Lỗi GitHub", f"Không thể kết nối hoặc tìm repo:\n{e.data.get('message', str(e))}")
        return None
    except Exception as e:
         custom_showerror("Lỗi GitHub", f"Lỗi không xác định khi kết nối GitHub: {e}")
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
            custom_showerror("Lỗi GitHub", f"Không tìm thấy file '{GITHUB_FILE_PATH}' trên nhánh '{GITHUB_BRANCH}'.")
        else:
            custom_showerror("Lỗi GitHub", f"Không thể tải file JSON từ GitHub:\n{e.data.get('message', str(e))}")
        return None, None
    except Exception as e:
         custom_showerror("Lỗi GitHub", f"Lỗi không xác định khi tải JSON: {e}")
         return None, None

# --- THÊM MỚI: HÀM TẢI THEME JSON ---
def load_theme_json_from_github_api(repo):
    """Tải nội dung JSON và SHA của file game_themes.json."""
    if not repo: return None, None
    print(f"Đang tải game_themes.json từ repo...")
    try:
        # Sửa file path
        contents = repo.get_contents("game_themes.json", ref=GITHUB_BRANCH) 
        content_str = base64.b64decode(contents.content).decode('utf-8')
        print(f"Tải theme thành công. SHA: {contents.sha}")
        return content_str, contents.sha
    except GithubException as e:
        if e.status == 404:
            custom_showerror("Lỗi GitHub", f"Không tìm thấy file 'game_themes.json'.")
        else:
            custom_showerror("Lỗi GitHub", f"Không thể tải file theme JSON: {e}")
        return None, None
    except Exception as e:
         custom_showerror("Lỗi GitHub", f"Lỗi không xác định khi tải theme JSON: {e}")
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
                    custom_showinfo("Thông báo", "Nội dung config không thay đổi. Bỏ qua upload.")
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
                 custom_showinfo("Thành công", "Đã cập nhật file JSON lên database thành công!")
                 return True, new_file_sha # Return success and the new file SHA
            except Exception as sha_error:
                 print(f"Lỗi khi lấy SHA mới của file sau update: {sha_error}")
                 custom_showinfo("Thành công", "Đã cập nhật file JSON lên Database! (Không thể lấy SHA mới)")
                 return True, None # Indicate success but SHA is unknown

    except GithubException as e:
        if e.status == 409:
             custom_showerror("Lỗi GitHub Upload (409)", "File trên GitHub đã bị thay đổi kể từ lần bạn tải về.\nVui lòng 'Tải Config (Làm mới)' để lấy phiên bản mới nhất trước khi upload.")
        else:
            custom_showerror("Lỗi GitHub Upload", f"Không thể cập nhật file:\n{e.data.get('message', str(e))}")
        return False, None
    except Exception as e:
         custom_showerror("Lỗi GitHub Upload", f"Lỗi không xác định khi upload: {e}")
         return False, None
# --- Hết hàm GitHub ---

# --- THÊM MỚI: HÀM UPLOAD THEME JSON ---
def upload_theme_json_to_github(repo, theme_dict_to_upload, current_sha):
    """Uploads the updated THEME dictionary to GitHub."""
    if not repo: return False, None

    # Convert dict to formatted JSON string
    json_string_to_upload = json.dumps(theme_dict_to_upload, indent=4, ensure_ascii=False)

    print(f"Chuẩn bị upload lên game_themes.json với SHA: {current_sha}")
    try:
        commit_message = f"Update game_themes.json via Updater Tool"

        # Tải nội dung hiện tại để so sánh
        current_content_str, _ = load_theme_json_from_github_api(repo)
        needs_upload = True
        if current_content_str:
            try:
                current_obj = json.loads(current_content_str)
                if current_obj == theme_dict_to_upload:
                    print("Theme config không thay đổi. Bỏ qua upload.")
                    needs_upload = False
                    return True, current_sha
            except json.JSONDecodeError: pass

        if needs_upload:
            update_result = repo.update_file(
                path="game_themes.json", # <-- SỬA FILE PATH
                message=commit_message,
                content=json_string_to_upload,
                sha=current_sha,
                branch=GITHUB_BRANCH,
            )

            # Lấy SHA mới của file
            updated_contents = repo.get_contents("game_themes.json", ref=GITHUB_BRANCH)
            new_file_sha = updated_contents.sha
            print(f"New theme file SHA: {new_file_sha}")
            return True, new_file_sha

    except GithubException as e:
        if e.status == 409:
             custom_showerror("Lỗi GitHub Upload (409)", "File theme trên GitHub đã bị thay đổi.\nHãy 'Tải Config (Làm mới)' lại Tab 2.")
        else:
             custom_showerror("Lỗi GitHub Upload", f"Không thể cập nhật file theme:\n{e}")
        return False, None
    except Exception as e:
         custom_showerror("Lỗi GitHub Upload", f"Lỗi không xác định khi upload theme: {e}")
         return False, None

# --- THÊM CÁC HÀM XỬ LÝ GOOGLE DRIVE ---

# Biến này sẽ lưu trữ dịch vụ Google Drive sau khi đăng nhập
drive_service = None
# Phạm vi (quyền) mà chúng ta yêu cầu: chỉ upload file
SCOPES = ['https://www.googleapis.com/auth/drive']

GOOGLE_DRIVE_FOLDER_ID = "1lO7qc485mhdLpirFgyhqMGKXAQvHoQYA"
ACCOUNT_CONFIG_FILENAME = "wgz_user_accounts.json"

def authenticate_google_drive():
    """Xác thực với Google Drive và trả về đối tượng service."""
    global drive_service
    creds = None
    
    # File token.json lưu trữ thông tin đăng nhập của người dùng.
    # Nó được tạo tự động sau lần đăng nhập đầu tiên.
    token_path = resource_path('token.json')
    creds_path = resource_path('credentials.json') # File bạn tải ở Bước 2
    
    if not os.path.exists(creds_path):
        custom_showerror("Lỗi Thiết Lập", "Không tìm thấy file 'credentials.json'.\nVui lòng làm theo Bước 2 trong hướng dẫn.")
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
                custom_showerror("Lỗi Đăng Nhập", f"Không thể lấy thông tin xác thực: {e}")
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
        custom_showerror("Lỗi API", f"Lỗi khi xây dựng dịch vụ Drive: {error}")
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
        media = MediaFileUpload(file_path, chunksize=UPLOAD_CHUNK_SIZE, resumable=True)
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

def download_via_api_logic(file_id, dest_path):
    """
    Phiên bản Racing: Tải Direct Stream bằng AuthorizedSession (requests).
    Tốc độ Max Speed (ngang trình duyệt/IDM) - Bypass Quota.
    """
    global drive_service
    
    # 1. Đảm bảo đã đăng nhập
    if not drive_service:
        try:
            print("API: Đang thử tự động đăng nhập lại...")
            try_auto_login_drive_thread()
            time.sleep(2)
        except: pass
    
    if not drive_service:
        raise Exception("Cần đăng nhập Google Drive để tải file này.")

    print(f"API: Đang khởi tạo luồng tải trực tiếp (Direct Stream) cho ID {file_id}...")

    try:
        # 2. Lấy Credentials mới nhất từ file token
        token_path = resource_path('token.json')
        if not os.path.exists(token_path):
             raise Exception("Không tìm thấy token xác thực.")
             
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
        # 3. Tạo phiên làm việc đã xác thực (Authorized Session)
        # Đây là "Thẻ bài" giúp requests đi qua cửa VIP của Google
        authed_session = AuthorizedSession(creds)
        
        # URL tải xuống trực tiếp của Drive API v3
        download_url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
        
        # 4. BẮT ĐẦU TẢI (Stream = True để không nạp RAM)
        # Mở kết nối duy nhất và duy trì nó
        with authed_session.get(download_url, stream=True) as response:
            response.raise_for_status() # Kiểm tra lỗi (403/404...)
            
            # Lấy tổng kích thước file
            total_size = int(response.headers.get('content-length', 0))
            
            # Mở file đích với bộ đệm lớn (1MB) để ổ cứng ghi mượt hơn
            with open(dest_path, 'wb', buffering=1024*1024) as f:
                start_time = time.time()
                downloaded = 0
                
                # Chunk size cho stream: 128KB là chuẩn vàng của requests để đạt tốc độ cao
                # (Không cần chunk quá lớn vì stream liên tục)
                stream_chunk_size = 128 * 1024 
                
                last_update_time = time.time()
                
                for chunk in response.iter_content(chunk_size=stream_chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Cập nhật UI (Giới hạn update mỗi 0.5s để không lag App)
                        current_time = time.time()
                        if current_time - last_update_time > 0.5:
                            elapsed = current_time - start_time
                            if elapsed > 0:
                                percent = int(downloaded / total_size * 100) if total_size > 0 else 0
                                speed_bps = downloaded / elapsed
                                speed_str = format_bytes(speed_bps) + "/s"
                                
                                progress_queue.put(("progress", {
                                    "percent": percent, 
                                    "speed": f"Direct Speed: {speed_str}", 
                                    "eta": "" 
                                }))
                            last_update_time = current_time

        print(f"API: Tải thành công (Direct Stream) -> {dest_path}")
        return True

    except Exception as e:
        error_msg = str(e)
        if "403" in error_msg:
             raise Exception("Lỗi 403: File bị Google chặn (Quota) hoặc không có quyền truy cập.")
        elif "404" in error_msg:
             raise Exception("Lỗi 404: File không tồn tại.")
        
        raise Exception(f"Lỗi tải Direct API: {e}")

# --- Logic chính (Download/Extract) ---
def download_and_extract_logic():
    # (Code hàm này không đổi so với phiên bản trước)
    global local_config
    global g_current_game_name

    progress_queue.put(("status", "DISABLE_BUTTONS"))

    selected_key = selected_option.get()
    mod_display_name = g_all_mods_flat[selected_key].get("name", selected_key)
    option_label.configure(text="Đang " + mod_display_name, style="White.TLabel")

    selected_option_data = g_all_mods_flat[selected_key]
    file_url = selected_option_data["url"]
    print(f"Downloading from: {file_url}") # Debug print
    version = selected_option_data["version"]
    file_type = selected_option_data.get("type", "zip")
    password = selected_option_data.get("password", None)
    print(f"--- DEBUG: Đã chọn mod: {mod_display_name}")
    print(f"--- DEBUG: Mật khẩu được lấy từ JSON: '{password}' (Loại: {type(password)})")
    delete_list = selected_option_data.get("delete_before_extract", [])

    destination_folder = path_entry.get()

    if 'last_used_folder' not in local_config:
        local_config['last_used_folder'] = "" # Đảm bảo key tồn tại
    local_config['last_used_folder'] = destination_folder
    save_local_config(local_config)

    sys.stderr = QueueIO(progress_queue)

    temp_archive_path = None # Khởi tạo

    try:
        target_path_to_use = None
            
        if file_type == "exe":
            # Đảm bảo target_exe_path đã được tính toán (dựa trên code cũ của bạn)
            sanitized_key = re.sub(r'[\\/*?:"<>|]', "", selected_key)
            sanitized_version = re.sub(r'[\\/*?:"<>|]', "", version)
            file_name = f"{sanitized_key}_{sanitized_version}.exe"
            target_exe_path = os.path.join(destination_folder, file_name)
            target_path_to_use = target_exe_path
        else:
            # Nếu là zip/rar -> Tạo đường dẫn vào thư mục TEMP
            temp_archive_path = os.path.join(os.environ['TEMP'], f"my_temp_download.{file_type}")
            target_path_to_use = temp_archive_path

        # Kiểm tra lần cuối
        if not target_path_to_use:
            raise Exception("Lỗi nội bộ: Không xác định được đường dẫn lưu file.")

        # 2. Kiểm tra nếu file exe đã có thì mở luôn
        if file_type == "exe" and os.path.exists(target_exe_path):
            progress_queue.put(("status", "File đã tồn tại. Đang mở..."))
            os.startfile(target_exe_path)
            sys.stderr = original_stderr
            progress_queue.put(("status", "ENABLE_BUTTONS"))
            return 

        # --- BẮT ĐẦU TẢI ---
        progress_queue.put(("status", "Bắt đầu tải file..."))
        
        try:
            # CÁCH 1: Thử dùng gdown (Nhanh)
            print(f"Đang thử tải bằng gdown vào: {target_path_to_use}")
            out = gdown.download(file_url, target_path_to_use, quiet=False, fuzzy=True)
            
            if not out: 
                raise Exception("gdown download failed (None returned)")

        except Exception as e_gdown:
            print(f"gdown thất bại: {e_gdown}")
            error_str = str(e_gdown).lower()
            
            # Nếu gặp lỗi Quota/Permission -> Chuyển sang API
            if "too many users" in error_str or "denied" in error_str or "permission" in error_str or "failed" in error_str:
                
                progress_queue.put(("status", "Link quá tải. Chuyển sang tải bằng API Google..."))
                
                file_id = extract_gdrive_id_from_url(file_url)
                if not file_id:
                    raise Exception(f"Không lấy được ID từ link: {file_url}")
                    
                # CÁCH 2: Tải bằng API (Fix lỗi NoneType ở đây)
                try:
                    # target_path_to_use giờ đã chắc chắn là string hợp lệ
                    download_via_api_logic(file_id, target_path_to_use)
                except Exception as e_api:
                    # CÁCH 3: Mở trình duyệt
                    msg_err = ""
                    if "Cần đăng nhập" in str(e_api):
                        msg_err = "File quá tải. Vui lòng Đăng nhập Drive ở Tab 3 rồi thử lại."
                    else:
                        msg_err = f"Lỗi tải file API: {e_api}"
                    
                    progress_queue.put(("download_complete", {"success": False, "title": "Lỗi Tải", "message": msg_err + "\n\nApp sẽ mở trình duyệt để bạn tải thủ công."}))
                    webbrowser.open(file_url)
                    raise Exception("Đã chuyển hướng sang trình duyệt.")
            else:
                raise e_gdown

        # --- KẾT THÚC TẢI ---

        if file_type == "exe":
            progress_queue.put(("status", "Đã tải xong! Đang mở file..."))
            os.startfile(target_exe_path)
            sys.stderr = original_stderr
            progress_queue.put(("status", "ENABLE_BUTTONS"))
            return

        elif file_type == "zip" or file_type == "rar":
            temp_archive_path = os.path.join(os.environ['TEMP'], f"my_temp_download.{file_type}")

            if os.path.exists(temp_archive_path):
                try: os.remove(temp_archive_path)
                except OSError as e: print(f"Cảnh báo: Không thể xóa file tạm cũ {temp_archive_path}: {e}")

            progress_queue.put(("status", "Bắt đầu tải file..."))
            gdown.download(file_url, temp_archive_path, quiet=False)

            # --- THAY THẾ: Logic Xóa bằng Logic Sao lưu ---
            if g_backup_enabled.get():

                if delete_list:
                    progress_queue.put(("status", "Đang sao lưu file cũ..."))

                    # 1. Tạo thư mục backup
                    backup_root_dir = os.path.join(destination_folder, "_BACKUPS")
                    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
                    # Lấy tên mod (đã có ở 'selected_key') và làm sạch nó
                    mod_name_for_backup = g_all_mods_flat[selected_key].get("name", "Unknown Mod")
                    safe_key_name = re.sub(r'[\\/*?:"<>|]', "", mod_name_for_backup)
                    backup_folder_name = f"{safe_key_name} - {timestamp}"
                    specific_backup_dir = os.path.join(backup_root_dir, backup_folder_name)

                try:
                    os.makedirs(specific_backup_dir, exist_ok=True)
                except Exception as e:
                    print(f"Lỗi khi tạo thư mục backup: {e}")
                    progress_queue.put(("status", f"Lỗi tạo backup dir: {e}"))
                    # Nếu không tạo được backup, dừng lại để bảo vệ file
                    raise Exception(f"Không thể tạo thư mục backup. Đã hủy cài đặt. {e}")

                # 2. Di chuyển file/folder vào thư mục backup
                moved_items = [] # Theo dõi các file đã di chuyển để khôi phục nếu lỗi
                try:
                    for item_name in delete_list:
                        source_path = os.path.join(destination_folder, item_name)
                        dest_path = os.path.join(specific_backup_dir, item_name)

                        if os.path.exists(source_path):
                            print(f"Đang sao lưu: {item_name} -> {specific_backup_dir}")
                            # Di chuyển (Move) file/folder
                            shutil.move(source_path, dest_path)
                            # Lưu lại (đích, nguồn) để khôi phục nếu cần
                            moved_items.append((dest_path, source_path))

                except Exception as e:
                    # Nếu có lỗi khi đang di chuyển (ví dụ file bị khóa),
                    # hãy cố gắng khôi phục lại những file đã di chuyển
                    print(f"Lỗi khi đang sao lưu {item_name}: {e}")
                    progress_queue.put(("status", f"Lỗi sao lưu: {e}. Đang khôi phục..."))

                    # --- Logic Khôi phục (Rollback) ---
                    for (moved_file_path, original_location) in moved_items:
                        try:
                            shutil.move(moved_file_path, original_location)
                        except Exception as restore_e:
                            progress_queue.put(("status", f"LỖI KHÔI PHỤC: {restore_e}"))
                    # --- Hết Rollback ---

                    # Dừng cài đặt
                    raise Exception(f"Không thể sao lưu file {item_name}. Đã hủy cài đặt. {e}")

                progress_queue.put(("status", f"Sao lưu thành công vào: {backup_folder_name}"))

            else: 
                # 2. Nếu TẮT backup, quay lại logic XÓA (như ban đầu)
                if delete_list:
                    progress_queue.put(("status", "Đang dọn dẹp file cũ (Backup đã tắt)..."))
                    for item_name in delete_list:
                        item_path = os.path.join(destination_folder, item_name)
                        try:
                            if os.path.exists(item_path):
                                if os.path.isfile(item_path) or os.path.islink(item_path): os.remove(item_path)
                                elif os.path.isdir(item_path): shutil.rmtree(item_path)
                        except Exception as e:
                            print(f"Lỗi khi xóa {item_path}: {e}")
                            progress_queue.put(("status", f"Lỗi khi dọn dẹp: {e}"))
                            # (Không dừng lại nếu xóa lỗi, chỉ cảnh báo)

            progress_queue.put(("status", "Đã tải xong! Đang giải nén..."))

            

            archive_object = None
            if file_type == "zip":
                temp_dir = os.path.join(destination_folder, "temp_extraction_92837")
                if os.path.isdir(temp_dir): shutil.rmtree(temp_dir)
                os.makedirs(temp_dir, exist_ok=True)
                pwd_bytes = bytes(password, 'utf-8') if password else None
                
                # --- THAY ĐỔI: BÁO TRẠNG THÁI VÀ DÙNG extractall() ---
                progress_queue.put(("status", "Đang giải nén ZIP... (Vui lòng chờ)"))
                # (Quan trọng) Yêu cầu UI cập nhật ngay lập tức
                try:
                    root.update_idletasks() 
                except:
                    pass # Bỏ qua nếu có lỗi

                # Dùng 'with' và 'extractall()' để có tốc độ tối đa
                with zipfile.ZipFile(temp_archive_path) as zf:
                    print(f"Extracting ALL ZIP to '{temp_dir}'...")
                    zf.extractall(temp_dir, pwd=pwd_bytes)
                
                shutil.copytree(temp_dir, destination_folder, dirs_exist_ok=True)
                shutil.rmtree(temp_dir)
                
            elif file_type == "rar":
                print("--- Đang xử lý file RAR (Chế độ Direct Write - Fix Code 9) ---")
                import re 
                import stat

                progress_queue.put(("status", "Đang chuẩn bị thư mục đích..."))
                
                # 1. Tìm UnRAR
                unrar_path = getattr(rarfile, 'UNRAR_TOOL', 'UnRAR.exe')
                if not os.path.exists(unrar_path) and os.path.exists("UnRAR.exe"):
                    unrar_path = "UnRAR.exe"

                # 2. XỬ LÝ QUYỀN HẠN TRƯỚC (Rất quan trọng để tránh Code 9)
                # Quét thư mục đích và gỡ bỏ thuộc tính "Read-only" của các file cũ
                # để UnRAR có thể ghi đè lên chúng mà không bị chặn.
                def remove_readonly_recursive(directory):
                    if not os.path.exists(directory): return
                    for root_dir, dirs, files in os.walk(directory):
                        for fname in files:
                            full_path = os.path.join(root_dir, fname)
                            try:
                                # Lấy thuộc tính hiện tại
                                file_atts = os.stat(full_path).st_mode
                                if not (file_atts & stat.S_IWRITE):
                                    # Nếu là Read-only, chuyển thành Writeable
                                    os.chmod(full_path, stat.S_IWRITE)
                            except: pass # Bỏ qua nếu file đang bị khóa bởi System

                # Chạy hàm xử lý quyền (nhanh)
                remove_readonly_recursive(destination_folder)

                # 3. XỬ LÝ ĐƯỜNG DẪN DÀI (Long Path Fix)
                # Thêm prefix \\?\ để Windows chấp nhận đường dẫn dài hơn 260 ký tự
                abs_dest_path = os.path.abspath(destination_folder)
                if not abs_dest_path.startswith("\\\\?\\"):
                    extended_path = "\\\\?\\" + abs_dest_path
                else:
                    extended_path = abs_dest_path

                # Tạo thư mục nếu chưa có
                if not os.path.exists(destination_folder):
                    os.makedirs(destination_folder, exist_ok=True)

                progress_queue.put(("status", "Đang giải nén trực tiếp..."))

                # 4. Cấu trúc lệnh giải nén TRỰC TIẾP
                cmd = [
                    unrar_path,
                    "x",                # Extract with full path
                    "-y",               # Yes to all (Overwrite automatically)
                    "-o+",              # Force Overwrite
                    "-kb",              # Keep broken files (giữ file nếu lỗi mạng, giúp debug)
                ]

                if password:
                    cmd.append(f"-p{password}")
                else:
                    cmd.append("-p-")

                cmd.append(temp_archive_path) # File nguồn
                cmd.append(extended_path)     # Thư mục đích (Đã fix Long Path)

                # 5. Chạy UnRAR
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,
                    text=True,
                    startupinfo=startupinfo,
                    errors="replace"
                )

                # Theo dõi tiến trình
                percent_pattern = re.compile(r"(\d{1,3})%")
                current_percent = 0
                
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        # Debug: In lỗi ra nếu có dòng nào chứa 'Error'
                        if "Error" in output or "Cannot" in output:
                            print(f"UnRAR Log: {output.strip()}")

                        match = percent_pattern.findall(output)
                        if match:
                            new_percent = int(match[-1])
                            if new_percent > current_percent:
                                current_percent = new_percent
                                progress_queue.put(("progress", {
                                    "percent": current_percent, 
                                    "speed": f"Đang giải nén: {current_percent}%", 
                                    "eta": ""
                                }))

                rc = process.poll()
                
                # Mã lỗi 0 = Thành công, 1 = Cảnh báo (vẫn OK)
                if rc != 0 and rc != 1:
                    err_msg = f"Lỗi giải nén RAR (Exit Code {rc})."
                    if rc == 9:
                        err_msg += "\nLỗi tạo file (Code 9). Kiểm tra: 1. Game đang mở? 2. Antivirus chặn file .dll?"
                    elif rc == 3:
                        err_msg += "\nLỗi CRC (File tải về bị hỏng/không khớp)."
                    elif rc == 11:
                        err_msg += "\nSai mật khẩu hoặc file hỏng."
                    
                    raise Exception(err_msg)

                progress_queue.put(("progress", {"percent": 100, "speed": "Hoàn tất", "eta": ""}))


            

            if temp_archive_path and os.path.exists(temp_archive_path):
                 try: os.remove(temp_archive_path)
                 except OSError as e: print(f"Cảnh báo: Không thể xóa file tạm {temp_archive_path} sau khi thành công: {e}")

                 
        print("Giải nén hoàn tất. Đang quét tìm file launcher để lưu đường dẫn chính xác...")

        # 1. Xác định tên file launcher cần tìm
        target_launcher_name = None
        
        # Ưu tiên 1: Lấy từ config người dùng (nếu có)
        if 'game_launchers' in local_config:
            target_launcher_name = local_config['game_launchers'].get(g_current_game_name)

        # Ưu tiên 2: Lấy từ JSON server
        if not target_launcher_name and 'download_options' in globals():
            mod_list = download_options.get(g_current_game_name, [])
            for _key, mod_data in mod_list:
                if mod_data.get("launch_file"):
                    target_launcher_name = mod_data.get("launch_file")
                    break
        
        # 2. Quét tìm file đó trong thư mục vừa giải nén
        final_saved_path = destination_folder # Mặc định là folder gốc (fallback)
        found_launcher = False

        if target_launcher_name:
            print(f"Đang tìm file: {target_launcher_name}...")
            # Dùng os.walk để tìm sâu trong tất cả thư mục con
            for root_dir, dirs, files in os.walk(destination_folder):
                if target_launcher_name in files:
                    found_at_path = os.path.join(root_dir, target_launcher_name)
                    
                    # --> ĐÂY LÀ CỐT LÕI: Cập nhật đường dẫn thành thư mục con chứa file
                    final_saved_path = root_dir 
                    found_launcher = True
                    
                    print(f"--> TÌM THẤY Launcher tại: {found_at_path}")
                    print(f"--> Đường dẫn game thực tế: {final_saved_path}")
                    
                    # Cập nhật biến toàn cục để nút "Chạy Game" sáng lên ngay
                    global g_current_launch_path
                    g_current_launch_path = found_at_path
                    break
        
        if not found_launcher:
            print("--> Không tìm thấy file launcher cụ thể, giữ nguyên đường dẫn gốc.")

        # 3. Lưu đường dẫn CHÍNH XÁC vào Config
        if g_current_game_name:
            if 'game_paths' not in local_config:
                local_config['game_paths'] = {}

            # Lưu path thực tế (thư mục con) thay vì destination_folder
            local_config['game_paths'][g_current_game_name] = final_saved_path
            
            # Cập nhật last_used luôn để lần sau mở đúng chỗ này
            local_config['last_used_folder'] = final_saved_path

            save_local_config(local_config)
            print(f"Đã lưu đường dẫn game chính xác: {final_saved_path}")

        # --- KẾT THÚC CODE MỚI ---

        option_label.configure(text="Đã Hoàn Thành " + mod_display_name, foreground="green") 
        progress_queue.put(("status", "Cài đặt thành công!"))
        
        msg = f"Đã cài đặt '{mod_display_name}' thành công!"
        if found_launcher:
            msg += f"\n\nĐã tự động nhận diện thư mục game:\n{final_saved_path}"

        progress_queue.put(("download_complete", {"success": True, "title": "Thành công", "message": msg}))

        new_version = g_all_mods_flat[selected_key]['version']
        if 'installed_versions' not in local_config: local_config['installed_versions'] = {}
        local_config['installed_versions'][selected_key] = new_version
        save_local_config(local_config)

        refresh_mod_list_ui()
        progress_queue.put(("installation_complete_refresh_grid", None))

    except (zipfile.BadZipFile, rarfile.BadRarFile) as e:
        print(f"--- DEBUG: BẮT LỖI: File hỏng (BadZipFile/BadRarFile) ---") 
        print(f"Lỗi file hỏng: {e}")
        msg = f"Lỗi: File tải về bị hỏng ({e})."
        progress_queue.put(("status", msg))
        progress_queue.put(("download_complete", {"success": False, "title": "Lỗi File", "message": msg}))
        
    except (RuntimeError, rarfile.RarWrongPassword) as e:
        print(f"--- DEBUG: BẮT LỖI: Sai mật khẩu (RuntimeError/WrongPassword) ---") 
        print(f"Lỗi sai mật khẩu: {e}")
        msg = "Lỗi: Sai mật khẩu!"
        progress_queue.put(("status", msg))
        progress_queue.put(("download_complete", {"success": False, "title": "Lỗi Mật khẩu", "message": msg}))
        
    except rarfile.PasswordRequired as e:
        print(f"--- DEBUG: BẮT LỖI: Thiếu mật khẩu (PasswordRequired) ---") 
        print(f"Lỗi thiếu mật khẩu: {e}")
        msg = "Lỗi: File này yêu cầu mật khẩu."
        progress_queue.put(("status", msg))
        progress_queue.put(("download_complete", {"success": False, "title": "Lỗi Mật khẩu", "message": msg}))
        
    except Exception as e:
        print(f"--- DEBUG: BẮT LỖI: Lỗi chung (Exception) ---") 
        msg = f"Lỗi không xác định: {e}"
        progress_queue.put(("status", msg))
        progress_queue.put(("download_complete", {"success": False, "title": "Lỗi", "message": msg}))
        print(f"Lỗi trong try (Exception chung): {e}")

    finally:
        sys.stderr = original_stderr
        progress_queue.put(("status", "ENABLE_BUTTONS"))

def add_folder_to_defender_exclusion(folder_path):
    """Tự động thêm folder vào Exclusion List (Cần Admin)"""
    try:
        folder_path = os.path.abspath(folder_path)
        cmd = [
            "powershell", 
            "-Command", 
            f"Add-MpPreference -ExclusionPath '{folder_path}'"
        ]
        subprocess.run(cmd, creationflags=0x08000000, check=True)
        return True
    except Exception as e:
        print(f"Lỗi thêm Exclusion: {e}")
        return False

# --- Các hàm cho Nút bấm ---
def start_download_thread():
    """(ĐÃ SỬA) Kiểm tra lỗi TRƯỚC KHI bắt đầu thread."""

    # --- THÊM MỚI: KIỂM TRA LỖI (VALIDATION) ---
    selected_key = selected_option.get()
    destination_folder = path_entry.get()

    # Kiểm tra 1: Đã chọn mod chưa?
    if not selected_key or selected_key == "updater":
        custom_showerror("Lỗi", "Vui lòng chọn một mod trong danh sách.")
        return # Dừng lại, không làm gì cả

    # Kiểm tra 2: Đường dẫn có hợp lệ không?
    if not destination_folder or not os.path.isdir(destination_folder):
        custom_showerror("Lỗi", "Đường dẫn folder mod không hợp lệ.\nVui lòng chọn một thư mục tồn tại.")
        return # Dừng lại, không làm gì cả

    # --- THÊM MỚI: KIỂM TRA WINDOWS DEFENDER ---
    
    if g_auto_add_exclusion.get() and sys.platform == "win32":
        
        # Kiểm tra quyền Admin (Cần Admin mới thêm được)
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        except:
            is_admin = False

        if is_admin:
            progress_queue.put(("status", "Đang kiểm tra Windows Defender..."))
            
            # Kiểm tra xem đã an toàn chưa (dùng hàm helper ở câu trả lời trước)
            is_safe = is_folder_excluded_from_defender(destination_folder)
            
            if is_safe:
                print("Folder đã nằm trong Exclusion. Bỏ qua bước thêm.")
            else:
                print("Folder chưa an toàn. Đang tự động thêm...")
                # Tự động thêm (dùng hàm helper ở câu trả lời trước)
                success = add_folder_to_defender_exclusion(destination_folder)
                
                if success:
                    print(f"Đã thêm {destination_folder} vào Exclusion thành công.")
                else:
                    # Nếu thêm thất bại (dù là Admin), báo lỗi nhưng không chặn tải (hoặc tùy bạn chọn)
                    custom_showwarning("Lỗi Defender", 
                                           "Không thể tự động thêm vào Exclusion.\n"
                                           "Vui lòng kiểm tra lại Defender hoặc thêm thủ công.")
        else:
            # Nếu tích checkbox mà KHÔNG chạy quyền Admin -> Báo lỗi và Dừng (hoặc hỏi tiếp tục)
            msg = (
                "Bạn đã chọn 'Tự động thêm vào Exclusion' nhưng App không chạy với quyền Admin.\n\n"
                "Vui lòng khởi động lại App bằng 'Run as Administrator' để tính năng này hoạt động.\n"
                "Hoặc bỏ tích checkbox để tiếp tục tải thường."
            )
            custom_showerror("Thiếu Quyền Admin", msg)
            return # Dừng lại, không tải nữa
        
    # Nếu tất cả kiểm tra đều qua:
    progress_bar['value'] = 0
    status_label.configure(text="Hãy chọn đường dẫn và bấm bắt đầu.", style="White.TLabel")
    if 'g_launch_game_button' in globals():
        g_launch_game_button.pack_forget()
    speed_label.config(text="")
    eta_label.config(text="")
    option_label.configure(text="GG", style="White.TLabel")

    root.after(100, process_queue)
    threading.Thread(target=download_and_extract_logic, daemon=True).start()

def get_system_info_text():
    """
    Phiên bản v3.0 (Ultimate): Lấy thông tin chi tiết sâu (VRAM, Hz, Disk, RAM Speed).
    Sử dụng PowerShell để truy xuất WMI/CIM.
    """
    import winreg
    import shutil
    import string
    
    info_text = []
    info_text.append(f"=== SYSTEM SNAPSHOT ({datetime.now().strftime('%Y-%m-%d %H:%M')}) ===")
    
    # Hàm helper để chạy PowerShell và nhận kết quả sạch
    def run_ps(cmd):
        try:
            full_cmd = ["powershell", "-NoProfile", "-Command", cmd]
            # 0x08000000 là cờ NO_WINDOW
            res = subprocess.check_output(full_cmd, creationflags=0x08000000).decode('utf-8', errors='ignore').strip()
            return res
        except:
            return None

    # 1. HỆ ĐIỀU HÀNH (OS)
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
        product_name, _ = winreg.QueryValueEx(key, "ProductName")
        current_build, _ = winreg.QueryValueEx(key, "CurrentBuild")
        display_version, _ = winreg.QueryValueEx(key, "DisplayVersion")
        winreg.CloseKey(key)
        
        # Logic Fix Win 11
        if "Windows 10" in product_name and int(current_build) >= 22000:
            product_name = product_name.replace("Windows 10", "Windows 11")
        
        arch = platform.machine()
        info_text.append(f"[OS] {product_name} (Ver: {display_version}, Build: {current_build}) - {arch}")
    except Exception as e:
        info_text.append(f"[OS] {platform.system()} {platform.release()}")

    # 2. CPU (Vi xử lý)
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
        cpu_name, _ = winreg.QueryValueEx(key, "ProcessorNameString")
        winreg.CloseKey(key)
        logical_cores = os.cpu_count()
        info_text.append(f"[CPU] {cpu_name.strip()} ({logical_cores} Threads)")
    except:
        info_text.append(f"[CPU] {platform.processor()}")

    # 3. RAM (Bộ nhớ trong + Tốc độ)
    try:
        # Lấy tổng dung lượng
        ram_bytes_cmd = 'Get-CimInstance Win32_ComputerSystem | Select-Object -ExpandProperty TotalPhysicalMemory'
        ram_bytes = int(run_ps(ram_bytes_cmd) or 0)
        ram_gb = round(ram_bytes / (1024**3), 2)
        
        # Lấy tốc độ RAM (Speed) - Lấy thanh đầu tiên tìm thấy
        ram_speed_cmd = 'Get-CimInstance Win32_PhysicalMemory | Select-Object -ExpandProperty Speed -First 1'
        ram_speed = run_ps(ram_speed_cmd)
        
        speed_str = f"@ {ram_speed} MHz" if ram_speed else ""
        info_text.append(f"[RAM] {ram_gb} GB {speed_str}")
    except:
        info_text.append("[RAM] Check failed")

    # 4. GPU (Card đồ họa + VRAM) - Rất quan trọng cho game
    try:
        # Lấy Name và AdapterRAM (VRAM)
        # AdapterRAM trả về bytes, cần chia đổi
        ps_script = """
        Get-CimInstance Win32_VideoController | ForEach-Object {
            $vram = [math]::Round($_.AdapterRAM / 1GB, 1)
            "$($_.Name) ($vram GB VRAM)"
        }
        """
        gpu_info = run_ps(ps_script)
        if gpu_info:
            # Xử lý xuống dòng nếu có nhiều GPU
            gpus = [g.strip() for g in gpu_info.splitlines() if g.strip()]
            info_text.append(f"[GPU] {', '.join(gpus)}")
        else:
             info_text.append("[GPU] Unknown")
    except:
        info_text.append("[GPU] Check failed")

    # 5. MÀN HÌNH (Độ phân giải + Hz) - MỚI
    try:
        ps_script = """
        Get-CimInstance Win32_VideoController | Select-Object -First 1 | ForEach-Object {
            "$($_.CurrentHorizontalResolution)x$($_.CurrentVerticalResolution) @ $($_.CurrentRefreshRate)Hz"
        }
        """
        display_info = run_ps(ps_script)
        if display_info and "x" in display_info:
            info_text.append(f"[DISPLAY] {display_info}")
    except: pass

    # 6. Ổ CỨNG (Dung lượng trống) - MỚI
    try:
        disk_info = []
        # Quét các ổ đĩa từ C đến Z
        drives = ['%s:' % d for d in string.ascii_uppercase if os.path.exists('%s:' % d)]
        for drive in drives:
            try:
                usage = shutil.disk_usage(drive)
                free_gb = round(usage.free / (1024**3), 1)
                total_gb = round(usage.total / (1024**3), 1)
                # Chỉ hiện nếu ổ đĩa lớn hơn 10GB (tránh ổ recovery/system nhỏ)
                if total_gb > 10:
                    disk_info.append(f"{drive} (Free: {free_gb}GB / {total_gb}GB)")
            except: pass
        
        if disk_info:
            info_text.append(f"[DISK] {' | '.join(disk_info)}")
    except: pass

    return "\n".join(info_text)

def _process_run_gemini():
    """
    Tiến trình chạy Gemini AI (Phiên bản Hardcoded Cookie - Bảo mật hơn).
    """
    import sys
    import os
    import time
    import traceback
    import threading
    import ctypes
    import base64 # <--- Cần import cái này
    
    # --- 1. SINGLETON CHECK ---
    kernel32 = ctypes.windll.kernel32
    mutex_name = "WGZ_Gemini_Singleton_Mutex"
    mutex = kernel32.CreateMutexA(None, False, mutex_name.encode("utf-8"))
    if kernel32.GetLastError() == 183:
        return
    
    # --- LOGGING ---
    temp_dir = os.environ.get('TEMP', os.path.expanduser('~'))
    log_path = os.path.join(temp_dir, "wgz_gemini_logic.txt")

    def log_debug(msg):
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                timestamp = time.strftime("%H:%M:%S")
                f.write(f"[{timestamp}] {msg}\n")
        except: pass

    try: os.remove(log_path)
    except: pass

    log_debug(f"--- PROCESS STARTED (PID: {os.getpid()}) ---")

    try:
        import webview
    except Exception as e:
        log_debug(f"CRASH: Import webview error: {e}")
        return

    try:
        # --- CẤU HÌNH ---
        FAKE_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0'
        app_data = os.getenv('APPDATA')
        profile_path = os.path.join(app_data, "NightreignModUpdater", "webview_profile")
        os.makedirs(profile_path, exist_ok=True)

        # --- HTML LOADER ---
        INITIAL_HTML = """
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body { background-color: #131314; color: #E3E3E3; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100vh; margin: 0; font-family: sans-serif; }
                    .loader { width: 50px; height: 50px; border: 4px solid #444746; border-top: 4px solid #4D9CFF; border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 20px; }
                    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
                </style>
            </head>
            <body>
                <div class="loader"></div>
                <div style="font-size: 18px;">Đang kết nối Gemini AI...</div>
            </body>
            </html>
        """

        # --- JS GHI ĐÈ ---
        OVERRIDE_JS = """
            document.documentElement.style.backgroundColor = "#131314";
            while(document.body.firstChild) { document.body.removeChild(document.body.firstChild); }
            document.body.style.cssText = "background-color: #131314; margin: 0; height: 100vh; display: flex; flex-direction: column; justify-content: center; align-items: center; font-family: sans-serif; color: #E3E3E3; overflow: hidden;";

            var style = document.createElement('style');
            style.textContent = `
                .loader { width: 50px; height: 50px; border: 4px solid #444746; border-top: 4px solid #4D9CFF; border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 20px; }
                @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            `;
            document.head.appendChild(style);

            var loaderDiv = document.createElement('div');
            loaderDiv.className = 'loader';
            var textDiv = document.createElement('div');
            textDiv.style.fontSize = '18px';
            textDiv.textContent = 'Đang xác kết nối với Gemini AI';
            
            document.body.appendChild(loaderDiv);
            document.body.appendChild(textDiv);
        """

        # --- [QUAN TRỌNG] HÀM GIẢI MÃ COOKIE TỪ CODE ---
        def get_embedded_cookie():
            try:
                # Dán chuỗi Base64 bạn vừa tạo ở Bước 1 vào đây:
                encrypted_cookie = "X19TZWN1cmUtMVBTSUQ9Zy5hMDAwM3doMC1HOTV5WHkwajdQVGJKbUtGb3pmVDNzN2NPM28tTG8wX1k4NmhMcVVGTVpCbVkzaEQwRlBEZnR6ekM0M1hUcDY4Z0FDZ1lLQVRrU0FSQVNGUUhHWDJNaVpmV0UzV2tMYXZHZ3VZYTdwNzNFSVJvVkFVRjh5S3F2YWh6YWNjUlZIR01XQkxZaEdyNEMwMDc2OyBfX1NlY3VyZS0zUFNJRD1nLmEwMDAzd2gwLUc5NXlYeTBqN1BUYkptS0ZvemZUM3M3Y08zby1MbzBfWTg2aExxVUZNWkIyYlFmeTRlaDNjdVlkS2pwdkR6MFBnQUNnWUtBZjRTQVJBU0ZRSEdYMk1pWU9ydHREaWxPVlFIQ1FzbU9hU3hxUm9WQVVGOHlLbzBDYl9TRWk1WG10djVmX2hFcXhEODAwNzY=" 
                
                # Giải mã về dạng text thường để sử dụng
                decoded_bytes = base64.b64decode(encrypted_cookie)
                return decoded_bytes.decode("utf-8").strip()
            except Exception as e:
                log_debug(f"Cookie Decode Error: {e}")
                return None

        # --- LUỒNG ĐIỀU KHIỂN ---
        def start_navigation(window):
            time.sleep(1.5)
            log_debug("Step 1: Navigating to robots.txt...")
            window.load_url("https://www.google.com/robots.txt")

        # --- XỬ LÝ SỰ KIỆN ---
        def on_loaded(window):
            try:
                current_url = window.get_current_url()
                log_debug(f"Event: Loaded -> {current_url}")

                if "robots.txt" in current_url:
                    log_debug("Step 2: Overriding UI...")
                    window.evaluate_js(OVERRIDE_JS)
                    time.sleep(1.0)
                    window.show()
                    # Lấy cookie từ hàm nội bộ thay vì đọc file
                    external_cookie = get_embedded_cookie()
                    
                    if external_cookie:
                        cookie_parts = external_cookie.split(';')
                        for part in cookie_parts:
                            if "=" in part:
                                key, value = part.split('=', 1)
                                js = f'document.cookie = "{key.strip()}={value.strip()}; domain=.google.com; path=/; Secure; SameSite=None";'
                                window.evaluate_js(js)
                    
                    time.sleep(0.5)
                    log_debug("Step 3: To Gemini...")
                    window.load_url("https://gemini.google.com/app")

                elif "gemini.google.com" in current_url:
                    log_debug("Step 4: Gemini Loaded. Locking Avatar...")
                    css_fix = """
                        var style = document.createElement('style');
                        style.textContent = `
                            a[href^="https://accounts.google.com"],
                            button[aria-label*="Google Account"],
                            button[aria-label*="Tài khoản Google"],
                            div[aria-label*="Google Account"],
                            div[aria-label*="Tài khoản Google"] {
                                pointer-events: none !important;
                                cursor: default !important;
                                opacity: 1 !important;
                            }
                        `;
                        document.head.appendChild(style);
                    """
                    window.evaluate_js(css_fix)

            except Exception as e:
                log_debug(f"OnLoaded Error: {e}")

        # --- KHỞI TẠO ---
        log_debug("Creating Window...")
        window = webview.create_window(
            'Gemini AI PRO', 
            html=INITIAL_HTML, 
            width=1200, height=800, 
            background_color='#131314',
            hidden=True 
        )
        
        window.events.loaded += lambda: on_loaded(window)

        t = threading.Thread(target=start_navigation, args=(window,))
        t.daemon = True
        t.start()

        webview.start(
            private_mode=False, 
            storage_path=profile_path,
            user_agent=FAKE_USER_AGENT,
            debug=False 
        )

    except Exception as e:
        log_debug(f"MAIN CRASH: {e}")

        
def action_flush_dns():
    """Chạy lệnh ipconfig /flushdns để sửa lỗi kết nối mạng."""
    try:
        # Chạy lệnh CMD ẩn (creationflags=0x08000000 để không hiện cửa sổ đen)
        subprocess.run(["ipconfig", "/flushdns"], shell=True, creationflags=0x08000000)
        custom_showinfo("Thành công", 
                            "Đã xóa bộ nhớ đệm DNS (Flush DNS)!\n\n"
                            "Nếu bạn gặp lỗi kết nối Drive/GitHub, hãy thử tải lại ngay bây giờ.")
    except Exception as e:
        custom_showerror("Lỗi", f"Không thể thực hiện lệnh: {e}")

def action_open_data_folder():
    """Mở thư mục AppData chứa config và cache."""
    global config_folder
    try:
        if os.path.exists(config_folder):
            os.startfile(config_folder)
        else:
            custom_showwarning("Lỗi", "Thư mục dữ liệu chưa được tạo.")
    except Exception as e:
        custom_showerror("Lỗi", f"Không thể mở thư mục: {e}")

def action_copy_system_info():
    """Thực hiện lấy thông tin và copy vào clipboard."""
    try:
        info = get_system_info_text()
        pyperclip.copy(info)
        winsound.MessageBeep(winsound.MB_OK) # Âm thanh 'Ting'
        custom_showinfo("Cấu Hình Máy", 
                            f"Đã copy cấu hình máy vào Clipboard!\n\n{info}\n\n(Bạn có thể paste nó vào Discord để nhờ hỗ trợ)")
    except Exception as e:
        custom_showerror("Lỗi", f"Không thể lấy thông tin máy: {e}")

# --- [THÊM MỚI] GLOBAL OPTIMIZER & PRIORITY LAUNCHER ---
def run_global_ram_cleaner():
    """
    Quét TOÀN BỘ các tiến trình đang chạy và ép nhả RAM (Trim Working Set).
    Không cần danh sách target, dọn sạch mọi thứ có thể.
    """
    import ctypes
    from ctypes import wintypes
    
    # Các hằng số API Windows
    PROCESS_SET_QUOTA = 0x0100
    PROCESS_QUERY_INFORMATION = 0x0400
    
    print("--- GLOBAL RAM CLEANER STARTED ---")
    
    # Sử dụng EnumProcesses để lấy danh sách tất cả PID (nhanh hơn tasklist)
    # Khai báo thư viện Psapi
    psapi = ctypes.windll.psapi
    
    # Chuẩn bị mảng để chứa danh sách PID
    arr_size = 1024 * 4 # Hỗ trợ tối đa 4096 process
    process_ids = (ctypes.c_ulong * arr_size)()
    bytes_returned = ctypes.c_ulong()
    
    # Lấy danh sách PID
    if psapi.EnumProcesses(ctypes.byref(process_ids), ctypes.sizeof(process_ids), ctypes.byref(bytes_returned)):
        count = int(bytes_returned.value / ctypes.sizeof(ctypes.c_ulong))
        cleaned = 0
        
        for i in range(count):
            pid = process_ids[i]
            if pid <= 4: continue # Bỏ qua System Idle và System
            
            try:
                # Mở process với quyền chỉnh sửa bộ nhớ
                handle = ctypes.windll.kernel32.OpenProcess(
                    PROCESS_SET_QUOTA | PROCESS_QUERY_INFORMATION, False, pid
                )
                
                if handle:
                    # Gọi API ép nhả RAM (-1, -1)
                    ctypes.windll.kernel32.SetProcessWorkingSetSize(handle, -1, -1)
                    ctypes.windll.kernel32.CloseHandle(handle)
                    cleaned += 1
            except Exception:
                pass # Bỏ qua các process hệ thống/admin nếu không có quyền

        print(f"Đã tối ưu bộ nhớ cho {cleaned} tiến trình toàn hệ thống.")
        return cleaned
    return 0

def launch_with_high_priority(file_path):
    """
    Phiên bản V2: Dùng PowerShell thay vì CMD.
    - Fix lỗi UAC bị minimize/ẩn.
    - Fix lỗi game chạy ngầm không hiện cửa sổ.
    - Vẫn giữ tính năng High Priority.
    """
    try:
        # Lấy thư mục làm việc
        working_dir = os.path.dirname(file_path)
        
        # Chuẩn hóa đường dẫn (đổi / thành \) để PowerShell không bị lỗi ký tự lạ
        file_path_win = os.path.normpath(file_path)
        working_dir_win = os.path.normpath(working_dir)

        # Câu lệnh PowerShell:
        # 1. Start-Process: Khởi chạy file
        # 2. -WindowStyle Normal: BẮT BUỘC hiển thị cửa sổ (Fix lỗi minimize)
        # 3. -PassThru: Trả về đối tượng process vừa tạo để chỉnh sửa tiếp
        # 4. PriorityClass = 'High': Đặt ưu tiên cao
        ps_command = (
            f"Start-Process -FilePath '{file_path_win}' "
            f"-WorkingDirectory '{working_dir_win}' "
            "-WindowStyle Normal "
            "-PassThru | ForEach-Object {$_.PriorityClass = 'High'}"
        )
        
        print(f"PowerShell Launch: {ps_command}")
        
        # Chạy PowerShell (ẩn cửa sổ console đen đi bằng cờ 0x08000000)
        subprocess.Popen(
            ["powershell", "-NoProfile", "-Command", ps_command],
            creationflags=0x08000000, 
            cwd=working_dir
        )
        return True

    except Exception as e:
        print(f"Lỗi Priority Launch (PowerShell): {e}")
        return False
def _perform_launch_tab2():
    """Hàm này chứa logic chạy game thực sự, được gọi sau khi delay."""
    global g_current_launch_path, g_smart_mode_enabled, g_auto_close

    # --- SMART MODE LOGIC ---
    if g_smart_mode_enabled.get():
        # 1. Dọn RAM
        threading.Thread(target=run_global_ram_cleaner, daemon=True).start()
        
        # 2. Chạy Game (Priority)
        try:
            success = launch_with_high_priority(g_current_launch_path)
            if not success:
                # Fallback
                exe_dir = os.path.dirname(g_current_launch_path)
                os.startfile(g_current_launch_path, cwd=exe_dir)
        except Exception as e:
            custom_showerror("Lỗi", f"Không thể khởi chạy: {e}")
            
    else:
        # --- NORMAL MODE ---
        try:
            exe_dir = os.path.dirname(g_current_launch_path)
            os.startfile(g_current_launch_path, cwd=exe_dir)
        except Exception as e:
            custom_showerror("Lỗi Khởi chạy", f"Lỗi: {e}")

    # --- AUTO CLOSE ---
    if g_auto_close.get():
        print("Auto-Close kích hoạt. Đang tắt tool...")
        # Đợi thêm 1 xíu sau khi lệnh chạy game được gửi đi rồi mới tắt
        root.after(1000, lambda: sys.exit(0))
        
# --- THÊM MỚI: HÀM KHỞI CHẠY GAME ---
def action_launch_game():
    """
    Kiểm tra cài đặt để chọn hiệu ứng:
    - Nếu BẬT Chaos: Nổ tung giao diện.
    - Nếu TẮT Chaos: Chỉ cho nút bay đi (nhẹ nhàng).
    """
    global g_current_launch_path, page_2_mod_list, g_launch_game_button
    global g_chaos_effect_enabled # Cần biến này

    if not g_current_launch_path or not os.path.exists(g_current_launch_path):
        custom_showerror("Lỗi", "Không tìm thấy đường dẫn file.")
        return

    # 1. Chạy hiệu ứng GIF trên ảnh bìa (Luôn chạy nếu có)
    if 'g_game_image_label' in globals() and g_game_image_label.winfo_exists():
        play_rocket_animation(target_widget=g_game_image_label)

    # 2. QUYẾT ĐỊNH HIỆU ỨNG CHUYỂN CẢNH
    if g_chaos_effect_enabled.get():
        # --- CAO CẤP: NỔ TUNG GIAO DIỆN ---
        animate_chaos_explosion(page_2_mod_list)

    # 3. Hẹn giờ chạy logic game (Vẫn là 2 giây)
    root.after(2000, _perform_launch_tab2)

def _perform_launch_page1(path_to_launch):
    """Logic chạy game thực sự cho Page 1."""
    global g_smart_mode_enabled, g_auto_close
    
    exe_dir = os.path.dirname(path_to_launch)
    
    # --- SMART MODE ---
    if g_smart_mode_enabled.get():
        threading.Thread(target=run_global_ram_cleaner, daemon=True).start()
        try:
            success = launch_with_high_priority(path_to_launch)
            if not success:
                os.startfile(path_to_launch, cwd=exe_dir)
        except Exception as e:
            custom_showerror("Lỗi Smart Mode", f"Lỗi: {e}")
            os.startfile(path_to_launch, cwd=exe_dir)
    else:
        # --- NORMAL MODE ---
        try:
            os.startfile(path_to_launch, cwd=exe_dir)
        except Exception as e:
            custom_showerror("Lỗi Khởi chạy", f"Lỗi: {e}")

    # --- AUTO CLOSE ---
    if g_auto_close.get():
        print("Auto-Close (Page 1) kích hoạt...")
        root.after(1000, lambda: sys.exit(0))

def action_launch_game_from_page_1(path_to_launch, btn_widget=None):
    if path_to_launch and os.path.exists(path_to_launch):
        
        # [SỬA] Truyền nút bấm vào animation
        if btn_widget:
            play_rocket_animation(target_widget=btn_widget)
        
        # Hẹn giờ chạy
        root.after(2000, lambda: _perform_launch_page1(path_to_launch))
        
    else:
        custom_showerror("Lỗi", "Không tìm thấy file khởi chạy.")
# --- HẾT THÊM MỚI ---

def browse_for_folder():
    # Lấy path đã lưu cuối cùng
    last_path = local_config.get("last_used_folder", "")
    if not os.path.isdir(last_path): # Kiểm tra nếu path còn hợp lệ
        last_path = ""

    folder_selected = filedialog.askdirectory(initialdir=last_path)
    if folder_selected:
        path_entry.delete(0, tk.END)
        path_entry.insert(0, folder_selected)

def action_add_custom_game_popup():
    """Mở cửa sổ thêm game ngoài."""
    popup = tk.Toplevel(root)
    popup.title("Thêm Game Ngoài")
    center_window_on_screen(popup, 450, 300)
    popup.transient(root)
    popup.grab_set()
    
    frame = ttk.Frame(popup, padding=20)
    frame.pack(fill=tk.BOTH, expand=True)

    # 1. Đường dẫn Launcher (.exe)
    ttk.Label(frame, text="File Khởi Chạy (.exe):").pack(anchor=tk.W)
    path_frame = ttk.Frame(frame)
    path_frame.pack(fill=tk.X, pady=(0, 10))

    # 2. Tên Game
    ttk.Label(frame, text="Tên Game:").pack(anchor=tk.W)
    entry_name = ttk.Entry(frame)
    entry_name.pack(fill=tk.X, pady=(0, 10))
    
    
    
    entry_path = ttk.Entry(path_frame)
    entry_path.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def browse_exe():
        f = filedialog.askopenfilename(filetypes=[("Executable", "*.exe"), ("All Files", "*.*")])
        if f:
            entry_path.delete(0, tk.END)
            entry_path.insert(0, f)
            # Tự động điền tên nếu chưa có
            if not entry_name.get():
                base = os.path.basename(f)
                name = os.path.splitext(base)[0]
                entry_name.insert(0, name)

    ttk.Button(path_frame, text="...", width=3, command=browse_exe).pack(side=tk.LEFT, padx=(5, 0))
    
    # 3. URL Hình Ảnh
    ttk.Label(frame, text="Link Ảnh Bìa (URL):").pack(anchor=tk.W)
    entry_url = ttk.Entry(frame)
    entry_url.pack(fill=tk.X, pady=(0, 10))
    ttk.Label(frame, text="(Gợi ý: Lấy link ảnh từ SteamGridDB hoặc Google Images)", 
              font=("Segoe UI", 8), foreground="gray").pack(anchor=tk.W)

    # --- LOGIC LƯU ---
    def save_custom_game():
        name = entry_name.get().strip()
        path = entry_path.get().strip()
        url = entry_url.get().strip()
        
        if not name or not path or not url:
            custom_showwarning("Thiếu thông tin", "Vui lòng điền đầy đủ thông tin.")
            return
            
        if not os.path.exists(path):
            custom_showerror("Lỗi", "File khởi chạy không tồn tại.")
            return

        # Tải và Lưu Ảnh vào ổ cứng
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            img_data = response.content
            
            # Tạo tên file an toàn
            safe_name = "".join([c for c in name if c.isalnum() or c in (' ', '-', '_')]).strip()
            img_filename = f"custom_{safe_name}.png"
            
            # Đảm bảo thư mục cache tồn tại
            if not os.path.exists(g_cache_dir):
                os.makedirs(g_cache_dir)
                
            local_img_path = os.path.join(g_cache_dir, img_filename)
            
            # Resize và Lưu (Để tiết kiệm dung lượng và load nhanh)
            with Image.open(io.BytesIO(img_data)) as img:
                # Resize về chuẩn 192x89 (nhỏ) hoặc 460x215 (lớn)
                # Ở đây ta lưu bản lớn để dùng cho cả 2
                img_resized = img.resize((460, 215), Image.Resampling.LANCZOS)
                img_resized.save(local_img_path, "PNG")
                
            # Cập nhật Config
            if 'custom_games' not in local_config:
                local_config['custom_games'] = {}
                
            local_config['custom_games'][name] = {
                "launch_path": path,
                "image_local_path": local_img_path,
                "original_url": url
            }
            
            save_local_config(local_config)
            custom_showinfo("Thành công", f"Đã thêm game '{name}'!")
            popup.destroy()
            
            # Refresh Lưới Game
            action_clear_game_search() 
            
        except Exception as e:
            custom_showerror("Lỗi", f"Không thể tải/lưu ảnh: {e}")

    ttk.Button(frame, text="Thêm Game", command=save_custom_game, style="Accent.TButton").pack(pady=10)

def action_set_game_path_from_page_2():
    """
    (ĐÃ SỬA) Mở dialog CHỌN FILE, lưu path VÀ LAUNCH FILE, và cập nhật UI.
    """
    global local_config, g_current_game_name, path_entry
    
    if not g_current_game_name:
        print("Lỗi: Không có game nào đang được chọn (g_current_game_name is None)")
        return

    # 1. Lấy path đã lưu (nếu có) để làm initialdir
    current_path = local_config.get("game_paths", {}).get(g_current_game_name, "")
    if not os.path.isdir(current_path):
        current_path = local_config.get("last_used_folder", "") # Fallback

    # --- SỬA: DÙNG askopenfilename ---
    file_selected = filedialog.askopenfilename(
        initialdir=current_path, 
        title=f"Chọn file khởi chạy (launch file) cho {g_current_game_name}",
        filetypes=[("All Files", "*.*")]
    )
    # --- HẾT SỬA ---
    
    if file_selected:
        # --- THÊM MỚI: Tách thư mục và tên file ---
        folder_selected = os.path.dirname(file_selected)
        launcher_selected = os.path.basename(file_selected)
        # --- HẾT THÊM MỚI ---

        # 2. Cập nhật path_entry (ô text)
        path_entry.delete(0, tk.END)
        path_entry.insert(0, folder_selected) # <-- SỬA: Dùng folder_selected
        
        # 3. Cập nhật và lưu config
        if 'game_paths' not in local_config:
            local_config['game_paths'] = {}
        if 'game_launchers' not in local_config: # Đảm bảo key tồn tại
            local_config['game_launchers'] = {}
            
        local_config['game_paths'][g_current_game_name] = folder_selected # <-- SỬA: Dùng folder_selected
        local_config['game_launchers'][g_current_game_name] = launcher_selected # <-- THÊM MỚI

        # Cũng cập nhật 'last_used_folder' để đồng bộ
        local_config['last_used_folder'] = folder_selected # <-- SỬA: Dùng folder_selected
        
        save_local_config(local_config)
        print(f"Đã lưu đường dẫn cho {g_current_game_name}: {folder_selected}")
        print(f"Đã lưu launch file cho {g_current_game_name}: {launcher_selected}")

        # 4. (Quan trọng) Chạy lại hàm kiểm tra nút "Launch Game"
        update_guide_text()

# --- [MỚI] HÀM HIỆN NÚT RESET ---
def show_reset_ui_button(parent_frame):
    """Tạo một nút Reset to ở giữa màn hình."""
    
    # 1. Tạo nút Reset
    reset_btn = ttk.Button(
        parent_frame,
        text="🔄 Khôi Phục Giao Diện",
        style="Accent.TButton", # Dùng style xanh cho nổi bật
        command=lambda: action_restore_ui(reset_btn)
    )
    
    # 2. Đặt nút vào chính giữa frame cha
    # Dùng place với relx/rely = 0.5 để căn giữa tuyệt đối
    reset_btn.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=200, height=50)
    
    # 3. (Tùy chọn) Hiệu ứng xuất hiện (Fade in hoặc Scale up)
    # Ở đây làm đơn giản là hiện ngay lập tức.

def action_restore_ui(reset_btn_widget):
    """
    Khôi phục giao diện bằng cách Pack lại các Frame chính về vị trí cũ.
    """
    global g_current_game_name
    
    print("Đang khôi phục giao diện...")
    
    # 1. Xóa nút reset
    reset_btn_widget.destroy()
    
    # 2. "Gọi hồn" các Frame chính quay về (Re-pack theo đúng thứ tự ban đầu)
    # Lưu ý: Phải dùng place_forget() để xóa tọa độ -10000 trước khi pack()
    
    try:
        # A. Ảnh Bìa
        if 'image_placeholder_frame' in globals():
            image_placeholder_frame.place_forget() 
            image_placeholder_frame.pack(pady=(0, 10)) # Pack lại vào Page 2
            
        # B. Thanh công cụ trên (Nút Quay lại / Chạy Game)
        if 'page_2_top_nav_frame' in globals():
            page_2_top_nav_frame.place_forget()
            page_2_top_nav_frame.pack(fill=tk.X, pady=(0, 10))

        # C. Khung Hướng dẫn
        if 'guide_frame' in globals():
            guide_frame.place_forget()
            guide_frame.pack(fill=tk.X, pady=(0, 5), padx=(10, 0))

        # D. Khung Danh sách Mod (Options)
        if 'options_frame' in globals():
            options_frame.place_forget()
            options_frame.pack(fill=tk.X, expand=False, pady=10, padx=(10, 0))
            
        # E. Khung Đường dẫn (Path)
        if 'path_frame' in globals():
            path_frame.place_forget()
            path_frame.pack(fill=tk.X, pady=(5, 10))
            
        # F. Khung Nút dưới cùng (Bắt đầu Cài đặt)
        if 'button_frame' in globals():
            button_frame.place_forget()
            button_frame.pack(pady=15)

        # 3. Vẽ lại nội dung bên trong (Để đảm bảo dữ liệu đúng)
        if g_current_game_name:
            show_page_2_for_game(g_current_game_name)
        else:
            # Fallback nếu mất tên game
            action_go_back_and_refresh_grid()
            
    except Exception as e:
        print(f"Lỗi khi khôi phục UI: {e}")
        custom_showerror("Lỗi", "Không thể khôi phục giao diện. Vui lòng khởi động lại App.")

# --- [CẬP NHẬT] HIỆU ỨNG CHAOS + NÚT RESET ---
def animate_chaos_explosion(container_frame):
    """
    Tách widget, cho bay tứ tung, và hiện nút Reset sau đó.
    """
    children = container_frame.winfo_children()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    flying_objects = []

    # 1. Tạo hiệu ứng nổ (Giữ nguyên logic cũ)
    for widget in children:
        try:
            if not widget.winfo_viewable(): continue
            
            widget.update_idletasks()
            x = widget.winfo_rootx()
            y = widget.winfo_rooty()
            w = widget.winfo_width()
            h = widget.winfo_height()
            
            if w < 2 or h < 2: continue

            img = ImageGrab.grab(bbox=(x, y, x+w, y+h))
            tk_img = ImageTk.PhotoImage(img)

            # Ẩn widget thật
            widget.place(x=-10000, y=-10000) 

            # Tạo mảnh vỡ bay
            fly_win = tk.Toplevel(root)
            fly_win.overrideredirect(True)
            fly_win.attributes('-topmost', True)
            fly_win.geometry(f"{w}x{h}+{x}+{y}")
            
            lbl = tk.Label(fly_win, image=tk_img, bd=0)
            lbl.image = tk_img 
            lbl.pack(fill="both", expand=True)

            vx = random.randint(-20, 20)
            vy = random.randint(-25, -5)
            if vx == 0: vx = 5
            
            flying_objects.append({
                "win": fly_win, "vx": vx, "vy": vy, "x": x, "y": y
            })

        except Exception as e:
            print(f"Lỗi tạo clone: {e}")

    # 2. Hàm vật lý (Giữ nguyên)
    def physics_loop():
        active_count = 0
        for obj in flying_objects:
            win = obj["win"]
            if not win.winfo_exists(): continue
            active_count += 1
            
            obj["x"] += obj["vx"]
            obj["y"] += obj["vy"]
            obj["vy"] += 1.5 # Trọng lực
            
            try:
                win.geometry(f"+{int(obj['x'])}+{int(obj['y'])}")
            except: pass

            if (obj["y"] > screen_height + 100) or (obj["x"] < -500) or (obj["x"] > screen_width + 500):
                win.destroy()

        if active_count > 0:
            root.after(20, physics_loop)

    physics_loop()

    # --- [MỚI] HẸN GIỜ HIỆN NÚT RESET ---
    # Sau 1.5 giây (khi các mảnh vỡ đã bay đi bớt), hiện nút Reset
    root.after(1500, lambda: show_reset_ui_button(container_frame))


# --- [PHIÊN BẢN FULL SCREEN + OPACITY] HIỆU ỨNG GIF MỜ ẢO ---
def play_rocket_animation(target_widget=None):
    """
    Tạo cửa sổ hiệu ứng mờ 50% đè lên đúng vị trí của widget mục tiêu (img_label).
    """
    global g_rocket_raw_data

    if not target_widget: return

    # 1. Lấy vị trí và kích thước CHÍNH XÁC của ảnh bìa (img_label) trên màn hình
    target_widget.update_idletasks()
    x = target_widget.winfo_rootx()
    y = target_widget.winfo_rooty()
    w = target_widget.winfo_width()
    h = target_widget.winfo_height()
    
    # Nếu chưa hiển thị thì bỏ qua
    if w < 2 or h < 2: return

    # 2. Kiểm tra dữ liệu GIF
    if not g_rocket_raw_data:
        try:
            if 'ROCKET_GIF_URL' in globals():
                response = requests.get(ROCKET_GIF_URL, timeout=5)
                g_rocket_raw_data = response.content
        except Exception as e:
            print(f"Lỗi tải GIF: {e}")
            return

    if not g_rocket_raw_data: return

    try:
        # 3. Tạo cửa sổ Overlay (Dùng Toplevel để chỉnh được Alpha)
        overlay_win = tk.Toplevel(root)
        
        # Đặt vị trí trùng khít với img_label
        overlay_win.geometry(f"{w}x{h}+{x}+{y}")
        
        overlay_win.overrideredirect(True) # Bỏ viền
        
        # --- QUAN TRỌNG: CHỈNH ĐỘ TRONG SUỐT ---
        overlay_win.attributes('-alpha', 0.7) # 0.5 = 50% Opacity
        # --------------------------------------

        # Gắn nó vào cửa sổ chính để không bị che bởi các app khác
        overlay_win.transient(root) 
        overlay_win.lift()

        # Cấu hình nền đen (để khi mờ đi nó sẽ làm tối ảnh game một chút)
        bg_color = 'black'
        overlay_win.config(bg=bg_color)

        # Nếu muốn GIF lọc nền đen (transparent color), bỏ comment dòng dưới:
        # overlay_win.attributes('-transparentcolor', bg_color) 

        label = tk.Label(overlay_win, bg=bg_color, bd=0)
        label.pack(fill=tk.BOTH, expand=True)

        # Hẹn giờ tắt sau 2 giây
        def close_animation():
            try:
                if overlay_win.winfo_exists():
                    overlay_win.destroy()
            except: pass
        
        overlay_win.after(2000, close_animation)

        # 4. Xử lý GIF
        im_data = io.BytesIO(g_rocket_raw_data)
        im = Image.open(im_data)
        
        def update_frame(frame_idx):
            try:
                if not overlay_win.winfo_exists(): return
            except: return

            try:
                # Giữ cửa sổ luôn nổi trên cùng trong app
                overlay_win.lift() 
                
                im.seek(frame_idx)
                # Resize ảnh bằng kích thước img_label
                current_frame = im.copy().resize((w, h), Image.Resampling.LANCZOS)
                tk_image = ImageTk.PhotoImage(current_frame)
                
                label.configure(image=tk_image)
                label.image = tk_image 
                
                duration = im.info.get('duration', 30)
                overlay_win.after(duration, lambda: update_frame(frame_idx + 1))
                
            except EOFError:
                pass # Dừng ở frame cuối
            except Exception:
                close_animation()

        update_frame(0)

    except Exception as e:
        print(f"Lỗi animation: {e}")


# --- THÊM MỚI: HÀM CHẠY ANIMATION CHO GIF ---
def animate_gif(delay):
    """Hàm lặp lại để cập nhật frame của GIF."""
    try:
        # Lấy frame tiếp theo
        frame = root.gif_frames[root.gif_frame_index]
        g_gif_label.configure(image=frame) # Cập nhật label

        # Tăng index, quay vòng nếu cần
        root.gif_frame_index += 1
        if root.gif_frame_index >= len(root.gif_frames):
            root.gif_frame_index = 0

        # Hẹn giờ để gọi lại hàm này sau 'delay' ms
        root.after(delay, animate_gif, delay)

    except Exception as e:
        # Dừng animation nếu có lỗi (ví dụ: cửa sổ đã đóng)
        print(f"Dừng animation GIF: {e}")

# --- Hàm xử lý queue ---
def process_queue():
    # (Code hàm này không đổi)
    global g_login_overlay_popup, g_login_overlay_label
    global download_options, local_config
    global g_dynamic_account_buttons
    global g_accounts_data_loaded, g_images_preloaded
    try:
        message_type, message_value = progress_queue.get_nowait()

        if message_type == "config_loaded":
            combined_data = message_value # Đây là {"mods": ..., "themes": ...}
            
            # 1. Gán theme ngay lập tức để thread preload có thể dùng
            global g_game_themes
            g_game_themes = combined_data.get("themes", {})
            
            # 2. Gán mod data toàn cục (dùng chung)
            global g_all_mods_flat
            g_all_mods_flat = combined_data.get("mods", fallback_options)

            # 3. Cập nhật thanh progress bar (như cũ)
            progress_bar.stop()
            progress_bar.config(mode="determinate")
            progress_bar['value'] = 0
            
            # 4. SỬA: Bắt đầu tải trước (preload) tất cả ảnh
            print("Config đã tải. Bắt đầu tải trước (preload) tất cả ảnh...")
            threading.Thread(target=preload_all_images_thread, 
                             args=(g_game_themes, g_all_mods_flat), # Truyền themes và mods
                             daemon=True).start()
            
            # 5. Bắt đầu tải Tab 2 (tài khoản)
            threading.Thread(target=try_auto_login_drive_thread, daemon=True).start()

        elif message_type == "status":
            if message_value == "DISABLE_BUTTONS":
                start_button.config(state=tk.DISABLED)
                browse_button.config(state=tk.DISABLED)
                show_page(page_3_progress) # <-- THÊM MỚI: Chuyển sang Trang 3
            elif message_value == "ENABLE_BUTTONS":
                start_button.config(state=tk.NORMAL)
                browse_button.config(state=tk.NORMAL)
                if g_current_page == page_3_progress:
                    show_page(page_2_mod_list)

                # Xử lý nếu đang ở trang 1
                elif not g_current_game_name: 
                    show_page(page_1_game_grid)
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
                status_label.configure(text=message_value, foreground="green")
                progress_bar['value'] = 100
                speed_label.config(text="Hoàn thành!")
                eta_label.config(text="")
            else:
                status_label.configure(text=message_value, style="White.TLabel")

        elif message_type == "progress":
            progress_data = message_value
            
            # --- START OF MODIFIED SECTION ---
            # Update speed/eta labels first (this logic is good)
            if "speed" in progress_data:
                speed_label.config(text=progress_data["speed"])
            if "eta" in progress_data:
                eta_text = progress_data['eta']
                eta_label.config(text=f"ETA: {eta_text}" if eta_text else "")

            # Now, handle the percentage and status text
            if "percent" in progress_data:
                percent = progress_data["percent"]
                progress_bar['value'] = percent
                
                # Get the current status text (e.g., "Đang tải file...")
                current_status_text = status_label.cget("text")
                
                base_text = ""
                # Check if we are downloading or extracting
                if current_status_text.startswith("Đã tải xong! Đang giải nén..."):
                    base_text = "Đang giải nén"
                elif current_status_text.startswith("Đang tải file..."):
                    base_text = "Đang tải file"
                # Check if text already has a percentage (e.g., "Đang giải nén: 50%")
                elif ":" in current_status_text:
                    base_text = current_status_text.split(":")[0]
                
                # Fallback: if it's a simple status, just use it
                elif "..." in current_status_text:
                     base_text = current_status_text.replace("...", "")

                # Only update the text if we have a valid base
                # and it's not an error/success message
                if base_text and "Lỗi" not in base_text and "thành công" not in base_text:
                    status_label.configure(text=f"{base_text}: {percent}%", style="White.TLabel")
                # If we are at 0%, just show the base text
                elif percent == 0 and base_text:
                    status_label.configure(text=f"{base_text}...", style="White.TLabel")
        
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
            MAX_COLS = 10
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
                        # --- SỬA LỖI THREADING & THÊM NGẮT DÒNG ---
                        def start_delete_with_confirm():
                            # 1. Tạo tin nhắn (thêm \n để ngắt dòng, giảm độ rộng)
                            message = f"Bạn có chắc chắn muốn XÓA VĨNH VIỄN file này\nkhỏi Google Drive không?\n\nFile: {fname}"

                            # 2. Hỏi xác nhận (chạy trong thread chính, an toàn)
                            if custom_askyesno("Xác nhận Xóa", message):
                                # 3. Chỉ bắt đầu thread nếu người dùng bấm "Yes"
                                threading.Thread(target=action_delete_drive_file_thread, args=(fid, fname), daemon=True).start()
                            else:
                                # 4. Báo cáo nếu người dùng hủy
                                progress_queue.put(("drive_log", "Đã hủy thao tác xóa."))

                        return start_delete_with_confirm # Trả về hàm mới
                        # --- HẾT SỬA ---

                    context_menu = tk.Menu(item_frame, tearoff=0)

                    # Thêm 2 lệnh copy
                    context_menu.add_command(label="Copy Tên File", command=create_copy_lambda(file_name, "Tên File"))
                    context_menu.add_command(label="Copy File ID", command=create_copy_lambda(file_id, "File ID"))

                    context_menu.add_separator()

                    # --- THÊM MỚI: Tùy chọn "Tạo Nhanh Option" (CÓ ĐIỀU KIỆN) ---
                    if file_name.lower().endswith((".exe", ".zip", ".rar")):

                        # Nút Tạo Nhanh (luôn bật)
                        def create_quick_add_lambda(fname, fid):
                            return lambda: action_quick_add_option(fname, fid)

                        context_menu.add_command(
                            label="Tạo Option Tải từ file này", 
                            command=create_quick_add_lambda(file_name, file_id)
                        )

                        context_menu.add_separator() # Thêm một dấu gạch nữa
                    # --- HẾT THÊM MỚI ---
                    
                    current_file_info = {"name": file_name, "id": file_id}
                    def create_update_lambda(info):
                        # Hàm lambda này sẽ gọi hàm mở popup
                        return lambda: open_single_file_updater_popup(info)

                    context_menu.add_command(
                        label="Cập nhật file này...",
                        command=create_update_lambda(current_file_info)
                    )
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
        
        elif message_type == "scan_report_ready":
            if scan_loading_window:
                scan_loading_window.destroy()
            show_scan_report(message_value["errors"], message_value["warnings"])

        elif message_type == "scan_failed":
            if scan_loading_window:
                scan_loading_window.destroy()
            custom_showerror("Lỗi Quét", f"Không thể hoàn thành quét: {message_value}")
        
        # --- THÊM MỚI: XỬ LÝ KẾT QUẢ KIỂM TRA CẬP NHẬT THỦ CÔNG ---
        elif message_type == "manual_update_check":
            if 'update_app_button' in globals():
                update_app_button.config(state=tk.NORMAL, text="Kiểm tra Cập nhật")

            config_data = message_value
            if not config_data:
                custom_showerror("Lỗi", "Không thể tải config. Kiểm tra lại mạng.")
                return

            # Chạy hàm check_for_updates và kiểm tra kết quả trả về
            found_update = check_for_updates(config_data) 

            # Nếu hàm trả về False (không tìm thấy update), thì báo cho người dùng
            if not found_update:
                custom_showinfo("Kiểm tra Cập nhật", "Bạn đang dùng phiên bản mới nhất!")

        elif message_type == "manual_update_check_failed":
            if 'update_app_button' in globals():
                update_app_button.config(state=tk.NORMAL, text="Kiểm tra Cập nhật")
            custom_showerror("Lỗi", f"Không thể kiểm tra cập nhật: {message_value}")

        # --- THÊM MỚI: XỬ LÝ UPLOAD BÍ MẬT ---
        elif message_type == "secret_status":
            if scan_loading_window and secret_loading_label:
                secret_loading_label.config(text=message_value)

        elif message_type == "secret_done":
            if scan_loading_window:
                scan_loading_window.destroy()
            if secret_window:
                secret_window.destroy() # Đóng cửa sổ bí mật
            custom_showinfo("Hoàn tất", "Đã upload thành công cả 2 file!")
            action_refresh_drive_list() # Tự động làm mới lưới

        elif message_type == "secret_error":
            if scan_loading_window:
                scan_loading_window.destroy()
            # Không đóng cửa sổ bí mật để user sửa lỗi
            custom_showerror("Lỗi Upload Bí mật", f"Upload thất bại:\n{message_value}", parent=secret_window)
        # --- HẾT THÊM MỚI ---
        elif message_type == "steam_path_found":
            path = message_value
            if 'g_steam_path_entry' in globals():
                current_path = g_steam_path_entry.get()
                if not current_path: # Chỉ điền nếu ô còn trống
                    print(f"Auto-fill Steam: {path}")
                    g_steam_path_entry.delete(0, tk.END)
                    g_steam_path_entry.insert(0, path)
                    # Tự động lưu vào config
                    action_save_path_settings()
                
        elif message_type == "riot_path_found":
            path = message_value
            if 'g_riot_path_entry' in globals():
                current_path = g_riot_path_entry.get()
                if not current_path: # Chỉ điền nếu ô còn trống
                    print(f"Auto-fill Riot: {path}")
                    g_riot_path_entry.delete(0, tk.END)
                    g_riot_path_entry.insert(0, path)
                    # Tự động lưu vào config
                    action_save_path_settings()
        elif message_type == "all_images_preloaded":
            g_images_preloaded = True
            print("Tất cả ảnh đã được tải trước. Đang hiển thị Lưới Game (Tab 1)...")
            mod_config_dict = message_value # Đây là g_all_mods_flat được truyền qua

            # --- Code này được di chuyển từ "config_loaded" ---
            
            # 1. Nhóm các mod theo game
            global download_options # Lưu lại dict đã nhóm
            download_options = {}
            for key, data in mod_config_dict.items():
                if key == "updater": continue
                game_name = data.get("game", "Khác")
                if game_name not in download_options:
                    download_options[game_name] = []
                download_options[game_name].append( (key, data) )

            # 2. Điền vào Lưới Game (Hàm này sẽ TỰ ĐỘNG XÓA loading spinner)
            populate_page_1_grid(download_options) 

            # 3. Hiển thị Trang 1 (dù nó đã ở đó)
            show_page(page_1_game_grid)
            
            # 4. Thiết lập đường dẫn
            status_label.configure(text="Hãy chọn đường dẫn và bấm bắt đầu.", style="White.TLabel")
            start_button.config(state=tk.NORMAL)
            browse_button.config(state=tk.NORMAL)
            
            # 5. Kiểm tra updates (dùng mod_config_dict)
            check_for_updates(mod_config_dict)
            
            # 6. Điền data cho Tab 4 và 5
            g_steam_path_entry.delete(0, tk.END)
            g_steam_path_entry.insert(0, local_config.get("steam_path", ""))

            if 'g_riot_path_entry' in globals():
                g_riot_path_entry.delete(0, tk.END)
                g_riot_path_entry.insert(0, local_config.get("riot_path", ""))
            check_and_draw_account_grid()
            
        elif message_type == "accounts_loaded":
            # --- SỬA: Lật cờ (flag) 2 ---
            
            g_accounts_data_loaded = True
            print("Cờ g_accounts_data_loaded đã được SET (Thành công).")
            check_and_draw_account_grid() # <-- Gọi hàm kiểm tra
            
        elif message_type == "accounts_load_failed":
            # --- SỬA: Lật cờ (flag) 2 (ngay cả khi thất bại) ---
            g_accounts_data_loaded = True # Vẫn set là "đã tải"
            print(f"Account load failed: {message_value}. Cờ g_accounts_data_loaded đã được SET (Thất bại).")
            check_and_draw_account_grid()

        elif message_type == "account_save_status":
            text, style = message_value
            new_state = tk.NORMAL # Mặc định là mở
            
            # Nếu tin nhắn là "Đang lưu...", đặt trạng thái là "vô hiệu hóa"
            if text == "Đang lưu...":
                new_state = tk.DISABLED # Khóa nút
            
            # 1. Vô hiệu hóa nút "Thêm Mới" (toàn cục)
            if 'g_acct_page_2_add_btn' in globals():
                try: g_acct_page_2_add_btn.config(state=new_state)
                except: pass # Bỏ qua nếu lỗi
            if 'g_acct_page_2_save_btn' in globals() and g_acct_page_2_save_btn:
                try: g_acct_page_2_save_btn.config(state=new_state)
                except: pass
            # 2. Vô hiệu hóa tất cả các nút "Sửa" / "Xóa" / "Đăng nhập" (động)
            for btn in g_dynamic_account_buttons:
                try:
                    btn.config(state=new_state)
                except tk.TclError:
                    pass # Bỏ qua nếu nút đã bị hủy (hiếm khi xảy ra)

            # 3. Cập nhật nhãn trạng thái (code cũ)
            if 'g_acct_save_status_label' in globals():
                g_acct_save_status_label.config(text=text, style=style)
                
                # Nếu là "Đã lưu!", tự động ẩn sau 3 giây (code cũ)
                if text == "Đã lưu!":
                    root.after(3000, lambda: g_acct_save_status_label.config(text=""))
        elif message_type == "login_status_update":
            # Cập nhật text trên nhãn (thay vì pop-up)
            if 'g_acct_login_status_label' in globals():
                try:
                    # Cập nhật text từ thread (ví dụ: "Đang tắt Riot Client...")
                    g_acct_login_status_label.config(text=message_value, style="White.TLabel")
                except tk.TclError: 
                    pass # Bỏ qua nếu có lỗi
        
        elif message_type == "login_status_hide":
            # Ẩn tin nhắn (xóa text) sau 3 giây
            # và hiển thị lỗi nếu có
            
            label_to_clear = None # Biến tạm để dùng trong hàm 'after'
            
            if 'g_acct_login_status_label' in globals():
                label_to_clear = g_acct_login_status_label
                
                if message_value: 
                    # Nếu có tin nhắn lỗi (ví dụ: "Hết thời gian chờ")
                    label_to_clear.config(text=message_value, foreground="red")
                    # Hiển thị pop-up lỗi CHÍNH THỨC
                    custom_showerror("Lỗi Đăng nhập Riot", message_value)
                else:
                    # Nếu không có lỗi (thành công)
                    label_to_clear.config(text="Hoàn tất!", foreground="green")
            
            # Tự động xóa text trên nhãn sau 3 giây
            if label_to_clear:
                root.after(3000, lambda: label_to_clear.config(text=""))

            try:           
                if 'g_acct_page_2_back_btn' in globals():
                    g_acct_page_2_back_btn.config(state=tk.NORMAL)
                if 'g_acct_page_2_add_btn' in globals():
                    g_acct_page_2_add_btn.config(state=tk.NORMAL)
                    
                for btn in g_dynamic_account_buttons:
                    try:
                        btn.config(state=tk.NORMAL)
                    except tk.TclError:
                        pass # Nút có thể đã bị hủy
            except Exception as e:
                print(f"Lỗi khi mở khóa nút: {e}")
        # --- THÊM MỚI: XỬ LÝ POP-UP SAU KHI TẢI XONG ---
        elif message_type == "download_complete":
            data = message_value
            if data["success"]:
                # Hiển thị pop-up thành công
                custom_showinfo(data["title"], data["message"])
            else:
                # Hiển thị pop-up lỗi
                custom_showerror(data["title"], data["message"])
        elif message_type == "game_image_loaded":
            image_tk = message_value
            if image_tk:
                g_game_image_label.config(image=image_tk)
                g_game_image_label.pack(fill=tk.BOTH, expand=True)
        elif message_type == "installation_complete_refresh_grid":
            print("Nhận được tín hiệu refresh, đang vẽ lại Lưới Game (Trang 1)...")
            try:
                # Lấy từ khóa tìm kiếm hiện tại (nếu có)
                search_term = ""
                if g_game_search_entry:
                    search_term = g_game_search_entry.get().lower()

                # Gọi hàm vẽ lại Trang 1
                populate_page_1_grid(download_options, search_term)
            except Exception as e:
                print(f"Lỗi khi tự động vẽ lại Lưới Game: {e}")
        # --- THÊM MỚI: XỬ LÝ KHI GIF TẢI XONG ---
        elif message_type == "gif_loaded":
            gif_data = message_value
            root.gif_frames = gif_data.get("frames", [])
            delay = gif_data.get("delay", 100)

            if root.gif_frames:
                root.gif_frame_index = 0
                # Bắt đầu vòng lặp animation
                animate_gif(delay)

        # --- THÊM MỚI: XỬ LÝ KẾT QUẢ UPLOAD THEME ---
        elif message_type == "theme_upload_success":
            global g_game_theme_sha
            # --- SỬA LỖI: Khai báo biến toàn cục danh sách kiểm tra ---
            global g_master_game_list 
            
            new_sha, new_game_name = message_value
            g_game_theme_sha = new_sha # Cập nhật SHA mới

            # Cập nhật cả 2 combobox
            game_list = sorted(list(g_game_themes.keys()))
            
            # --- SỬA LỖI: Cập nhật danh sách Master để bộ Validate không báo lỗi ---
            g_master_game_list = game_list 
            
            game_list_with_add = game_list + ["Thêm Game..."]
            g_admin_game_combobox['values'] = game_list_with_add

            # Cập nhật listbox trong modal
            populate_theme_listbox()

            # Xóa form trong modal
            g_theme_name_entry.delete(0, tk.END)
            g_theme_url_entry.delete(0, tk.END)

            if new_game_name:
                g_admin_game_combobox.set(new_game_name) # Tự động chọn game mới

        elif message_type == "theme_upload_failed":
            custom_showerror("Lỗi Upload Theme", message_value, parent=g_theme_manager_window)
            # Tải lại config (vì có thể local và remote đã lệch)
            action_load_from_github_wrapper()
        elif message_type == "anydesk_id_sent_to_discord":
            anydesk_id = message_value
            custom_showinfo("Đã gửi Yêu cầu",
                                f"Đã tự động gửi ID ({anydesk_id}) của bạn đến Discord\n\n"
                                "Vui lòng giữ cửa sổ AnyDesk mở và đợi kết nối.",
                                parent=root)
        
        elif message_type == "anydesk_id_retrieved_locally":
            anydesk_id = message_value
        # --- THÊM MỚI: XỬ LÝ HỒI ĐÁP CỦA ANYDESK ---
        elif message_type == "anydesk_error":
            # --- SỬA TIÊU ĐỀ Ở ĐÂY ---
            custom_showerror("Lỗi RustDesk",  # <--- Đổi thành RustDesk
                                 f"Thông báo:\n{message_value}",
                                 parent=root)
        
        elif message_type == "anydesk_done":
            # Bất kể thành công hay lỗi, bật lại nút
            if 'g_anydesk_button' in globals():
                try:
                    g_anydesk_button.config(state=tk.NORMAL, text="🚀 Hỗ trợ Từ xa")
                except tk.TclError:
                    pass
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
        if custom_askyesno("Xác nhận thoát", "Đm dang tải file. m có chắc chắn muốn thoát? \n (Việc tải sẽ bị hủy và phải tải lại từ đầu)"):
            # Nếu người dùng chọn "Yes", thoát chương trình
            try:
                stop_translator_service() # Giết tiến trình con
            except: pass
            root.destroy()
            sys.exit(0)
        # else: (Nếu chọn "No", không làm gì cả, cửa sổ tiếp tục)
    else:
        try:
            stop_translator_service() # Giết tiến trình con
        except: pass
        # Nếu không đang tải, thoát luôn
        root.destroy()
        sys.exit(0)

# --- Hàm áp dụng theme cho title bar ---

def apply_theme_to_titlebar(root_window):
    # (Code hàm này không đổi)
    current_theme = sv_ttk.get_theme()
    version = sys.getwindowsversion()
    if version.major >= 10:
        if version.build >= 22000:
            color = "#2f2f2f" if current_theme == "dark" else "#fafafa"
            try: pywinstyles.change_header_color(root_window, color)
            except Exception as e: print(f"Lỗi pywinstyles (Win11): {e}")
        else:
            try: pywinstyles.apply_style(root_window, current_theme)
            except Exception as e: print(f"Lỗi pywinstyles (Win10): {e}")
    else: print("Warning: Title bar theming only supported on Windows 10/11.")







# --- Chạy ứng dụng ---
if __name__ == '__main__':

    if "--gemini" in sys.argv:
        try:
            _process_run_gemini()
        except Exception as e:
            # Ghi log lỗi ra file nếu cần vì không có console
            with open("gemini_crash.log", "w") as f:
                f.write(str(e))
        sys.exit(0)

    multiprocessing.freeze_support()
    
    if sys.platform.startswith('win'):
        multiprocessing.set_executable(sys.executable)
    if sys.stdout is None:
        import io
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()
    try:
        app_mutex_name = b"WGZ_GameUpdater_Singleton_Mutex"
        g_singleton_lock = SingleInstance(app_mutex_name)
        
    except Exception as e:
        print(f"Cảnh báo: Không thể tạo singleton mutex: {e}")
    # --- Cài đặt cửa sổ Giao diện (UI) ---
    enforce_admin_rights()

    prevent_system_sleep_and_boost_priority()
    
    root = TkinterDnD.Tk()
    root.withdraw()
    # --- SPLASH SCREEN (BEGIN) ---
    splash = tk.Toplevel(root)
    splash.title("Loading")

    # Kích thước splash screen
    splash_width = 350
    splash_height = 200

    center_window_on_screen(splash, splash_width, splash_height)

    # Xóa viền cửa sổ
    splash.overrideredirect(True) 

    # Thêm style cho splash (dùng màu nền tối)
    splash_style = ttk.Style()
    splash_style.configure("Splash.TFrame", background="#2b2b2b")
    splash_style.configure("Splash.TLabel", background="#2b2b2b", foreground="white", font=("Segoe UI", 10))
    splash_style.configure("Splash.Header.TLabel", background="#2b2b2b", foreground="white", font=("Segoe UI", 14, "bold"))

    # Dùng Frame để có thể thêm viền
    splash_frame = ttk.Frame(splash, style="Splash.TFrame", borderwidth=1, relief="solid")
    splash_frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(splash_frame, text="WGZ Game Updater", style="Splash.Header.TLabel").pack(pady=(20, 10))
    try:
        # Giả sử bạn có file 'logo.png' trong resource
        icon_path = resource_path("logo.png") 
        splash_img = Image.open(icon_path).resize((50, 50), Image.Resampling.LANCZOS)
        # Phải lưu lại, nếu không sẽ bị Python xóa mất
        root.splash_logo_tk = ImageTk.PhotoImage(splash_img) 
        ttk.Label(splash_frame, image=root.splash_logo_tk, style="Splash.TLabel").pack(pady=5)
    except Exception as e:
        print(f"Không thể tải logo cho splash (bỏ qua): {e}")

    status_label_splash = ttk.Label(splash_frame, text="Đang khởi động core system...", style="Splash.TLabel")
    status_label_splash.pack(pady=10)
    splash.update()

    # Bắt buộc Tkinter phải vẽ splash screen ngay lập tức

    app_width = 1050
    app_height = 950

    # Lấy kích thước màn hình
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Tính toán vị trí x, y để căn giữa
    x = (screen_width // 2) - (app_width // 2)
    y = (screen_height // 2) - (app_height // 2)

    # Đặt kích thước VÀ vị trí cho cửa sổ
    root.geometry(f'{app_width}x{app_height}+{x}+{y}')
    root.minsize(800, 550)
    root.resizable(False,False)

    g_backup_enabled = tk.BooleanVar(value=local_config.get("backup_enabled", False))
    root.cached_images = {}
    # --- Định nghĩa Style ---

    style = ttk.Style()
    style.configure("Red.TLabel", foreground="red")
    style.configure("Green.TLabel", foreground="green")
    style.configure("White.TLabel", foreground="white") # Cho theme tối
    style.configure("New.TLabel", foreground="red", font=('TkDefaultFont', 9, 'bold'))
    style.configure("Green.TRadiobutton", foreground="green")
    style.configure("Installed.TLabel", foreground="green")



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

    # --- BẮT ĐẦU CODE CHO TAB 2 ("Quản lý Account") ---
    account_tab_frame = ttk.Frame(notebook, padding=(10, 10))
    # (Lưu ý: Dòng notebook.add() đã được di chuyển lên trên)
    notebook.add(account_tab_frame, text=" Share Acc Game ")
    # --- Biến Global cho Tab Account ---
    g_acct_current_page = None
    g_acct_page_1_grid = None
    g_acct_page_2_list = None
    g_acct_grid_container = None
    g_acct_list_treeview = None
    g_acct_current_game = None # Tên game đang xem


    g_user_accounts_data = {} 
    g_user_accounts_file_id = None
    g_accounts_loaded = False
    g_dynamic_account_buttons = []
    g_login_overlay_popup = None
    g_login_overlay_label = None
    g_accounts_data_loaded = False
    g_images_preloaded = False
    g_acct_has_unsaved_changes = False
    g_acct_page_2_save_btn = None
    # --- Hai trang (Frames) cho Tab Account ---
    g_acct_page_1_grid = ttk.Frame(account_tab_frame, padding=(10, 10))
    g_acct_page_1_grid.place(relx=0, rely=0, relwidth=1, relheight=1)

    g_tab2_loading_frame = ttk.Frame(g_acct_page_1_grid, name="tab2_loading_frame")
    g_tab2_loading_frame.pack(expand=True, anchor=tk.CENTER)
            
    ttk.Label(g_tab2_loading_frame, text="Đang tải dữ liệu tài khoản...").pack(pady=5)
    tab2_loader = ttk.Progressbar(g_tab2_loading_frame, orient="horizontal", length=200, mode="indeterminate")
    tab2_loader.pack(pady=10)
    tab2_loader.start(10)

    g_acct_page_1_top_frame = ttk.Frame(g_acct_page_1_grid)
    g_acct_page_1_top_frame.pack(fill=tk.X, pady=(0, 10))
            
    # --- DI CHUYỂN NÚT: "Thêm Account Mới" (từ Trang 2) ---
    g_acct_page_2_add_btn = ttk.Button(
        g_acct_page_1_top_frame, # <-- THAY ĐỔI: Parent là g_acct_page_1_top_frame
        text="➕ Thêm Account Mới", 
        command=lambda: open_add_edit_account_popup(None), # None = Thêm mới
        style="Accent.TButton"
    )
    g_acct_page_2_add_btn.pack(side=tk.RIGHT)

    g_acct_page_2_list = ttk.Frame(account_tab_frame, padding=(10, 10))
    g_acct_page_2_list.place(relx=1, rely=0, relwidth=1, relheight=1) # Ẩn bên phải

    g_acct_current_page = g_acct_page_1_grid

    def switch_account_page(page_to_show):
        """Chuyển đổi giữa 2 trang (Grid và List) - Không animation."""
        global g_acct_current_page
        
        if g_acct_current_page == page_to_show:
            return
            
        # Ẩn trang cũ
        g_acct_current_page.place(relx=1, rely=0, relwidth=1, relheight=1)
        
        # Hiện trang mới
        page_to_show.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        g_acct_current_page = page_to_show

    # --- Trang 1: Lưới Game/Dịch vụ ---

    # (Chúng ta sẽ tạo canvas và grid trong hàm populate)

    # --- Trang 2: Danh sách Tài khoản ---
    g_acct_page_2_top_frame = ttk.Frame(g_acct_page_2_list)
    g_acct_page_2_top_frame.pack(fill=tk.X, pady=(0, 10))

    g_acct_page_2_back_btn = ttk.Button(
        g_acct_page_2_top_frame, 
        text="❮ Quay lại", 
        command=lambda: switch_account_page(g_acct_page_1_grid)
    )
    g_acct_page_2_back_btn.pack(side=tk.LEFT)

    global g_acct_save_status_label
    g_acct_save_status_label = ttk.Label(g_acct_page_1_top_frame, text="", anchor=tk.W)
    g_acct_save_status_label.pack(side=tk.LEFT, padx=5)

    g_acct_page_2_add_btn_DUPLICATE = ttk.Button( # Đặt tên biến khác một chút
        g_acct_page_2_top_frame, 
        text="➕ Thêm Account Mới", 
        command=lambda: open_add_edit_account_popup(None), # None = Thêm mới
        style="Accent.TButton"
    )

    g_acct_page_2_save_btn = ttk.Button(
        g_acct_page_1_top_frame,
        text="💾 Lưu Thay Đổi",
        command=save_accounts_to_drive_thread, # <-- Gọi thẳng hàm upload
        style="Accent.TButton", # Nút "Lưu" sẽ là nút chính
        state=tk.DISABLED # Bắt đầu ở trạng thái mờ
    )
    g_acct_page_2_save_btn.pack(side=tk.RIGHT, padx=(0, 5))
    g_acct_page_2_add_btn_DUPLICATE.pack(side=tk.RIGHT)

    global g_acct_login_status_label
    g_acct_login_status_label = ttk.Label(g_acct_page_2_top_frame, text="", anchor=tk.CENTER)
    g_acct_login_status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

    # Khung Treeview (danh sách)
    # Khung chứa Canvas và Scrollbar
    g_acct_list_frame = ttk.LabelFrame(g_acct_page_2_list, text="Accounts đã lưu")
    g_acct_list_frame.pack(fill=tk.BOTH, expand=True)

    # 1. Tạo Canvas và Scrollbar (giống Tab 1)
    g_acct_list_canvas = tk.Canvas(g_acct_list_frame, borderwidth=0, highlightthickness=0)
    g_acct_list_scrollbar = ttk.Scrollbar(g_acct_list_frame, orient="vertical", command=g_acct_list_canvas.yview)
    g_acct_list_canvas.configure(yscrollcommand=g_acct_list_scrollbar.set)

    g_acct_list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    g_acct_list_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # 2. Tạo Frame nội dung BÊN TRONG Canvas (để chứa các Card)
    global g_acct_list_container
    g_acct_list_container = ttk.Frame(g_acct_list_canvas, padding=(10, 10))

    # 3. Đặt Frame nội dung vào Canvas
    g_acct_list_canvas_window_id = g_acct_list_canvas.create_window((0, 0), window=g_acct_list_container, anchor="nw")

    # --- Các hàm helper cho việc cuộn (Tương tự Tab 1) ---
    def on_acct_list_content_frame_configure(event):
        """Cập nhật scroll region của canvas."""
        g_acct_list_canvas.configure(scrollregion=g_acct_list_canvas.bbox("all"))

    def on_acct_list_canvas_configure(event):
        """Đảm bảo frame nội dung luôn fill chiều rộng của canvas."""
        g_acct_list_canvas.itemconfig(g_acct_list_canvas_window_id, width=event.width - 4)

    # 4. Bind (gắn) các sự kiện cuộn
    g_acct_list_container.bind("<Configure>", on_acct_list_content_frame_configure)
    g_acct_list_canvas.bind("<Configure>", on_acct_list_canvas_configure)

    def mark_accounts_as_dirty():
        """Kích hoạt nút 'Lưu' và hiển thị trạng thái 'chưa lưu'."""
        global g_acct_has_unsaved_changes, g_acct_page_2_save_btn, g_acct_save_status_label
        g_acct_has_unsaved_changes = True
        if 'g_acct_page_2_save_btn' in globals() and g_acct_page_2_save_btn:
            g_acct_page_2_save_btn.config(state=tk.NORMAL)
        if 'g_acct_save_status_label' in globals() and g_acct_save_status_label:
            g_acct_save_status_label.config(text="Có thay đổi chưa lưu...", foreground="red")

    def mark_accounts_as_saved():
        """Vô hiệu hóa nút 'Lưu' (được gọi sau khi tải hoặc lưu thành công)."""
        global g_acct_has_unsaved_changes, g_acct_page_2_save_btn
        g_acct_has_unsaved_changes = False
        if 'g_acct_page_2_save_btn' in globals() and g_acct_page_2_save_btn:
            g_acct_page_2_save_btn.config(state=tk.DISABLED)

    # --- Các hàm Logic cho Tab Account ---
    def check_and_draw_account_grid():
        """
        (Hàm Mới) Kiểm tra xem cả hai luồng (Tải ảnh và Tải account)
        đã hoàn thành chưa. Nếu rồi, mới vẽ Tab 2.
        """
        global g_images_preloaded, g_accounts_data_loaded
        
        if g_images_preloaded and g_accounts_data_loaded:
            print("--- ĐIỀU KIỆN ĐỦ: Cả ảnh và account đã sẵn sàng. Đang vẽ Tab 2... ---")
            populate_account_game_grid()
        else:
            # Báo cáo trạng thái hiện tại (để debug)
            print(f"--- ĐIỀU KIỆN CHƯA ĐỦ: Images={g_images_preloaded}, Accounts={g_accounts_data_loaded}. Đang chờ... ---")

    def populate_account_game_grid():
        """
        (ĐÃ VIẾT LẠI)
        Tạo lưới game dựa trên các key (Game) từ g_user_accounts_data.
        """
        global g_acct_grid_container, g_acct_page_1_grid
        global g_game_themes, g_user_accounts_data 

        try:
            # Tìm widget có tên 'tab2_loading_frame' và xóa nó
            loading_frame = g_acct_page_1_grid.nametowidget("tab2_loading_frame")
            if loading_frame:
                loading_frame.destroy()
        except KeyError:
            pass # Không tìm thấy (đã bị xóa từ trước), bỏ qua
        # --- HẾT THÊM MỚI ---
        
        # --- SỬA LOGIC: Quyết định hiển thị Prompt hay Lưới ---
        if not drive_service:
            # 1. TẠO PROMPT (Nếu chưa có)
            global g_acct_login_prompt_label
            if not 'g_acct_login_prompt_label' in globals():
                g_acct_login_prompt_label = ttk.Label(
                    g_acct_page_1_grid, 
                    text="Vui lòng Đăng nhập Google Drive (ở Tab 'Upload Lên Drive')\nđể tải và quản lý tài khoản.",
                    justify=tk.CENTER,
                    style="secondary.TLabel"
                )
            # 2. HIỂN THỊ PROMPT (Luôn luôn)
            g_acct_login_prompt_label.pack(expand=True)
            return # <-- QUAN TRỌNG: Dừng hàm tại đây
        else:
            # 3. ẨN PROMPT (Nếu tồn tại)
            if 'g_acct_login_prompt_label' in globals():
                try:
                    g_acct_login_prompt_label.pack_forget()
                except: pass

        # 1. Tạo Canvas Scroll (CHỈ 1 LẦN)
        if g_acct_grid_container is None:
            canvas_host_frame = ttk.Frame(g_acct_page_1_grid)
            canvas_host_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)
            page_1_scrollbar = ttk.Scrollbar(canvas_host_frame, orient="vertical")
            page_1_canvas = tk.Canvas(canvas_host_frame, borderwidth=0, highlightthickness=0, yscrollcommand=page_1_scrollbar.set)
            page_1_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            page_1_scrollbar.config(command=page_1_canvas.yview)
            g_acct_grid_container = ttk.Frame(page_1_canvas)
            canvas_window_id = page_1_canvas.create_window((0, 0), window=g_acct_grid_container, anchor="n")
            g_acct_grid_container.bind("<Configure>", lambda e, c=page_1_canvas: c.configure(scrollregion=c.bbox("all")))
            page_1_canvas.bind("<Configure>", lambda e, c=page_1_canvas, w=canvas_window_id: c.itemconfig(w, width=e.width - 4))
        
        # 2. Xóa các card game CŨ
        for widget in g_acct_grid_container.winfo_children():
            widget.destroy()

        # 3. Lấy danh sách game CÓ account (Code không đổi)
        user_accounts_data = g_user_accounts_data 
        game_names_with_accounts = sorted(user_accounts_data.keys())

        # 6. Vẽ lưới game
        MAX_COLS = 4    
        col = 0
        row = 0
        
        # --- SỬA LOGIC: XÓA NÚT "Thêm Dịch vụ" ---
        # (Vì giờ đây chúng ta thêm bằng cách chọn game trong pop-up)

        # --- SỬA LOGIC: LẶP QUA CÁC KEY GAME ---
        for game_name in game_names_with_accounts: # (Key giờ là "Elden Ring", "Steam", v.v.)
            icon_img = None 
            
            # 1. Ưu tiên icon Steam/Riot (đã được cache bởi preload)
            if game_name == "Steam":
                icon_img = root.steam_icon_small
            elif game_name == "Riot":
                icon_img = root.riot_icon_small
            
            # 2. Lấy icon game (từ cache, thông qua load_image_from_url)
            if not icon_img:
                image_url = g_game_themes.get(game_name)
                if image_url:
                    # Hàm này sẽ tự động lấy từ cache (vì preload đã chạy)
                    icon_img = load_image_from_url(image_url, size=(192, 89))
            
            # 3. Dùng icon mặc định (từ cache)
            if not icon_img:
                icon_img = root.default_game_icon_small
            
            # (Code tạo Card Frame, img_label, name_label... không đổi)
            card_frame = ttk.Frame(g_acct_grid_container, style="Card.TFrame", cursor="hand2")
            card_frame.grid(row=row, column=col, padx=10, pady=10, sticky="ew")
            card_frame.columnconfigure(0, weight=1)

            if icon_img:
                img_label = ttk.Label(card_frame, image=icon_img, cursor="hand2")
                img_label.grid(row=0, column=0, pady=(10, 5), padx=10)
            else:
                img_label = ttk.Label(card_frame, text="[Lỗi Tải Ảnh]", style="secondary.TLabel", cursor="hand2")
                img_label.grid(row=0, column=0, pady=(10, 5), padx=10)

            name_label = ttk.Label(card_frame, text=game_name, anchor=tk.CENTER, cursor="hand2", font=("Segoe UI", 10, "bold"))
            name_label.grid(row=1, column=0, pady=(0, 10), padx=10, sticky="ew")

            # (Code Click -> Mở Trang 2 không đổi)
            cmd = lambda e, g=game_name: show_account_list_for_game(g)

            card_frame.bind("<Button-1>", cmd)
            img_label.bind("<Button-1>", cmd)
            name_label.bind("<Button-1>", cmd)

            col += 1
            if col >= MAX_COLS:
                col = 0
                row += 1

        for i in range(MAX_COLS): g_acct_grid_container.columnconfigure(i, weight=0)

    def on_acct_list_mouse_wheel(event):
        """(HÀM MỚI) Cho phép cuộn bằng bánh xe chuột trên Tab Account."""
        global g_acct_list_canvas
        try:
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
            
            g_acct_list_canvas.yview_scroll(scroll_amount, "units")
        except Exception as e:
            print(f"Lỗi cuộn chuột Tab Account: {e}")

    def show_account_list_for_game(game_name):
        """
        (ĐÃ VIẾT LẠI)
        Vẽ các card tài khoản VÀ GẮN SỰ KIỆN CUỘN CHUỘT.
        """
        global g_user_accounts_data, g_acct_list_container, g_acct_current_game, g_dynamic_account_buttons
        
        g_acct_current_game = game_name 
        
        g_acct_list_frame.config(text=f"Accounts đã lưu cho: {game_name}")

        for widget in g_acct_list_container.winfo_children():
            widget.destroy()
            
        g_dynamic_account_buttons.clear()
        
        game_accounts = g_user_accounts_data.get(game_name, [])
        
        if not game_accounts:
            ttk.Label(g_acct_list_container, 
                    text="Không có tài khoản nào được lưu cho dịch vụ này.", 
                    style="secondary.TLabel").pack(pady=10)

        # --- LẤY ICON DỊCH VỤ (Làm ảnh dự phòng) ---
        service_icon_img = None 
        if g_acct_current_game == "Steam":
            service_icon_img = root.steam_icon_small
        elif g_acct_current_game == "Riot":
            service_icon_img = root.riot_icon_small
        else:
            service_icon_img = root.cached_game_icons_small.get(g_acct_current_game, root.default_game_icon_small)

        # --- THÊM MỚI: Danh sách widget để bind ---
        widgets_to_bind = [g_acct_list_container]

        # --- Vẽ các Card mới ---
        for i, acc_info in enumerate(game_accounts):
            
            # 1. Tạo Card (Frame) cho mỗi account
            card = ttk.Frame(g_acct_list_container, style="Card.TFrame", padding=10)
            card.pack(fill=tk.X, expand=True, pady=(0, 10))
            widgets_to_bind.append(card)
            
            # 2. Frame bên trái (Nút Đăng nhập)
            left_frame = ttk.Frame(card)
            left_frame.pack(side=tk.LEFT, padx=(0, 15), fill=tk.Y)
            widgets_to_bind.append(left_frame)
            

            acc_type = acc_info.get('type', 'steam').lower()
            btn_icon = None
            
            if acc_type == 'steam':
                btn_icon = getattr(root, 'steam_icon_tiny', None)
            elif acc_type == 'riot':
                btn_icon = getattr(root, 'riot_icon_tiny', None)

            login_btn = ttk.Button(
                left_frame, 
                text="Đăng nhập", 
                image=btn_icon,    # Icon dịch vụ (Steam/Riot)
                compound=tk.BOTTOM,
                style="Accent.TButton",
                command=lambda index=i: action_login_by_index(index)
            )
            login_btn.pack(expand=True, fill=tk.BOTH)
            g_dynamic_account_buttons.append(login_btn)
            widgets_to_bind.append(login_btn)

            # 3. Frame ở giữa (Thông tin)
            mid_frame = ttk.Frame(card)
            mid_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
            widgets_to_bind.append(mid_frame)

            nickname = acc_info.get('nickname', 'N/A')
            username = acc_info.get('username', 'N/A')
            acc_type = acc_info.get('type', 'N/A').capitalize()
            game_display_tag = acc_info.get('game', None) 
            
            icon_to_use = None
            if game_display_tag:
                icon_to_use = root.cached_game_icons_small.get(game_display_tag)
                if not icon_to_use:
                    image_url = g_game_themes.get(game_display_tag)
                    if image_url:
                        try:
                            icon_to_use = load_image_from_url(image_url, size=(192, 89))
                            if icon_to_use:
                                root.cached_game_icons_small[game_display_tag] = icon_to_use
                        except Exception as e:
                            print(f"Lỗi tải ảnh game '{game_display_tag}': {e}")
                            icon_to_use = None 
            
            if not icon_to_use:
                icon_to_use = service_icon_img

            if icon_to_use:
                img_label = ttk.Label(mid_frame, image=icon_to_use)
                img_label.grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky=tk.W)
                widgets_to_bind.append(img_label)

            # Dùng grid để căn chỉnh thông tin
            # (Tạo và bind các label)
            l1 = ttk.Label(mid_frame, text="Nickname:", style="secondary.TLabel")
            l1.grid(row=1, column=0, sticky=tk.W)
            v1 = ttk.Label(mid_frame, text=nickname, font=("Segoe UI", 10, "bold"))
            v1.grid(row=1, column=1, sticky=tk.W, padx=5)
            
            l2 = ttk.Label(mid_frame, text="Game (Tag):", style="secondary.TLabel")
            l2.grid(row=2, column=0, sticky=tk.W)
            v2 = ttk.Label(mid_frame, text=(game_display_tag if game_display_tag else "(Không gán Game)"))
            v2.grid(row=2, column=1, sticky=tk.W, padx=5)

            l3 = ttk.Label(mid_frame, text="Dịch vụ:", style="secondary.TLabel")
            l3.grid(row=3, column=0, sticky=tk.W)
            v3 = ttk.Label(mid_frame, text=acc_type)
            v3.grid(row=3, column=1, sticky=tk.W, padx=5)
            
            widgets_to_bind.extend([l1, v1, l2, v2, l3, v3])

            # 4. Frame bên phải (Nút Sửa/Xóa)
            right_frame = ttk.Frame(card)
            right_frame.pack(side=tk.RIGHT, fill=tk.Y)
            widgets_to_bind.append(right_frame)

            edit_btn = tk.Button(
                right_frame, 
                text="Sửa",
                width=10,         # Màu nền Đỏ (Thay cho style Danger)
                fg="white",                 # Màu chữ Trắng
                activeforeground="white",   # Màu chữ khi nhấn
                relief='groove',
                borderwidth=1,              # Đặt độ dày viền bằng 0
                highlightthickness=0,              # (Tùy chọn) Làm phẳng nút cho đẹp
                cursor="hand2", 
                command=lambda index=i: open_add_edit_account_popup(index)
            )
            edit_btn.pack(pady=(0, 5))
            
            delete_btn = tk.Button(
                right_frame, 
                text="Xóa", 
                width=10,
                bg="#c94e4e",               # Màu nền Đỏ (Thay cho style Danger)
                fg="white",                 # Màu chữ Trắng
                activebackground="#a13e3e", # Màu khi nhấn vào (Đỏ đậm hơn)
                activeforeground="white",   # Màu chữ khi nhấn
                relief='groove',              # (Tùy chọn) Làm phẳng nút cho đẹp
                borderwidth=1,              # Đặt độ dày viền bằng 0
                highlightthickness=0,
                cursor="hand2",             # (Tùy chọn) Con trỏ bàn tay
                command=lambda index=i: delete_selected_account_by_index(index)
            )
            delete_btn.pack()
            
            g_dynamic_account_buttons.append(edit_btn)
            g_dynamic_account_buttons.append(delete_btn)
            widgets_to_bind.extend([edit_btn, delete_btn])

        # --- THÊM MỚI: GẮN (BIND) TẤT CẢ WIDGETS ---
        for widget in widgets_to_bind:
            try:
                widget.bind("<MouseWheel>", on_acct_list_mouse_wheel)
                widget.bind("<Button-4>", on_acct_list_mouse_wheel) # Linux scroll up
                widget.bind("<Button-5>", on_acct_list_mouse_wheel) # Linux scroll down
            except tk.TclError as e:
                print(f"Lỗi khi bind widget: {e}")
        
        # Cũng bind canvas chính
        g_acct_list_canvas.bind("<MouseWheel>", on_acct_list_mouse_wheel)
        g_acct_list_canvas.bind("<Button-4>", on_acct_list_mouse_wheel)
        g_acct_list_canvas.bind("<Button-5>", on_acct_list_mouse_wheel)
        # --- HẾT THÊM MỚI ---

        # Chuyển trang
        switch_account_page(g_acct_page_2_list)

    # --- Xử lý Đăng nhập, Thêm, Sửa, Xóa ---

    def action_login_by_index(item_index):
        """
        (Hàm MỚI thay thế on_account_double_click)
        Lấy thông tin từ index và chạy đăng nhập.
        """
        print("--- DEBUG: 1. Đã bấm nút 'Đăng nhập' ---") # DEBUG 1
        global local_config, g_user_accounts_data, g_acct_current_game
        global g_login_overlay_popup, g_login_overlay_label
        
        # Lấy thông tin account từ config
        try:
            acc_info = g_user_accounts_data[g_acct_current_game][item_index]
            username = acc_info.get("username")
            password = acc_info.get("password", "")
            acc_type = acc_info.get("type", "steam")
            print(f"--- DEBUG: 2. Lấy thông tin thành công. Type: {acc_type}, User: {username} ---") # DEBUG 2
            
        except Exception as e:
            print(f"--- DEBUG: LỖI NGHIÊM TRỌNG. Không thể lấy thông tin account: {e} ---") # DEBUG 3
            custom_showerror("Lỗi", "Không thể lấy thông tin account này.")
            return

        # --- LOGIC ĐĂNG NHẬP (Giữ nguyên từ code cũ) ---
        if acc_type == "steam":
            print("--- DEBUG: 3a. Bắt đầu logic Steam ---")
            steam_path = local_config.get("steam_path", "")
            if not steam_path or not os.path.exists(steam_path):
                custom_showerror("Lỗi", "Đường dẫn 'steam.exe' không hợp lệ.")
                return
            
            print(f"Đang chạy Steam cho user: {username}")
            try:
                subprocess.Popen([steam_path, "-shutdown"]) 
                time.sleep(3) 
                subprocess.Popen([steam_path, "-login", username, password])
            except Exception as e:
                custom_showerror("Lỗi", f"Không thể chạy Steam: {e}")

        elif acc_type == "riot":
            # (Giữ lại các DEBUG print của bạn nếu muốn)
            print("--- DEBUG: 3b. Bắt đầu logic Riot ---") 
            riot_path = local_config.get("riot_path", "")
            print(f"--- DEBUG: 4. Lấy Riot Path từ config: '{riot_path}' ---")
            
            # Bước kiểm tra đường dẫn (Giữ nguyên)
            if not riot_path:
                print("--- DEBUG: LỖI 5a. Riot Path BỊ RỖNG. Dừng lại. ---")
                custom_showerror("Lỗi", "Đường dẫn Riot Client BỊ RỖNG.\nVui lòng vào Tab 'Credit' -> 'Cài Đặt' để thiết lập.")
                return
                
            if not os.path.exists(riot_path):
                print(f"--- DEBUG: LỖI 5b. Path '{riot_path}' KHÔNG TỒN TẠI. Dừng lại. ---")
                custom_showerror("Lỗi", f"Đường dẫn Riot Client KHÔNG TỒN TẠI:\n{riot_path}\n\nVui lòng kiểm tra lại.")
                return

            # --- SỬA: KHÔNG TẠO POP-UP, CHỈ SET LABEL ---
            print("--- DEBUG: 6. Đường dẫn HỢP LỆ. Cập nhật label và chạy Thread... ---")
            try:
                # Cập nhật nhãn trạng thái ngay lập tức
                if 'g_acct_login_status_label' in globals():
                    g_acct_login_status_label.config(text="Đang bắt đầu...", style="White.TLabel")
                    global g_dynamic_account_buttons

                if 'g_acct_page_2_back_btn' in globals():
                    g_acct_page_2_back_btn.config(state=tk.DISABLED)
                if 'g_acct_page_2_add_btn' in globals():
                    g_acct_page_2_add_btn.config(state=tk.DISABLED)
                    
                for btn in g_dynamic_account_buttons:
                    try:
                        btn.config(state=tk.DISABLED)
                    except tk.TclError:
                        pass
            except Exception as e:
                print(f"Lỗi khi set label: {e}")

            # --- BẮT ĐẦU THREAD (NHƯ CŨ) ---
            print(f"Bắt đầu thread đăng nhập Riot cho: {username}")
            threading.Thread(
                target=launch_riot_login_thread, 
                args=(riot_path, username, password), 
                daemon=True
            ).start()
            print("--- DEBUG: 9. Đã khởi động Thread. Hàm action_login_by_index kết thúc. ---")

    def delete_selected_account_by_index(item_index):
        """(Hàm MỚI thay thế delete_selected_account)"""
        global g_user_accounts_data, g_acct_current_game
        
        # Lấy nickname để xác nhận
        try:
            nickname = g_user_accounts_data[g_acct_current_game][item_index]["nickname"]
        except Exception:
            nickname = "Account đã chọn"
            
        if custom_askyesno("Xác nhận Xóa", f"Bạn có chắc chắn muốn xóa '{nickname}'?"):
            try:
                g_user_accounts_data[g_acct_current_game].pop(item_index)
                
                if not g_user_accounts_data[g_acct_current_game]:
                    del g_user_accounts_data[g_acct_current_game]
                
                mark_accounts_as_dirty()
                
                # Refresh
                show_account_list_for_game(g_acct_current_game) # Refresh danh sách
                populate_account_game_grid() # Refresh lưới (vì game có thể bị xóa)
                
            except Exception as e:
                custom_showerror("Lỗi", f"Không thể xóa account: {e}")



    def open_add_edit_account_popup(edit_index):
        """
        (ĐÃ SỬA LOGIC LƯU)
        Pop-up Thêm/Sửa.
        """
        global g_acct_current_game, g_user_accounts_data, g_game_themes

        popup = tk.Toplevel(root)
        popup.transient(root)
        popup.grab_set()
        form_frame = ttk.Frame(popup, padding=20)
        form_frame.pack()

        # --- Lấy dữ liệu cũ (nếu là Sửa) ---
        is_editing = (edit_index is not None)
        old_data = {}
        if is_editing:
            popup.title(f"Sửa Account (từ {g_acct_current_game})")
            try:
                old_data = g_user_accounts_data[g_acct_current_game][edit_index]
            except:
                custom_showerror("Lỗi", "Không thể tìm thấy dữ liệu account để sửa.")
                popup.destroy()
                return
        else:
            popup.title(f"Thêm Account vào {g_acct_current_game}")

        # --- Tạo Form (Code không đổi) ---
        widgets = {}
        
        # 1. DỊCH VỤ (Service) (BẮT BUỘC)
        ttk.Label(form_frame, text="Dịch vụ (Service):").pack()
        service_list = ["Steam", "Riot"] 
        service_combo = ttk.Combobox(form_frame, values=service_list, state="readonly", width=38)
        service_combo.pack(pady=5)
        
        default_service = g_acct_current_game # Mặc định
        if is_editing:
            default_service = old_data.get("type", "steam").capitalize() 
        if default_service not in service_list:
            default_service = "Steam"
            
        service_combo.set(default_service)
        widgets["service"] = service_combo 

        # 2. GAME (Tag) (BẮT BUỘC)
        ttk.Label(form_frame, text="Game (Key chính):").pack()
        
        # --- SỬA LỖI: Chuyển .keys() thành set() TRƯỚC khi dùng | ---
        game_list = sorted(list(set(g_game_themes.keys()) | {"Steam", "Riot"}))
        # --- HẾT SỬA LỖI ---
        
        game_combo = ttk.Combobox(form_frame, values=game_list, state="readonly", width=38)
        game_combo.pack(pady=5)
        
        default_game_to_set = "" # Mặc định là chuỗi rỗng (an toàn)

        if is_editing:
            # Nếu đang SỬA, lấy game đã lưu (fallback về game đang xem)
            default_game_to_set = old_data.get("game", g_acct_current_game)
        else:
            # Nếu đang THÊM MỚI, chỉ đặt game mặc định nếu nó không phải là None
            if g_acct_current_game is not None:
                default_game_to_set = g_acct_current_game
                
        # Giờ đây default_game_to_set sẽ là Tên Game (str) hoặc "" (str), không bao giờ là None
        game_combo.set(default_game_to_set)
        widgets["game"] = game_combo 
        
        # 3. Nickname (Code không đổi)
        ttk.Label(form_frame, text="Tên gợi nhớ (Nickname):").pack()
        nickname_entry = ttk.Entry(form_frame, width=40)
        nickname_entry.pack(pady=5)
        nickname_entry.insert(0, old_data.get("nickname", ""))
        widgets["nickname"] = nickname_entry

        # 4. Username (Code không đổi)
        ttk.Label(form_frame, text="Username Đăng nhập:").pack()
        username_entry = ttk.Entry(form_frame, width=40)
        username_entry.pack(pady=5)
        username_entry.insert(0, old_data.get("username", ""))
        widgets["username"] = username_entry
        
        # 5. Password (Code không đổi)
        ttk.Label(form_frame, text="Password:").pack()
        password_entry = ttk.Entry(form_frame, width=40, show="*")
        password_entry.pack(pady=5)
        password_entry.insert(0, old_data.get("password", ""))
        widgets["password"] = password_entry
        
        # --- Hàm Lưu (Code không đổi) ---
        def save_account():
            global g_user_accounts_data
            
            selected_service = widgets["service"].get()
            selected_game = widgets["game"].get()

            if not selected_game:
                custom_showwarning("Thiếu thông tin", "Bạn phải chọn một Game.", parent=popup)
                return
                
            account_type = selected_service.lower()
            game_to_save = selected_game
            
            new_data = {
                "nickname": widgets["nickname"].get().strip(),
                "username": widgets["username"].get().strip(),
                "password": widgets["password"].get().strip(),
                "type": account_type,
                "game": game_to_save
            }
            
            if not new_data["nickname"] or not new_data["username"]:
                custom_showwarning("Thiếu thông tin", "Nickname và Username là bắt buộc.", parent=popup)
                return

            if is_editing:
                original_game_key = g_acct_current_game 
                
                if selected_game == original_game_key:
                    account_list = g_user_accounts_data.setdefault(original_game_key, [])
                    account_list[edit_index] = new_data
                else:
                    g_user_accounts_data.setdefault(selected_game, []).append(new_data)
                    try:
                        g_user_accounts_data[original_game_key].pop(edit_index)
                        if not g_user_accounts_data[original_game_key]:
                            del g_user_accounts_data[original_game_key]
                    except Exception as e:
                        print(f"Lỗi khi xóa item cũ trong lúc di chuyển: {e}")
            else:
                g_user_accounts_data.setdefault(selected_game, []).append(new_data)

            mark_accounts_as_dirty()

            populate_account_game_grid()
            
            show_account_list_for_game(g_acct_current_game) 
            
            popup.destroy()

        # --- Nút Bấm ---
        save_button = ttk.Button(form_frame, text="Lưu", command=save_account, style="Accent.TButton")
        save_button.pack(pady=10)
        popup.update_idletasks() # Bắt Toplevel tính toán kích thước
        width = popup.winfo_width()
        height = popup.winfo_height()
        center_window_on_screen(popup, width, height)

    def action_go_back_and_refresh_grid():
        """
        (HÀM MỚI) Refresh Lưới Game (Trang 1) và quay lại đó.
        """
        global download_options, g_game_search_entry

        print("Đang quay lại và làm mới Lưới Game (Trang 1)...")
        try:
            # Lấy từ khóa tìm kiếm hiện tại (nếu có)
            search_term = ""
            if g_game_search_entry:
                search_term = g_game_search_entry.get().lower()

            # 1. Gọi hàm vẽ lại Trang 1
            # (download_options là biến toàn cục đã có)
            populate_page_1_grid(download_options, search_term)

            # 2. Quay lại Trang 1
            show_page(page_1_game_grid)
        except Exception as e:
            print(f"Lỗi khi quay lại và làm mới Lưới Game: {e}")
            # Fallback: Dù lỗi cũng quay lại
            show_page(page_1_game_grid)


    # --- HẾT CODE CHO TAB 2 ("Quản lý Account") ---
    # --- THÊM MỚI: TẠO 3 KHUNG TRANG (PAGE) ---
    page_1_game_grid = ttk.Frame(main_tab_frame, padding=(10, 10))
    page_2_mod_list = ttk.Frame(main_tab_frame, padding=(10, 10))
    page_3_progress = ttk.Frame(main_tab_frame, padding=(10, 10))

    page_1_game_grid.place(relx=0, rely=0, relwidth=1, relheight=1)
    g_tab1_loading_frame = ttk.Frame(page_1_game_grid, name="tab1_loading_frame")
    g_tab1_loading_frame.pack(expand=True, anchor=tk.CENTER)

    ttk.Label(g_tab1_loading_frame, text="Đang tải danh sách game và themes...").pack(pady=5)
    tab1_loader = ttk.Progressbar(g_tab1_loading_frame, orient="horizontal", length=200, mode="indeterminate")
    tab1_loader.pack(pady=10)
    tab1_loader.start(10)

    page_2_mod_list.place(relx=1, rely=0, relwidth=1, relheight=1) # Bắt đầu ở bên phải
    page_3_progress.place(relx=1, rely=0, relwidth=1, relheight=1) # Bắt đầu ở bên phải

    # Biến global để theo dõi trang/animation
    global g_current_page, g_is_animating
    g_current_page = page_1_game_grid # Bắt đầu ở Trang 1
    g_is_animating = False

    global g_launch_game_button
    g_current_launch_path = None

    # 1. Tạo khung cố định (placeholder) với kích thước LỚN
    image_placeholder_frame = ttk.Frame(
        page_2_mod_list, 
        width=460, 
        height=215
    )
    image_placeholder_frame.pack(pady=(0, 10))

    # 2. Ngăn khung co lại (RẤT QUAN TRỌNG)
    image_placeholder_frame.pack_propagate(False) 

    # 3. Tạo Label ảnh BÊN TRONG khung placeholder (KHÔNG .pack() ở đây)
    global g_game_image_label
    g_game_image_label = ttk.Label(image_placeholder_frame, anchor=tk.CENTER)

    # --- THÊM MỚI: TẠO LABEL CHO GIF ---
    global g_gif_label
    g_gif_label = ttk.Label(page_3_progress)
    root.gif_frames = [] # Nơi lưu các frame
    root.gif_frame_index = 0

    page_2_top_nav_frame = ttk.Frame(page_2_mod_list)
    page_2_top_nav_frame.pack(fill=tk.X, pady=(0, 10))

    # 1. Nút "Quay lại" (Bên trái)
    page_2_back_button = ttk.Button(page_2_top_nav_frame, text="❮ Quay lại (Chọn Game)", 
                                    command=action_go_back_and_refresh_grid)
    page_2_back_button.pack(side=tk.LEFT)

    g_launch_game_button = ttk.Button(
        page_2_top_nav_frame, 
        text="🚀 Chạy Game", 
        command=action_launch_game, 
        style="Accent.TButton"
    )

    global g_set_path_button
    g_set_path_button = ttk.Button(
        page_2_top_nav_frame,
        text="⚙️", 
        command=action_set_game_path_from_page_2,
        width=2 
    )
    CreateToolTip(g_set_path_button, "Chọn đường dẫn đến file khởi động game")

    # 2. Nút "Bắt đầu Cài đặt" (Bên phải)
    # (Đã di chuyển từ dưới lên đây)

    # Cấu hình grid của main_tab_frame
    main_tab_frame.grid_rowconfigure(0, weight=1)
    main_tab_frame.grid_columnconfigure(0, weight=1)


    def show_page(page_to_show):
        """(ĐÃ SỬA) Chuyển trang (KHÔNG có hiệu ứng trượt)."""
        global g_current_page, page_2_back_button, g_set_path_button
        
        # Nếu đang ở trang đó, không làm gì
        if g_current_page == page_to_show:
            return 
        
        # Ẩn các nút nếu rời Trang 2
        if g_current_page == page_2_mod_list and page_to_show != page_3_progress:
            if 'g_launch_game_button' in globals():
                g_launch_game_button.pack_forget()
            if 'page_2_back_button' in globals():
                page_2_back_button.pack_forget()
            if 'g_set_path_button' in globals():
                g_set_path_button.pack_forget()

        print(f"Đang chuyển trang: {g_current_page.winfo_name()} -> {page_to_show.winfo_name()}")

        # --- SỬA LỖI: Bỏ animation ---
        # 1. Ẩn trang hiện tại (đặt nó ở relx=1, bên phải)
        g_current_page.place(relx=1, rely=0, relwidth=1, relheight=1)
        
        # 2. Hiển thị trang mới (đặt nó ở relx=0, ngay giữa)
        page_to_show.place(relx=0, rely=0, relwidth=1, relheight=1)
        page_to_show.tkraise() # Đảm bảo nó ở trên cùng
        
        # 3. Cập nhật trang hiện tại
        g_current_page = page_to_show
        # --- HẾT SỬA ---

    # --- THÊM MỚI: HÀM ANIMATION TRƯỢT ---
    def animate_slide(page_from, page_to, direction="left"):
        """
        Hàm animation chính. Di chuyển page_from ra và page_to vào.
        'direction' quyết định hướng trượt.
        """
        global g_is_animating, g_current_page
        if g_is_animating:
            return # Nếu đang chạy, không làm gì cả
        g_is_animating = True

        # ---- Cài đặt vị trí ----
        # Vị trí bắt đầu của trang mới (page_to)
        start_relx_to = 1.0 if direction == "left" else -1.0
        # Vị trí kết thúc của trang cũ (page_from)
        target_relx_from = -1.0 if direction == "left" else 1.0
        
        # Đặt trang mới vào vị trí bắt đầu và đưa nó lên trên
        page_to.place(relx=start_relx_to, rely=0, relwidth=1, relheight=1)
        page_to.tkraise()

        # ---- Cài đặt Animation Loop ----
        steps = 30 # Tổng số bước cho animation
        delay_ms = 16 # Thời gian mỗi bước (ms). 8ms ~ 120 FPS
                    # Bạn có thể tăng lên 16ms (~60 FPS) nếu thấy giật

        def step_loop(current_step):
            """Hàm con được gọi lặp lại cho mỗi bước animation."""
            global g_is_animating, g_current_page

            # 1. Tính toán tiến trình (progress)
            progress = current_step / steps
            # Dùng công thức "Ease-Out" để animation mượt hơn ở cuối
            ease_progress = (1 - math.cos(progress * math.pi)) / 2

            # 2. Tính vị trí X mới
            if direction == "left":
                # Trang cũ (từ 0) -> (tới -1)
                new_relx_from = 0.0 - ease_progress
                # Trang mới (từ 1) -> (tới 0)
                new_relx_to = 1.0 - ease_progress
            else: # "right"
                # Trang cũ (từ 0) -> (tới 1)
                new_relx_from = 0.0 + ease_progress
                # Trang mới (từ -1) -> (tới 0)
                new_relx_to = -1.0 + ease_progress

            # 3. Cập nhật vị trí 2 trang
            page_from.place(relx=new_relx_from, rely=0, relwidth=1, relheight=1)
            page_to.place(relx=new_relx_to, rely=0, relwidth=1, relheight=1)

            # 4. Lặp lại hoặc Kết thúc
            if current_step < steps:
                # Nếu chưa xong, gọi lại hàm này sau 'delay_ms'
                root.after(delay_ms, step_loop, current_step + 1)
            else:
                # Hoàn tất!
                # Đặt dứt điểm 2 trang vào vị trí cuối cùng
                page_from.place(relx=target_relx_from, rely=0, relwidth=1, relheight=1)
                page_to.place(relx=0, rely=0, relwidth=1, relheight=1) 
                
                # Cập nhật trạng thái
                g_is_animating = False
                g_current_page = page_to # Cập nhật trang hiện tại là trang mới
        
        # Bắt đầu vòng lặp animation từ bước 1
        step_loop(1)

    # --- THÊM MỚI: HÀM CONFIGURE CHO CANVAS TRANG 1 ---
    def on_page_1_content_configure(event):
        """Cập nhật scroll region của canvas Trang 1."""
        page_1_canvas.configure(scrollregion=page_1_canvas.bbox("all"))

    def on_page_1_canvas_configure(event):
        """(SỬA) Căn giữa lưới game (g_game_grid_container) theo chiều ngang."""
        canvas_width = event.width
        page_1_canvas.coords(page_1_canvas_window_id, (canvas_width / 2) - 35 , 0)
    # --- Nội dung Tab 1 ---




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



    # --- THÊM MỚI: HÀM TẢI ẢNH TỪ URL ---
    def load_image_from_url(url, size=(192, 89)):
        """
        Tải ảnh từ URL, resize, và trả về PhotoImage.
        Sử dụng 3 cấp cache: RAM -> Ổ cứng -> Internet.
        """
        global g_cache_dir # Lấy thư mục cache
        
        # 1. TẠO KEY VÀ FILE PATH
        # Tạo một key duy nhất (gồm URL và kích thước)
        cache_key = f"{url}_{size[0]}x{size[1]}"
        
        # Tạo tên file an toàn bằng cách "băm" (hash) key đó
        # (Điều này tránh các ký tự không hợp lệ trong tên file)
        cache_filename = f"{hashlib.sha256(cache_key.encode('utf-8')).hexdigest()}.png"
        cache_file_path = os.path.join(g_cache_dir, cache_filename)

        # 2. KIỂM TRA CACHE CẤP 1 (RAM)
        if cache_key in root.cached_images:
            return root.cached_images[cache_key]

        # 3. KIỂM TRA CACHE CẤP 2 (Ổ CỨNG)
        try:
            if os.path.exists(cache_file_path):
                # print(f"Cache HIT (Ổ cứng): {cache_key}")
                # Tải ảnh từ file cache
                img = Image.open(cache_file_path)
                # (Không cần resize vì chúng ta đã lưu file đã resize)
                
                img_tk = ImageTk.PhotoImage(img)
                root.cached_images[cache_key] = img_tk # Lưu vào RAM cho lần sau
                return img_tk
        except Exception as e:
            print(f"Lỗi đọc file cache (sẽ tải lại): {cache_file_path}. Lỗi: {e}")
            try:
                os.remove(cache_file_path) # Xóa file cache hỏng
            except:
                pass # Bỏ qua nếu xóa lỗi

        # 4. KIỂM TRA CACHE CẤP 3 (INTERNET) - (Cache MISS)
        try:
            # print(f"Cache MISS (Internet): {cache_key}")
            response = requests.get(url, timeout=5)
            response.raise_for_status()

            image_data = response.content
            img = Image.open(io.BytesIO(image_data))
            
            # --- SỬA LOGIC: Đảm bảo ảnh có kênh Alpha (RGBA) ---
            # Điều này rất quan trọng để lưu file PNG trong suốt
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            # --- HẾT SỬA ---

            img = img.resize(size, Image.Resampling.LANCZOS)
            
            # --- LƯU VÀO Ổ CỨNG ---
            try:
                img.save(cache_file_path, "PNG") # Lưu file .png đã resize
            except Exception as e:
                print(f"Lỗi lưu file cache: {e}")
            # --- HẾT LƯU ---
            
            img_tk = ImageTk.PhotoImage(img)
            root.cached_images[cache_key] = img_tk # Lưu vào RAM
            return img_tk
            
        except Exception as e:
            print(f"Lỗi khi tải ảnh từ URL '{url}': {e}")
            root.cached_images[cache_key] = None # Lưu lỗi (None) vào RAM
            return None

    # Lưu vào root để không bị garbage-collected
    root.drive_icon_zip = load_drive_icon("zip_icon.png")
    root.drive_icon_exe = load_drive_icon("exe_icon.png")
    root.drive_icon_rar = load_drive_icon("rar_icon.png")
    root.drive_icon_unknown = load_drive_icon("unknown_icon.png")
    # --- HẾT THÊM MỚI ---
    # 1. Tạo options_frame (LabelFrame) làm frame host CỐ ĐỊNH
    # Frame này sẽ có chiều cao CỐ ĐỊNH và chứa cả canvas lẫn scrollbar
    options_frame = ttk.LabelFrame(page_2_mod_list, text="Bro muốn làm gì?", padding=(5, 5), height=275)
    options_frame.pack(fill=tk.X, expand=False, pady=10, padx=(10, 0))
    options_frame.pack_propagate(False) # RẤT QUAN TRỌNG: Giữ chiều cao cố định

    # --- THÊM MỚI: KHUNG HƯỚNG DẪN CHỌN ĐƯỜNG DẪN ---
    # 1. Đặt chiều cao cố định (ví dụ: 100px)
    guide_frame = ttk.LabelFrame(page_2_mod_list, text="💡 Hướng dẫn chọn đường dẫn", padding=(5, 5), height=100)
    guide_frame.pack(fill=tk.X, pady=(0, 5), padx=(10, 0))
    # 2. Ngăn frame tự co dãn theo nội dung
    guide_frame.pack_propagate(False) 

    # 3. Thêm Scrollbar
    guide_scrollbar = ttk.Scrollbar(guide_frame, orient="vertical")
    guide_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=(0, 2), padx=(0, 2)) 

    # 4. Thay thế Label bằng Text widget
    guide_text_widget = tk.Text(
        guide_frame, 
        wrap="word", # Tự động xuống dòng
        relief=tk.FLAT, # Bỏ viền
        borderwidth=0,
        highlightthickness=0,
        yscrollcommand=guide_scrollbar.set
    )
    guide_text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # 5. Gắn scrollbar
    guide_scrollbar.config(command=guide_text_widget.yview)

    # 6. Chèn text mặc định và khóa widget
    guide_text_widget.insert(tk.END, "Hãy chọn một mod ở trên để xem hướng dẫn...")
    guide_text_widget.config(state=tk.DISABLED)

    # 2. Tạo Scrollbar BÊN TRONG options_frame
    scrollbar = ttk.Scrollbar(options_frame, orient="vertical")
    # Pack scrollbar BÊN PHẢI. Thêm padding nhỏ để không dính viền
    # scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=(0, 2), padx=(0, 2)) 

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

    # --- THÊM MỚI: HÀM CẬP NHẬT TEXT HƯỚNG DẪN ---
    def update_guide_text():
        """
        (ĐÃ VIẾT LẠI) 
        1. Cập nhật text hướng dẫn.
        2. Kiểm tra file khởi chạy và Ẩn/Hiện nút "Khởi chạy".
        """
        global g_current_launch_path, g_all_mods_flat, g_launch_game_button, path_entry

        # 1. ẨN NÚT (Mặc định) VÀ RESET PATH
        # (Nút sẽ được hiện lại ở Bước 5 nếu file tồn tại)
        if 'g_launch_game_button' in globals():
            g_launch_game_button.pack_forget()
            
        if 'g_set_path_button' in globals():
            try:
                g_set_path_button.pack_forget()
            except tk.TclError:
                pass
        g_current_launch_path = None 

        try:
            guide_text_widget.config(state=tk.NORMAL) # Mở khóa để sửa
            guide_text_widget.delete("1.0", tk.END) # Xóa text cũ

            selected_key = selected_option.get()

            # 2. KIỂM TRA XEM CÓ CHỌN MOD KHÔNG
            if selected_key and selected_key in g_all_mods_flat:

                # 3. LẤY DATA
                selected_option_data = g_all_mods_flat[selected_key] 

                # 4. CẬP NHẬT HƯỚNG DẪN PATH
                raw_guide = selected_option_data.get("path_guide")
                if raw_guide:
                    guide_text = str(raw_guide) # Đảm bảo là string
                else:
                    guide_text = "Không có hướng dẫn cho mod này."
                guide_text_widget.insert(tk.END, guide_text)

                # 5. KIỂM TRA FILE KHỞI CHẠY (LOGIC MỚI)
                if 'game_launchers' in local_config:
                    found_launch_file = local_config['game_launchers'].get(g_current_game_name)
                    if found_launch_file:
                        print(f"Đã tìm thấy launch file do người dùng cài đặt: {found_launch_file}")


                # Ưu tiên 2: Lấy từ JSON (nếu local không có)
                if not found_launch_file:
                    mod_list = download_options.get(g_current_game_name, [])
                    for _key, mod_data in mod_list:
                        if mod_data.get("launch_file"):
                            found_launch_file = mod_data.get("launch_file")
                            print(f"Đã tìm thấy launch file từ JSON: {found_launch_file}")
                            break # Lấy file đầu tiên tìm thấy

                destination_folder = local_config.get("game_paths", {}).get(g_current_game_name, "")

                # 6. Kiểm tra file (logic không đổi, chỉ đổi tên biến)
                # Chỉ kiểm tra nếu:
                # - Tìm thấy một "launch_file"
                # - Ô đường dẫn không rỗng
                # - Đường dẫn là một thư mục có thật
                if found_launch_file and destination_folder and os.path.isdir(destination_folder):

                    full_file_path = os.path.join(destination_folder, found_launch_file)

                    # Nếu tìm thấy file...
                    if os.path.exists(full_file_path) and os.path.isfile(full_file_path):
                        print(f"Persistent Check (Page 2): Tìm thấy file khởi chạy: {full_file_path}")
                        g_current_launch_path = full_file_path
                    else:
                        # (Debug) Báo nếu đã cấu hình nhưng không tìm thấy file
                        print(f"Persistent Check (Page 2): Đã cấu hình '{found_launch_file}' nhưng không tìm thấy tại '{destination_folder}'")

            else:
                # (Nếu không có mod nào được chọn)
                guide_text_widget.insert(tk.END, "Hãy chọn một mod ở trên để xem hướng dẫn...")

        except Exception as e:
            print(f"Lỗi khi cập nhật hướng dẫn/launch button: {e}")
            guide_text_widget.delete("1.0", tk.END)
            guide_text_widget.insert(tk.END, "Lỗi khi tải hướng dẫn.")
        finally:
            guide_text_widget.config(state=tk.DISABLED)
            try:
                # --- [SỬA ĐỔI: ĐỔI THỨ TỰ PACK] ---
                
                # 1. Pack nút "Đặt đường dẫn" (⚙️) TRƯỚC 
                # -> Kết quả: Nó sẽ nằm ở NGOÀI CÙNG BÊN PHẢI
                if 'g_set_path_button' in globals():
                    g_set_path_button.pack(side=tk.RIGHT, padx=(0, 5)) 

                # 2. Pack nút "Chạy Game" (🚀) SAU
                # -> Kết quả: Nó sẽ nằm bên TRÁI nút bánh răng
                if 'g_launch_game_button' in globals():
                    g_launch_game_button.pack(side=tk.RIGHT, padx=(0, 10)) 
                    
                    # Cấu hình trạng thái (ENABLE/DISABLE)
                    if g_current_launch_path:
                        g_launch_game_button.config(state=tk.NORMAL)
                    else:
                        g_launch_game_button.config(state=tk.DISABLED)

            except Exception as e:
                print(f"Lỗi khi pack nút bên phải: {e}")
            # --- (END) THAY ĐỔI ---


    def on_game_search(event):
        """Lọc lưới game ở Trang 1 dựa trên nội dung ô tìm kiếm."""
        if not g_game_search_entry: # Nếu UI chưa sẵn sàng
            return

        search_term = g_game_search_entry.get().lower()

        # Gọi lại hàm populate, truyền vào dict đã nhóm và từ khóa
        populate_page_1_grid(download_options, search_term)

    # --- THÊM MỚI: HÀM XÓA TÌM KIẾM (BỊ THIẾU) ---
    def action_clear_game_search():
        """Xóa ô tìm kiếm và hiển thị lại tất cả game."""
        if not g_game_search_entry:
            return
        g_game_search_entry.delete(0, tk.END) # Xóa text

        # Gọi lại hàm populate với search_term rỗng
        # (Lưu ý: 'download_options' là biến toàn cục)
        populate_page_1_grid(download_options, search_term="")

    def action_delete_custom_game(game_name):
        """Xóa game custom khỏi danh sách."""
        if custom_askyesno("Xóa Game", f"Bạn có chắc chắn muốn xóa game '{game_name}' khỏi danh sách không?\n(File game trên máy sẽ KHÔNG bị xóa)."):
            try:
                # Xóa khỏi config
                if game_name in local_config['custom_games']:
                    del local_config['custom_games'][game_name]
                    save_local_config(local_config)
                    
                    # Làm mới lưới
                    action_clear_game_search()
                    custom_showinfo("Đã xóa", f"Đã xóa '{game_name}'.")
            except Exception as e:
                custom_showerror("Lỗi", f"Không thể xóa: {e}")

    def action_change_game_image(game_name, is_custom):
        """Đổi ảnh bìa cho game (Cả Custom và Server)."""
        new_url = custom_askstring("Đổi Ảnh", f"Nhập URL hình ảnh mới cho '{game_name}':")
        
        if not new_url: return
        
        try:
            # 1. Tải ảnh về
            response = requests.get(new_url, timeout=10)
            response.raise_for_status()
            img_data = response.content
            
            # 2. Tạo tên file cache an toàn
            safe_name = "".join([c for c in game_name if c.isalnum() or c in (' ', '-', '_')]).strip()
            img_filename = f"override_{safe_name}.png"
            local_img_path = os.path.join(g_cache_dir, img_filename)
            
            # 3. Resize và Lưu
            if not os.path.exists(g_cache_dir): os.makedirs(g_cache_dir)
            
            with Image.open(io.BytesIO(img_data)) as img:
                # Lưu bản chất lượng cao (460x215)
                img_resized = img.resize((460, 215), Image.Resampling.LANCZOS)
                img_resized.save(local_img_path, "PNG")
                
            # 4. Lưu đường dẫn vào Config
            if is_custom:
                # Nếu là game custom, cập nhật trực tiếp vào custom_games
                local_config['custom_games'][game_name]['image_local_path'] = local_img_path
            else:
                # Nếu là game server, lưu vào theme_overrides
                if 'theme_overrides' not in local_config:
                    local_config['theme_overrides'] = {}
                local_config['theme_overrides'][game_name] = local_img_path
                
            save_local_config(local_config)
            
            # 5. Xóa cache RAM cũ để nó load ảnh mới
            keys_to_remove = [k for k in root.cached_images.keys() if safe_name in k or game_name in k]
            for k in keys_to_remove:
                del root.cached_images[k]

            # 6. Làm mới giao diện
            action_clear_game_search()
            custom_showinfo("Thành công", "Đã cập nhật ảnh bìa!")

        except Exception as e:
            custom_showerror("Lỗi", f"Không thể tải ảnh: {e}")

    def action_rename_game(game_key):
        """Đổi tên hiển thị của game (Alias)."""
        # Lấy tên hiện tại (nếu đã đổi thì lấy tên đổi, chưa thì lấy tên gốc)
        current_alias = local_config.get('display_name_overrides', {}).get(game_key, game_key)
        
        new_name = custom_askstring("Đổi Tên", f"Nhập tên mới cho '{game_key}':", initialvalue=current_alias)
        
        if new_name is not None: # Nếu không bấm Cancel
            if not new_name.strip() or new_name.strip() == game_key:
                # Nếu để trống hoặc nhập trùng tên gốc -> Xóa Alias (Reset)
                if game_key in local_config['display_name_overrides']:
                    del local_config['display_name_overrides'][game_key]
            else:
                # Lưu tên mới
                local_config['display_name_overrides'][game_key] = new_name.strip()
                
            save_local_config(local_config)
            action_clear_game_search() # Làm mới giao diện

    def action_remove_custom_image(game_key):
        """Xóa ảnh custom để quay về ảnh gốc từ Server."""
        if custom_askyesno("Khôi phục ảnh", f"Bạn muốn xóa ảnh tùy chỉnh của '{game_key}'\nvà quay lại dùng ảnh gốc từ Server?"):
            try:
                # Xóa khỏi config
                if game_key in local_config['theme_overrides']:
                    del local_config['theme_overrides'][game_key]
                    save_local_config(local_config)
                
                # Xóa cache RAM để nó load lại ảnh gốc
                # (Tìm các key cache chứa tên game và xóa)
                safe_name = "".join([c for c in game_key if c.isalnum() or c in (' ', '-', '_')]).strip()
                keys_to_del = [k for k in root.cached_images.keys() if safe_name in k]
                for k in keys_to_del:
                    del root.cached_images[k]
                    
                action_clear_game_search() # Làm mới giao diện
                custom_showinfo("Thành công", "Đã khôi phục ảnh gốc.")
                
            except Exception as e:
                custom_showerror("Lỗi", f"Lỗi khi xóa ảnh: {e}")

    def show_game_context_menu(event, game_key, is_custom):
        """
        Menu chuột phải thông minh:
        - Luôn hiện: Đổi Ảnh, Đổi Tên.
        - Nếu là Server Game + Có Ảnh Custom: Hiện nút 'Khôi phục ảnh gốc'.
        - Nếu là Custom Game: Hiện nút 'Xóa Game'.
        """
        menu = tk.Menu(root, tearoff=0)
        
        # 1. Đổi Tên (Cho tất cả)
        menu.add_command(label="✏️ Đổi Tên Game", command=lambda: action_rename_game(game_key))
        
        # 2. Đổi Ảnh (Cho tất cả)
        menu.add_command(label="🖼️ Đổi Ảnh (URL)", command=lambda: action_change_game_image(game_key, is_custom))
        
        # 3. Khôi phục ảnh gốc (Chỉ cho Server Game đang dùng ảnh custom)
        # Kiểm tra xem game này có trong danh sách override không
        if not is_custom and game_key in local_config.get('theme_overrides', {}):
            menu.add_command(label="↩️ Khôi phục Ảnh Gốc", command=lambda: action_remove_custom_image(game_key))

        menu.add_separator()

        # 4. Xóa Game (Chỉ cho Custom Game)
        if is_custom:
            menu.add_command(label="❌ Xóa Game Khỏi List", command=lambda: action_delete_custom_game(game_key))
            
        menu.post(event.x_root, event.y_root)

    # --- THÊM MỚI: CÁC HÀM ĐIỀU HƯỚNG MỚI ---
    def populate_page_1_grid(game_groups, search_term=""):
        """(ĐÃ NÂNG CẤP) Hiển thị lưới game bao gồm cả Game Tùy Chỉnh."""
        global g_game_grid_container, g_game_search_entry, page_1_canvas, page_1_canvas_window_id

        style.configure("HoverAccent.TButton", background="#0078d4", foreground="white", font=("Segoe UI", 10, "bold"), borderwidth=1, focuscolor="none")
        style.map("HoverAccent.TButton", background=[('active', '#ff0000'), ('disabled', '#cccccc')], foreground=[('active', 'cyan')])

        def create_page1_launch_cmd(path):
            def launch_and_stop_event(event=None):
                action_launch_game_from_page_1(path)
                return "break" 
            return launch_and_stop_event
        
        try:
            loading_frame = page_1_game_grid.nametowidget("tab1_loading_frame")
            if loading_frame:
                loading_frame.destroy()
                root.update_idletasks() 
        except KeyError: pass
        
        # =========================================================================
        # [THÊM MỚI] NÚT GEMINI AI PRO (Góc Phải Trên Cùng)
        # =========================================================================
        gemini_btn = ttk.Button(
            page_1_game_grid, 
            text="✨ Gemini AI PRO", 
            command=action_open_gemini_pro, 
            style="Accent.TButton"
        )
        # relx=1.0, y=10, anchor="ne" -> Căn theo mép phải, cách trên 10px
        gemini_btn.place(relx=1.0, x=-20, y=10, anchor="ne")
        CreateToolTip(gemini_btn, "Mở trợ lý Google Gemini ngay trong App.")
        # =========================================================================

        # --- 1. THANH TÌM KIẾM & NÚT THÊM GAME ---
        if g_game_search_entry is None:
            # ... (Code logo cũ giữ nguyên) ...
            try:
                image_path = resource_path("logo.png")
                my_image = Image.open(image_path).resize((150, 150), Image.Resampling.LANCZOS)
                tk_image = ImageTk.PhotoImage(my_image)
                ttk.Label(page_1_game_grid, image=tk_image, anchor=tk.CENTER).pack(pady=(10, 15))
                root.tk_image = tk_image
            except: pass

            search_frame = ttk.Frame(page_1_game_grid)
            search_frame.pack(fill=tk.X, pady=(0, 15), padx=50)

            ttk.Label(search_frame, text="Tìm game:").pack(side=tk.LEFT, padx=(0, 10))

            g_game_search_entry = ttk.Entry(search_frame)
            g_game_search_entry.pack(fill=tk.X, expand=True, side=tk.LEFT)
            g_game_search_entry.bind("<Return>", on_game_search)

            ttk.Button(search_frame, text="X", command=action_clear_game_search, width=3).pack(side=tk.LEFT, padx=(5,0))
            
            # [MỚI] Nút Thêm Game
            add_game_btn = ttk.Button(search_frame, text="➕ Thêm Game", command=action_add_custom_game_popup)
            add_game_btn.pack(side=tk.LEFT, padx=(10, 0))
            CreateToolTip(add_game_btn, "Thêm game bên ngoài vào Launcher.\n(Cần file .exe và link ảnh).")

        # --- 2. TẠO CANVAS (Giữ nguyên code cũ) ---
        if g_game_grid_container is None:
            canvas_host_frame = ttk.Frame(page_1_game_grid)
            canvas_host_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)
            path_label_credit = ttk.Label(page_1_game_grid, text="by Mr-Mime 2025", style="secondary.TLabel")
            path_label_credit.pack(side=tk.BOTTOM, pady=(5, 5))
            page_1_scrollbar = ttk.Scrollbar(canvas_host_frame, orient="vertical")
            page_1_canvas = tk.Canvas(canvas_host_frame, borderwidth=0, highlightthickness=0, yscrollcommand=page_1_scrollbar.set)
            page_1_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            page_1_scrollbar.config(command=page_1_canvas.yview)
            g_game_grid_container = ttk.Frame(page_1_canvas)
            page_1_canvas_window_id = page_1_canvas.create_window((0, 0), window=g_game_grid_container, anchor="n")
            g_game_grid_container.bind("<Configure>", on_page_1_content_configure)
            page_1_canvas.bind("<Configure>", on_page_1_canvas_configure)
            page_1_canvas.bind("<MouseWheel>", on_mouse_wheel)
            g_game_grid_container.bind("<MouseWheel>", on_mouse_wheel)
            page_1_canvas.bind("<Button-4>", on_mouse_wheel)
            page_1_canvas.bind("<Button-5>", on_mouse_wheel)
            g_game_grid_container.bind("<Button-4>", on_mouse_wheel)
            g_game_grid_container.bind("<Button-5>", on_mouse_wheel)

        for widget in g_game_grid_container.winfo_children(): widget.destroy()

        if not hasattr(root, 'cached_game_icons_small'): root.cached_game_icons_small = {}

        # --- 3. HỢP NHẤT DANH SÁCH GAME ---
        # A. Game từ Server (GitHub)
        server_games = sorted(game_groups.keys())
        custom_games_data = local_config.get('custom_games', {})
        # [MỚI] Lấy danh sách override
        theme_overrides = local_config.get('theme_overrides', {})
        
        custom_game_names = sorted(custom_games_data.keys())
        all_game_names = custom_game_names + server_games 
        
        if search_term:
            search_term = search_term.lower()
            filtered_names = [name for name in all_game_names if search_term in name.lower()]
        else:
            filtered_names = all_game_names

        # 4. VẼ LƯỚI
        MAX_COLS = 4
        col = 0
        row = 0

        for game_name in filtered_names:
            is_custom = game_name in custom_games_data
            icon_img = None
            full_path_to_launch = None
            
            # --- XỬ LÝ HÌNH ẢNH (LOGIC MỚI) ---
            
            # 1. Kiểm tra xem có ảnh Override (Ưu tiên cao nhất cho Server Game) không
            override_path = theme_overrides.get(game_name)
            
            local_img_path_to_load = None
            
            if is_custom:
                # Game Custom: Lấy path từ config của nó
                local_img_path_to_load = custom_games_data[game_name].get("image_local_path")
            elif override_path and os.path.exists(override_path):
                # Game Server: Nếu có override thì dùng
                local_img_path_to_load = override_path
                
            # Nếu có đường dẫn file local (Custom hoặc Override), tải nó
            if local_img_path_to_load and os.path.exists(local_img_path_to_load):
                try:
                    cache_key = f"local_{local_img_path_to_load}"
                    if cache_key in root.cached_images:
                        icon_img = root.cached_images[cache_key]
                    else:
                        with Image.open(local_img_path_to_load) as img:
                            img_resized = img.resize((192, 89), Image.Resampling.LANCZOS)
                            icon_img = ImageTk.PhotoImage(img_resized)
                            root.cached_images[cache_key] = icon_img
                except: pass

            # Nếu vẫn chưa có ảnh (Server Game chưa override), tải từ URL Server
            if not icon_img and not is_custom:
                image_url = g_game_themes.get(game_name)
                if image_url:
                    icon_img = load_image_from_url(image_url, size=(192, 89))
            
            # Fallback icon mặc định
            if not icon_img:
                icon_img = root.default_game_icon_small

            # --- XỬ LÝ ĐƯỜNG DẪN (Giữ nguyên) ---
            if is_custom:
                full_path_to_launch = custom_games_data[game_name].get("launch_path")
            else:
                current_global_path = local_config.get("game_paths", {}).get(game_name, "")
                found_launch_file = None
                if 'game_launchers' in local_config:
                    found_launch_file = local_config['game_launchers'].get(game_name)
                if not found_launch_file:
                    mod_list = game_groups.get(game_name, [])
                    for _key, mod_data in mod_list:
                        if mod_data.get("launch_file"):
                            found_launch_file = mod_data.get("launch_file")
                            break
                if found_launch_file and current_global_path and os.path.isdir(current_global_path):
                    full_path = os.path.join(current_global_path, found_launch_file)
                    if os.path.exists(full_path) and os.path.isfile(full_path):
                        full_path_to_launch = full_path

            # --- VẼ CARD ---
            card_frame = ttk.Frame(g_game_grid_container, style="Card.TFrame", cursor="hand2")
            card_frame.grid(row=row, column=col, padx=10, pady=10, sticky="ew")
            card_frame.columnconfigure(0, weight=1)

            img_label = ttk.Label(card_frame, image=icon_img, cursor="hand2")
            img_label.grid(row=0, column=0, pady=(10, 5), padx=10)

            display_name = local_config.get('display_name_overrides', {}).get(game_name, game_name)
            if is_custom:
                display_name = f"★ {display_name}"
            name_label = ttk.Label(card_frame, text=display_name, anchor=tk.CENTER, cursor="hand2", font=("Segoe UI", 10, "bold"))
            name_label.grid(row=1, column=0, pady=(0, 10), padx=10, sticky="ew")

            # Nút Chạy (Logic cũ)
            btn_text = "Chưa Cài Đặt"
            btn_state = tk.DISABLED
            btn_style = "TButton"
            
            if full_path_to_launch:
                btn_text = "🚀 Chạy Game"
                btn_state = tk.NORMAL
                btn_style = "HoverAccent.TButton"
                
            launch_button_page1 = ttk.Button(card_frame, text=btn_text, state=btn_state, style=btn_style)
            launch_button_page1.grid(row=2, column=0, pady=(0, 10), padx=10, sticky="ew")

            # --- BINDING EVENTS (CLICK CHUỘT TRÁI - CŨ) ---
            if full_path_to_launch:
                click_cmd = lambda e, p=full_path_to_launch, t=img_label: action_launch_game_from_page_1(p, t)
                launch_button_page1.bind("<Button-1>", click_cmd)
            
            if is_custom:
                if full_path_to_launch:
                    card_cmd = lambda e, p=full_path_to_launch, t=img_label: action_launch_game_from_page_1(p, t)
                    card_frame.bind("<Button-1>", card_cmd)
                    img_label.bind("<Button-1>", card_cmd)
                    name_label.bind("<Button-1>", card_cmd)
            else:
                nav_cmd = lambda event, g=game_name: show_page_2_for_game(g)
                card_frame.bind("<Button-1>", nav_cmd)
                img_label.bind("<Button-1>", nav_cmd)
                name_label.bind("<Button-1>", nav_cmd)

            # --- [MỚI] BINDING CHUỘT PHẢI (CONTEXT MENU) ---
            # Sử dụng lambda với default argument (g=game_name, c=is_custom) để bắt đúng giá trị trong vòng lặp
            right_click_cmd = lambda e, g=game_name, c=is_custom: show_game_context_menu(e, g, c)
        
            card_frame.bind("<Button-3>", right_click_cmd)
            img_label.bind("<Button-3>", right_click_cmd)
            name_label.bind("<Button-3>", right_click_cmd)
            # (Không bind nút chạy game để tránh bấm nhầm)

            # Scroll bind
            for w in [card_frame, img_label, name_label, launch_button_page1]:
                w.bind("<MouseWheel>", on_mouse_wheel)
                w.bind("<Button-4>", on_mouse_wheel)
                w.bind("<Button-5>", on_mouse_wheel)

            col += 1
            if col >= MAX_COLS:
                col = 0
                row += 1

        for i in range(MAX_COLS): g_game_grid_container.columnconfigure(i, weight=0)



    def show_page_2_for_game(game_name):
        """(ĐÃ VIẾT LẠI) Tải ảnh, điền mod, và chuyển sang Trang 2."""
        global g_current_game_name, g_game_image_label, g_game_themes, local_config # <-- SỬA 1: Thêm 'local_config'
        
        local_config = load_local_config() # <-- SỬA 2: Thêm dòng này
        
        g_current_game_name = game_name
        path_entry.delete(0, tk.END)
        # 1. Lấy path đã lưu cho game này
        last_used_folder = local_config.get("last_used_folder", "")

        path_entry.insert(0, last_used_folder)

        if 'g_launch_game_button' in globals():
            g_launch_game_button.pack_forget()
        global page_2_back_button, g_set_path_button
        
        page_2_back_button.pack(side=tk.LEFT)
        # Đặt lại tiêu đề khung
        options_frame.config(text=f"Các mod cho: {game_name}")

        # Xóa ảnh cũ (nếu có)
        g_game_image_label.pack_forget()
        g_game_image_label.config(image='')

        # --- THÊM MỚI: LOGIC TẢI ẢNH (TRONG THREAD) ---
        def load_game_image_thread():
            """
            (Chạy ngầm) Lấy ảnh cho Trang 2 (Ưu tiên ảnh Local/Override).
            """
            global g_game_image_label, g_game_themes, local_config

            icon_img = None
            
            # 1. Tải lại config để đảm bảo lấy được thay đổi mới nhất
            current_config = load_local_config()
            custom_games = current_config.get('custom_games', {})
            theme_overrides = current_config.get('theme_overrides', {})
            
            # 2. Tìm đường dẫn ảnh trong máy (Local Path)
            local_path = None
            
            if game_name in custom_games:
                # Nếu là game Custom -> Lấy path từ config custom
                local_path = custom_games[game_name].get("image_local_path")
            elif game_name in theme_overrides:
                # Nếu là game Server nhưng có Override -> Lấy path override
                local_path = theme_overrides[game_name]
                
            # 3. Nếu có ảnh local -> Load từ ổ cứng
            if local_path and os.path.exists(local_path):
                try:
                    # Tạo key cache riêng cho ảnh to
                    cache_key = f"local_big_{local_path}"
                    
                    if cache_key in root.cached_images:
                        icon_img = root.cached_images[cache_key]
                    else:
                        with Image.open(local_path) as img:
                            # Resize to cho Trang 2 (460x215)
                            img_resized = img.resize((460, 215), Image.Resampling.LANCZOS)
                            icon_img = ImageTk.PhotoImage(img_resized)
                            root.cached_images[cache_key] = icon_img
                            print(f"Đã load ảnh local cho Page 2: {game_name}")
                except Exception as e:
                    print(f"Lỗi load ảnh local Page 2: {e}")

            # 4. Nếu chưa có ảnh (không có local), dùng URL từ Server
            if not icon_img:
                image_url = g_game_themes.get(game_name)
                if image_url:
                    # Hàm này sẽ tự động cache
                    icon_img = load_image_from_url(image_url, size=(460, 215))

            # 5. Nếu vẫn không có, dùng icon mặc định
            if not icon_img:
                icon_img = root.default_game_icon_large 

            # 6. Gửi về queue để cập nhật UI
            progress_queue.put(("game_image_loaded", icon_img))

        # Bắt đầu tải ảnh ngầm (Việc này nhanh, giữ nguyên)
        threading.Thread(target=load_game_image_thread, daemon=True).start()
        
        # --- SỬA LỖI TỐI ƯU HÓA (BEGIN) ---
        
        # 1. XÓA SẠCH WIDGET CŨ (của game trước) NGAY LẬP TỨC
        # (Di chuyển code 'destroy' từ hàm update_radio_buttons lên đây)
        for widget in content_frame.winfo_children(): 
            widget.destroy()
        
        # 2. CHUYỂN TRANG NGAY LẬP TỨC (Khi trang còn trống)
        # (Hàm này giờ chỉ là `place()`, rất nhanh)
        show_page(page_2_mod_list) 
        
        # 3. HẸN GIỜ (10ms) ĐỂ BẮT ĐẦU VẼ CÁC NÚT MỚI
        # Điều này cho phép UI chuyển trang mượt mà trước khi bị "khóa"
        root.after(10, update_radio_buttons_text_for_game, game_name)

    def update_mod_button_states(selected_key):
        """Cập nhật trạng thái text và STYLE của tất cả các nút chọn mod."""
        global g_mod_buttons, g_current_selected_key
        g_current_selected_key = selected_key
        
        # --- (BEGIN) THAY ĐỔI: Unpack tuple (select_button, checkmark_button) ---
        for key, (select_button, checkmark_button) in g_mod_buttons.items():
            try:
                if key == selected_key:
                    # Nút CHỌN (bên phải): Đổi thành "✓"
                    select_button.config(text="   ", style="Accent.TButton", state=tk.NORMAL)
                    
                    # Nút CHECK (bên trái): Hiện "✓" và bật
                    checkmark_button.config(text="   ", state=tk.NORMAL)
                else:
                    # Nút CHỌN (bên phải): Trả về text rỗng
                    select_button.config(text="", style="TButton", state=tk.NORMAL)
                    
                    # Nút CHECK (bên trái): Ẩn text và mờ
                    checkmark_button.config(text="", state=tk.DISABLED)
            except tk.TclError:
                pass

    def update_radio_buttons_text_for_game(game_name_to_show):
        """(ĐÃ VIẾT LẠI) Dùng Accent.TButton để chọn."""
        global local_config, radio_buttons, g_mod_buttons, g_current_selected_key
        
        # Reset trackers
        g_mod_buttons.clear()
        g_current_selected_key = None
        selected_option.set("") # Xóa lựa chọn cũ

        radio_buttons = [] # Vẫn giữ, dù không dùng, để tránh lỗi ở chỗ khác

        style.configure("New.TLabel", foreground="red", font=('TkDefaultFont', 9, 'bold'))
        style.configure("Installed.TLabel", foreground="green")

        # --- Hàm helper để đóng/mở (toggle) ---
        # (Hàm này không đổi)
        def create_toggle_function(mod_frame, button, separator_widget):
            def toggle():
                if mod_frame.winfo_viewable(): 
                    mod_frame.pack_forget()    
                    button.config(text=f"{button.game_name} ▸") 
                else:
                    mod_frame.pack(fill=tk.X, expand=True, before=separator_widget, padx=(15, 0)) 
                    button.config(text=f"{button.game_name} ▾") 
            return toggle

        first_key_to_select = None

        mod_list = download_options.get(game_name_to_show, [])

        # --- HÀM CLICK MỚI (Đơn giản) ---
        def create_click_handler(key_value):
            def handler(event=None):
                # 1. Cập nhật biến (để nút "Bắt đầu" hoạt động)
                selected_option.set(key_value)
                # 2. Cập nhật hướng dẫn
                update_guide_text()
                # 3. Cập nhật trạng thái các nút "Chọn"
                update_mod_button_states(key_value)
            return handler
        # --- KẾT THÚC HÀM CLICK ---

        for (key, data) in mod_list:
            
            display_name = data.get("name", "LỖI: THIẾU TÊN")
            online_version = data.get("version")
            if not online_version: continue 

            installed_version = local_config.get("installed_versions", {}).get(key, "Chưa cài đặt")

            # 1. Tạo Row Frame (Card nhỏ)
            # (Không cần cursor="hand2" nữa)
            row_frame = ttk.Frame(content_frame, style="Card.TFrame", padding=(10, 5))
            row_frame.pack(fill=tk.X, pady=2) 
            
            # --- (BEGIN) THAY ĐỔI: THÊM FRAME NÚT ✓ BÊN TRÁI ---
            # 1.a. Tạo frame chứa nút check bên trái
            checkmark_frame = ttk.Frame(row_frame) # Đặt chiều rộng cố định
            checkmark_frame.pack(side=tk.LEFT,padx=(0, 0))
            
            # 1.b. Tạo nút check (sẽ được 'update_mod_button_states' điều khiển)
            checkmark_button = ttk.Button(
                checkmark_frame, 
                text="",                # Bắt đầu rỗng
                style="Accent.TButton", # Dùng style Accent
                state=tk.DISABLED       # Bắt đầu mờ
            )
            checkmark_button.pack(fill=tk.Y, expand=True)
            # --- (END) THAY ĐỔI ---

            # --- Frame bên trái cho Text ---
            # (Không thay đổi)
            left_frame = ttk.Frame(row_frame)
            left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
            left_frame.columnconfigure(0, weight=1) 

            # --- Frame bên phải cho Nút ---
            # (Không thay đổi)
            right_frame = ttk.Frame(row_frame)
            right_frame.pack(side=tk.RIGHT, padx=(0, 0))

            # 2. Tạo Tên Mod (Label)
            # (Không thay đổi)
            name_label = ttk.Label(left_frame, text=display_name, font=("Segoe UI", 10, "bold"), anchor=tk.CENTER)
            name_label.grid(row=0, column=0, sticky="ew")

            # --- (BEGIN) THAY ĐỔI: Thêm 2 widget mới vào all_widgets_to_bind ---
            all_widgets_to_bind = [row_frame, checkmark_frame, checkmark_button, left_frame, right_frame, name_label] 
            # --- (END) THAY ĐỔI ---

            # 3. Tạo các Label Trạng thái
            # (Không thay đổi)
            if online_version == installed_version:
                status_text = f"✓ Đã cài đặt ({online_version})"
                status_label = ttk.Label(left_frame, text=status_text, style="Installed.TLabel", anchor=tk.CENTER) 
                status_label.grid(row=1, column=0, sticky="ew", pady=(2, 0)) 
                all_widgets_to_bind.append(status_label)
            else:
                if installed_version == "Chưa cài đặt":
                    status_text = f"🔥 Cần cài đặt ({online_version})"
                else:
                    status_text = f"🔥 Cập nhật ({online_version})" 
                
                new_label = ttk.Label(left_frame, text=status_text, style="New.TLabel", anchor=tk.CENTER)
                new_label.grid(row=1, column=0, sticky="ew", pady=(2, 0))
                all_widgets_to_bind.append(new_label)

            # 4. Lấy key đầu tiên để tự động chọn
            # (Không thay đổi)
            if first_key_to_select is None:
                first_key_to_select = key

            # 5. TẠO NÚT "CHỌN" (Accent.TButton)
            # (Không thay đổi)
            click_command = create_click_handler(key)
            
            select_button = ttk.Button(
                right_frame, 
                text="Chọn", 
                command=click_command
            )
            select_button.pack(fill=tk.Y, expand=True)
            
            # --- (BEGIN) THAY ĐỔI: Lưu cả 2 nút (dạng tuple) ---
            g_mod_buttons[key] = (select_button, checkmark_button)
            # --- (END) THAY ĐỔI ---

            all_widgets_to_bind.append(select_button) # Thêm vào để bind scroll

            # 6. Bind Mousewheel VÀ CLICK
            # (Không thay đổi)
            for widget in all_widgets_to_bind:
                try:
                    # Bind cuộn chuột (như cũ)
                    widget.bind("<MouseWheel>", on_mouse_wheel)
                    widget.bind("<Button-4>", on_mouse_wheel) 
                    widget.bind("<Button-5>", on_mouse_wheel)

                    # --- SỬA Ở ĐÂY: Bind Click chuột trái ---
                    # (Không cần bind cho chính select_button, vì nó đã có 'command')
                    if widget != select_button:
                        widget.bind("<Button-1>", click_command)

                except tk.TclError as e:
                    print(f"Lỗi khi bind widget: {e}")

        # 7. Tự động chọn mod đầu tiên
        # (Không thay đổi)
        if first_key_to_select:
            # 1. Cập nhật biến
            selected_option.set(first_key_to_select)
            # 2. Cập nhật hướng dẫn
            update_guide_text()
            # 3. Cập nhật trạng thái các nút
            update_mod_button_states(first_key_to_select)

    def refresh_mod_list_ui():
        """
        (Hàm mới) Xóa và vẽ lại danh sách mod (Trang 2) 
        để cập nhật trạng thái (ví dụ: "Đã cài đặt").
        """
        global content_frame, g_current_game_name
        
        # Kiểm tra xem Trang 2 có đang hoạt động không
        if not g_current_game_name or not content_frame.winfo_exists():
            print("Lỗi: Không thể refresh mod list (UI không tồn tại).")
            return

        print(f"Đang làm mới danh sách mod cho: {g_current_game_name}")
        
        # 1. Xóa tất cả các nút mod cũ (ĐIỀU QUAN TRỌNG NHẤT)
        for widget in content_frame.winfo_children(): 
            widget.destroy()
            
        # 2. Gọi hàm vẽ lại các nút mod mới
        # (Hàm này sẽ đọc config mới và vẽ lại đúng trạng thái)
        update_radio_buttons_text_for_game(g_current_game_name)


    path_frame = ttk.Frame(page_2_mod_list)
    path_frame.pack(fill=tk.X, pady=(5, 10))
    path_label = ttk.Label(path_frame, text="Đường dẫn folder mod:")
    path_label.pack(side=tk.LEFT, padx=(0, 10))
    path_entry = ttk.Entry(path_frame)
    path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
    path_entry.bind("<FocusOut>", lambda e: update_guide_text())

    # --- THÊM MỚI: CHECKBOX TỰ ĐỘNG EXCLUSION ---
    # Biến lưu trạng thái checkbox
    g_auto_add_exclusion = tk.BooleanVar(value=False) 

    # Tạo Checkbox
    defender_checkbox = ttk.Checkbutton(
        page_2_mod_list, 
        text="🛡️ Tự động thêm thư mục này vào Exclusion (để tránh bị xóa file)",
        variable=g_auto_add_exclusion,
        style="Switch.TCheckbutton" # Hoặc để trống nếu chưa định nghĩa style này
    )
    # Pack nó ngay trên button_frame
    defender_checkbox.pack(pady=(5, 0)) 
    CreateToolTip(defender_checkbox, "Nếu tích: App sẽ tự động thêm folder này vào danh sách loại trừ của Windows Defender\nnếu nó chưa nằm trong đó.")

    button_frame = ttk.Frame(page_2_mod_list)
    button_frame.pack(pady=15)
    browse_button = ttk.Button(button_frame, text="Tìm đường dẫn...", command=browse_for_folder)
    browse_button.pack(side=tk.LEFT, padx=10)

    start_button = ttk.Button(button_frame, text="Bắt đầu Cài đặt", 
                            command=start_download_thread, style="Accent.TButton")
    start_button.pack(side=tk.LEFT, padx=10)

    option_label = ttk.Label(page_3_progress, text = "GG", anchor=tk.W, style="White.TLabel")

    progress_bar = ttk.Progressbar(page_3_progress, orient="horizontal", length=100, mode="indeterminate")

    status_frame = ttk.Frame(page_3_progress)

    status_label = ttk.Label(status_frame, text="Hãy chọn đường dẫn và bấm bắt đầu.", anchor=tk.W, style="White.TLabel")
    status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
    eta_label = ttk.Label(status_frame, text="", style="secondary.TLabel", anchor=tk.E, width=8)
    eta_label.pack(side=tk.RIGHT, padx=(10,0))
    speed_label = ttk.Label(status_frame, text="", style="secondary.TLabel", anchor=tk.E, width=12)
    speed_label.pack(side=tk.RIGHT)

    # --- THÊM MỚI: CĂN GIỮA CHO TRANG 3 ---
    # Thêm các frame rỗng để đẩy nội dung vào giữa
    ttk.Frame(page_3_progress).pack(side=tk.TOP, expand=True)
    option_label.pack(side=tk.TOP, pady=(5, 5))
    g_gif_label.pack(side=tk.TOP, pady=(5, 5))
    progress_bar.pack(side=tk.TOP, fill=tk.X, pady=(10, 5)) # <-- ĐÃ XÓA fill=tk.X
    status_frame.pack(side=tk.TOP, fill=tk.X, pady=(10, 5))  # <-- ĐÃ XÓA fill=tk.X
    ttk.Frame(page_3_progress).pack(side=tk.TOP, expand=True)

    # --- Hết Nội dung Tab 1 ---

    # --- SỬA: Tạo UI cho Tab 2 ("Upload Config") ---
    second_tab_frame = ttk.Frame(notebook, padding=(10, 10))
    notebook.add(second_tab_frame, text="Thêm/Xóa Option Tải")

    # --- Variables ---
    current_config_data = {} # Dictionary để giữ config đang sửa
    current_github_sha = None # SHA của file đã tải từ GitHub
    g_currently_selected_id = None
    g_game_theme_sha = None # BIẾN MỚI: SHA cho file game_themes.json
    g_master_game_list = []
    g_search_timer = None
    g_theme_manager_window = None
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
    cols = ("ID", "Option Name", "Version", "Type", "Game")
    options_treeview = ttk.Treeview(tree_frame, columns=cols, show='headings', yscrollcommand=tree_scrollbar.set, height=15)
    options_treeview.pack(expand=True, fill=tk.BOTH)
    move_button_frame = ttk.Frame(tree_frame)
    move_button_frame.pack(fill=tk.X, pady=5)

    # (Chúng ta sẽ thêm 'command' ở bước 3)
    move_up_button = ttk.Button(move_button_frame, text="▲ Di chuyển Lên",
                                command=lambda: action_move_option("up"))
    move_up_button.pack(side=tk.LEFT, padx=5, expand=True)

    move_down_button = ttk.Button(move_button_frame, text="▼ Di chuyển Xuống",
                                command=lambda: action_move_option("down"))
    move_down_button.pack(side=tk.LEFT, padx=5, expand=True)
    tree_scrollbar.config(command=options_treeview.yview)
    for col in cols:
        options_treeview.heading(col, text=col)
        options_treeview.column(col, width=100, anchor=tk.W)
    options_treeview.column("ID", width=40, anchor=tk.CENTER, stretch=tk.NO)
    options_treeview.column("Option Name", width=180)
    options_treeview.column("Version", width=100)
    options_treeview.column("Type", width=70)
    options_treeview.column("Game", width=120)

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
    # --- THÊM MỚI: TẠO GAME COMBOBOX (Dropdown) ---
    row_game = ttk.Frame(edit_form_frame)
    row_game.pack(fill=tk.X, pady=2)
    label_game = ttk.Label(row_game, text="Game:", width=15, anchor=tk.W)
    label_game.pack(side=tk.LEFT)

    # Tạo Combobox (không "readonly" để cho phép gõ tên mới)
    global g_admin_game_combobox
    g_admin_game_combobox = ttk.Combobox(row_game, values=[], state="normal")
    g_admin_game_combobox.pack(side=tk.LEFT, expand=True, fill=tk.X)
    g_admin_game_combobox.bind("<<ComboboxSelected>>", lambda e: on_game_combobox_select(e))
    g_admin_game_combobox.bind("<KeyRelease>", lambda e: on_game_combobox_search(e))
    g_admin_game_combobox.bind("<FocusOut>", lambda e: on_game_combobox_validate(e))
    # Lưu nó vào form_widgets để các hàm khác có thể dùng
    form_widgets["Game:"] = g_admin_game_combobox
    create_form_row(edit_form_frame, "Password:")
    create_form_row(edit_form_frame, "Delete List:", widget_type="Text")
    delete_help = ttk.Label(edit_form_frame, text="(Nhập file/folder, mỗi cái một dòng)", style="secondary.TLabel")
    delete_help.pack(fill=tk.X)

    create_form_row(edit_form_frame, "Path Guide:", widget_type="Text")
    guide_help = ttk.Label(edit_form_frame, text="(Hướng dẫn chọn đường dẫn cho Tab 1)", style="secondary.TLabel")
    guide_help.pack(fill=tk.X)
    create_form_row(edit_form_frame, "Launch File:") # <-- ĐỔI KEY
    exe_help = ttk.Label(edit_form_frame, text="(Tên file, ví dụ: run.bat, game.exe)", style="secondary.TLabel") # <-- ĐỔI TEXT
    exe_help.pack(fill=tk.X)
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
                (key, data.get("name", "LỖI: THIẾU TÊN"), data.get("version", ""), 
                    data.get("type", "zip"), data.get("game", "Khác"))
            ))

    def on_treeview_select(event):
        """Fills the form when an item in the treeview is selected."""
        selected_items = options_treeview.selection()
        if not selected_items:
            clear_form() # Clear form if selection is removed
            return

        selected_key = selected_items[0] # Get the item ID (which is the option key)

        global g_currently_selected_id
        g_currently_selected_id = selected_key

        if selected_key in current_config_data:
            data = current_config_data[selected_key]
            form_widgets["Option Name:"].delete(0, tk.END)
            form_widgets["Option Name:"].insert(0, data.get("name") or "")

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
            form_widgets["Game:"].set("")
            form_widgets["Game:"].insert(0, data.get("game") or "Khác")
            form_widgets["Version:"].delete(0, tk.END)
            form_widgets["Version:"].insert(0, data.get("version") or "")
            form_widgets["Type:"].set(data.get("type", "zip"))
            form_widgets["Password:"].delete(0, tk.END)
            form_widgets["Password:"].insert(0, data.get("password", "") or "") # Insert empty string if None/null

            delete_list_widget = form_widgets["Delete List:"]
            delete_list_widget.config(state=tk.NORMAL) # Allow editing
            delete_list_widget.delete("1.0", tk.END)
            delete_items = data.get("delete_before_extract", [])
            if delete_items:
                delete_list_widget.insert("1.0", "\n".join(delete_items))
            
            guide_widget = form_widgets["Path Guide:"]
            guide_widget.config(state=tk.NORMAL)
            guide_widget.delete("1.0", tk.END)
            guide_text = data.get("path_guide") # Lấy giá trị, có thể là None
            if guide_text: # Chỉ chèn nếu guide_text không phải None và không rỗng
                guide_widget.insert("1.0", guide_text)
            
            form_widgets["Launch File:"].delete(0, tk.END)
            form_widgets["Launch File:"].insert(0, data.get("launch_file") or "")

    options_treeview.bind('<<TreeviewSelect>>', on_treeview_select)

    # --- Form Button Functions ---
    def clear_form():
        global g_currently_selected_id
        g_currently_selected_id = None
        form_widgets["Option Name:"].delete(0, tk.END)
        form_widgets["URL:"].delete(0, tk.END)
        form_widgets["Game:"].delete(0, tk.END)
        form_widgets["Version:"].delete(0, tk.END)
        form_widgets["Type:"].set("zip")
        form_widgets["Password:"].delete(0, tk.END)
        form_widgets["Delete List:"].config(state=tk.NORMAL)
        form_widgets["Delete List:"].delete("1.0", tk.END)
        form_widgets["Path Guide:"].config(state=tk.NORMAL)
        form_widgets["Path Guide:"].delete("1.0", tk.END)
        form_widgets["Launch File:"].delete(0, tk.END)
        options_treeview.selection_remove(options_treeview.selection())

    def action_add_update_option():
        """(ĐÃ VIẾT LẠI) Thêm hoặc Cập nhật option dựa trên ID."""
        global current_config_data, g_currently_selected_id

        # 1. Lấy tất cả dữ liệu từ form (như cũ)
        option_name_display = form_widgets["Option Name:"].get().strip() # Đây là "name"
        if not option_name_display:
            custom_showwarning("Thiếu tên", "Vui lòng nhập 'Option Name'.")
            return
        if option_name_display.lower() == "updater":
            custom_showerror("Tên Bị Cấm", "Bạn không thể đặt tên 'updater'")
            return

        url_input = form_widgets["URL:"].get().strip()
        final_url = url_input
        if url_input and "/" not in url_input and ":" not in url_input and "drive.google.com" not in url_input:
            final_url = f"https://drive.google.com/uc?id={url_input}"

        game_name = form_widgets["Game:"].get().strip()
        if not game_name:
            custom_showerror("Thiếu Game", "Bạn phải chọn một Game từ dropdown.")
            return
        if game_name == "Thêm Game...":
            custom_showerror("Thiếu Game", 
                                "Bạn đã chọn 'Thêm Game...' nhưng chưa thêm game nào.\n\n"
                                "Vui lòng chọn một game đã tồn tại, hoặc thêm game mới.")
            return
        version = form_widgets["Version:"].get().strip()
        option_type = form_widgets["Type:"].get()
        password = form_widgets["Password:"].get().strip()
        delete_list_raw = form_widgets["Delete List:"].get("1.0", tk.END).strip()
        delete_list = [line.strip() for line in delete_list_raw.splitlines() if line.strip()]
        path_guide_text = form_widgets["Path Guide:"].get("1.0", tk.END).strip()
        launch_file_name = form_widgets["Launch File:"].get().strip()
        # 2. Tạo đối tượng data (Giờ 'name' ở bên trong)
        new_data = {
            "name": option_name_display, # <-- TÊN MỚI Ở ĐÂY
            "url": final_url,
            "version": version,
            "game": game_name if game_name else "Khác",
            "type": option_type,
            "password": password if password else None, 
            "delete_before_extract": delete_list,
            "path_guide": path_guide_text if path_guide_text else None,
            "launch_file": launch_file_name if launch_file_name else None
        }

        # --- 3. LOGIC MỚI: KIỂM TRA UPDATE HAY LÀ ADD ---
        target_key = None

        if g_currently_selected_id:
            # --- CHẾ ĐỘ UPDATE ---
            # (Đang chọn 1 item trong list)
            target_key = g_currently_selected_id
            print(f"Đang cập nhật ID: {target_key}")
            current_config_data[target_key] = new_data
        else:
            # --- CHẾ ĐỘ THÊM MỚI ---
            # (Không chọn item nào, hoặc bấm "Xóa Hết")

            # Kiểm tra xem tên này đã tồn tại chưa
            for k, v in current_config_data.items():
                if v.get("name") == option_name_display:
                    custom_showwarning("Trùng Tên", f"Tên '{option_name_display}' đã tồn tại (với ID {k}).\nNếu bạn muốn SỬA nó, hãy click vào nó trong danh sách.")
                    return

            # Tìm ID mới (số lớn nhất + 1)
            new_id = 0
            for key_str in current_config_data.keys():
                if key_str.isdigit(): # Chỉ kiểm tra các key là số
                    new_id = max(new_id, int(key_str))

            target_key = str(new_id + 1) # Key mới (dạng string)
            print(f"Đang thêm mới với ID: {target_key}")
            current_config_data[target_key] = new_data

        # --- HẾT LOGIC MỚI ---

        populate_treeview() # Refresh

        # Select và focus vào item
        if target_key:
            options_treeview.selection_set(target_key)
            options_treeview.focus(target_key)

        upload_status_label.config(text=f"'{option_name_display}' (ID: {target_key}) đã được thêm/cập nhật.", style="White.TLabel")

    def action_delete_option():
        global current_config_data
        selected_items = options_treeview.selection()
        if not selected_items:
            custom_showwarning("Chưa chọn", "Vui lòng chọn một option trong danh sách để xóa.")
            return
        selected_key = selected_items[0] # Đây là ID (ví dụ: "1")

        # --- SỬA: Lấy tên để hiển thị ---
        option_name_display = current_config_data.get(selected_key, {}).get("name", selected_key)

        if custom_askyesno("Xác nhận xóa", f"Bạn có chắc chắn muốn xóa option '{option_name_display}' (ID: {selected_key})?"):
            if selected_key in current_config_data:
                del current_config_data[selected_key]
                populate_treeview()
                clear_form()
                upload_status_label.config(text=f"'{option_name_display}' đã được xóa cục bộ.", foreground="red")
            else: custom_showerror("Lỗi", "Option đã chọn không còn tồn tại?")

    # --- THÊM MỚI: HÀM DI CHUYỂN ITEM ---
    def action_move_option(direction):
        """Di chuyển item đã chọn lên hoặc xuống trong danh sách."""
        global current_config_data

        selected_items = options_treeview.selection()
        if not selected_items:
            custom_showwarning("Chưa chọn", "Vui lòng chọn một option để di chuyển.")
            return

        selected_key = selected_items[0] # Đây là ID (ví dụ: "2")

        # Chuyển dict thành list (để giữ trật tự)
        items_list = list(current_config_data.items())

        # Tìm vị trí (index) của item đã chọn
        current_index = -1
        for i, (key, data) in enumerate(items_list):
            if key == selected_key:
                current_index = i
                break

        if current_index == -1:
            print(f"Lỗi: Không tìm thấy key {selected_key} trong list")
            return # Không tìm thấy (lỗi)

        # Tính vị trí mới
        if direction == "up":
            new_index = current_index - 1
            if new_index < 0:
                print("Đã ở trên cùng")
                return # Đã ở trên cùng
        else: # "down"
            new_index = current_index + 1
            if new_index >= len(items_list):
                print("Đã ở dưới cùng")
                return # Đã ở dưới cùng

        # Di chuyển item
        item_to_move = items_list.pop(current_index)
        items_list.insert(new_index, item_to_move)

        # Tạo lại dictionary (đã sắp xếp lại)
        # (Dùng dict() sẽ giữ trật tự chèn (insertion order) trong Python 3.7+)
        current_config_data = dict(items_list)

        # Cập nhật UI
        populate_treeview()

        # Chọn lại item vừa di chuyển
        options_treeview.selection_set(selected_key)
        options_treeview.focus(selected_key)

        upload_status_label.config(text="Đã thay đổi thứ tự. (Nhớ 'Lưu Config')")

    # --- THÊM MỚI: HÀM LOGIC SEARCH (DEBOUNCED) ---
    def do_game_search():
        """Lọc danh sách dropdown (được gọi sau khi hết giờ hẹn)."""
        global g_master_game_list, g_admin_game_combobox, g_search_timer
        g_search_timer = None # Xóa timer

        current_text = g_admin_game_combobox.get().lower()

        if not current_text:
            filtered_list = g_master_game_list + ["Thêm Game..."]
        else:
            filtered_list = [game for game in g_master_game_list if current_text in game.lower()]
            filtered_list.append("Thêm Game...")

        g_admin_game_combobox['values'] = filtered_list
        g_admin_game_combobox.event_generate('<Down>')


    # --- THÊM MỚI: LOGIC SEARCH VÀ VALIDATE CHO COMBOBOX ---
    def on_game_combobox_search(event):
        """Hẹn giờ lọc danh sách (debounce) sau khi người dùng gõ."""
        global g_search_timer

        # Nếu đang có hẹn giờ cũ, hủy nó
        if g_search_timer:
            root.after_cancel(g_search_timer)

        g_search_timer = root.after(1000, do_game_search)

    def on_game_combobox_validate(event):
        """Kiểm tra giá trị khi người dùng click ra ngoài."""
        global g_master_game_list, g_admin_game_combobox

        current_text = g_admin_game_combobox.get()
        if not current_text: return # Nếu trống thì thôi

        # Nếu text không hợp lệ VÀ không phải "Thêm Game..."
        valid_options = g_master_game_list + ["Thêm Game..."]

        if current_text not in valid_options:
            # Tự động chọn "best match" đầu tiên
            for game in g_master_game_list:
                if current_text.lower() in game.lower():
                    g_admin_game_combobox.set(game)
                    return # Tìm thấy, thoát

            # Nếu không tìm thấy match nào, xóa nó
            custom_showerror("Tên không hợp lệ", 
                                f"'{current_text}' không phải là một game hợp lệ.\n"
                                "Vui lòng chọn từ danh sách hoặc 'Thêm Game...'.",
                                parent=root)
            g_admin_game_combobox.set("")



    def on_game_combobox_select(event):
        """Được gọi khi chọn item trong dropdown Game."""
        selected_game = g_admin_game_combobox.get()
        if selected_game == "Thêm Game...":
            # Mở modal quản lý
            open_game_theme_manager()
            # Xóa lựa chọn "Thêm Game..."
            g_admin_game_combobox.set("")

    def open_game_theme_manager():
        """Mở cửa sổ modal để Thêm/Xóa game theme."""
        global g_theme_manager_window, g_theme_listbox, g_theme_name_entry, g_theme_url_entry

        if g_theme_manager_window is not None:
            try: g_theme_manager_window.destroy()
            except: pass

        g_theme_manager_window = tk.Toplevel(root)
        g_theme_manager_window.title("Quản lý Game Theme")
        g_theme_manager_window.geometry("600x400")
        g_theme_manager_window.transient(root)
        g_theme_manager_window.grab_set()

        main_frame = ttk.Frame(g_theme_manager_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Cột trái: Danh sách
        list_frame = ttk.LabelFrame(main_frame, text="Game Themes Hiện tại")
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        list_scroll = ttk.Scrollbar(list_frame, orient="vertical")
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        g_theme_listbox = tk.Listbox(list_frame, yscrollcommand=list_scroll.set)
        g_theme_listbox.pack(fill=tk.BOTH, expand=True)
        list_scroll.config(command=g_theme_listbox.yview)

        # Điền vào listbox
        populate_theme_listbox()

        # Cột phải: Form
        form_frame = ttk.Frame(main_frame, width=250)
        form_frame.pack(side=tk.LEFT, fill=tk.Y)

        # Form Thêm
        add_frame = ttk.LabelFrame(form_frame, text="Thêm Game Mới")
        add_frame.pack(fill=tk.X)

        ttk.Label(add_frame, text="Tên Game:").pack(anchor=tk.W, padx=5, pady=(5,0))
        g_theme_name_entry = ttk.Entry(add_frame)
        g_theme_name_entry.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(add_frame, text="URL Hình ảnh:").pack(anchor=tk.W, padx=5, pady=(5,0))
        g_theme_url_entry = ttk.Entry(add_frame)
        g_theme_url_entry.pack(fill=tk.X, padx=5, pady=5)

        add_button = ttk.Button(add_frame, text="Thêm Mới", 
                                style="Accent.TButton",
                                command=action_add_game_theme)
        add_button.pack(pady=10, padx=5)

        # Form Xóa
        delete_frame = ttk.LabelFrame(form_frame, text="Xóa Game")
        delete_frame.pack(fill=tk.X, pady=20)

        delete_button = ttk.Button(delete_frame, text="Xóa Game Đã Chọn",
                                style="Danger.TButton",
                                command=action_delete_game_theme)
        delete_button.pack(pady=10, padx=5)

    def populate_theme_listbox():
        """Làm mới Listbox trong modal."""
        if not g_theme_listbox: return

        g_theme_listbox.delete(0, tk.END)
        sorted_games = sorted(g_game_themes.keys())
        for game_name in sorted_games:
            g_theme_listbox.insert(tk.END, game_name)

    def action_add_game_theme():
        """LLogic cho nút 'Thêm Mới' trong modal."""
        global g_game_themes

        name = g_theme_name_entry.get().strip()
        url = g_theme_url_entry.get().strip()

        if not name or not url:
            custom_showerror("Thiếu thông tin", "Vui lòng nhập cả Tên Game và URL.", parent=g_theme_manager_window)
            return

        if name in g_game_themes:
            custom_showerror("Trùng tên", "Tên game này đã tồn tại.", parent=g_theme_manager_window)
            return

        # Thêm vào dict
        g_game_themes[name] = url

        # Bắt đầu upload
        threading.Thread(target=upload_theme_json_thread, 
                        args=(name,), 
                        daemon=True).start()

    def action_delete_game_theme():
        """Logic cho nút 'Xóa' trong modal."""
        global g_game_themes
        try:
            selected_game = g_theme_listbox.get(g_theme_listbox.curselection())
        except tk.TclError:
            custom_showwarning("Chưa chọn", "Vui lòng chọn một game trong danh sách để xóa.", parent=g_theme_manager_window)
            return

        if custom_askyesno("Xác nhận", f"Bạn có chắc chắn muốn xóa game theme '{selected_game}'?\n(Việc này không xóa các mod option.)", parent=g_theme_manager_window):
            if selected_game in g_game_themes:
                del g_game_themes[selected_game]
                # Bắt đầu upload (không cần tên)
                threading.Thread(target=upload_theme_json_thread, 
                                args=(None,), 
                                daemon=True).start()

    def upload_theme_json_thread(newly_added_game_name=None):
        """(Chạy ngầm) Upload file game_themes.json."""
        global g_game_theme_sha

        repo = get_github_repo()
        if not repo:
            progress_queue.put(("theme_upload_failed", "Không thể kết nối repo."))
            return

        # Gửi dict g_game_themes hiện tại
        success, new_sha = upload_theme_json_to_github(repo, g_game_themes, g_game_theme_sha)

        if success and new_sha:
            progress_queue.put(("theme_upload_success", (new_sha, newly_added_game_name)))
        else:
            progress_queue.put(("theme_upload_failed", "Upload thất bại. (Xem log GitHub)"))


    add_update_button.config(command=action_add_update_option)
    clear_button.config(command=clear_form)

    # --- Top Button Functions ---
    def action_load_from_github_wrapper():
        """(ĐÃ SỬA) Tải cả config Mod và config Theme VÀ CẢ 2 SHA."""
        global current_config_data, current_github_sha, g_game_themes, g_game_theme_sha
        upload_status_label.config(text="Đang tải từ GitHub...", style="White.TLabel")
        root.update_idletasks()

        repo = get_github_repo()
        if not repo:
            upload_status_label.config(text="Lỗi kết nối repo.", foreground="red")
            return

        # 1. Tải Config Mod (như cũ)
        json_content, sha = load_json_from_github_api(repo)

        # 2. Tải Config Theme (MỚI)
        theme_content, theme_sha = load_theme_json_from_github_api(repo)

        # 3. Xử lý Config Theme
        if theme_content and theme_sha:
            try:
                g_game_themes = json.loads(theme_content)
                g_game_theme_sha = theme_sha # <-- LƯU SHA THEME

                global g_master_game_list
                g_master_game_list = sorted(list(g_game_themes.keys())) # Lưu gốc

                game_list_with_add = g_master_game_list + ["Thêm Game..."] 
                g_admin_game_combobox['values'] = game_list_with_add
            except Exception as e:
                custom_showerror("Lỗi", f"Lỗi đọc file game_themes.json: {e}")
                g_game_themes = {}
                g_admin_game_combobox['values'] = ["Thêm Game..."]
        else:
            g_game_themes = {}
            g_admin_game_combobox['values'] = ["Thêm Game..."]

        # 4. Xử lý Config Mod (như cũ)
        if json_content is not None and sha is not None:
            try:
                current_config_data = json.loads(json_content)
                current_github_sha = sha # <-- LƯU SHA MOD
                populate_treeview()
                clear_form()
                upload_status_label.config(text="Đã tải config từ database", foreground="green")
            except Exception as e:
                custom_showerror("Lỗi", f"Lỗi không xác định khi xử lý JSON: {e}")
                upload_status_label.config(text="Lỗi xử lý JSON.", foreground="red")
        else:
            upload_status_label.config(text="Tải JSON từ GitHub thất bại.", foreground="red")
            current_config_data = {}; current_github_sha = None; populate_treeview()

    def action_upload_to_github_wrapper():
        global current_github_sha
        if not current_config_data:
            custom_showwarning("Chưa có dữ liệu", "Không có dữ liệu config để upload.")
            return
        if current_github_sha is None:
            custom_showwarning("Thiếu SHA", "Vui lòng 'Tải Config' trước khi upload.")
            return
        repo = get_github_repo()
        if not repo: return
        if custom_askyesno("Xác nhận Cập Nhật", "Bạn có chắc chắn muốn ghi đè file config bằng dữ liệu hiện tại?"):
            entered_pin = custom_askstring("Xác nhận PIN", "Nhập mã PIN quản trị:", show='*')
            correct_pin = "2408" # Mã PIN cứng

            if entered_pin != correct_pin:
                custom_showerror("Sai PIN", "Mã PIN không chính xác. Đã hủy upload.")
                return # Dừng nếu PIN sai
            upload_status_label.config(text="Đang upload lên GitHub...", style="White.TLabel")
            root.update_idletasks()
            success, new_sha = upload_json_to_github(repo, current_config_data, current_github_sha)
            if success:
                if new_sha:
                    current_github_sha = new_sha
                    upload_status_label.config(text="Upload thành công!", foreground="green")
                else:
                    current_github_sha = None
                    upload_status_label.config(text="Upload thành công! (Nên tải lại config)", style="White.TLabel") # Dùng style
            else:
                upload_status_label.config(text="Upload thất bại.", foreground="red") # Dùng style

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

    def action_browse_upload_files():
        """Thay thế cho việc kéo thả file vào Tab 3."""
        # Cho phép chọn nhiều file
        file_paths = filedialog.askopenfilenames(title="Chọn file để upload lên Drive")
        
        if file_paths:
            # Xóa danh sách cũ (giống logic kéo thả cũ)
            files_to_upload_list.clear()
            drop_target_listbox.delete(0, tk.END)
            
            for path in file_paths:
                files_to_upload_list.append(path)
                drop_target_listbox.insert(tk.END, os.path.basename(path))
                
            # Bật nút upload
            upload_files_button.config(state=tk.NORMAL)

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

    def try_auto_login_drive_thread():
        """(Chạy ngầm) Tự động đăng nhập Drive nếu có token.json."""
        global drive_service
        
        token_path = resource_path('token.json')
        creds_path = resource_path('credentials.json')
        
        if not os.path.exists(creds_path): 
            progress_queue.put(("accounts_load_failed", "credentials.json missing")) # <-- THÊM MỚI
            return # Không có file credentials
        if not os.path.exists(token_path): 
            progress_queue.put(("accounts_load_failed", "token.json missing")) # <-- THÊM MỚI
            return # Chưa đăng nhập lần nào
        
        try:
            print("Đang thử tự động đăng nhập Google Drive...")
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            
            # Nếu token hết hạn, làm mới
            if not creds.valid and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            
            if creds.valid:
                drive_service = build('drive', 'v3', credentials=creds)
                print("Tự động đăng nhập Drive thành công.")
                
                # --- BẮT ĐẦU TẢI ACCOUNT CONFIG ---
                load_accounts_from_drive_thread() # (Không cần thread lồng nhau)
            else:
                print("Tự động đăng nhập thất bại (token không hợp lệ).")
                progress_queue.put(("accounts_load_failed", "Invalid token")) # <-- THÊM MỚI
                
        except Exception as e:
            print(f"Lỗi khi tự động đăng nhập Drive: {e}")
            progress_queue.put(("accounts_load_failed", str(e)))

    def action_drive_login():
        entered_pin = custom_askstring("Xác nhận PIN", "Nhập mã PIN quản trị:", show='*')
        correct_pin = "2408" # Mã PIN cứng

        if entered_pin != correct_pin:
            custom_showerror("Sai PIN", "Mã PIN không chính xác. Đã hủy upload.")
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
            threading.Thread(target=load_accounts_from_drive_thread, daemon=True).start()
        else:
            drive_auth_button.config(text="Đăng nhập Google Drive", state=tk.NORMAL)

    def action_start_upload_all():
        # Bắt đầu upload tất cả các file trong danh sách
        if not drive_service:
            custom_showwarning("Chưa Đăng Nhập", "Vui lòng đăng nhập Google Drive trước.")
            return
            
        if not files_to_upload_list:
            custom_showinfo("Không có file", "Vui lòng kéo file vào ô bên trên trước.")
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
        
        # --- THÊM MỚI: KIỂM TRA, KHÔNG CHO XÓA FILE JSON ---
        if file_name.lower().endswith(".json"):
            custom_showerror("Không thể Xóa", f"Không được phép xóa file này\nFile: {file_name}")
            progress_queue.put(("drive_log", f"Đã chặn thao tác xóa file JSON: {file_name}"))
            return # Dừng hàm ngay lập tức
        # --- HẾT THÊM MỚI ---

        if not drive_service:
            custom_showerror("Lỗi", "Chưa đăng nhập Google Drive.")
            return
        
        try:
            # 3. Thực thi (Giữ nguyên)
            drive_service.files().delete(fileId=file_id).execute()

            # 4. Báo thành công và Yêu cầu Refresh (Giữ nguyên)
            progress_queue.put(("drive_log", f"Đã xóa {file_name} thành công."))
            progress_queue.put(("refresh_drive_list", None)) # <-- Yêu cầu tải lại lưới

        except HttpError as error:
            custom_showerror("Lỗi Xóa", f"Lỗi khi xóa file: {error}")
            progress_queue.put(("drive_log", f"Lỗi khi xóa {file_name}."))
        except Exception as e:
            custom_showerror("Lỗi Xóa", f"Lỗi không xác định: {e}")
            progress_queue.put(("drive_log", f"Lỗi khi xóa {file_name}."))
    # --- Giao diện cho Tab 3 ---

    # --- THÊM MỚI: CÁC HÀM "TRỢ LÝ AI" ---
    def action_start_scan():
        """Bắt đầu quá trình quét lỗi đồng bộ."""
        global scan_loading_window, drive_service

        if not drive_service:
            custom_showerror("Lỗi", "Vui lòng đăng nhập Google Drive trước.")
            return

        # Hiển thị cửa sổ "Đang tải"
        scan_loading_window = tk.Toplevel(root)
        scan_loading_window.title("Đang Quét...")
        center_window_on_screen(scan_loading_window, 350, 100)
        scan_loading_window.transient(root) # Giữ nó luôn ở trên app chính
        scan_loading_window.grab_set() # Chặn tương tác với app chính
        loading_label = ttk.Label(scan_loading_window, text="Đang so sánh file GitHub JSON và Google Drive...")
        loading_label.pack(expand=True, padx=20, pady=20)

        # Bắt đầu luồng quét
        threading.Thread(target=scan_logic_thread, daemon=True).start()

    def scan_logic_thread():
        """(Chạy ngầm) Tải JSON, tải list Drive và so sánh."""
        global drive_service
        errors_list = []
        warnings_list = []

        try:
            # 1. Tải GitHub JSON (dùng hàm đã có của Tab 1)
            print("Scan: Đang tải config GitHub...")
            github_data = load_config_from_github()
            if not github_data:
                github_data = fallback_options # Dùng fallback nếu tải lỗi

            # 2. Tải danh sách file Google Drive
            print("Scan: Đang tải danh sách Google Drive...")
            response_files = drive_service.files().list(
                q=f"'{GOOGLE_DRIVE_FOLDER_ID}' in parents and trashed = false",
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            drive_files = response_files.get('files', [])

            # 3. So Sánh (Phần "AI")
            print("Scan: Đang so sánh...")

            # Lấy tất cả File ID được dùng trong JSON
            json_file_ids = set()
            for key, data in github_data.items():
                if key == "updater": continue

                url_or_id = data.get("url")
                file_id = extract_gdrive_id_from_url(url_or_id) # Dùng helper

                if file_id:
                    json_file_ids.add(file_id)
                else:
                    errors_list.append(f"Option '{key}': URL không hợp lệ hoặc không phải Google Drive.")

            # Lấy tất cả File ID có trên Drive
            drive_file_map = {file['id']: file['name'] for file in drive_files}
            drive_file_ids = set(drive_file_map.keys())

            # 4. Tìm Lỗi (Có trong JSON, nhưng không có trên Drive)
            broken_ids = json_file_ids - drive_file_ids # Phép trừ tập hợp
            for broken_id in broken_ids:
                # Tìm xem item nào đang dùng ID bị hỏng này
                item_name = "[Không tìm thấy tên]"
                item_key = "[?]"
                for key, data in github_data.items():
                    if extract_gdrive_id_from_url(data.get("url")) == broken_id:
                        item_name = data.get("name", "[TÊN BỊ LỖI]")
                        item_key = key
                        break
                errors_list.append(f"Option '{item_name}' (ID: {item_key}): File ID '{broken_id}' KHÔNG TỒN TẠI trên Drive.")
            # --- HẾT SỬA ---

            # 5. Tìm Cảnh Báo (Có trên Drive, nhưng không dùng trong JSON)
            orphaned_ids = drive_file_ids - json_file_ids # Phép trừ tập hợp
            for orphaned_id in orphaned_ids:
                file_name = drive_file_map[orphaned_id]
                # Thêm dictionary thay vì string
                warnings_list.append({"name": file_name, "id": orphaned_id})

            print("Scan: Hoàn tất so sánh.")
            # Gửi báo cáo về cho queue
            progress_queue.put(("scan_report_ready", {"errors": errors_list, "warnings": warnings_list}))

        except Exception as e:
            print(f"Lỗi khi quét: {e}")
            progress_queue.put(("scan_failed", str(e)))

    def show_scan_report(errors, warnings):
        """Tạo cửa sổ Toplevel MỚI để hiển thị báo cáo TƯƠNG TÁC."""
        report_window = tk.Toplevel(root)
        report_window.title("Báo Cáo Quét Lỗi Đồng Bộ")
        center_window_on_screen(report_window, 700, 500)
        report_window.transient(root)
        report_window.grab_set()

        report_frame = ttk.Frame(report_window, padding=10)
        report_frame.pack(fill=tk.BOTH, expand=True)

        report_text = tk.Text(report_frame, wrap="word", height=20, width=80, relief=tk.FLAT)
        report_scroll = ttk.Scrollbar(report_frame, orient="vertical", command=report_text.yview)
        report_text['yscrollcommand'] = report_scroll.set

        report_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        report_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # --- SỬA: Thêm các tag màu cho LINK ---
        report_text.tag_configure("header", font=("Segoe UI", 14, "bold"), spacing3=10)
        report_text.tag_configure("error", foreground="red", font=("Segoe UI", 10, "bold"))
        report_text.tag_configure("warning", foreground="#FFB000") # Màu vàng cam
        report_text.tag_configure("success", foreground="green")
        report_text.tag_configure("note", foreground=style.lookup("TLabel", "foreground"), lmargin1=10, lmargin2=10)

        # Tag cho link (màu xanh, gạch chân)
        report_text.tag_configure("quick_add_link", foreground="dodgerblue", underline=True, font=("Segoe UI", 9, "underline"))
        report_text.tag_configure("delete_link", foreground="#FF6347", underline=True, font=("Segoe UI", 9, "underline")) # Màu đỏ cà chua
        # --- HẾT SỬA ---

        # --- Chèn nội dung vào Text ---
        if not errors and not warnings:
            report_text.insert(tk.END, "QUÉT HOÀN TẤT\n", "header")
            report_text.insert(tk.END, "Chúc mừng! File JSON và Google Drive của bạn đã đồng bộ hoàn hảo.", "success")
        else:
            if errors:
                report_text.insert(tk.END, f"LỖI ({len(errors)}) - CẦN SỬA NGAY\n", "header")
                report_text.insert(tk.END, "(Các option này trong JSON đang trỏ đến file không tồn tại trên Drive)\n\n", "note")
                for i, err in enumerate(errors):
                    report_text.insert(tk.END, f" {i+1}. {err}\n", "error")
                report_text.insert(tk.END, "\n\n")

            if warnings:
                report_text.insert(tk.END, f"CẢNH BÁO ({len(warnings)}) - NÊN DỌN DẸP\n", "header")
                report_text.insert(tk.END, "(Các file này có trên Drive nhưng không được dùng. Bạn có thể xóa chúng, hoặc dùng 'Tạo Option Tải'.)\n\n", "note")

                # --- SỬA: Vòng lặp tạo link ---
                for i, warn_item in enumerate(warnings):
                    file_name = warn_item['name']
                    file_id = warn_item['id']

                    # 1. Chèn text cảnh báo
                    report_text.insert(tk.END, f" {i+1}. File: ", "warning")
                    report_text.insert(tk.END, f"{file_name}\n", "warning")

                    # 2. Tạo tag duy nhất cho mỗi link
                    qa_tag = f"qa_{file_id}" # Quick Add tag
                    del_tag = f"del_{file_id}" # Delete tag

                    # 3. Chèn các link
                    report_text.insert(tk.END, "      ") # Thụt lề
                    report_text.insert(tk.END, "[Tạo Option Tải]", ("quick_add_link", qa_tag))
                    report_text.insert(tk.END, "   ")
                    report_text.insert(tk.END, "[Xóa File này]", ("delete_link", del_tag))
                    report_text.insert(tk.END, "\n\n")

                    # 4. Gắn (Bind) sự kiện cho các tag duy nhất đó
                    # Dùng lambda để truyền đúng file_info (gồm name và id)
                    report_text.tag_bind(
                        qa_tag, 
                        "<Button-1>", 
                        lambda e, win=report_window, info=warn_item: handle_quick_add_click(win, info)
                    )
                    report_text.tag_bind(
                        del_tag, 
                        "<Button-1>", 
                        lambda e, win=report_window, info=warn_item: handle_delete_click(win, info)
                    )

                    # 5. Thêm hiệu ứng con trỏ chuột
                    report_text.tag_bind(qa_tag, "<Enter>", lambda e: report_text.config(cursor="hand2"))
                    report_text.tag_bind(qa_tag, "<Leave>", lambda e: report_text.config(cursor=""))
                    report_text.tag_bind(del_tag, "<Enter>", lambda e: report_text.config(cursor="hand2"))
                    report_text.tag_bind(del_tag, "<Leave>", lambda e: report_text.config(cursor=""))
                # --- HẾT SỬA ---

        report_text.config(state=tk.DISABLED) # Chỉ đọc


    # Frame trên cho các nút
    drive_button_frame = ttk.Frame(third_tab_frame)
    drive_button_frame.pack(fill=tk.X, pady=5)

    drive_auth_button = ttk.Button(drive_button_frame, text="Đăng nhập Google Drive", command=action_drive_login, style="Accent.TButton")
    drive_auth_button.pack(side=tk.LEFT, padx=5)

    upload_files_button = ttk.Button(drive_button_frame, text="📤", command=action_start_upload_all, style="Accent.TButton", state=tk.DISABLED)
    upload_files_button.pack(side=tk.LEFT, padx=5)
    CreateToolTip(upload_files_button, "Upload Tất Cả File")

    clear_upload_list_button = ttk.Button(drive_button_frame, text="🧹",  command=action_clear_upload_list, style="Danger.TButton")
    clear_upload_list_button.pack(side=tk.LEFT, padx=5)
    CreateToolTip(clear_upload_list_button, "Xóa Danh Sách Upload")

    drive_refresh_button = ttk.Button(drive_button_frame, text="🔄", command=action_refresh_drive_list)
    drive_refresh_button.pack(side=tk.LEFT, padx=5)
    CreateToolTip(drive_refresh_button, "Tải Danh Sách File (Làm mới)")

    scan_button = ttk.Button(drive_button_frame, text="🤖", command=action_start_scan)
    scan_button.pack(side=tk.LEFT, padx=5)
    CreateToolTip(scan_button, "Quét Lỗi Đồng Bộ")
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


    # ---HÀM TẠO NHANH OPTION ---
    def action_quick_add_option(file_name, file_id):
        """(ĐÃ VIẾT LẠI) Tự động tải config và thêm option mới với ID số."""
        global current_config_data, current_github_sha

        # --- TỰ ĐỘNG TẢI CONFIG NẾU CHƯA CÓ ---
        if current_github_sha is None:
            custom_showinfo("Thông báo", 
                                "Đây là lần 'Tạo Nhanh' đầu tiên.\n"
                                "Ứng dụng sẽ tự động tải config từ GitHub trước...")

            action_load_from_github_wrapper() 

            if current_github_sha is None:
                custom_showerror("Lỗi", "Tải config từ GitHub thất bại.\nKhông thể 'Tạo Nhanh'. Vui lòng thử lại.")
                return
        # --- HẾT TẢI TỰ ĐỘNG ---

        print(f"Thêm nhanh option cho: {file_name}")

        # 1. Tự động phát hiện loại file
        file_type = "zip" # Mặc định
        if file_name.lower().endswith(".rar"):
            file_type = "rar"
        elif file_name.lower().endswith(".exe"):
            file_type = "exe"

        # 2. Lấy tên file (bỏ đuôi) để dùng làm TÊN HIỂN THỊ
        base_name = os.path.splitext(file_name)[0]

        # 3. Tạo URL đầy đủ
        final_url = f"https://drive.google.com/uc?id={file_id}"

        # 4. KIỂM TRA TÊN BỊ TRÙNG
        existing_id = None
        for k, v in current_config_data.items():
            if v.get("name") == base_name:
                existing_id = k
                break

        target_key = None
        new_data = {
            "name": base_name, # <-- TÊN HIỂN THỊ
            "url": final_url, 
            "version": "CHƯA SET VERSION", # Placeholder
            "type": file_type,
            "password": None, 
            "delete_before_extract": [],
            "path_guide": None # Thêm key này (trống)
        }

        if existing_id:
            # --- CHẾ ĐỘ UPDATE ---
            if not custom_askyesno("Xác nhận Ghi đè", 
                f"Tên '{base_name}' đã tồn tại (ID: {existing_id}).\n"
                "Bạn có muốn ghi đè URL/Type (giữ Version cũ) không?"):
                return

            target_key = existing_id
            # Giữ lại các giá trị cũ
            old_data = current_config_data[target_key]
            new_data["version"] = old_data.get("version", "CHƯA SET VERSION")
            new_data["password"] = old_data.get("password")
            new_data["delete_before_extract"] = old_data.get("delete_before_extract", [])
            new_data["path_guide"] = old_data.get("path_guide")

            # Chỉ cập nhật
            current_config_data[target_key] = new_data

        else:
            # --- CHẾ ĐỘ THÊM MỚI ---
            # Tìm ID mới (số lớn nhất + 1)
            new_id = 0
            for key_str in current_config_data.keys():
                if key_str.isdigit():
                    new_id = max(new_id, int(key_str))

            target_key = str(new_id + 1) # Key mới
            current_config_data[target_key] = new_data

        # 6. Làm mới Treeview (Tab 2)
        try:
            populate_treeview()
            # Tự động chọn
            options_treeview.selection_set(target_key)
            options_treeview.focus(target_key)
        except Exception as e:
            print(f"Lỗi khi làm mới treeview (nền): {e}")

        # 7. Thông báo
        custom_showinfo("Đã Thêm Nhanh", 
            f"Đã thêm/cập nhật '{base_name}' (ID: {target_key}) vào config.\n\n"
            "VUI LÒNG:\n"
            "1. Chuyển qua Tab 2.\n"
            "2. (Đã tự động chọn)\n"
            "3. Nhập 'Version' và bấm 'Thêm / Cập nhật'.\n"
            "4. Bấm 'Lưu Config' để hoàn tất.")

    def handle_quick_add_click(report_window, file_info):
        """Đóng báo cáo và gọi hàm 'Tạo Nhanh Option'."""
        report_window.destroy() # Đóng cửa sổ báo cáo
        action_quick_add_option(file_info['name'], file_info['id'])

    def handle_delete_click(report_window, file_info):
        """Đóng báo cáo và gọi logic xóa (có xác nhận)."""
        report_window.destroy() # Đóng cửa sổ báo cáo

        # Chúng ta sao chép logic xác nhận an toàn (từ thread chính) ở đây
        message = f"Bạn có chắc chắn muốn XÓA VĨNH VIỄN file này\nkhỏi Google Drive không?\n\nFile: {file_info['name']}"

        if custom_askyesno("Xác nhận Xóa (Từ Trợ lý AI)", message):
            # Chỉ bắt đầu thread nếu người dùng bấm "Yes"
            threading.Thread(target=action_delete_drive_file_thread, 
                            args=(file_info['id'], file_info['name']), 
                            daemon=True).start()
        else:
            progress_queue.put(("drive_log", "Đã hủy thao tác xóa."))

    g_single_update_window = None # Biến global để theo dõi popup

    def open_single_file_updater_popup(file_info):
        """Mở popup chọn file để cập nhật (Dùng Nút bấm thay vì Kéo thả)."""
        global g_single_update_window, drive_service

        if g_single_update_window is not None:
            try: g_single_update_window.destroy()
            except: pass

        if not drive_service:
            custom_showerror("Lỗi", "Chưa đăng nhập Google Drive.")
            return

        target_name = file_info['name']
        target_ext = os.path.splitext(target_name)[1].lower() 

        # Tạo cửa sổ
        g_single_update_window = tk.Toplevel(root)
        g_single_update_window.title("Cập nhật File")
        center_window_on_screen(g_single_update_window, 400, 250) # Tăng chiều cao xíu
        g_single_update_window.transient(root)
        g_single_update_window.grab_set()

        main_frame = ttk.Frame(g_single_update_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Info
        ttk.Label(main_frame, text=f"Đang cập nhật file:\n{target_name}", justify=tk.CENTER).pack(pady=5)
        ttk.Label(main_frame, text=f"(Yêu cầu file đuôi: {target_ext})", style="secondary.TLabel").pack(pady=5)

        # --- HÀM XỬ LÝ KHI BẤM NÚT ---
        def on_browse_file():
            # Mở dialog chọn file đúng đuôi
            file_path = filedialog.askopenfilename(
                title=f"Chọn file {target_ext} thay thế",
                filetypes=[(f"{target_ext} file", f"*{target_ext}"), ("All files", "*.*")]
            )
            
            if file_path:
                # Kiểm tra đuôi lần nữa cho chắc
                local_ext = os.path.splitext(file_path)[1].lower()
                if local_ext != target_ext:
                    custom_showerror("Sai định dạng", 
                        f"File bạn chọn có đuôi {local_ext}.\nBắt buộc phải là {target_ext}.")
                    return

                # Nếu đúng, đóng popup và chạy thread upload luôn
                g_single_update_window.destroy()
                
                # Gọi thread upload (Hàm này bạn đã có sẵn trong code)
                threading.Thread(target=single_file_upload_thread, 
                                args=(file_path, file_info), 
                                daemon=True).start()

        # --- GIAO DIỆN NÚT BẤM ---
        select_frame = ttk.LabelFrame(main_frame, text="Chọn file mới từ máy")
        select_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        ttk.Button(select_frame, text="📂 Chọn File...", command=on_browse_file, style="Accent.TButton").pack(fill=tk.X, padx=20, pady=20)

    def handle_single_file_drop(event, file_info, target_ext, drop_listbox, popup_window):
        """Xử lý khi file được thả vào popup cập nhật."""
        drop_listbox.delete(0, tk.END)

        raw_paths = root.tk.splitlist(event.data)
        if not raw_paths:
            drop_listbox.insert(tk.END, "Lỗi: Không thể đọc file.")
            return

        local_file_path = raw_paths[0]
        if not (os.path.exists(local_file_path) and os.path.isfile(local_file_path)):
            drop_listbox.insert(tk.END, "Lỗi: Đây không phải là file.")
            return

        # === BƯỚC VALIDATION (KIỂM TRA ĐỊNH DẠNG) ===
        dropped_ext = os.path.splitext(local_file_path)[1].lower()
        if dropped_ext != target_ext:
            drop_listbox.insert(tk.END, f"Lỗi: File phải có đuôi {target_ext}. (File bạn thả là {dropped_ext})")
            custom_showerror("Sai định dạng file",
                                f"Bạn đang cố cập nhật file '{file_info['name']}' (đuôi {target_ext}).\n\n"
                                f"File bạn vừa thả vào có đuôi {dropped_ext}.\n\n"
                                "Vui lòng thả file có cùng định dạng.",
                                parent=popup_window)
            return

        # === VALIDATION THÀNH CÔNG ===
        drop_listbox.insert(tk.END, f"Đang chuẩn bị upload: {os.path.basename(local_file_path)}")

        # Vô hiệu hóa popup
        popup_window.grab_release()
        popup_window.destroy()

        # Bắt đầu thread upload
        threading.Thread(target=single_file_upload_thread, 
                        args=(local_file_path, file_info), 
                        daemon=True).start()

    def single_file_upload_thread(local_path, file_info):
        """
        (SMOOTH & FAST) Upload tốc độ cao với thanh tiến trình cập nhật MƯỢT MÀ.
        """
        target_id = file_info['id']
        target_name = file_info['name']

        progress_queue.put(("drive_log", f"🚀 Upload '{target_name}' (Smooth Mode)..."))
        
        # --- HÀM CALLBACK ĐỂ CẬP NHẬT UI ---
        # Hàm này sẽ được gọi liên tục bên trong ProgressStream
        def update_progress_ui(current, total):
            percent = int((current / total) * 100)
            
            # Tính tốc độ (đơn giản hóa để UI mượt)
            # (Lưu ý: Tốc độ hiển thị ở đây là tốc độ ĐỌC Ổ CỨNG để đẩy lên RAM, 
            # nó tương đương tốc độ mạng nếu mạng nhanh, hoặc nhanh hơn nếu mạng chậm)
            
            progress_queue.put(("drive_upload_progress", {
                "percent": percent,
                "status_text": f"🚀 Đang tải lên: {percent}% ({format_bytes(current)} / {format_bytes(total)})",
                "speed_text": "Đang chạy...", # Có thể tính toán speed kỹ hơn nếu muốn
                "eta_text": ""
            }))

        stream = None
        try:
            global drive_service
            file_size = os.path.getsize(local_path)

            # --- CẤU HÌNH CHUNK LỚN (GIỮ NGUYÊN ĐỂ TỐI ƯU TỐC ĐỘ) ---
            # Dùng 256MB cho 8GB RAM
            chunk_size = 256 * 1024 * 1024 
            if file_size < chunk_size:
                chunk_size = file_size
            
            # Đảm bảo chia hết cho 256KB
            if chunk_size > 256 * 1024:
                chunk_size = int(chunk_size / (256 * 1024)) * (256 * 1024)

            # --- KÍCH HOẠT PROGRESS STREAM ---
            # Thay vì io.open thường, ta dùng class bọc của chúng ta.
            # Quan trọng: Không dùng buffering lớn ở đây, để hàm read() được gọi thường xuyên hơn -> UI mượt hơn.
            stream = ProgressStream(local_path, callback=update_progress_ui, mode='rb')

            media = MediaIoBaseUpload(
                stream,
                mimetype='application/octet-stream',
                chunksize=chunk_size,
                resumable=True
            )

            request = drive_service.files().update(
                fileId=target_id,
                media_body=media,
                fields='id'
            )

            # --- VÒNG LẶP UPLOAD ---
            response = None
            while response is None:
                # chunk_status sẽ là None cho đến khi hết 1 chunk lớn (256MB)
                # NHƯNG: ProgressStream vẫn đang âm thầm chạy và cập nhật UI ở nền
                chunk_status, response = request.next_chunk()
                
                # (Không cần cập nhật UI ở đây nữa vì ProgressStream đã làm rồi)

            if response:
                print(f"Upload xong ID: {target_id}")
                progress_queue.put(("drive_log", f"✅ Hoàn tất: '{target_name}'"))
                progress_queue.put(("refresh_drive_list", None))
                
                # Set 100% lần cuối cho chắc chắn
                progress_queue.put(("drive_upload_progress", {
                    "percent": 100, "status_text": "Hoàn tất!", "speed_text": "", "eta_text": ""
                }))

        except HttpError as error:
            print(f"Lỗi HttpError: {error}")
            progress_queue.put(("drive_log", f"❌ LỖI API: {error}"))
            progress_queue.put(("drive_upload_progress", {"status_text": "Lỗi Mạng!", "percent": 0}))
        except Exception as e:
            print(f"Lỗi Exception: {e}")
            progress_queue.put(("drive_log", f"❌ LỖI: {e}"))
            progress_queue.put(("drive_upload_progress", {"status_text": "Lỗi!", "percent": 0}))
        finally:
            if stream:
                stream.close()
            
            root.after(2000, lambda: progress_queue.put(("drive_upload_progress", {
                "percent": 0, "status_text": "Sẵn sàng.", "speed_text": "", "eta_text": ""
            })))

    # Frame cho ô kéo thả
    drop_target_frame = ttk.LabelFrame(third_tab_frame, text="File chờ upload", padding=(10, 10))
    drop_target_frame.pack(fill=tk.BOTH, expand=True, pady=5)

    # --- THÊM NÚT NÀY VÀO ---
    btn_browse_tab3 = ttk.Button(drop_target_frame, text="📂 Chọn File từ máy tính...", command=action_browse_upload_files)
    btn_browse_tab3.pack(fill=tk.X, pady=(0, 5)) # Nằm trên listbox

    # --- LISTBOX (GIỮ NGUYÊN để hiển thị danh sách) ---
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
    fourth_tab_frame = ttk.Frame(notebook, padding=(15, 15))
    notebook.add(fourth_tab_frame, text=" Cài Đặt & Credit ") # Đổi tên tab cho đúng ý nghĩa

    # --- 1. HEADER (Thông tin App) ---
    header_frame = ttk.Frame(fourth_tab_frame)
    header_frame.pack(fill=tk.X, pady=(0, 15))

    # Logo/Title bên trái, Info bên phải (hoặc căn giữa tùy ý, ở đây căn giữa cho đẹp)
    credit_title_label = ttk.Label(
        header_frame,
        text=f"WGZ Game Updater {CURRENT_VERSION}",
        font=("Segoe UI", 16, "bold"),
        anchor=tk.CENTER
    )
    credit_title_label.pack()

    credit_author_label = ttk.Label(
        header_frame,
        text="Dev: Mr-Mime (hoangdangnhatkha)",
        style="secondary.TLabel",
        anchor=tk.CENTER
    )
    credit_author_label.pack()
    settings_container = ttk.Frame(fourth_tab_frame)
    settings_container.pack(fill=tk.X, pady=5)
    settings_container.columnconfigure(0, weight=1)
    settings_container.columnconfigure(1, weight=1)
    setting_frame = ttk.LabelFrame(settings_container, text="⚙️ Chế Độ Hoạt Động", padding=10)
    setting_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
    # Link GitHub
    def open_github(event):
        webbrowser.open_new_tab("https://github.com/hoangdangnhatkha/-WGZ-GameUpdater")

    credit_github_label = ttk.Label(
        header_frame,
        text="GitHub Repository",
        foreground="#4a90e2", cursor="hand2", font=("Segoe UI", 9, "underline"),
        anchor=tk.CENTER
    )
    credit_github_label.pack(pady=(2, 0))
    credit_github_label.bind("<Button-1>", open_github)
    credit_thanks_label = ttk.Label(
        header_frame, # Quan trọng: Pack vào header_frame
        text="Chỉ dành cho việc tải, upload và chia sẻ game của Discord WIBU's Gaming Zone",
        style="secondary.TLabel",
        font=("Segoe UI", 9, "italic"), # Chữ nghiêng cho đẹp
        anchor=tk.CENTER
    )
    credit_thanks_label.pack(pady=(5, 0))
    # --- THÊM MỚI: NÚT BẬT/TẮT BACKUP ---


    def action_clear_image_cache():
        """Xóa toàn bộ thư mục cache ảnh trên ổ cứng."""
        global g_cache_dir
        if not os.path.isdir(g_cache_dir):
            custom_showinfo("Hoàn tất", "Không tìm thấy thư mục cache ảnh (đã sạch).")
            return

        if custom_askyesno("Xác nhận Xóa Cache",
                            "Bạn có chắc chắn muốn xóa toàn bộ cache ảnh?\n"
                            "(Lần khởi động sau sẽ phải tải lại tất cả ảnh.)"):
            try:
                # Xóa toàn bộ thư mục và tạo lại
                shutil.rmtree(g_cache_dir)
                os.makedirs(g_cache_dir, exist_ok=True)
                
                # Xóa cache RAM
                root.cached_images.clear()
                
                custom_showinfo("Hoàn tất", "Đã xóa toàn bộ cache ảnh thành công.")
            except Exception as e:
                custom_showerror("Lỗi", f"Không thể xóa thư mục cache: {e}")

    # --- [TÍNH NĂNG] SỔ TAY GHI CHÚ (CLICK-THROUGH SWITCH) ---
    g_notes_window = None
    g_notes_is_ghost = False # Biến theo dõi trạng thái

    def set_window_click_through(hwnd, enable):
        """Hàm helper để bật/tắt chế độ xuyên thấu chuột."""
        try:
            import ctypes
            GWL_EXSTYLE = -20
            WS_EX_LAYERED = 0x00080000
            WS_EX_TRANSPARENT = 0x00000020
            
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            
            if enable:
                # Thêm cờ Transparent
                new_style = style | WS_EX_LAYERED | WS_EX_TRANSPARENT
                print("Note: Chế độ Bóng ma (Click-Through) -> ON")
            else:
                # Gỡ bỏ cờ Transparent (giữ lại Layered để dùng Alpha)
                new_style = (style & ~WS_EX_TRANSPARENT) | WS_EX_LAYERED
                print("Note: Chế độ Chỉnh sửa -> ON")
                
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
        except Exception as e:
            print(f"Lỗi set style: {e}")

    def action_toggle_notes():
        """
        Quản lý Sổ tay:
        - Nếu chưa mở -> Mở lên (Chế độ sửa).
        - Nếu đang mở (Ghost) -> Chuyển về chế độ Sửa.
        - Nếu đang mở (Sửa) -> Đóng lại (Hoặc chuyển Ghost tùy ý).
        """
        global g_notes_window, g_notes_is_ghost

        # --- TRƯỜNG HỢP 1: ĐANG MỞ THÌ CHUYỂN CHẾ ĐỘ ---
        if g_notes_window is not None:
            if g_notes_is_ghost:
                # Đang là Ghost -> Chuyển thành Edit (Unlock)
                g_notes_is_ghost = False
                
                # Lấy HWND và tắt xuyên thấu
                g_notes_window.update_idletasks()
                import ctypes
                hwnd = ctypes.windll.user32.GetParent(g_notes_window.winfo_id())
                if hwnd == 0: hwnd = g_notes_window.winfo_id()
                set_window_click_through(hwnd, False)
                
                # Thay đổi giao diện để báo hiệu
                g_notes_window.attributes('-alpha', 0.9) # Đậm hơn
                # Hiện lại thanh tiêu đề (nếu muốn logic phức tạp hơn, ở đây ta đổi màu viền)
                g_notes_window.config(bg="#4a90e2") # Viền xanh dương (Edit Mode)
                
                # Focus vào cửa sổ
                g_notes_window.lift()
                g_notes_window.focus_force()
            else:
                # Đang là Edit -> Đóng lại (Hoặc bạn có thể chọn ẩn đi)
                g_notes_window.destroy()
                g_notes_window = None
                g_notes_is_ghost = False
            return

        # --- TRƯỜNG HỢP 2: CHƯA MỞ -> TẠO MỚI ---
        try:
            g_notes_window = tk.Toplevel(root)
            g_notes_window.title("Notes")
            g_notes_window.geometry("350x250+50+150") 
            g_notes_window.overrideredirect(True)
            g_notes_window.attributes('-topmost', True)
            g_notes_window.attributes('-alpha', 0.9)
            g_notes_window.config(bg="#4a90e2") # Viền xanh (Edit Mode)

            # Padding frame (để tạo viền màu)
            padding_frame = tk.Frame(g_notes_window, bg="#4a90e2", padx=2, pady=2)
            padding_frame.pack(fill=tk.BOTH, expand=True)

            # Khung nội dung chính
            main_frame = ttk.Frame(padding_frame, style="Card.TFrame")
            main_frame.pack(fill=tk.BOTH, expand=True)

            # 1. THANH TIÊU ĐỀ
            title_bar = tk.Frame(main_frame, bg="#333", height=30)
            title_bar.pack(fill=tk.X)
            
            lbl_title = tk.Label(title_bar, text="📝 Đang Sửa (Kéo để di chuyển)", bg="#333", fg="white", cursor="fleur")
            lbl_title.pack(side=tk.LEFT, padx=5)

            # --- NÚT KHÓA (LOCK BUTTON) ---
            def lock_notes():
                global g_notes_is_ghost
                g_notes_is_ghost = True
                
                # 1. Đổi giao diện
                g_notes_window.attributes('-alpha', 0.4) # Mờ đi (Ghost)
                g_notes_window.config(bg="#333") # Mất viền xanh
                padding_frame.config(padx=0, pady=0) # Bỏ padding
                
                # 2. Kích hoạt Click-Through
                g_notes_window.update_idletasks()
                import ctypes
                hwnd = ctypes.windll.user32.GetParent(g_notes_window.winfo_id())
                if hwnd == 0: hwnd = g_notes_window.winfo_id()
                set_window_click_through(hwnd, True)
                
                print("Đã khóa Note. Bấm nút trên App chính để Sửa lại.")

            btn_lock = tk.Label(title_bar, text=" 🔒 Xong ", bg="#28a745", fg="white", cursor="hand2", font=("Segoe UI", 9, "bold"))
            btn_lock.pack(side=tk.RIGHT, padx=2)
            btn_lock.bind("<Button-1>", lambda e: lock_notes())
            CreateToolTip(btn_lock, "Bấm vào đây để khóa Note và cho phép chuột bấm xuyên qua.\n(Để sửa lại: Bấm nút 'Sổ Tay Game' ở App chính)")

            # 2. VÙNG NỘI DUNG
            text_area = tk.Text(main_frame, bg="#222", fg="#00FF00", insertbackground="white", 
                                font=("Consolas", 10), bd=0, highlightthickness=0)
            text_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            text_area.images = [] 

            # --- Paste & Resize Logic (Giữ nguyên) ---
            def handle_paste(event):
                try:
                    img = ImageGrab.grabclipboard()
                    if isinstance(img, Image.Image):
                        orig_w, orig_h = img.size
                        target_w = int(orig_w * 0.7)
                        target_h = int(orig_h * 0.7)
                        img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                        
                        curr_w = g_notes_window.winfo_width()
                        curr_h = g_notes_window.winfo_height()
                        new_w = max(curr_w, target_w + 30)
                        new_h = max(curr_h, target_h + 60)
                        g_notes_window.geometry(f"{new_w}x{new_h}")
                        
                        tk_img = ImageTk.PhotoImage(img)
                        text_area.images.append(tk_img)
                        text_area.image_create(tk.INSERT, image=tk_img)
                        text_area.insert(tk.INSERT, "\n") 
                        return "break" 
                    return None
                except: pass

            text_area.bind("<Control-v>", handle_paste)
            text_area.insert("1.0", "Ctrl+V: Dán ảnh.\nBấm '🔒 Xong' để khóa & Click xuyên qua.\n")

            # --- Di chuyển cửa sổ ---
            def start_move(event):
                g_notes_window.x = event.x
                g_notes_window.y = event.y

            def do_move(event):
                deltax = event.x - g_notes_window.x
                deltay = event.y - g_notes_window.y
                x = g_notes_window.winfo_x() + deltax
                y = g_notes_window.winfo_y() + deltay
                g_notes_window.geometry(f"+{x}+{y}")

            lbl_title.bind("<ButtonPress-1>", start_move)
            lbl_title.bind("<B1-Motion>", do_move)
            title_bar.bind("<ButtonPress-1>", start_move)
            title_bar.bind("<B1-Motion>", do_move)

            # Resize Grip (Giữ nguyên)
            grip = tk.Label(main_frame, bg="#555", cursor="sizing")
            grip.place(relx=1.0, rely=1.0, x=0, y=0, anchor="se", width=15, height=15)
            def start_resize(event):
                g_notes_window.start_w = g_notes_window.winfo_width()
                g_notes_window.start_h = g_notes_window.winfo_height()
                g_notes_window.start_x = event.x_root
                g_notes_window.start_y = event.y_root
            def do_resize(event):
                delta_w = event.x_root - g_notes_window.start_x
                delta_h = event.y_root - g_notes_window.start_y
                new_w = max(g_notes_window.start_w + delta_w, 100)
                new_h = max(g_notes_window.start_h + delta_h, 100)
                g_notes_window.geometry(f"{new_w}x{new_h}")
            grip.bind("<ButtonPress-1>", start_resize)
            grip.bind("<B1-Motion>", do_resize)

        except Exception as e:
            print(f"Lỗi Notes: {e}")
            g_notes_window = None

    # --- [THÊM MỚI] TÍNH NĂNG TÂM ẢO (CROSSHAIR) ---
    g_crosshair_window = None 

    def action_toggle_crosshair():
        """
        Bật/Tắt tâm ngắm ảo.
        Sử dụng Windows API để cho phép click xuyên qua (Click-Through).
        """
        global g_crosshair_window
        
        # Import các hằng số Windows API
        try:
            import ctypes
            GWL_EXSTYLE = -20
            WS_EX_LAYERED = 0x00080000
            WS_EX_TRANSPARENT = 0x00000020 # Cờ quan trọng nhất: Click xuyên qua
        except ImportError:
            custom_showerror("Lỗi", "Tính năng này yêu cầu thư viện ctypes (Windows).")
            return

        # Nếu đang bật -> Tắt đi
        if g_crosshair_window is not None:
            try:
                g_crosshair_window.destroy()
            except: pass
            g_crosshair_window = None
            print("Đã tắt Crosshair.")
            return

        # Nếu đang tắt -> Bật lên
        try:
            g_crosshair_window = tk.Toplevel(root)
            g_crosshair_window.title("Crosshair")
            
            # 1. Cấu hình hình học
            w, h = 30, 30
            screen_w = root.winfo_screenwidth()
            screen_h = root.winfo_screenheight()
            x = (screen_w // 2) - (w // 2)
            y = (screen_h // 2) - (h // 2)
            
            g_crosshair_window.geometry(f"{w}x{h}+{x}+{y}")
            g_crosshair_window.overrideredirect(True) 
            g_crosshair_window.attributes('-topmost', True) 
            
            # 2. Màu nền trong suốt
            bg_color = '#000001' 
            g_crosshair_window.config(bg=bg_color)
            try:
                g_crosshair_window.attributes('-transparentcolor', bg_color)
            except Exception: pass

            # 3. Vẽ Tâm
            canvas = tk.Canvas(g_crosshair_window, width=w, height=h, bg=bg_color, highlightthickness=0)
            canvas.pack()
            
            center = w // 2
            length = 8
            thickness = 2
            
            # Vẽ dấu cộng màu xanh lá (Lime)
            canvas.create_line(center - length, center, center + length + 1, center, fill="#00FF00", width=thickness)
            canvas.create_line(center, center - length, center, center + length + 1, fill="#00FF00", width=thickness)
            
            # --- [QUAN TRỌNG] KÍCH HOẠT CHẾ ĐỘ XUYÊN THẤU ---
            # Phải update idletasks để window có ID (HWND) trước khi gọi API
            g_crosshair_window.update_idletasks() 
            
            hwnd = ctypes.windll.user32.GetParent(g_crosshair_window.winfo_id())
            if hwnd == 0: # Fallback nếu không lấy được parent
                hwnd = g_crosshair_window.winfo_id()
                
            # Lấy style hiện tại
            current_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            
            # Thêm cờ Transparent (Xuyên thấu chuột) và Layered
            new_style = current_style | WS_EX_LAYERED | WS_EX_TRANSPARENT
            
            # Áp dụng style mới
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
            
            print("Đã bật Crosshair (Click-Through Mode).")

        except Exception as e:
            print(f"Lỗi bật Crosshair: {e}")
            g_crosshair_window = None

    # --- THÊM MỚI: HÀM DỌN DẸP TEMP ---
    def action_clean_temp_files():
        """
        (PHIÊN BẢN MẠNH) Quét và xóa TOÀN BỘ file trong thư mục %TEMP% của Windows.
        Tự động bỏ qua các file đang được sử dụng (Locked files).
        """
        import shutil # Đảm bảo đã import thư viện này

        temp_dir = os.environ.get('TEMP')
        if not temp_dir or not os.path.isdir(temp_dir):
            custom_showerror("Lỗi", "Không thể tìm thấy thư mục Temp của Windows.")
            return

        # 1. Cảnh báo người dùng (Vì hành động này xóa rộng hơn)
        if not custom_askyesno("Xác nhận Dọn Sạch", 
                                f"Bạn sắp xóa TOÀN BỘ file rác trong thư mục Temp:\n{temp_dir}\n\n"
                                "Lưu ý:\n"
                                "• Hành động này sẽ giải phóng dung lượng ổ C.\n"
                                "• Các file đang được Windows/App khác sử dụng sẽ tự động được giữ lại.\n\n"
                                "Bạn có muốn tiếp tục không?"):
            return

        # 2. Bắt đầu dọn dẹp
        deleted_count = 0
        skipped_count = 0
        bytes_freed = 0
        
        print("--- Bắt đầu dọn dẹp toàn bộ Temp ---")
        
        try:
            # Lấy danh sách tất cả file/folder
            all_items = os.listdir(temp_dir)
            
            for item in all_items:
                item_path = os.path.join(temp_dir, item)
                
                try:
                    # Lấy kích thước trước khi xóa (để báo cáo)
                    current_size = 0
                    if os.path.isfile(item_path):
                        current_size = os.path.getsize(item_path)
                    
                    # XÓA FILE
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        os.remove(item_path)
                        deleted_count += 1
                        bytes_freed += current_size
                        
                    # XÓA FOLDER (Dùng shutil.rmtree)
                    elif os.path.isdir(item_path):
                        # Tính sơ bộ size folder (nếu muốn chính xác phải duyệt đệ quy, nhưng sẽ chậm)
                        shutil.rmtree(item_path)
                        deleted_count += 1
                        
                except Exception:
                    # Nếu lỗi (PermissionDenied, FileInUse...) -> Bỏ qua
                    skipped_count += 1
                    
        except Exception as e:
            custom_showerror("Lỗi", f"Lỗi khi quét thư mục Temp: {e}")
            return

        # 3. Hiển thị kết quả
        msg = (f"Đã dọn dẹp xong!\n\n"
            f"✅ Đã xóa: {deleted_count} mục\n"
            f"🛡️ Đang sử dụng (Bỏ qua): {skipped_count} mục\n"
            f"💾 Dung lượng giải phóng: {format_bytes(bytes_freed)} (ước tính)")
            
        custom_showinfo("Dọn Dẹp Hoàn Tất", msg)

    # --- [TÍNH NĂNG MỚI] GEMINI AI PRO BROWSER ---
    def action_open_gemini_pro():
        """
        Khởi động Gemini bằng Subprocess gọi lại chính file EXE này với cờ riêng.
        Cách này ổn định nhất cho PyInstaller --onefile.
        """
        try:
            import subprocess
            
            # Lấy đường dẫn file chạy hiện tại (dù là .py hay .exe)
            current_executable = sys.executable
            
            # Nếu đang chạy code .py (Dev mode), sys.executable là python.exe
            # ta cần truyền thêm tên file script.
            cmd = [current_executable]
            if not getattr(sys, 'frozen', False):
                cmd.append(sys.argv[0]) # Thêm tên file .py
                
            # Thêm cờ hiệu lệnh
            cmd.append("--gemini")
            
            print(f"Đang khởi động Gemini subprocess: {cmd}")
            
            # Chạy tiến trình tách biệt hoàn toàn
            subprocess.Popen(
                cmd,
                creationflags=0x00000008, # DETACHED_PROCESS (Không dính dáng console cha)
                close_fds=True
            )
            
        except Exception as e:
            custom_showerror("Lỗi", f"Không thể mở Gemini: {e}")

    def on_secret_click(event):
        """Đếm số lần click vào label dung lượng."""
        global g_secret_click_count, drive_service

        

        g_secret_click_count += 1

        # Đặt lại bộ đếm sau 2 giây
        event.widget.after(2000, lambda: globals().update(g_secret_click_count=0))

        if g_secret_click_count == 3:
            if not drive_service:
                custom_showwarning("Chưa đăng nhập", "Bạn phải đăng nhập Google Drive trước.")
                return
            print("Đã kích hoạt tính năng bí mật!")
            g_secret_click_count = 0
            open_secret_uploader()

    def action_browse_secret_exe():
        """Thay thế kéo thả cho Secret Uploader."""
        file_path = filedialog.askopenfilename(
            title="Chọn file .exe bản build mới",
            filetypes=[("Executable", "*.exe")]
        )
        
        if file_path:
            secret_drop_listbox.delete(0, tk.END)
            secret_drop_listbox.insert(tk.END, file_path)

    def open_secret_uploader():
        """Mở cửa sổ upload bí mật."""
        global secret_drop_listbox, secret_exe_id_entry, secret_zip_id_entry, secret_window

        secret_window = tk.Toplevel(root)
        secret_window.title("Secret Updater Config")
        secret_window.after(10, lambda: apply_theme_to_titlebar(secret_window))
        center_window_on_screen(secret_window, 500, 350)
        secret_window.transient(root)
        secret_window.grab_set()

        main_frame = ttk.Frame(secret_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Khung kéo thả
        drop_frame = ttk.LabelFrame(main_frame, text="1. Kéo 1 file .exe (bản build mới) vào đây")
        drop_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        ttk.Button(drop_frame, text="📂 Chọn File .exe", command=action_browse_secret_exe).pack(fill=tk.X, padx=5, pady=5)
        secret_drop_listbox = tk.Listbox(drop_frame, height=3)
        secret_drop_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        secret_drop_listbox.drop_target_register(DND_FILES)
        secret_drop_listbox.dnd_bind('<<Drop>>', handle_secret_drop)

        # 2. Khung config
        config_frame = ttk.LabelFrame(main_frame, text="2. Cấu hình Link Drive")
        config_frame.pack(fill=tk.X, pady=5)

        row1 = ttk.Frame(config_frame)
        row1.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(row1, text="File ID của .EXE Chính:", width=22).pack(side=tk.LEFT)
        secret_exe_id_entry = ttk.Entry(row1)
        secret_exe_id_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        secret_exe_id_entry.insert(0, local_config.get("secret_exe_id", ""))

        row2 = ttk.Frame(config_frame)
        row2.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(row2, text="File ID của Bundle (.ZIP):", width=22).pack(side=tk.LEFT)

        secret_zip_id_entry = ttk.Entry(row2)
        secret_zip_id_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        secret_zip_id_entry.insert(0, local_config.get("secret_zip_id", ""))
        # 3. Nút bắt đầu
        start_button = ttk.Button(main_frame, text="Bắt đầu Upload Lên 2 Link", 
                                command=start_secret_upload, style="Accent.TButton")
        start_button.pack(pady=10)

    def handle_secret_drop(event):
        """Xử lý khi kéo file vào cửa sổ bí mật."""
        secret_drop_listbox.delete(0, tk.END) # Chỉ cho phép 1 file
        raw_paths = root.tk.splitlist(event.data)

        if raw_paths:
            file_path = raw_paths[0] # Lấy file đầu tiên
            if os.path.exists(file_path) and os.path.isfile(file_path) and file_path.endswith(".exe"):
                secret_drop_listbox.insert(tk.END, file_path)
            else:
                secret_drop_listbox.insert(tk.END, "Lỗi: Chỉ chấp nhận 1 file .exe")

    def start_secret_upload():
        """Bắt đầu luồng upload bí mật."""
        global scan_loading_window # Tái sử dụng cửa sổ loading

        try:
            file_path = secret_drop_listbox.get(0)
        except tk.TclError:
            custom_showerror("Lỗi", "Chưa kéo file .exe vào.", parent=secret_window)
            return

        exe_id = secret_exe_id_entry.get().strip()
        zip_id = secret_zip_id_entry.get().strip()

        # --- THÊM MỚI: Lưu ID mới vào config ---
        global local_config
        local_config["secret_exe_id"] = exe_id
        local_config["secret_zip_id"] = zip_id
        save_local_config(local_config)
        print("Đã lưu secret File IDs vào settings.json")

        if not file_path or not exe_id or not zip_id:
            custom_showerror("Lỗi", "Vui lòng kéo file và điền cả 2 File ID.", parent=secret_window)
            return

        if not file_path.endswith(".exe"):
            custom_showerror("Lỗi", "File kéo vào phải là file .exe.", parent=secret_window)
            return

        # Hiển thị cửa sổ "Đang tải"
        scan_loading_window = tk.Toplevel(root)
        scan_loading_window.title("Đang Upload...")
        center_window_on_screen(scan_loading_window, 350, 100)
        scan_loading_window.transient(secret_window)
        scan_loading_window.grab_set()

        global secret_loading_label # Cần global để cập nhật text
        secret_loading_label = ttk.Label(scan_loading_window, text="Đang chuẩn bị...")
        secret_loading_label.pack(expand=True, padx=20, pady=20)

        threading.Thread(target=secret_upload_thread, 
                        args=(file_path, exe_id, zip_id), 
                        daemon=True).start()

    def secret_upload_thread(file_path, exe_id, zip_id):
        """(Chạy ngầm) Upload file .exe, nén .zip, và upload .zip."""
        try:
            # --- 1. UPLOAD FILE .EXE CHÍNH ---
            progress_queue.put(("secret_status", "Đang upload file .exe chính..."))
            _secret_update_file(file_path, exe_id)

            # --- 2. NÉN BUNDLE .ZIP ---
            progress_queue.put(("secret_status", "Đang nén file .zip (gồm .exe và updater.exe)..."))

            # SỬA: Tìm updater.exe BÊN CẠNH file .exe MỚI được thả vào
            # 'file_path' là đường dẫn đến .exe MỚI (ví dụ: C:\NewBuild\WGZGameUpdater.exe)
            new_app_dir = os.path.dirname(file_path)
            updater_path = os.path.join(new_app_dir, "updater.exe")

            if not os.path.exists(updater_path):
                raise FileNotFoundError(f"Không tìm thấy 'updater.exe' trong cùng thư mục với file bạn vừa thả vào:\n({new_app_dir})")

            temp_zip_path = os.path.join(os.environ['TEMP'], "_temp_secret_bundle.zip")

            # Xóa file zip cũ nếu có
            if os.path.exists(temp_zip_path):
                os.remove(temp_zip_path)

            print(f"Đang nén '{file_path}' và '{updater_path}' vào '{temp_zip_path}'")
            with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Thêm file .exe mới (đặt tên là tên file gốc)
                zf.write(file_path, arcname=os.path.basename(file_path))
                # Thêm file updater.exe
                zf.write(updater_path, arcname="updater.exe")

            print("Nén file .zip thành công.")

            # --- 3. UPLOAD FILE .ZIP ---
            progress_queue.put(("secret_status", "Đang upload file .zip..."))
            _secret_update_file(temp_zip_path, zip_id)

            # --- 4. DỌN DẸP ---
            progress_queue.put(("secret_status", "Đang dọn dẹp file tạm..."))
            if os.path.exists(temp_zip_path):
                os.remove(temp_zip_path)

            progress_queue.put(("secret_done", "Hoàn thành cả 2 file!"))

        except Exception as e:
            print(f"Lỗi trong secret_upload_thread: {e}")
            progress_queue.put(("secret_error", str(e)))

    def _secret_update_file(file_path, file_id):
        """Hàm helper (chạy ngầm) để upload (update) 1 file."""
        global drive_service
        try:
            print(f"Đang update File ID: {file_id} bằng file: {file_path}")
            # Dùng MediaFileUpload (không cần chunk)
            media_body = MediaFileUpload(file_path, resumable=False)

            # Gọi .update() để ghi đè file đã có
            drive_service.files().update(
                fileId=file_id,
                media_body=media_body
            ).execute()
            print(f"Update thành công File ID: {file_id}")

        except HttpError as error:
            # Nếu lỗi, thử tạo file mới (phòng trường hợp ID bị xóa)
            if error.resp.status == 404:
                print(f"Lỗi 404: File ID {file_id} không tồn tại. Đang thử tạo file mới...")
                file_metadata = {'name': os.path.basename(file_path), 'parents': [GOOGLE_DRIVE_FOLDER_ID]}
                media_body = MediaFileUpload(file_path, resumable=False)
                new_file = drive_service.files().create(
                    body=file_metadata,
                    media_body=media_body,
                    fields='id'
                ).execute()
                print(f"TẠO FILE MỚI THAY THẾ. ID MỚI: {new_file.get('id')}")
                progress_queue.put(("secret_status", f"Cảnh báo: ID cũ {file_id} bị lỗi.\nĐã tạo file mới với ID: {new_file.get('id')}"))
            else:
                raise error # Ném lại lỗi nếu không phải 404
            
    drive_storage_label.bind("<Button-1>", on_secret_click)

    # Hàm on_backup_toggle (không đổi, chỉ copy vào đây)
    # Logic Toggle Backup
    def on_backup_toggle():
        global local_config
        is_enabled = g_backup_enabled.get()
        local_config["backup_enabled"] = is_enabled
        save_local_config(local_config)
        print(f"Backup: {is_enabled}")

    backup_checkbutton = ttk.Checkbutton(
        setting_frame,
        text="💾 Tự động sao lưu (Backup)",
        variable=g_backup_enabled,
        command=on_backup_toggle,
        style="Switch.TCheckbutton"
    )
    backup_checkbutton.pack(anchor=tk.W, pady=5)
    CreateToolTip(backup_checkbutton, "Sao lưu file cũ vào folder _BACKUPS trước khi cập nhật/cài đặt.")
    g_smart_mode_enabled = tk.BooleanVar(value=local_config.get("smart_mode_enabled", False))

    def on_smart_mode_toggle():
        global local_config
        is_enabled = g_smart_mode_enabled.get()
        local_config["smart_mode_enabled"] = is_enabled
        save_local_config(local_config)
        print(f"Smart Game Mode: {is_enabled}")

    smart_checkbutton = ttk.Checkbutton(
        setting_frame, 
        text="🚀 Smart Game Mode (Ưu tiên Game & Dọn RAM toàn hệ thống)",
        variable=g_smart_mode_enabled,
        command=on_smart_mode_toggle,
        style="Switch.TCheckbutton"
    )
    # pady=(0, 10) để tạo khoảng cách phía dưới tách biệt với các nút dọn dẹp
    smart_checkbutton.pack(anchor=tk.W, pady=5) 

    CreateToolTip(smart_checkbutton, "1. Dọn RAM cho TẤT CẢ ứng dụng đang chạy.\n"
                                    "2. Chạy Game với mức ưu tiên CPU CAO (High Priority).")

    g_auto_close = tk.BooleanVar(value=local_config.get("auto_close", False))

    def on_auto_close_toggle():
        global local_config
        local_config["auto_close"] = g_auto_close.get()
        save_local_config(local_config)
        print(f"Auto Close: {g_auto_close.get()}")

    # Tạo Checkbox
    auto_close_check = ttk.Checkbutton(
        setting_frame,
        text="👻 Tự động tắt App khi vào Game",
        variable=g_auto_close,
        command=on_auto_close_toggle,
        style="Switch.TCheckbutton"
    )
    auto_close_check.pack(anchor=tk.W, pady=5)
    CreateToolTip(auto_close_check, "Sau khi bấm 'Chạy Game', ứng dụng này sẽ tự tắt\nđể giải phóng hoàn toàn RAM cho game.")

    # --- [THÊM MỚI] NÚT GẠT HIỆU ỨNG VỤ NỔ ---
    g_chaos_effect_enabled = tk.BooleanVar(value=local_config.get("chaos_effect_enabled", False)) # Mặc định là Bật (True)

    def on_chaos_effect_toggle():
        global local_config
        local_config["chaos_effect_enabled"] = g_chaos_effect_enabled.get()
        save_local_config(local_config)
        print(f"Chaos Effect: {g_chaos_effect_enabled.get()}")

    chaos_checkbutton = ttk.Checkbutton(
        setting_frame,
        text="💥 Ảo Thuật của Uchiha Itachi ",
        variable=g_chaos_effect_enabled,
        command=on_chaos_effect_toggle,
        style="Switch.TCheckbutton"
    )
    chaos_checkbutton.pack(anchor=tk.W, pady=5)
    CreateToolTip(chaos_checkbutton, "Khi bấm 'Chạy Game', giao diện sẽ nổ tung bay tứ tán.\nTắt đi nếu bạn thích sự nghiêm túc.")

    g_auto_translator = tk.BooleanVar(value=local_config.get("auto_start_translator", False))

    def on_translator_toggle():
        global local_config
        is_enabled = g_auto_translator.get()
        
        # 1. Lưu vào config
        local_config["auto_start_translator"] = is_enabled
        save_local_config(local_config)
        
        # 2. Xử lý Bật/Tắt ngay lập tức
        if is_enabled:
            start_translator_service()
            print("Translator: ON")
        else:
            stop_translator_service()
            print("Translator: OFF")

    translator_check = ttk.Checkbutton(
        setting_frame,
        text="🔮 Bật/Tắt Chức Năng Dịch Game ENG-VN (HotKey: Alt + ~)",
        variable=g_auto_translator,
        command=on_translator_toggle,
        style="Switch.TCheckbutton"
    )
    translator_check.pack(anchor=tk.W, pady=5)
    CreateToolTip(translator_check, "Tự động bật công cụ dịch (Alt + ~) khi mở App.\nNếu tắt, công cụ sẽ đóng ngay lập tức.")
    # --- Cột Phải: Công Cụ & Bảo Trì ---
    tools_frame = ttk.LabelFrame(settings_container, text="🛠️ Công Cụ & Bảo Trì", padding=10)
    tools_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

    # --- CẤU HÌNH LƯỚI ĐỂ CÁC NÚT BẰNG NHAU TUYỆT ĐỐI ---
    # uniform="btn_group": Ép buộc 2 cột này phải có cùng kích thước, bất kể nội dung text dài ngắn.
    tools_frame.columnconfigure(0, weight=1, uniform="btn_group")
    tools_frame.columnconfigure(1, weight=1, uniform="btn_group")
    # Cho phép giãn chiều cao nếu cần (tùy chọn)
    tools_frame.rowconfigure(0, weight=1)
    tools_frame.rowconfigure(1, weight=1)

    # Hàng 1 (Row 0)
    clean_temp_button = ttk.Button(tools_frame, text="Dọn %TEMP%", command=action_clean_temp_files)
    clean_temp_button.grid(row=0, column=0, sticky="nsew", padx=2, pady=2, ipady=5)
    CreateToolTip(clean_temp_button, "Xóa file .zip/.rar tạm tải về.")

    clear_img_cache_button = ttk.Button(tools_frame, text="Xóa Cache Ảnh", command=action_clear_image_cache)
    clear_img_cache_button.grid(row=0, column=1, sticky="nsew", padx=2, pady=2, ipady=5)
    CreateToolTip(clear_img_cache_button, "Tải lại ảnh bìa game nếu bị lỗi.")

    # Hàng 2 (Row 1)
    snapshot_btn = ttk.Button(tools_frame, text="📋 Kiểm Tra Cấu Hình", command=action_copy_system_info)
    snapshot_btn.grid(row=1, column=0, sticky="nsew", padx=2, pady=2, ipady=5)
    CreateToolTip(snapshot_btn, "Copy thông tin CPU/RAM/GPU để nhờ hỗ trợ.")

    global update_app_button
    update_app_button = ttk.Button(tools_frame, text="Kiểm tra Update App", command=action_manual_check_for_updates)
    update_app_button.grid(row=1, column=1, sticky="nsew", padx=2, pady=2, ipady=5)

    crosshair_btn = ttk.Button(tools_frame, text="🎯 Bật/Tắt Tâm Ảo", command=action_toggle_crosshair)
    crosshair_btn.grid(row=2, column=0, sticky="nsew", padx=2, pady=2, ipady=5)
    CreateToolTip(crosshair_btn, "Hiển thị tâm ngắm (Crosshair) màu xanh giữa màn hình.\nHỗ trợ bắn không cần ngắm (No-scope) trong game.")

    open_data_btn = ttk.Button(tools_frame, text="📂 Mở Data Folder", command=action_open_data_folder)
    open_data_btn.grid(row=2, column=1, sticky="nsew", padx=2, pady=2, ipady=5)
    CreateToolTip(open_data_btn, "Mở thư mục chứa settings.json và file log.")

    notes_btn = ttk.Button(tools_frame, text="📝 Note Dán Màn Hình", command=action_toggle_notes)
    notes_btn.grid(row=3, column=0, sticky="nsew", padx=2, pady=2, ipady=5)
    CreateToolTip(notes_btn, "Hiện tờ giấy ghi chú trong suốt trên màn hình game.\nDùng để ghi mật khẩu, nhiệm vụ...")


    # --- 3. PATH SETTINGS (Đường dẫn) ---
    path_settings_frame = ttk.LabelFrame(fourth_tab_frame, text="🔗 Liên Kết Launcher (Tự động tìm thấy)", padding=10)
    path_settings_frame.pack(fill=tk.X, pady=10)

    # Dùng Grid để căn thẳng hàng
    path_settings_frame.columnconfigure(1, weight=1)


    def action_save_path_settings():
        """Lấy đường dẫn từ Entry và lưu vào config."""
        global local_config
        
        try:
            # 1. Lấy giá trị từ các ô Entry
            # (Thêm kiểm tra 'in globals()' để tránh lỗi nếu UI chưa tạo)
            if 'g_steam_path_entry' in globals():
                steam_path = g_steam_path_entry.get()
                local_config["steam_path"] = steam_path
                print(f"Đã lưu Steam Path: {steam_path}")
                
            if 'g_riot_path_entry' in globals():
                riot_path = g_riot_path_entry.get()
                local_config["riot_path"] = riot_path
                print(f"Đã lưu Riot Path: {riot_path}")

            # 2. Lưu file settings.json
            save_local_config(local_config)
            
        except Exception as e:
            print(f"Lỗi khi lưu cài đặt đường dẫn: {e}")


    def action_launch_rustdesk():
        """
        Hiển thị hộp thoại tùy chỉnh (Custom Dialog) để chọn chế độ chạy RustDesk.
        Có áp dụng Theme cho Titlebar.
        """
        # 1. Tạo biến lưu kết quả
        selection_result = [None] 

        # 2. Tạo cửa sổ Dialog
        dialog = tk.Toplevel(root)
        dialog.title("Tùy chọn Hỗ trợ")
        
        # --- [MỚI] ÁP DỤNG THEME CHO TITLE BAR ---
        # Gọi hàm apply_theme_to_titlebar cho cửa sổ con này
        # Dùng .after(10) để đảm bảo cửa sổ đã khởi tạo xong trước khi tô màu
        dialog.after(10, lambda: apply_theme_to_titlebar(dialog))
        # -----------------------------------------
        
        # Kích thước và căn giữa
        dialog_width = 320
        dialog_height = 180
        center_window_on_screen(dialog, dialog_width, dialog_height)
        
        dialog.transient(root) 
        dialog.grab_set()      
        dialog.resizable(False, False)

        # Frame nội dung
        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        # Tiêu đề
        lbl = ttk.Label(
            frame, 
            text="Bạn muốn khởi động RustDesk như thế nào?", 
            wraplength=280, 
            justify=tk.CENTER,
            font=("Segoe UI", 10)
        )
        lbl.pack(pady=(0, 15))

        # --- Hàm xử lý chọn ---
        def on_choose_discord():
            selection_result[0] = True
            dialog.destroy() 

        def on_choose_local():
            selection_result[0] = False
            dialog.destroy() 

        # --- Nút bấm ---
        btn_discord = ttk.Button(
            frame, 
            text="🚀 Gửi ID lên Discord (Nhờ Admin)", 
            command=on_choose_discord, 
            style="Accent.TButton"
        )
        btn_discord.pack(fill=tk.X, pady=5)

        btn_local = ttk.Button(
            frame, 
            text="📂 Chỉ mở RustDesk (Không gửi)", 
            command=on_choose_local
        )
        btn_local.pack(fill=tk.X, pady=5)

        # --- CHỜ NGƯỜI DÙNG CHỌN ---
        root.wait_window(dialog)

        # 3. Xử lý kết quả
        if selection_result[0] is None:
            return

        send_to_discord = selection_result[0]
        discord_name = "Ẩn danh"

        # 4. Nếu chọn Gửi Discord -> Mới hỏi tên
        if send_to_discord:
            import getpass
            pc_user = getpass.getuser()
            discord_name = custom_askstring(
                "Xác nhận danh tính", 
                "Nhập tên để còn biết ai chứ mày: ",
                initialvalue=pc_user,
                parent=root
            )
            if not discord_name: 
                return 

        # 5. Bắt đầu chạy Thread
        if 'g_anydesk_button' in globals():
            g_anydesk_button.config(state=tk.DISABLED, text="Đang mở RustDesk...")
        
        threading.Thread(target=launch_rustdesk_thread, args=(send_to_discord, discord_name), daemon=True).start()

    def apply_anydesk_connection_fix():
        """
        Sửa file config của AnyDesk để tắt 'Direct Connection' (Kết nối trực tiếp).
        Giúp sửa lỗi Connecting/Disconnected liên tục.
        """
        try:
            # AnyDesk lưu config ở %APPDATA%\AnyDesk\user.conf hoặc system.conf
            appdata = os.getenv('APPDATA')
            conf_dir = os.path.join(appdata, "AnyDesk")
            
            # Đảm bảo thư mục tồn tại
            if not os.path.exists(conf_dir):
                os.makedirs(conf_dir, exist_ok=True)
                
            # Chúng ta sẽ sửa file user.conf (file này ghi đè cài đặt hệ thống)
            conf_file = os.path.join(conf_dir, "user.conf")
            
            print(f"Đang cấu hình AnyDesk tại: {conf_file}")
            
            lines = []
            # 1. Đọc nội dung cũ nếu file tồn tại
            if os.path.exists(conf_file):
                try:
                    with open(conf_file, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                except Exception as e:
                    print(f"Lỗi đọc config cũ: {e}")

            # 2. Xóa dòng cấu hình cũ (nếu có) để tránh trùng lặp
            # Key cần tìm: ad.anynet.direct_connection
            new_lines = [line for line in lines if "ad.anynet.direct_connection" not in line]
            
            # 3. Thêm dòng cấu hình mới (0 = Disable, 1 = Enable)
            new_lines.append("ad.anynet.direct_connection=0\n")
            
            # 4. Ghi lại file
            with open(conf_file, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
                
            print("--> Đã tắt 'Direct Connection' trong config thành công.")
            return True

        except Exception as e:
            print(f"Lỗi khi sửa config AnyDesk: {e}")
            return False

    def launch_rustdesk_thread(send_to_discord, discord_name):
        """
        (RUSTDESK FULL: AUTO INSTALL + SERVICE FIX)
        1. Kiểm tra nếu chưa cài -> Tự động cài vào Program Files.
        2. Cài đặt và Bật Service để lấy ID/Pass ổn định.
        3. Dùng cơ chế 'Fire and Forget' để tránh treo App.
        """
        CREATE_NO_WINDOW = 0x08000000 
        rustdesk_id = None
        temp_password = "WGZSupport2025" 
        
        # Định nghĩa các đường dẫn
        program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        installed_dir = os.path.join(program_files, "RustDesk")
        installed_exe = os.path.join(installed_dir, "RustDesk.exe")
        
        # --- HÀM HELPER: CHẠY LỆNH AN TOÀN ---
        def run_command_safe(cmd_list, wait_time=5):
            """Chạy lệnh với timeout để tránh treo App."""
            try:
                print(f"Executing: {' '.join(cmd_list)}")
                process = subprocess.Popen(
                    cmd_list, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=CREATE_NO_WINDOW
                )
                try:
                    stdout, stderr = process.communicate(timeout=wait_time)
                    return True
                except subprocess.TimeoutExpired:
                    print(f"Lệnh tốn quá {wait_time}s (có thể đang chạy ngầm). Bỏ qua...")
                    return True 
            except Exception as e:
                print(f"Lỗi lệnh: {e}")
                return False
        # -------------------------------------

        try:
            # --- BƯỚC 1: TẮT RUSTDESK CŨ ---
            print("Đang đóng RustDesk cũ...")
            run_command_safe(["taskkill", "/F", "/IM", "RustDesk.exe"], wait_time=2)
            time.sleep(1)

            # --- BƯỚC 2: TÌM FILE GỐC (PORTABLE) ---
            portable_exe = resource_path("RustDesk.exe")
            if not os.path.exists(portable_exe):
                portable_exe = "RustDesk.exe" 
            
            if not os.path.exists(portable_exe) and not os.path.exists(installed_exe):
                progress_queue.put(("anydesk_error", "Không tìm thấy file RustDesk.exe gốc để cài đặt."))
                return

            # --- BƯỚC 3: KIỂM TRA & CÀI ĐẶT (NẾU CẦN) ---
            target_exe = portable_exe 

            if os.path.exists(installed_exe):
                print("Phát hiện RustDesk đã được cài đặt.")
                target_exe = installed_exe
            else:
                print("Chưa cài đặt. Đang kích hoạt bộ cài...")
                if os.path.exists(portable_exe):
                    # 1. Chạy lệnh cài đặt nhưng KHÔNG đợi (Popen không communicate ngay)
                    print(f"Executing Install: {portable_exe} --install --silent")
                    install_proc = run_command_safe([portable_exe, "--install", "--silent"], wait_time=0)
                    
                    # 2. Vòng lặp kiểm tra file (Polling) thay vì Wait
                    # Quét mỗi 1 giây, tối đa 20 giây. Hễ thấy file là dừng.
                    print("Đang đợi file xuất hiện trong Program Files...")
                    install_success = False
                    for i in range(60):
                        if os.path.exists(installed_exe):
                            print(f"--> File đã xuất hiện sau {i+1} giây!")
                            install_success = True
                            break
                        time.sleep(1)
                    
                    if install_success:
                        # Chờ thêm 2s để file được ghi hoàn tất
                        time.sleep(2)
                        target_exe = installed_exe
                        print("Cài đặt hoàn tất (Smart Check).")
                        
                        # (Tùy chọn) Kill tiến trình cài đặt nếu nó còn treo
                        try: install_proc.kill() 
                        except: pass
                    else:
                        print("Cài đặt quá lâu hoặc thất bại. Dùng bản Portable.")
                        target_exe = portable_exe

            # --- BƯỚC 4: XỬ LÝ SERVICE (TỐI ƯU HÓA) ---
            print(f"Đang cấu hình Service cho: {target_exe}")
            
            # 1. Kiểm tra xem Service đã tồn tại chưa (để tránh bị timeout 10s vô ích)
            service_exists = False
            try:
                # Lệnh "sc query RustDesk" trả về 0 nếu service tồn tại, 1060 nếu không có
                check_svc = subprocess.run(
                    ["sc", "query", "RustDesk"], 
                    capture_output=True, 
                    text=True, 
                    creationflags=CREATE_NO_WINDOW
                )
                if check_svc.returncode == 0:
                    service_exists = True
                    print("Service 'RustDesk' đã tồn tại. Bỏ qua bước cài đặt.")
            except: pass

            # 2. Chỉ cài đặt nếu chưa có
            if not service_exists:
                # Tăng timeout lên 15s cho chắc chắn
                run_command_safe([target_exe, "--install-service"], wait_time=15)
                time.sleep(1)

            # 3. Đảm bảo đường dẫn Service trỏ đúng vào file exe hiện tại (Quan trọng khi update)
            # Nếu file exe thay đổi vị trí, lệnh này sẽ cập nhật lại đường dẫn cho Service
            try:
                subprocess.run(
                    ["sc", "config", "RustDesk", f"binPath= \"{target_exe}\""],
                    capture_output=True,
                    creationflags=CREATE_NO_WINDOW
                )
            except: pass

            # 4. Bật Service (Timeout 5s)
            # Dùng 'sc start' đôi khi nhanh hơn 'net start'
            run_command_safe(["sc", "start", "RustDesk"], wait_time=5)
            time.sleep(2)

            # --- BƯỚC 5: KHỞI ĐỘNG GIAO DIỆN ---
            print("Mở giao diện RustDesk...")
            subprocess.Popen([target_exe])

            # --- BƯỚC 6: CHỜ GUI VÀ LẤY ID ---
            print("⏳ Đang đợi cửa sổ App...")
            for i in range(20): 
                if gw.getWindowsWithTitle('RustDesk'):
                    break
                time.sleep(0.5)

            print("⏳ Đang lấy ID...")
            # Hàm lấy ID nội bộ
            def get_id_local():
                # Thử lệnh cmd trước
                try:
                    proc = subprocess.Popen([target_exe, "--get-id"], stdout=subprocess.PIPE, text=True, creationflags=CREATE_NO_WINDOW)
                    out, _ = proc.communicate(timeout=3)
                    val = out.strip().replace(" ", "")
                    if val.isdigit() and len(val) > 6: return val
                except: pass
                
                # Thử đọc file config
                paths = [
                    os.path.join(os.getenv('APPDATA'), 'RustDesk', 'config'),
                    os.path.join(os.getenv('LOCALAPPDATA'), 'RustDesk', 'config'),
                    os.path.join(os.environ.get("ProgramData", "C:\\ProgramData"), 'RustDesk', 'config') # Thêm ProgramData
                ]
                for d in paths:
                    for f in ['RustDesk.toml', 'RustDesk2.toml']:
                        full = os.path.join(d, f)
                        if os.path.exists(full):
                            try:
                                with open(full, 'r', encoding='utf-8') as file:
                                    match = re.search(r'id\s*=\s*[\'"]?(\d+)[\'"]?', file.read())
                                    if match: return match.group(1)
                            except: pass
                return None

            # Vòng lặp chờ ID
            for i in range(15):
                rustdesk_id = get_id_local()
                if rustdesk_id: break
                time.sleep(1)
                print(f"Đang chờ ID... {i}/15")

            # --- BƯỚC 7: XỬ LÝ KẾT QUẢ ---
            if rustdesk_id:
                print(f"✅ ID: {rustdesk_id}")
                
                # Đặt mật khẩu
                print("Đang đặt mật khẩu...")
                run_command_safe([target_exe, "--password", temp_password], wait_time=3)

                # Gửi thông báo
                install_status = "Installed & Service Running" if target_exe == installed_exe else "Portable Mode (Service Fix)"
                
                if send_to_discord and "YOUR_ID" not in DISCORD_WEBHOOK_URL:
                    try:
                        content_ping = ""
                        embed = {
                            "title": "🚀 Hỗ trợ RustDesk",
                            "color": 65280, 
                            "fields": [
                                { "name": "👤 User", "value": f"**{discord_name}**", "inline": True },
                                { "name": "🆔 ID", "value": f"```{rustdesk_id}```", "inline": True },
                                { "name": "🔑 Pass", "value": f"```{temp_password}```", "inline": True },
                                { "name": "💻 Status", "value": install_status, "inline": False }
                            ],
                            "footer": { "text": "WGZ Updater" }
                        }
                        requests.post(DISCORD_WEBHOOK_URL, json={
                            "content": content_ping, "username": "Bot RustDesk", "embeds": [embed]
                        }, timeout=5)
                        progress_queue.put(("anydesk_id_sent_to_discord", rustdesk_id))
                    except:
                        progress_queue.put(("anydesk_id_retrieved_locally", rustdesk_id))
                else:
                    progress_queue.put(("anydesk_id_retrieved_locally", rustdesk_id))
            else:
                progress_queue.put(("anydesk_error", "Không lấy được ID. Vui lòng kiểm tra lại RustDesk."))

        except Exception as e:
            print(f"Lỗi RustDesk: {e}")
            progress_queue.put(("anydesk_error", str(e)))
        
        finally:
            progress_queue.put(("anydesk_done", None))


    # --- THÊM MỚI: CÀI ĐẶT ĐƯỜNG DẪN STEAM ---
    ttk.Label(path_settings_frame, text="Steam Path:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
    global g_steam_path_entry
    g_steam_path_entry = ttk.Entry(path_settings_frame)
    g_steam_path_entry.grid(row=0, column=1, sticky="ew")
    g_steam_path_entry.bind("<FocusOut>", lambda e: action_save_path_settings())

    def browse_steam_exe():
        file_selected = filedialog.askopenfilename(title="Tìm steam.exe", filetypes=[("Executable", "steam.exe")])
        if file_selected:
            g_steam_path_entry.delete(0, tk.END)
            g_steam_path_entry.insert(0, file_selected)
            action_save_path_settings()

    ttk.Button(path_settings_frame, text="...", width=3, command=browse_steam_exe).grid(row=0, column=2, padx=(5, 0))

    # -- Riot --
    ttk.Label(path_settings_frame, text="Riot Client:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
    global g_riot_path_entry
    g_riot_path_entry = ttk.Entry(path_settings_frame)
    g_riot_path_entry.grid(row=1, column=1, sticky="ew", pady=(10, 0))
    g_riot_path_entry.bind("<FocusOut>", lambda e: action_save_path_settings())

    def browse_riot_exe():
        file_selected = filedialog.askopenfilename(title="Tìm RiotClientServices.exe", filetypes=[("Executable", "RiotClientServices.exe")])
        if file_selected:
            g_riot_path_entry.delete(0, tk.END)
            g_riot_path_entry.insert(0, file_selected)
            action_save_path_settings()

    ttk.Button(path_settings_frame, text="...", width=3, command=browse_riot_exe).grid(row=1, column=2, padx=(5, 0), pady=(10, 0))


    # --- 4. SUPPORT SECTION ---
    support_frame = ttk.LabelFrame(fourth_tab_frame, text="🆘 Hỗ Trợ Kỹ Thuật", padding=10)
    support_frame.pack(fill=tk.X, pady=(0, 10))

    support_layout = ttk.Frame(support_frame)
    support_layout.pack(fill=tk.X)

    ttk.Label(support_layout, text="Gặp lỗi khó? Yêu cầu hỗ trợ từ xa.", style="secondary.TLabel").pack(side=tk.LEFT)

    global g_anydesk_button
    g_anydesk_button = ttk.Button(
        support_layout,
        text="🚀 Hỗ Trợ Từ Xa", # <--- Đổi tên hiển thị
        command=action_launch_rustdesk,    # <--- Đổi hàm gọi
        style="Accent.TButton"
    )
    g_anydesk_button.pack(side=tk.RIGHT)
    CreateToolTip(g_anydesk_button, "Mở RustDesk để Admin điều khiển máy hỗ trợ sửa lỗi.")

    # --- CREDITS FOOTER ---
    footer_label = ttk.Label(fourth_tab_frame, text="WIBU's Gaming Zone © 2025", style="secondary.TLabel", font=("Segoe UI", 8))
    footer_label.pack(side=tk.BOTTOM, pady=5)
    # --- Hàm cho luồng tải config ban đầu ---

    def load_config_thread():
        """(ĐÃ SỬA) Tải cả config mod VÀ config theme."""
        global fallback_options

        # 1. Tải config Mod (như cũ)
        mod_config = load_config_from_github()
        if not mod_config:
            mod_config = fallback_options

        # 2. Tải config Theme (MỚI)
        theme_config = {}
        try:
            # (Chúng ta dùng lại link raw của file config, chỉ thay tên file)
            theme_url = "https://raw.githubusercontent.com/hoangdangnhatkha/-WGZ-GameUpdater/refs/heads/main/game_themes.json"
            cache_buster = f"?_={int(time.time())}"
            full_theme_url = theme_url + cache_buster

            print(f"Đang tải config theme: {full_theme_url}")
            response = requests.get(full_theme_url, timeout=10)
            response.raise_for_status()
            theme_config = response.json()
            print("Tải config theme thành công.")

        except Exception as e:
            print(f"Lỗi khi tải game_themes.json (sẽ dùng icon mặc định): {e}")
            theme_config = {} # Dùng dict rỗng nếu lỗi

        # 3. Gộp 2 kết quả và gửi về 1 message
        combined_data = {
            "mods": mod_config,
            "themes": theme_config
        }
        progress_queue.put(("config_loaded", combined_data))

    def preload_rocket_gif_thread():
        """
        Chạy ngầm ngay khi mở App để tải GIF vào RAM.
        Giúp bấm nút 'Chạy Game' là hiện hiệu ứng ngay lập tức.
        """
        global g_rocket_raw_data, ROCKET_GIF_URL
        
        if g_rocket_raw_data: 
            return # Đã có dữ liệu thì thôi

        try:
            print(f"Đang tải trước (Preload) GIF hiệu ứng...")
            response = requests.get(ROCKET_GIF_URL, timeout=10)
            response.raise_for_status()
            g_rocket_raw_data = response.content # Lưu dữ liệu thô vào RAM
            print("✅ Tải trước GIF hiệu ứng hoàn tất!")
        except Exception as e:
            print(f"⚠️ Lỗi khi tải trước GIF (Sẽ thử lại khi bấm nút): {e}")

    # --- THÊM MỚI: HÀM TẢI GIF ĐỘNG ---
    def load_gif_frames_thread():
        """(Chạy ngầm) Tải GIF từ URL và tách các frame."""
        try:
            print(f"Đang tải GIF từ: {GIF_URL}")
            response = requests.get(GIF_URL, timeout=10)
            response.raise_for_status()

            gif_data = io.BytesIO(response.content)
            with Image.open(gif_data) as img:
                frames = []
                delay = img.info.get('duration', 100) # Lấy delay, mặc định 100ms

                for i in range(img.n_frames):
                    img.seek(i)
                    # Tạo một bản copy của frame và chuyển sang RGBA
                    frame_rgba = img.copy().convert('RGBA')
                    tk_frame = ImageTk.PhotoImage(frame_rgba)
                    frames.append(tk_frame)

            if frames:
                print(f"Tải GIF thành công, {len(frames)} frames, delay {delay}ms.")
                # Gửi danh sách frame và delay về queue
                progress_queue.put(("gif_loaded", {"frames": frames, "delay": delay}))
            else:
                print("Lỗi: GIF không có frame nào.")

        except Exception as e:
            print(f"Lỗi nghiêm trọng khi tải hoặc xử lý GIF: {e}")

    def preload_all_images_thread(themes_dict, mod_config_dict):
        """
        (ĐÃ SỬA) Tải và cache TẤT CẢ các ảnh game (Song song).
        """
        try:
            # 1. Tải các icon mặc định/dịch vụ (tuần tự, vì chúng quan trọng)
            # (Bạn cần điền URL chính xác vào đây)
            print("Đang tải icon mặc định...")
            root.default_game_icon_small = load_image_from_url("https://i.imgur.com/g0tAUc2.png", size=(192, 89))
            root.default_game_icon_large = load_image_from_url("https://i.imgur.com/g0tAUc2.png", size=(460, 215))
            steam_url = "https://images.icon-icons.com/2428/PNG/512/steam_black_logo_icon_147078.png"
            riot_url = "https://cdn2.steamgriddb.com/icon_thumb/ada216e157757c965a766aae6e21423a.png"
            root.steam_icon_small = load_image_from_url(steam_url, size=(89, 89))
            root.riot_icon_small = load_image_from_url(riot_url, size=(89, 89))
            root.steam_icon_tiny = load_image_from_url(steam_url, size=(32, 32))
            root.riot_icon_tiny = load_image_from_url(riot_url, size=(32, 32))
            print(f"Bắt đầu tải trước {len(themes_dict)} ảnh themes (song song)...")
            
            # 2. Dùng ThreadPoolExecutor để tải song song
            # 'max_workers=10' có nghĩa là tải 10 ảnh cùng lúc
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                
                # Tạo danh sách các "công việc" cần thực hiện
                futures = []
                for game_name, url in themes_dict.items():
                    if url:
                        # Gửi công việc tải size nhỏ
                        futures.append(executor.submit(load_image_from_url, url, (192, 89)))
                        # Gửi công việc tải size lớn
                        futures.append(executor.submit(load_image_from_url, url, (460, 215)))
                
                # (Không bắt buộc) Chờ tất cả công việc hoàn thành
                concurrent.futures.wait(futures)

            print("Tải trước (preload) ảnh song song hoàn tất.")

        except Exception as e:
            print(f"Lỗi trong quá trình tải trước ảnh (song song): {e}")
        finally:
            # 3. Gửi tin nhắn (như cũ)
            progress_queue.put(("all_images_preloaded", mod_config_dict))

    root.update_idletasks()


    status_label_splash.config(text="Đang tải thư viện: Google Drive & GitHub...")
    splash.update()
    root.protocol("WM_DELETE_WINDOW", on_closing)
    status_label.configure(text="Đang tải config phiên bản...", style="White.TLabel")
    progress_bar.start(10)
    start_button.config(state=tk.DISABLED)
    browse_button.config(state=tk.DISABLED)
    root.after(100, process_queue)
    threading.Thread(target=load_config_thread, daemon=True).start()
    threading.Thread(target=load_gif_frames_thread, daemon=True).start()
    threading.Thread(target=auto_find_paths_thread, daemon=True).start()
    threading.Thread(target=preload_rocket_gif_thread, daemon=True).start()
    if local_config.get("auto_start_translator", False):
        print("Config bật: Tự động chạy Translator...")
        # Chạy trong thread để không làm chậm khởi động app chính
        threading.Thread(target=start_translator_service, daemon=True).start()
    # Hủy splash screen
    splash.destroy()
    sv_ttk.set_theme("dark")
    # Hiển thị cửa sổ chính
    root.deiconify()

    # Đưa cửa sổ chính lên trên cùng
    root.after(10, lambda: apply_theme_to_titlebar(root))

    root.title("[WGZ] Game Updater")
    root.attributes('-topmost', 1) 
    root.focus_force()
    root.attributes('-topmost', 0)
    root.mainloop()