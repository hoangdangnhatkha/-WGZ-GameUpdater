# Save this file as 'CapNhatNightReignMod_Ui.py'
import sys
import os
import socketio
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
import google.generativeai as genai
try:
    from key_secrets import GEMINI_API_KEY, GROK_API_KEYS  # XÓA GROQ_API_KEYS
except ImportError:
    GEMINI_API_KEY = ""
    GROK_API_KEYS = []

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
g_show_steam_details = None

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
    Kích thước tự động điều chỉnh theo nội dung.
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
    
    # Giữ nguyên lbl_icon
    lbl_icon = tk.Label(header_frame, text=icon_text, font=("Segoe UI", 20), bg=style.lookup("TFrame", "background"), fg=icon_color)
    lbl_icon.pack(side=tk.LEFT, padx=(0, 10))
    
    # Nội dung tin nhắn
    lbl_msg = ttk.Label(
        main_frame, 
        text=message, 
        wraplength=450, # Tăng wraplength lên 450 để cho phép cửa sổ rộng hơn
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
        btn_yes = ttk.Button(btn_frame, text="Có (Yes)", style="Accent.TButton", command=lambda: on_close(True))
        btn_yes.pack(side=tk.RIGHT, padx=5)
        btn_no = ttk.Button(btn_frame, text="Không (No)", command=lambda: on_close(False))
        btn_no.pack(side=tk.RIGHT, padx=5)
        
    elif dialog_type == "error":
        btn_ok = ttk.Button(btn_frame, text="Đóng", style="Danger.TButton", command=lambda: on_close(None))
        btn_ok.pack(side=tk.RIGHT)
        
    else: # info, warning
        btn_ok = ttk.Button(btn_frame, text="OK", style="Accent.TButton", command=lambda: on_close(None))
        btn_ok.pack(side=tk.RIGHT)

    # --- LOGIC ĐIỀU CHỈNH KÍCH THƯỚC ĐỘNG ---
    # 1. Yêu cầu Tkinter tính toán kích thước tối thiểu
    dlg.geometry('')
    dlg.update_idletasks()

    # 2. Lấy kích thước tính toán (Đảm bảo chiều rộng không quá 700px và có kích thước tối thiểu)
    required_width = min(700, max(300, dlg.winfo_reqwidth()))
    required_height = max(150, dlg.winfo_reqheight())

    # 3. Căn giữa cửa sổ với kích thước mới
    center_window_on_screen(dlg, required_width, required_height)
    # --- KẾT THÚC LOGIC KÍCH THƯỚC ĐỘNG ---

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
    # Đặt wraplength lớn hơn để đảm bảo nó co giãn tốt
    lbl_prompt = ttk.Label(main_frame, text=prompt, wraplength=450, justify=tk.LEFT)
    lbl_prompt.pack(fill=tk.X, pady=(0, 10))

    # Ô nhập liệu (Entry)
    # Entry widget có kích thước cố định, nên nó giúp định hình chiều rộng tối thiểu
    entry = ttk.Entry(main_frame, width=40) 
    
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

    # --- LOGIC ĐIỀU CHỈNH KÍCH THƯỚC ĐỘNG ---
    # 1. Yêu cầu Tkinter tính toán kích thước tối thiểu
    dlg.geometry('')
    dlg.update_idletasks()

    # 2. Lấy kích thước tính toán (Đảm bảo có kích thước tối thiểu)
    required_width = min(600, max(300, dlg.winfo_reqwidth()))
    required_height = max(150, dlg.winfo_reqheight())

    # 3. Căn giữa cửa sổ với kích thước mới
    center_window_on_screen(dlg, required_width, required_height)
    # --- KẾT THÚC LOGIC KÍCH THƯỚC ĐỘNG ---
    
    # Phím tắt
    dlg.bind("<Return>", lambda e: on_ok())
    dlg.bind("<Escape>", lambda e: on_cancel())

    # Chờ đóng cửa sổ
    root.wait_window(dlg)
    
    return result[0]

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
global g_show_login_selector
g_show_login_selector = None # Biến này sẽ chứa hàm mở popup
g_game_search_entry = None
g_game_grid_container = None
g_all_mods_flat = {}
g_game_themes = {}
global g_mod_buttons
g_mod_buttons = {}
global g_current_selected_key
g_current_selected_key = None
CURRENT_VERSION = "1.3.6"
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
    Kiểm tra cập nhật và gọi Updater (Chế độ ONEDIR).
    """
    try:
        updater_info = config_data.get("updater")
        if not updater_info: return False

        latest_version_str = updater_info.get("latest_version")
        if not latest_version_str: return False

        if version.parse(latest_version_str) > version.parse(CURRENT_VERSION):
            print(f"Phát hiện phiên bản mới: {latest_version_str}")
            notes = updater_info.get("release_notes", "Không có ghi chú.")
            url = updater_info.get("download_url") 

            if not url: return False

            message = (
                f"Đã có phiên bản mới: {latest_version_str}!\n"
                f"(Bạn đang dùng: {CURRENT_VERSION})\n\n"
                f"Ghi chú:\n{notes}\n\n"
                "Bấm OK để tự động tải và cập nhật (dạng Folder)."
            )

            custom_showwarning("Cập Nhật Hệ Thống", message)
            
            try:
                # 1. Xác định vị trí updater.exe hiện tại (nằm trong folder game)
                if getattr(sys, 'frozen', False):
                    app_dir = os.path.dirname(sys.executable)
                    exe_name = os.path.basename(sys.executable)
                else:
                    app_dir = os.path.dirname(os.path.abspath(__file__))
                    exe_name = "CapNhatNightReignMod_UI.py" # Tên giả khi dev

                local_updater_path = os.path.join(app_dir, "updater.exe")

                # 2. Copy updater ra thư mục Temp (để tránh lỗi đang lock file)
                temp_dir = os.environ['TEMP']
                temp_updater_path = os.path.join(temp_dir, "WGZ_Updater_Temp.exe")
                
                if os.path.exists(local_updater_path):
                    shutil.copy2(local_updater_path, temp_updater_path)
                else:
                    custom_showerror("Lỗi", "Không tìm thấy file 'updater.exe' trong thư mục game.")
                    webbrowser.open_new_tab(url)
                    return True

                # 3. Chạy updater từ Temp
                # Tham số: [URL_Tải_Zip] [Thư_Mục_Cài_Đặt] [Tên_File_Exe_Chính]
                print(f"Gọi updater tại: {temp_updater_path}")
                subprocess.Popen([temp_updater_path, url, app_dir, exe_name])
                
                # 4. Thoát app chính ngay lập tức
                root.destroy()
                sys.exit(0)

            except Exception as e:
                custom_showerror("Lỗi Cập Nhật", f"Không thể chạy updater: {e}\nSẽ mở link tải thủ công.")
                webbrowser.open_new_tab(url)
            
            return True
        else:
            print("Ứng dụng đã ở phiên bản mới nhất.")
            return False

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

def auto_fix_legacy_paths():
    """
    (AUTO-FIX V2 - MẠNH MẼ HƠN)
    1. Sửa đường dẫn cũ (tên file trọc lóc -> đường dẫn tương đối).
    2. TỰ ĐỘNG TÌM VÀ THÊM nếu launcher bị thiếu trong config.
    """
    global local_config, g_all_mods_flat
    is_changed = False
    
    if 'game_paths' not in local_config: return
    if 'game_launchers' not in local_config: local_config['game_launchers'] = {}

    print("--- AUTO-FIX V2: Đang quét và sửa lỗi đường dẫn... ---")

    # Tạo bản đồ: Tên Game -> Tên File EXE chuẩn (Lấy từ dữ liệu Server/Fallback)
    # Để biết mình cần tìm file gì
    game_exe_map = {}
    
    # Lấy từ g_all_mods_flat (dữ liệu tải từ GitHub)
    if 'g_all_mods_flat' in globals() and g_all_mods_flat:
        for mod_data in g_all_mods_flat.values():
            g_name = mod_data.get("game")
            l_file = mod_data.get("launch_file")
            if g_name and l_file:
                # Chỉ lấy tên file (bỏ folder) để dùng cho việc quét
                game_exe_map[g_name] = os.path.basename(l_file)

    # Duyệt qua các game đã cài
    for game_name, root_path in local_config['game_paths'].items():
        if not root_path or not os.path.exists(root_path): continue

        current_launcher = local_config['game_launchers'].get(game_name)
        target_filename = game_exe_map.get(game_name) # Tên file chuẩn cần tìm (vd: _The Spell...exe)

        # --- TRƯỜNG HỢP 1: Bị thiếu Launcher trong Config (Trường hợp của bạn) ---
        if not current_launcher and target_filename:
            print(f"Phát hiện thiếu Launcher cho '{game_name}'. Đang quét tìm '{target_filename}'...")
            
            found_rel = None
            # Quét đệ quy trong thư mục game
            for root_dir, dirs, files in os.walk(root_path):
                if target_filename in files:
                    full_path = os.path.join(root_dir, target_filename)
                    try:
                        # Tính đường dẫn tương đối (VD: The.Spell.../_The Spell...exe)
                        found_rel = os.path.relpath(full_path, root_path)
                        break
                    except: pass
            
            if found_rel:
                print(f"-> Đã tìm thấy và khôi phục: {found_rel}")
                local_config['game_launchers'][game_name] = found_rel
                is_changed = True
            else:
                print(f"-> Không tìm thấy file '{target_filename}' trong '{root_path}'")

        # --- TRƯỜNG HỢP 2: Có Launcher nhưng lưu sai (Kiểu cũ) ---
        elif current_launcher:
            # Nếu launcher không chứa dấu gạch (tức là lưu mỗi tên file)
            if '\\' not in current_launcher and '/' not in current_launcher:
                direct_path = os.path.join(root_path, current_launcher)
                
                # Nếu file không nằm ngay ở root -> Quét tìm lại
                if not os.path.exists(direct_path):
                    print(f"Fix đường dẫn sai cho '{game_name}' ({current_launcher})...")
                    found_rel = None
                    for root_dir, dirs, files in os.walk(root_path):
                        if current_launcher in files:
                            full_path = os.path.join(root_dir, current_launcher)
                            try:
                                found_rel = os.path.relpath(full_path, root_path)
                                break
                            except: pass
                    
                    if found_rel:
                        print(f"-> Đã sửa thành: {found_rel}")
                        local_config['game_launchers'][game_name] = found_rel
                        is_changed = True

    if is_changed:
        save_local_config(local_config)
        print("--- AUTO-FIX: Đã cập nhật settings.json thành công. ---")
    else:
        print("--- AUTO-FIX: Config không có lỗi gì mới. ---")

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
    (FIX SSL ERROR) Tải config account bằng AuthorizedSession (Requests)
    thay vì httplib2 để tránh lỗi WRONG_VERSION_NUMBER.
    """
    global drive_service, g_user_accounts_data, g_user_accounts_file_id
    global g_accounts_loaded

    if g_accounts_loaded:
        print("Config account đã được tải. Bỏ qua.")
        return

    # Kiểm tra token
    token_path = resource_path('token.json')
    if not os.path.exists(token_path):
        print("Chưa có token.json, bỏ qua tải account.")
        return

    try:
        # 1. Tạo Session xác thực (Mạnh hơn drive_service chuẩn)
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        authed_session = AuthorizedSession(creds)

        print(f"Đang tìm file config account: {ACCOUNT_CONFIG_FILENAME}...")
        
        # 2. Tìm ID file (Vẫn dùng drive_service để list file vì nó nhẹ)
        # Nếu drive_service chưa init (do lỗi SSL khi build), ta dùng requests để tìm luôn
        found_file_id = None
        
        if drive_service:
            try:
                query = f"name = '{ACCOUNT_CONFIG_FILENAME}' and '{GOOGLE_DRIVE_FOLDER_ID}' in parents and trashed = false"
                response = drive_service.files().list(q=query, fields='files(id, name)').execute()
                files = response.get('files', [])
                if files: found_file_id = files[0]['id']
            except Exception as e:
                print(f"Lỗi tìm file bằng Service: {e}. Đang thử cách khác...")

        # Nếu drive_service lỗi, tìm thủ công bằng requests (Fallback)
        if not found_file_id:
            search_url = "https://www.googleapis.com/drive/v3/files"
            params = {
                "q": f"name = '{ACCOUNT_CONFIG_FILENAME}' and '{GOOGLE_DRIVE_FOLDER_ID}' in parents and trashed = false",
                "fields": "files(id, name)"
            }
            res = authed_session.get(search_url, params=params)
            if res.status_code == 200:
                files = res.json().get('files', [])
                if files: found_file_id = files[0]['id']

        # 3. Tải nội dung
        if found_file_id:
            g_user_accounts_file_id = found_file_id
            print(f"Tìm thấy ID: {g_user_accounts_file_id}. Đang tải trực tiếp (Requests)...")
            
            download_url = f"https://www.googleapis.com/drive/v3/files/{g_user_accounts_file_id}?alt=media"
            response = authed_session.get(download_url)
            response.raise_for_status() # Báo lỗi nếu 403/404
            
            file_content = response.content # Dữ liệu dạng bytes
            print("Tải config account hoàn tất (Direct).")
            
            try:
                # Parse JSON
                raw_data = json.loads(file_content.decode('utf-8'))
                
                # Logic di chuyển dữ liệu cũ (như code cũ)
                is_old_structure = False
                if raw_data:
                    first_key = next(iter(raw_data.keys()))
                    if first_key == "Steam" or first_key == "Riot":
                        is_old_structure = True
                
                if is_old_structure:
                    print("Phát hiện cấu trúc cũ. Đang di chuyển...")
                    g_user_accounts_data = migrate_data_to_game_keys(raw_data)
                    # Lưu lại cấu trúc mới
                    threading.Thread(target=save_accounts_to_drive_thread, daemon=True).start()
                else:
                    g_user_accounts_data = raw_data

            except json.JSONDecodeError:
                print("Lỗi: File config JSON bị hỏng. Dùng dict rỗng.")
                g_user_accounts_data = {}
        else:
            print("Không tìm thấy config. Đang tạo file mới...")
            g_user_accounts_data = {}
            # Tạo file mới (vẫn dùng logic cũ hoặc requests)
            new_id = create_empty_account_file_on_drive()
            if new_id:
                g_user_accounts_file_id = new_id

        # Đánh dấu đã tải xong
        mark_accounts_as_saved()
        g_accounts_loaded = True
        progress_queue.put(("accounts_loaded", None))

    except Exception as e:
        print(f"Lỗi nghiêm trọng khi tải Account (Fixed Version): {e}")
        # Không hiện popup lỗi làm phiền, chỉ log
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
    """
    (FINAL FIX) Tự động lấy SHA mới nhất trước khi upload.
    Xử lý an toàn kết quả trả về để không báo lỗi ảo.
    """
    if not repo: return False, None

    # Convert dict to formatted JSON string
    json_string_to_upload = json.dumps(theme_dict_to_upload, indent=4, ensure_ascii=False)

    print(f"Chuẩn bị logic upload theme...")
    
    try:
        commit_message = f"Update game_themes.json via Updater Tool"

        # 1. LUÔN LUÔN tải bản mới nhất từ GitHub để lấy SHA thực tế
        # (Sửa lỗi SHA: None trong log của bạn)
        current_content_str, fresh_sha = load_theme_json_from_github_api(repo)
        
        # Quyết định dùng SHA nào (Ưu tiên cái mới tải về)
        sha_to_use = fresh_sha if fresh_sha else current_sha

        # 2. So sánh nội dung (tránh upload nếu không đổi)
        needs_upload = True
        if current_content_str:
            try:
                current_obj = json.loads(current_content_str)
                if current_obj == theme_dict_to_upload:
                    print("Theme config không thay đổi. Bỏ qua upload.")
                    needs_upload = False
                    return True, sha_to_use
            except json.JSONDecodeError: pass

        if needs_upload:
            print(f"Đang thực hiện upload với SHA: {sha_to_use}")
            
            # 3. Thực hiện Upload
            update_result = repo.update_file(
                path="game_themes.json",
                message=commit_message,
                content=json_string_to_upload,
                sha=sha_to_use, # Dùng SHA mới nhất
                branch=GITHUB_BRANCH,
            )

            # 4. Lấy SHA mới một cách an toàn (Tránh lỗi 'NoneType')
            new_file_sha = None
            try:
                # Thử lấy SHA của file content
                if 'content' in update_result and update_result['content']:
                    new_file_sha = update_result['content'].sha
                # Nếu không, lấy SHA của commit (fallback)
                elif 'commit' in update_result:
                    new_file_sha = update_result['commit'].sha
            except:
                pass # Nếu lỗi lấy SHA, bỏ qua, vẫn tính là upload thành công

            print(f"Upload thành công! New SHA: {new_file_sha}")
            custom_showinfo("Thành công", "Đã cập nhật thêm/xóa file theme lên Database!")
            return True, new_file_sha

    except GithubException as e:
        if e.status == 409:
             custom_showerror("Lỗi GitHub Upload (409)", "File theme trên GitHub đã bị thay đổi.\nHãy thử lại, tool sẽ tự lấy SHA mới.")
        else:
             custom_showerror("Lỗi GitHub Upload", f"Không thể cập nhật file theme:\n{e.data.get('message', str(e))}")
        return False, None
    except Exception as e:
         custom_showerror("Lỗi GitHub Upload", f"Lỗi không xác định: {e}")
         return False, None

# --- THÊM CÁC HÀM XỬ LÝ GOOGLE DRIVE ---

# Biến này sẽ lưu trữ dịch vụ Google Drive sau khi đăng nhập
drive_service = None
# Phạm vi (quyền) mà chúng ta yêu cầu: chỉ upload file
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/userinfo.email',
    'openid'
]

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
    (PHIÊN BẢN PRO: RESUME DOWNLOAD)
    Hỗ trợ tải nối tiếp (Resume) khi mạng rớt.
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

    print(f"API: Đang khởi tạo luồng tải (Smart Resume) cho ID {file_id}...")

    try:
        # 2. Lấy thông tin kích thước file gốc từ Server
        try:
            file_metadata = drive_service.files().get(fileId=file_id, fields="size, name").execute()
            total_size = int(file_metadata.get('size', 0))
        except Exception as e:
            raise Exception(f"Không thể lấy thông tin file (có thể do quyền truy cập): {e}")

        # 3. Kiểm tra file hiện tại trên ổ cứng
        existing_size = 0
        if os.path.exists(dest_path):
            existing_size = os.path.getsize(dest_path)

        # 4. Quyết định chế độ tải
        headers = {}
        mode = 'wb' # Mặc định: Ghi mới (Write Binary)
        
        if existing_size == total_size and total_size > 0:
            print(f"API: File đã tải hoàn tất ({format_bytes(total_size)}). Bỏ qua.")
            return True # Đã xong
            
        elif existing_size > 0 and existing_size < total_size:
            print(f"API: Phát hiện file tải dở ({format_bytes(existing_size)} / {format_bytes(total_size)}). Đang tải nối tiếp (Resume)...")
            headers = {'Range': f'bytes={existing_size}-'} # Chỉ tải từ byte tiếp theo
            mode = 'ab' # Ghi nối tiếp (Append Binary)
        
        elif existing_size > total_size:
            print("API: File lỗi (lớn hơn file gốc). Tải lại từ đầu.")
            existing_size = 0 # Reset về 0 để tính % cho đúng

        # 5. Thiết lập kết nối
        token_path = resource_path('token.json')
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        authed_session = AuthorizedSession(creds)
        download_url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"

        # 6. BẮT ĐẦU TẢI (Stream)
        with authed_session.get(download_url, headers=headers, stream=True) as response:
            # Lưu ý: Nếu Resume thành công, Server trả về 206. Nếu không hỗ trợ, trả về 200.
            if response.status_code not in [200, 206]:
                raise Exception(f"Lỗi tải (Code {response.status_code}): {response.text}")
            
            # Nếu Server từ chối Resume (trả về 200 thay vì 206), ta phải tải lại từ đầu
            if mode == 'ab' and response.status_code == 200:
                print("Server không hỗ trợ Resume. Chuyển sang tải lại từ đầu...")
                mode = 'wb'
                existing_size = 0 

            with open(dest_path, mode, buffering=1024*1024) as f:
                start_time = time.time()
                downloaded_this_session = 0
                stream_chunk_size = 128 * 1024 
                last_update_time = time.time()
                
                for chunk in response.iter_content(chunk_size=stream_chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded_this_session += len(chunk)
                        
                        # Tính tổng đã tải (Cũ + Mới)
                        current_total = existing_size + downloaded_this_session
                        
                        # Cập nhật UI mỗi 0.5s
                        current_time = time.time()
                        if current_time - last_update_time > 0.5:
                            elapsed = current_time - start_time
                            if elapsed > 0:
                                percent = int(current_total / total_size * 100) if total_size > 0 else 0
                                speed_bps = downloaded_this_session / elapsed
                                speed_str = format_bytes(speed_bps) + "/s"
                                
                                # Tính thời gian còn lại
                                remaining_bytes = total_size - current_total
                                eta_seconds = (remaining_bytes / speed_bps) if speed_bps > 0 else 0
                                eta_str = format_time(eta_seconds)

                                progress_queue.put(("progress", {
                                    "percent": percent, 
                                    "speed": f"{speed_str}", 
                                    "eta": eta_str 
                                }))
                            last_update_time = current_time

        print(f"API: Tải thành công -> {dest_path}")
        return True

    except Exception as e:
        error_msg = str(e)
        if "416" in error_msg: # Range Not Satisfiable (File có thể đã xong hoặc bị đổi)
             print("Lỗi Range (416). File có thể đã thay đổi. Đang thử tải lại...")
             if os.path.exists(dest_path): os.remove(dest_path)
             return download_via_api_logic(file_id, dest_path) # Đệ quy thử lại từ đầu
             
        raise Exception(f"Lỗi tải Direct API: {e}")

def download_single_part(url, target_path, part_index, total_parts):
    """
    Hàm hỗ trợ tải 1 file đơn lẻ (Có xử lý gdown + API + Quota).
    """
    global drive_service, notebook, third_tab_frame # Để chuyển tab nếu cần

    # Cập nhật UI báo đang tải Part mấy
    status_msg = f"Đang tải Part {part_index}/{total_parts}..."
    progress_queue.put(("status", status_msg))
    
    # 1. Thử tải bằng Gdown
    try:
        print(f"[{part_index}/{total_parts}] Downloading: {target_path}")
        out = gdown.download(url, target_path, quiet=False, fuzzy=True)
        
        # Kiểm tra kết quả gdown
        if not out:
            if os.path.exists(target_path) and os.path.getsize(target_path) > 1024 * 1024:
                print(f"Part {part_index} tải xong (gdown trả None nhưng file ok).")
                return True
            else:
                raise Exception("gdown download failed")
        return True

    except Exception as e_gdown:
        print(f"Gdown lỗi Part {part_index}: {e_gdown}")
        
        # Check file lần nữa
        if os.path.exists(target_path) and os.path.getsize(target_path) > 1024 * 1024:
            return True

        # Xử lý lỗi Quota / Permission
        error_str = str(e_gdown).lower()
        if "too many users" in error_str or "denied" in error_str or "permission" in error_str or "failed" in error_str:
            
            # --- Logic check đăng nhập (như cũ) ---
            if not drive_service:
                msg = (
                    f"⚠️ Lỗi tải Part {part_index}: QUÁ GIỚI HẠN (Quota).\n\n"
                    "Vui lòng đăng nhập Google Drive (Tab 3) để tải tiếp."
                )
                if custom_askyesno("Yêu cầu Đăng nhập", msg):
                    def switch_to_tab3(): notebook.select(third_tab_frame)
                    root.after(0, switch_to_tab3)
                    raise Exception("Đã dừng để đăng nhập.")
                else:
                    raise Exception("Link quá tải. Cần đăng nhập.")
            
            else:
                # Tải bằng API
                progress_queue.put(("status", f"Part {part_index}: Dùng API (Bypass Quota)..."))
                file_id = extract_gdrive_id_from_url(url)
                if not file_id: raise Exception(f"Không lấy được ID: {url}")
                
                download_via_api_logic(file_id, target_path)
                return True
        else:
            raise e_gdown

def download_and_extract_logic():
    """
    (FULL CODE) Hỗ trợ tải Multi-Part, Backup đầy đủ, Giải nén và Tìm Launcher.
    """
    global local_config
    global g_current_game_name

    progress_queue.put(("status", "DISABLE_BUTTONS"))

    selected_key = selected_option.get()
    if selected_key not in g_all_mods_flat:
        progress_queue.put(("status", "Lỗi: Không tìm thấy thông tin mod."))
        progress_queue.put(("status", "ENABLE_BUTTONS"))
        return

    mod_data = g_all_mods_flat[selected_key]
    mod_display_name = mod_data.get("name", selected_key)
    option_label.configure(text="Đang xử lý: " + mod_display_name, style="White.TLabel")

    # --- LẤY DANH SÁCH URL (Hỗ trợ cả key "url" và "urls") ---
    url_list = mod_data.get("urls", [])
    if not url_list:
        single_url = mod_data.get("url")
        if single_url:
            url_list = [single_url]

    if not url_list:
        progress_queue.put(("download_complete", {"success": False, "title": "Lỗi Config", "message": "Không tìm thấy link tải trong config."}))
        progress_queue.put(("status", "ENABLE_BUTTONS"))
        return

    version = mod_data.get("version", "")
    file_type = mod_data.get("type", "zip") # zip, rar, exe
    password = mod_data.get("password", None)
    delete_list = mod_data.get("delete_before_extract", [])
    destination_folder = path_entry.get()

    # 1. Tạo folder đích nếu chưa có
    if not os.path.exists(destination_folder):
        try: 
            os.makedirs(destination_folder, exist_ok=True)
        except Exception as e:
            progress_queue.put(("download_complete", {"success": False, "title": "Lỗi", "message": f"Lỗi tạo folder: {e}"}))
            progress_queue.put(("status", "ENABLE_BUTTONS"))
            return

    # 2. Lưu config đường dẫn
    if 'last_used_folder' not in local_config: 
        local_config['last_used_folder'] = ""
    local_config['last_used_folder'] = destination_folder
    save_local_config(local_config)

    sys.stderr = QueueIO(progress_queue)
    
    downloaded_files_paths = [] # Lưu danh sách file đã tải để xử lý sau

    try:
        # --- 3. XỬ LÝ BACKUP HOẶC XÓA FILE CŨ ---
        # (Chỉ làm 1 lần trước khi tải part đầu tiên)
        if g_backup_enabled.get():
            if delete_list:
                progress_queue.put(("status", "Đang sao lưu file cũ..."))
                
                backup_root_dir = os.path.join(destination_folder, "_BACKUPS")
                timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
                
                # Làm sạch tên mod để tạo tên folder
                safe_key_name = re.sub(r'[\\/*?:"<>|]', "", mod_display_name)
                backup_folder_name = f"{safe_key_name} - {timestamp}"
                specific_backup_dir = os.path.join(backup_root_dir, backup_folder_name)

                try:
                    os.makedirs(specific_backup_dir, exist_ok=True)
                except Exception as e:
                    raise Exception(f"Không thể tạo thư mục backup: {e}")

                moved_items = []
                try:
                    for item_name in delete_list:
                        source_path = os.path.join(destination_folder, item_name)
                        dest_path = os.path.join(specific_backup_dir, item_name)

                        if os.path.exists(source_path):
                            print(f"Đang sao lưu: {item_name} -> {specific_backup_dir}")
                            shutil.move(source_path, dest_path)
                            moved_items.append((dest_path, source_path))
                except Exception as e:
                    # Rollback nếu lỗi
                    print(f"Lỗi backup, đang khôi phục: {e}")
                    for (moved, orig) in moved_items:
                        try: shutil.move(moved, orig)
                        except: pass
                    raise Exception(f"Lỗi sao lưu file {item_name}: {e}")
        else:
            # Nếu không backup thì xóa thẳng
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
                    except Exception as e:
                        print(f"Lỗi khi xóa {item_path}: {e}")

        # --- 4. VÒNG LẶP TẢI CÁC PART (SMART RESUME) ---
        total_parts = len(url_list)
        
        progress_queue.put(("overall_progress", {
            "percent": 0, 
            "text": f"Tiến độ chung: 0/{total_parts} Part"
        }))

        # Tạo tên file an toàn
        safe_name = re.sub(r'[\\/*?:"<>|]', "", mod_display_name).strip().replace(" ", "_")
        if len(safe_name) > 50: safe_name = safe_name[:50]

        for idx, url in enumerate(url_list):
            part_num = idx + 1
            
            # Đặt tên file
            if file_type == "exe":
                fname = f"{safe_name}.exe" if total_parts == 1 else f"{safe_name}.part{part_num}.exe"
            elif file_type == "rar":
                fname = f"{safe_name}.rar" if total_parts == 1 else f"{safe_name}.part{part_num}.rar"
            else: # zip
                fname = f"{safe_name}.zip" if total_parts == 1 else f"{safe_name}.part{part_num}.zip"

            target_path = os.path.join(destination_folder, fname)
            downloaded_files_paths.append(target_path)

            # --- [QUAN TRỌNG] XÓA ĐOẠN CHECK FILE CŨ ---
            # Chúng ta KHÔNG dùng `if os.path.exists... continue` nữa.
            # Thay vào đó, ta gọi thẳng hàm tải. Hàm tải sẽ tự lo việc Resume.
            
            # Cập nhật thông báo
            progress_queue.put(("status", f"Đang xử lý Part {part_num}/{total_parts}..."))

            # Gọi hàm tải
            try:
                # Nếu là link Google Drive, ưu tiên dùng API Resume của chúng ta
                file_id = extract_gdrive_id_from_url(url)
                if file_id and drive_service:
                    # Dùng hàm API mới có tính năng Resume xịn
                    download_via_api_logic(file_id, target_path)
                else:
                    # Link thường hoặc chưa login -> Dùng gdown (gdown cũng tự hỗ trợ resume ở mức cơ bản)
                    # Hoặc gọi hàm helper cũ
                    download_single_part(url, target_path, part_num, total_parts)
            except Exception as e:
                raise Exception(f"Lỗi tải Part {part_num}: {e}")
            
            # Cập nhật thanh tổng
            percent_done = int((part_num / total_parts) * 100)
            progress_queue.put(("overall_progress", {
                "percent": percent_done,
                "text": f"Tiến độ chung: {part_num}/{total_parts} Part ({percent_done}%)"
            }))
            
            progress_queue.put(("progress", {"percent": 0, "speed": "", "eta": ""}))

        # --- 5. XỬ LÝ SAU KHI TẢI XONG (GIẢI NÉN HOẶC CHẠY) ---
        
        # A. Nếu là EXE
        if file_type == "exe":
            main_exe = downloaded_files_paths[0]
            progress_queue.put(("status", "Đã tải xong. Đang mở file cài đặt..."))
            os.startfile(main_exe)
            sys.stderr = original_stderr
            progress_queue.put(("status", "ENABLE_BUTTONS"))
            return

        # B. Nếu là RAR (Hỗ trợ Multi-part tự động)
        elif file_type == "rar":
            progress_queue.put(("status", "Đang giải nén (UnRAR)..."))
            
            import stat
            unrar_path = getattr(rarfile, 'UNRAR_TOOL', 'UnRAR.exe')
            if not os.path.exists(unrar_path) and os.path.exists("UnRAR.exe"): 
                unrar_path = "UnRAR.exe"

            # Chỉ cần giải nén file đầu tiên (Part 1), UnRAR tự tìm các part sau
            first_part_path = downloaded_files_paths[0]
            
            # Xử lý quyền Read-Only (tránh lỗi Access Denied)
            def remove_readonly_recursive(directory):
                if not os.path.exists(directory): return
                for root_dir, dirs, files in os.walk(directory):
                    for fname in files:
                        full_path = os.path.join(root_dir, fname)
                        try:
                            file_atts = os.stat(full_path).st_mode
                            if not (file_atts & stat.S_IWRITE):
                                os.chmod(full_path, stat.S_IWRITE)
                        except: pass
            
            remove_readonly_recursive(destination_folder)

            # Fix đường dẫn dài (Long Path) cho Windows
            abs_dest = os.path.abspath(destination_folder)
            if not abs_dest.startswith("\\\\?\\"):
                ext_dest = "\\\\?\\" + abs_dest 
            else:
                ext_dest = abs_dest
            
            # Lệnh UnRAR: x=extract, -y=yes to all, -o+=overwrite, -kb=keep broken
            cmd = [
                unrar_path, 
                "x", 
                "-y", 
                "-o+", 
                "-kb"
            ]
            
            if password:
                cmd.append(f"-p{password}")
            else:
                cmd.append("-p-")
            
            cmd.append(first_part_path)
            cmd.append(ext_dest)
            
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

            # Đọc log tiến trình từ UnRAR
            pat = re.compile(r"(\d{1,3})%")
            curr = 0
            while True:
                line = proc_output = process.stdout.readline()
                if not line and process.poll() is not None: break
                if line:
                    m = pat.findall(line)
                    if m:
                        new_p = int(m[-1])
                        if new_p > curr:
                            curr = new_p
                            progress_queue.put(("progress", {
                                "percent": curr, 
                                "speed": f"UnRAR: {curr}%", 
                                "eta": ""
                            }))

            if process.poll() not in [0, 1]: 
                raise Exception(f"Lỗi giải nén RAR (Exit Code {process.poll()})")

        # C. Nếu là ZIP
        elif file_type == "zip":
            pwd_bytes = bytes(password, 'utf-8') if password else None
            try: root.update_idletasks()
            except: pass
            
            # Với Zip nhiều phần rời rạc, ta lặp qua từng file và giải nén đè lên nhau
            for i, z_path in enumerate(downloaded_files_paths):
                progress_queue.put(("status", f"Đang giải nén Part {i+1}/{total_parts}..."))
                try:
                    with zipfile.ZipFile(z_path) as zf:
                        zf.extractall(destination_folder, pwd=pwd_bytes)
                except Exception as e:
                    raise Exception(f"Lỗi giải nén file {os.path.basename(z_path)}: {e}")

        # --- 6. DỌN DẸP FILE NÉN ---
        progress_queue.put(("status", "Đang dọn dẹp file tạm..."))
        for f_path in downloaded_files_paths:
            if os.path.exists(f_path):
                try: 
                    os.remove(f_path)
                    print(f"Đã xóa file tạm: {f_path}")
                except: 
                    print(f"Không xóa được: {f_path}")

        # --- 7. TÌM FILE CHẠY & HOÀN TẤT (ĐÃ SỬA LOGIC PATH) ---
        print("Cài đặt hoàn tất. Đang cập nhật đường dẫn...")
        
        target_launcher_string = None # Chuỗi user nhập hoặc config server (VD: "SubFolder/Game.exe")
        
        # Ưu tiên 1: Config user (nếu đã từng lưu)
        if 'game_launchers' in local_config:
            target_launcher_string = local_config['game_launchers'].get(g_current_game_name)
        
        # Ưu tiên 2: Config server (Option tải về)
        if not target_launcher_string and 'download_options' in globals():
            mod_list = download_options.get(g_current_game_name, [])
            for _key, mod_data in mod_list:
                if mod_data.get("launch_file"):
                    target_launcher_string = mod_data.get("launch_file")
                    break
        
        final_saved_path = destination_folder # Folder gốc (D:/New folder)
        found_launcher = False
        final_relative_launcher_path = "" # Cái sẽ lưu vào json (SubFolder/Game.exe)

        if target_launcher_string:
            # --- TRƯỜNG HỢP A: User nhập đường dẫn tương đối (Có Folder con) ---
            # Ví dụ: "The.Spell.Brigade.../_The Spell...exe"
            potential_direct_path = os.path.join(destination_folder, target_launcher_string)
            
            if os.path.exists(potential_direct_path) and os.path.isfile(potential_direct_path):
                # Tìm thấy chính xác theo đường dẫn user nhập!
                print(f"Tìm thấy chính xác theo cấu hình: {potential_direct_path}")
                found_launcher = True
                final_relative_launcher_path = target_launcher_string # Giữ nguyên cấu trúc folder
                
                global g_current_launch_path
                g_current_launch_path = potential_direct_path

            # --- TRƯỜNG HỢP B: Không thấy (hoặc user chỉ nhập tên file), phải đi quét ---
            else:
                print("Không thấy đường dẫn chính xác, đang quét deep scan...")
                target_filename_only = os.path.basename(target_launcher_string) # Chỉ lấy tên file.exe
                
                # Quét đệ quy
                for root_dir, dirs, files in os.walk(destination_folder):
                    if target_filename_only in files:
                        found_at_path = os.path.join(root_dir, target_filename_only)
                        
                        found_launcher = True
                        g_current_launch_path = found_at_path
                        
                        # TÍNH TOÁN ĐƯỜNG DẪN TƯƠNG ĐỐI (QUAN TRỌNG)
                        # Để lần sau biết nó nằm trong folder nào
                        try:
                            final_relative_launcher_path = os.path.relpath(found_at_path, destination_folder)
                        except:
                            final_relative_launcher_path = target_filename_only
                            
                        print(f"Deep scan tìm thấy tại: {final_relative_launcher_path}")
                        break
        
        # Cập nhật config đường dẫn
        if g_current_game_name:
            if 'game_paths' not in local_config: local_config['game_paths'] = {}
            if 'game_launchers' not in local_config: local_config['game_launchers'] = {}
            
            # Lưu Path gốc (D:/New folder)
            local_config['game_paths'][g_current_game_name] = final_saved_path
            
            # Lưu Launcher Relative (SubFolder/Game.exe) -> Đây là cái giúp Uninstall hoạt động đúng
            if found_launcher and final_relative_launcher_path:
                local_config['game_launchers'][g_current_game_name] = final_relative_launcher_path
            
            local_config['last_used_folder'] = final_saved_path
            save_local_config(local_config)

        # Thông báo thành công
        option_label.configure(text="Đã Hoàn Thành " + mod_display_name, foreground="green") 
        progress_queue.put(("status", "Cài đặt thành công!"))
        
        msg = f"Đã cài đặt '{mod_display_name}' thành công!"
        if found_launcher: 
            msg += f"\n\nĐã nhận diện file chạy:\n{final_relative_launcher_path}"
        
        progress_queue.put(("download_complete", {"success": True, "title": "Thành công", "message": msg}))

        # Cập nhật phiên bản đã cài
        new_ver = g_all_mods_flat[selected_key].get('version', 'v1.0')
        if 'installed_versions' not in local_config: local_config['installed_versions'] = {}
        local_config['installed_versions'][selected_key] = new_ver
        save_local_config(local_config)
        
        # Refresh giao diện
        progress_queue.put(("installation_complete_refresh_grid", None))

    except Exception as e:
        # Bắt lỗi chung
        msg = f"Lỗi: {e}"
        print(f"Exception during process: {e}")
        progress_queue.put(("download_complete", {"success": False, "title": "Lỗi", "message": msg}))
        progress_queue.put(("status", "Lỗi Cài Đặt"))
    
    finally:
        # Khôi phục stderr
        sys.stderr = original_stderr
        
        # Dọn dẹp file nén nếu còn sót lại do lỗi
        for f_path in downloaded_files_paths:
            if os.path.exists(f_path):
                try: os.remove(f_path)
                except: pass
                
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
            textDiv.textContent = 'Đang kết nối với Gemini AI';
            
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
                    log_debug("Step 4: Gemini Loaded. Locking Avatar & Hiding Settings...")
                    css_fix = """
                        var style = document.createElement('style');
                        style.textContent = `
                            /* Khóa nút Tài khoản (Account) - Giữ nguyên hiển thị nhưng không click được */
                            a[href^="https://accounts.google.com"],
                            button[aria-label*="Google Account"],
                            button[aria-label*="Tài khoản Google"],
                            div[aria-label*="Google Account"],
                            div[aria-label*="Tài khoản Google"] {
                                pointer-events: none !important;
                                cursor: default !important;
                                opacity: 1 !important;
                            }

                            /* Ẩn hoàn toàn nút Cài đặt (Settings) & Trợ giúp (Help) */
                            button[aria-label*="Settings"],
                            button[aria-label*="Cài đặt"],
                            button[aria-label*="Help"],
                            button[aria-label*="Trợ giúp"],
                            a[href*="support.google.com"] {
                                display: none !important;
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

def launch_with_high_priority(file_path, args=""):
    """
    Phiên bản V3: Hỗ trợ ArgumentList để truyền Resolution.
    """
    try:
        working_dir = os.path.dirname(file_path)
        file_path_win = os.path.normpath(file_path)
        working_dir_win = os.path.normpath(working_dir)

        # Xây dựng lệnh PowerShell
        # -ArgumentList: Truyền các tham số (như -w 1920 -h 1080) vào game
        ps_command = (
            f"Start-Process -FilePath '{file_path_win}' "
            f"-WorkingDirectory '{working_dir_win}' "
            f"-ArgumentList '{args}' "  # <-- THÊM MỚI
            "-WindowStyle Normal "
            "-PassThru | ForEach-Object {$_.PriorityClass = 'High'}"
        )
        
        print(f"PowerShell Launch: {ps_command}")
        
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

def _perform_launch_page1(path_to_launch, launch_args=""):
    """Logic chạy game thực sự cho Page 1 (Có hỗ trợ Args)."""
    global g_smart_mode_enabled, g_auto_close
    
    exe_dir = os.path.dirname(path_to_launch)
    
    print(f"Launching with Args: {launch_args}")

    # --- SMART MODE ---
    if g_smart_mode_enabled.get():
        threading.Thread(target=run_global_ram_cleaner, daemon=True).start()
        try:
            # Truyền args vào hàm priority
            success = launch_with_high_priority(path_to_launch, args=launch_args)
            if not success:
                # Fallback: Nếu lỗi Priority thì dùng subprocess thường
                subprocess.Popen([path_to_launch] + launch_args.split(), cwd=exe_dir)
        except Exception as e:
            custom_showerror("Lỗi Smart Mode", f"Lỗi: {e}")
            # Fallback
            subprocess.Popen([path_to_launch] + launch_args.split(), cwd=exe_dir)
    else:
        # --- NORMAL MODE ---
        try:
            # Dùng subprocess thay vì os.startfile để truyền được tham số
            subprocess.Popen([path_to_launch] + launch_args.split(), cwd=exe_dir)
        except Exception as e:
            custom_showerror("Lỗi Khởi chạy", f"Lỗi: {e}")

    # --- AUTO CLOSE ---
    if g_auto_close.get():
        print("Auto-Close (Page 1) kích hoạt...")
        root.after(1000, lambda: sys.exit(0))

def action_launch_game_from_page_1(path_to_launch, btn_widget=None):
    if path_to_launch and os.path.exists(path_to_launch):
        
        # --- [THÊM MỚI] LOGIC TÌM RESOLUTION ---
        launch_args = ""
        try:
            # Tìm game key dựa trên path (Hơi ngược nhưng hiệu quả)
            # Hoặc đơn giản hơn: Chúng ta sẽ truyền game_name vào hàm này ở bước Binding
            # Nhưng để tránh sửa quá nhiều, ta quét config custom_games:
            for g_name, g_data in local_config.get('custom_games', {}).items():
                if g_data.get('launch_path') == path_to_launch:
                    res = g_data.get('resolution')
                    if res and "x" in res:
                        w, h = res.split("x")
                        # Chuỗi lệnh chuẩn cho Unity, Unreal, Source Engine
                        launch_args = f"-screen-width {w} -screen-height {h} -width {w} -height {h}"
                        print(f"--> Áp dụng Resolution Custom: {res}")
                    break
        except Exception as e:
            print(f"Lỗi đọc resolution: {e}")
        # ---------------------------------------

        # Hiệu ứng Rocket
        if btn_widget:
            play_rocket_animation(target_widget=btn_widget)
        
        # Hẹn giờ chạy (truyền thêm launch_args)
        root.after(2000, lambda: _perform_launch_page1(path_to_launch, launch_args))
        
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
    (CẬP NHẬT) Cho phép chọn BẤT KỲ file nào làm file chạy (All Files).
    """
    global local_config, g_current_game_name, path_entry
    
    if not g_current_game_name:
        return

    # 1. Lấy path cũ
    current_path = local_config.get("game_paths", {}).get(g_current_game_name, "")
    if not os.path.isdir(current_path):
        current_path = local_config.get("last_used_folder", "")

    # --- THAY ĐỔI: Chấp nhận mọi loại file ---
    file_selected = filedialog.askopenfilename(
        initialdir=current_path, 
        title=f"Chọn file khởi chạy cho {g_current_game_name}",
        filetypes=[("All Files", "*.*")] # Không giới hạn .exe nữa
    )
    
    if file_selected:
        folder_selected = os.path.dirname(file_selected)
        launcher_selected = os.path.basename(file_selected)

        # 2. Cập nhật UI
        if 'path_entry' in globals() and path_entry:
            path_entry.delete(0, tk.END)
            path_entry.insert(0, folder_selected)
        
        # 3. Lưu Config
        if 'game_paths' not in local_config: local_config['game_paths'] = {}
        if 'game_launchers' not in local_config: local_config['game_launchers'] = {}
            
        local_config['game_paths'][g_current_game_name] = folder_selected
        local_config['game_launchers'][g_current_game_name] = launcher_selected
        local_config['last_used_folder'] = folder_selected
        
        save_local_config(local_config)
        print(f"Đã set path: {folder_selected} | File: {launcher_selected}")

        # 4. Refresh Giao diện (Để cập nhật trạng thái "Đã cài đặt")
        if 'download_options' in globals():
            populate_page_1_grid(download_options)
        else:
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
            threading.Thread(target=auto_fix_legacy_paths, daemon=True).start()
            # 5. Bắt đầu tải Tab 2 (tài khoản)
            threading.Thread(target=try_auto_login_drive_thread, daemon=True).start()
        elif message_type == "overall_progress":
            data = message_value
            percent = data.get("percent", 0)
            text = data.get("text", "")
            
            if 'overall_progress_bar' in globals():
                overall_progress_bar['value'] = percent
            
            if 'overall_status_label' in globals():
                overall_status_label.config(text=text)
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
            MAX_COLS = 12
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
            
            # (Code fix lỗi kẹt cửa sổ giữ nguyên...)
            try:
                if root.state() == 'iconic':
                    root.deiconify() 
                root.lift() 
                root.attributes('-topmost', 1) 
                root.attributes('-topmost', 0) 
                root.focus_force() 
            except Exception as e:
                print(f"Lỗi khi đánh thức cửa sổ: {e}")

            if data["success"]:
                # Hiển thị pop-up thành công
                custom_showinfo(data["title"], data["message"])
            else:
                # Hiển thị pop-up lỗi
                custom_showerror(data["title"], data["message"])
                
                # --- [THÊM MỚI] SAU KHI BÁO LỖI -> QUAY VỀ TRANG 1 ---
                print("Gặp lỗi tải, quay về màn hình chính...")
                
                # 1. Chuyển về trang lưới game
                show_page(page_1_game_grid)
                
                # 2. Reset các trạng thái trên trang progress (để lần sau vào sạch sẽ)
                status_label.configure(text="Sẵn sàng.", style="White.TLabel")
                progress_bar['value'] = 0
                speed_label.config(text="")
                eta_label.config(text="")
                
                # 3. (Tùy chọn) Bật lại các nút nếu chúng đang tắt
                start_button.config(state=tk.NORMAL)
                browse_button.config(state=tk.NORMAL)
        elif message_type == "game_image_loaded":
            image_tk = message_value
            if image_tk:
                g_game_image_label.config(image=image_tk)
                g_game_image_label.pack(fill=tk.BOTH, expand=True)
        elif message_type == "installation_complete_refresh_grid":
            print("Nhận được tín hiệu refresh, đang vẽ lại Lưới Game (Trang 1)...")
            try:
                # 1. Lấy từ khóa tìm kiếm (nếu có)
                search_term = ""
                if g_game_search_entry:
                    search_term = g_game_search_entry.get().lower()

                # 2. Vẽ lại giao diện Library
                populate_page_1_grid(download_options, search_term)
                
                # 3. [THÊM MỚI] Chuyển ngay về Trang 1 (Library)
                show_page(page_1_game_grid) 
                
                # (Tùy chọn) Reset các nhãn trạng thái để giao diện sạch sẽ
                status_label.configure(text="Sẵn sàng.", style="White.TLabel")
                progress_bar['value'] = 0
                speed_label.config(text="")
                eta_label.config(text="")

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




# --- [TÍNH NĂNG MỚI] OVERLAY QUẢNG CÁO + BỘ ĐẾM GIỜ ---
def show_new_feature_banner(parent, title, message, link_url=None):
    """
    Hiển thị banner quảng cáo góc phải trên với bộ đếm ngược tự động tắt.
    """
    # Thời gian hiển thị (giây)
    AUTO_CLOSE_SECONDS = 30

    # 1. Tạo Frame chứa (Container)
    banner_frame = tk.Frame(parent, bg="#FFD700", padx=2, pady=2)
    
    # Vị trí: Góc phải trên (như cũ)
    banner_frame.place(relx=1.0, rely=0.0, x=-20, y=50, anchor="ne") 

    inner_frame = tk.Frame(banner_frame, bg="#212121")
    inner_frame.pack(fill=tk.BOTH, expand=True)

    # 2. Header: Tiêu đề + Timer + Nút Tắt
    header_frame = tk.Frame(inner_frame, bg="#212121")
    header_frame.pack(fill=tk.X, padx=5, pady=(5, 0))

    # Icon & Title
    tk.Label(header_frame, text="📢", bg="#212121", fg="#FFD700", font=("Segoe UI", 10)).pack(side=tk.LEFT)
    tk.Label(header_frame, text=title, bg="#212121", fg="#FFD700", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=5)

    def close_banner():
        try:
            if banner_frame.winfo_exists():
                banner_frame.destroy()
        except: pass

    # Nút Tắt (X) - Pack trước để nằm ngoài cùng bên phải
    close_btn = tk.Label(header_frame, text="✖", bg="#212121", fg="gray", cursor="hand2", font=("Arial", 9))
    close_btn.pack(side=tk.RIGHT, padx=(5, 0))
    close_btn.bind("<Button-1>", lambda e: close_banner())
    
    # --- [MỚI] LABEL ĐẾM NGƯỢC ---
    # Nằm bên trái nút X
    timer_lbl = tk.Label(header_frame, text=f"({AUTO_CLOSE_SECONDS}s)", bg="#212121", fg="#666666", font=("Segoe UI", 8))
    timer_lbl.pack(side=tk.RIGHT)

    # 3. Nội dung Message
    msg_label = tk.Label(
        inner_frame, 
        text=message, 
        bg="#212121", 
        fg="white", 
        justify=tk.LEFT,
        wraplength=220, 
        font=("Segoe UI", 9)
    )
    msg_label.pack(fill=tk.X, padx=10, pady=5)

    # 4. Link
    if link_url:
        def open_link(e):
            webbrowser.open_new_tab(link_url)
            close_banner()

        link_lbl = tk.Label(
            inner_frame, 
            text="👉 Xem ngay", 
            bg="#212121", 
            fg="#4a90e2", 
            font=("Segoe UI", 9, "underline"), 
            cursor="hand2"
        )
        link_lbl.pack(anchor=tk.E, padx=10, pady=(0, 10))
        link_lbl.bind("<Button-1>", open_link)

    # 5. Hiệu ứng nhấp nháy viền
    def flash_border(state):
        try:
            if not banner_frame.winfo_exists(): return
            color = "#FFD700" if state else "#FFA500" 
            banner_frame.config(bg=color)
            parent.after(800, lambda: flash_border(not state))
        except: pass
    
    flash_border(True)
    
    # --- [MỚI] LOGIC ĐẾM NGƯỢC ---
    def update_timer(seconds_left):
        try:
            if not banner_frame.winfo_exists(): return # Nếu đã đóng tay thì dừng
            
            if seconds_left > 0:
                # Cập nhật số giây
                timer_lbl.config(text=f"({seconds_left}s)")
                # Gọi lại sau 1 giây (1000ms)
                parent.after(1000, lambda: update_timer(seconds_left - 1))
            else:
                # Hết giờ -> Đóng
                close_banner()
        except: pass

    # Bắt đầu đếm ngược
    update_timer(AUTO_CLOSE_SECONDS)

def setup_custom_titlebar(root_window, app_title="App Name", on_google_login=None):
    """
    Tạo thanh tiêu đề tùy chỉnh phong cách Modern (Windows 11 Style).
    """
    # 1. Cấu hình cửa sổ không viền
    root_window.overrideredirect(True)
    
    # --- MÀU SẮC MODERN (Dark Theme) ---
    BG_COLOR = "#1c1c1c"       # Màu nền tối hơn, sang hơn
    FG_COLOR = "#ffffff"       # Màu chữ trắng
    BTN_HOVER_BG = "#333333"   # Màu hover nhẹ cho nút thường
    CLOSE_HOVER_BG = "#e81123" # Màu đỏ chuẩn Windows khi hover nút đóng
    ACCENT_COLOR = "#4cc2ff"   # Màu xanh điểm nhấn
    
    # 2. Frame Thanh Tiêu Đề (Tăng chiều cao lên 40px cho thoáng)
    title_bar = tk.Frame(root_window, bg=BG_COLOR, relief='flat', bd=0, height=40)
    title_bar.pack(side=tk.TOP, fill=tk.X)
    title_bar.pack_propagate(False) # Cố định chiều cao

    # --- LOGIC DI CHUYỂN CỬA SỔ (DRAG WINDOW) ---
    def start_move(event):
        root_window.x = event.x
        root_window.y = event.y

    def do_move(event):
        deltax = event.x - root_window.x
        deltay = event.y - root_window.y
        x = root_window.winfo_x() + deltax
        y = root_window.winfo_y() + deltay
        root_window.geometry(f"+{x}+{y}")

    # Bind sự kiện kéo thả cho nền title bar
    title_bar.bind("<ButtonPress-1>", start_move)
    title_bar.bind("<B1-Motion>", do_move)

    # --- KHU VỰC TRÁI: ICON & TÊN APP & ONLINE ---
    left_container = tk.Frame(title_bar, bg=BG_COLOR)
    left_container.pack(side=tk.LEFT, padx=10)
    left_container.bind("<ButtonPress-1>", start_move)
    left_container.bind("<B1-Motion>", do_move)

    # 1. Icon App (Nếu có)
    try:
        icon_path = resource_path("logo.png") 
        img = Image.open(icon_path).resize((22, 22), Image.Resampling.LANCZOS)
        icon_tk = ImageTk.PhotoImage(img)
        lbl_icon = tk.Label(left_container, image=icon_tk, bg=BG_COLOR, bd=0)
        lbl_icon.image = icon_tk
        lbl_icon.pack(side=tk.LEFT, padx=(0, 10))
        lbl_icon.bind("<ButtonPress-1>", start_move)
        lbl_icon.bind("<B1-Motion>", do_move)
    except: pass

    # 2. Tên App (Font Segoe UI Semibold)
    lbl_title = tk.Label(left_container, text=app_title, bg=BG_COLOR, fg=FG_COLOR, font=("Segoe UI Semibold", 10))
    lbl_title.pack(side=tk.LEFT)
    lbl_title.bind("<ButtonPress-1>", start_move)
    lbl_title.bind("<B1-Motion>", do_move)

    # 3. Trạng thái Online (Phân cách bằng dấu gạch đứng)
    separator = tk.Label(left_container, text=" | ", bg=BG_COLOR, fg="#555555", font=("Segoe UI", 10))
    separator.pack(side=tk.LEFT, padx=5)
    separator.bind("<ButtonPress-1>", start_move)
    separator.bind("<B1-Motion>", do_move)

    global g_online_count_label
    g_online_count_label = tk.Label(
        left_container, 
        text="● Connecting...", 
        bg=BG_COLOR, 
        fg="#888888", 
        font=("Segoe UI", 9),
        bd=0
    )
    g_online_count_label.pack(side=tk.LEFT)
    g_online_count_label.bind("<ButtonPress-1>", start_move)
    g_online_count_label.bind("<B1-Motion>", do_move)

    # --- KHU VỰC PHẢI: USER PROFILE & WINDOW CONTROLS ---
    
    # Frame chứa các nút điều khiển cửa sổ (Close, Min, Max)
    window_controls_frame = tk.Frame(title_bar, bg=BG_COLOR)
    window_controls_frame.pack(side=tk.RIGHT, fill=tk.Y)

    # Hàm tạo nút điều khiển chuẩn Windows 11
    def create_sys_btn(symbol, cmd, is_close=False):
        # Nút Close sẽ có màu đỏ khi hover, nút khác màu xám
        hover_bg = CLOSE_HOVER_BG if is_close else BTN_HOVER_BG
        hover_fg = "white" # Chữ luôn trắng khi hover
        
        btn = tk.Button(
            window_controls_frame, 
            text=symbol, 
            bg=BG_COLOR, 
            fg=FG_COLOR, 
            bd=0, 
            font=("Segoe UI", 10), 
            width=6, # Rộng hơn để dễ bấm
            command=cmd, 
            activebackground=hover_bg, 
            activeforeground=hover_fg,
            cursor="arrow"
        )
        btn.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Hiệu ứng Hover
        btn.bind("<Enter>", lambda e: btn.config(bg=hover_bg, fg=hover_fg))
        btn.bind("<Leave>", lambda e: btn.config(bg=BG_COLOR, fg=FG_COLOR))
        return btn

    # Nút Close (✕)
    def custom_on_close():
        if 'on_closing' in globals():
            globals()['on_closing']()
        else:
            root_window.destroy()
            sys.exit(0)
    create_sys_btn("✕", custom_on_close, is_close=True)

    # Nút Maximize (◻)
    def toggle_max():
        if root_window.state() == "zoomed":
            root_window.state("normal")
        else:
            root_window.state("zoomed")
    create_sys_btn("◻", toggle_max)

    # Nút Minimize (─)
    def minimize_win():
        root_window.state('withdraw')
        root_window.overrideredirect(False)
        root_window.state('iconic')
        
    def on_map(event):
        if event.widget == root_window and root_window.state() == 'normal':
            if not root_window.overrideredirect():
                root_window.overrideredirect(True)
    root_window.bind('<Map>', on_map)
    
    create_sys_btn("─", minimize_win)

    # --- KHU VỰC USER / GOOGLE LOGIN (Nằm bên trái nút Minimize) ---
    global g_titlebar_google_frame
    g_titlebar_google_frame = tk.Frame(title_bar, bg=BG_COLOR)
    g_titlebar_google_frame.pack(side=tk.RIGHT, padx=(0, 5), fill=tk.Y)

    # Nút Đăng Nhập Mặc Định (Style bo tròn nhẹ)
    # Dùng Canvas hoặc Frame bọc Button để căn chỉnh đẹp hơn
    btn_google = tk.Button(
        g_titlebar_google_frame,
        text=" Đăng nhập ", 
        bg="#4285F4",       
        fg="white",
        font=("Segoe UI", 9, "bold"),
        bd=0,
        cursor="hand2",
        command=on_google_login,
        relief="flat"
    )
    # Căn giữa theo chiều dọc bằng pack kết hợp pady ảo
    btn_google.pack(ipady=4, pady=4) 

    # Hover cho nút Login
    btn_google.bind("<Enter>", lambda e: btn_google.config(bg="#357ae8"))
    btn_google.bind("<Leave>", lambda e: btn_google.config(bg="#4285F4"))

    return title_bar


# ==========================================
# [TÍNH NĂNG MỚI] KẾT NỐI SERVER ONLINE
# ==========================================
sio = socketio.Client()

# Địa chỉ Server của bạn (Lấy từ IP Oracle Cloud bạn đã cung cấp)
SERVER_URL = "http://140.83.53.151:3000"

@sio.event
def connect():
    print("✅ Đã kết nối tới Server Game!")
    # Lấy tên người dùng máy tính để làm tên hiển thị tạm thời
    import getpass
    username = getpass.getuser()
    
    # Gửi sự kiện đăng nhập lên server
    sio.emit('client-login', username)

@sio.on('update-user-list')
def on_user_list(data):
    count = len(data)
    print(f"👥 Danh sách Online cập nhật: {count} người")
    
    # --- CẬP NHẬT LÊN TITLE BAR ---
    if 'g_online_count_label' in globals():
        try:
            # Thay "🟢" bằng "●" và tô màu xanh neon (#4cff00)
            g_online_count_label.config(text=f"● Online: {count}", fg="#4cff00")
        except:
            pass

@sio.event
def disconnect():
    print("❌ Mất kết nối Server.")
    # Cập nhật trạng thái Offline lên Title Bar
    if 'g_online_count_label' in globals():
        try:
            g_online_count_label.config(text="🔴 Offline", fg="#ff4d4d")
        except: pass

def start_socket_service():
    """Hàm chạy ngầm để kết nối server"""
    try:
        sio.connect(SERVER_URL)
        sio.wait()
    except Exception as e:
        print(f"Không thể kết nối Server Game: {e}")

# ==========================================

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
    setup_custom_titlebar(
        root, 
        app_title="[WGZ] Game Updater v" + CURRENT_VERSION, 
        on_google_login=lambda: g_show_login_selector() if g_show_login_selector else custom_showwarning("Chờ chút", "App đang tải, vui lòng đợi...")
    )
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
    
    app_width = 1250
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
    root.cached_game_icons_small = {}
    # --- Định nghĩa Style ---

    style = ttk.Style()
    style.configure("Red.TLabel", foreground="red")
    style.configure("Green.TLabel", foreground="green")
    style.configure("White.TLabel", foreground="white") # Cho theme tối
    style.configure("New.TLabel", foreground="red", font=('TkDefaultFont', 9, 'bold'))
    style.configure("Green.TRadiobutton", foreground="green")
    style.configure("Installed.TLabel", foreground="green")
    style.configure("Big.Accent.TButton", font=("Segoe UI", 10, "bold"))


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
    global g_page1_ui_refs
    g_page1_ui_refs = {}

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
        MAX_COLS = 5    
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

    def update_single_game_card_state(game_name):
        """
        (HÀM MỚI) Chỉ cập nhật trạng thái nút bấm của 1 game duy nhất trên Trang 1.
        Không vẽ lại toàn bộ lưới -> Siêu nhanh.
        """
        global local_config, g_page1_ui_refs

        # Kiểm tra xem game này có tồn tại trên giao diện không
        if game_name not in g_page1_ui_refs:
            return

        widgets = g_page1_ui_refs[game_name]
        btn = widgets["btn"]
        img_label = widgets["img_label"]

        # 1. Kiểm tra lại đường dẫn (Logic giống hệt populate)
        full_path_to_launch = None
        
        # Check Custom Game
        if 'custom_games' in local_config and game_name in local_config['custom_games']:
             full_path_to_launch = local_config['custom_games'][game_name].get("launch_path")
        else:
            # Check Server Game
            current_global_path = local_config.get("game_paths", {}).get(game_name, "")
            found_launch_file = local_config.get('game_launchers', {}).get(game_name)
            
            # Nếu config user chưa có, tìm trong dữ liệu tải về (fallback)
            if not found_launch_file and 'download_options' in globals():
                for _key, mod_data in download_options.get(game_name, []):
                    if mod_data.get("launch_file"):
                        found_launch_file = mod_data.get("launch_file"); break
            
            if found_launch_file and current_global_path and os.path.isdir(current_global_path):
                full_path = os.path.join(current_global_path, found_launch_file)
                if os.path.exists(full_path): full_path_to_launch = full_path

        # 2. Cập nhật giao diện nút bấm
        if full_path_to_launch:
            btn.config(text="🚀 Chạy Game", state=tk.NORMAL, style="HoverAccent.TButton")
            
            # Cập nhật lệnh click (Bind lại sự kiện)
            # Lưu ý: Bind Button-1 sẽ ghi đè bind cũ, rất tiện.
            click_cmd = lambda e, p=full_path_to_launch, t=img_label: action_launch_game_from_page_1(p, t)
            btn.bind("<Button-1>", click_cmd)
        else:
            btn.config(text="Chưa Cài Đặt", state=tk.DISABLED, style="TButton")
            # (Không cần unbind, vì disabled thì không bấm được)

        print(f"Đã cập nhật trạng thái thẻ game: {game_name}")

    def action_go_back_and_refresh_grid():
        """(ĐÃ TỐI ƯU) Quay lại và chỉ cập nhật game vừa xem."""
        global g_current_game_name
        
        print("Quay lại Trang 1...")
        
        # Cập nhật nút bấm cho game vừa thao tác (nếu có)
        if g_current_game_name:
            update_single_game_card_state(g_current_game_name)
            
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
        """(PERFORMANCE FIX) Chuyển trang mượt mà bằng place_forget."""
        global g_current_page, page_2_back_button, g_set_path_button
        
        if g_current_page == page_to_show:
            return 
        
        # Ẩn các nút điều hướng nếu rời Trang 2
        if g_current_page == page_2_mod_list and page_to_show != page_3_progress:
            if 'g_launch_game_button' in globals():
                g_launch_game_button.pack_forget()
            if 'page_2_back_button' in globals():
                page_2_back_button.pack_forget()
            if 'g_set_path_button' in globals():
                try: g_set_path_button.pack_forget()
                except: pass

        # --- [TỐI ƯU HÓA] ---
        # Thay vì đẩy sang phải (relx=1), ta gỡ bỏ hoàn toàn trang cũ (place_forget)
        # Điều này giải phóng tài nguyên render ngay lập tức -> Hết giật
        if g_current_page:
            g_current_page.place_forget()
        
        # Hiện trang mới
        page_to_show.place(relx=0, rely=0, relwidth=1, relheight=1)
        page_to_show.tkraise()
        
        g_current_page = page_to_show

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

    def make_circle_avatar(image_data, size=(30, 30)):
        """Chuyển đổi dữ liệu ảnh thành hình tròn (Avatar)."""
        try:
            # 1. Load ảnh từ data
            im = Image.open(io.BytesIO(image_data)).convert("RGBA")
            
            # 2. Resize
            im = im.resize(size, Image.Resampling.LANCZOS)
            
            # 3. Tạo mặt nạ tròn
            mask = Image.new("L", size, 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, size[0], size[1]), fill=255)
            
            # 4. Áp dụng mặt nạ
            output = Image.new("RGBA", size, (0, 0, 0, 0))
            output.paste(im, (0, 0), mask=mask)
            
            return ImageTk.PhotoImage(output)
        except Exception as e:
            print(f"Lỗi tạo avatar: {e}")
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

    def action_uninstall_game_logic(game_name):
        """
        (FIX V5 - UNINSTALLER THÔNG MINH)
        - Hỗ trợ xóa sub-folder (cài đặt chuẩn).
        - Hỗ trợ xóa root folder (cài đặt trực tiếp) nếu user xác nhận.
        - Hỗ trợ chỉ xóa config nếu không tìm thấy file.
        """
        global local_config, g_all_mods_flat
        
        # 1. Lấy thông tin cấu hình
        configured_path = local_config.get("game_paths", {}).get(game_name, "")
        launcher_name = local_config.get("game_launchers", {}).get(game_name, "")
        
        # Nếu chưa set đường dẫn thì chỉ dọn config
        if not configured_path:
            if custom_askyesno("Xóa khỏi danh sách", f"Game '{game_name}' chưa được thiết lập đường dẫn.\nBạn có muốn xóa nó khỏi danh sách 'Đã Cài Đặt' không?"):
                cleanup_config_only(game_name)
            return

        target_folder_to_delete = None
        is_root_install = False # Cờ đánh dấu nếu game cài trực tiếp vào folder gốc

        # --- BƯỚC 1: QUÉT TÌM FILE CHẠY ĐỂ XÁC ĐỊNH FOLDER ---
        # Ưu tiên quét file thực tế trên ổ cứng thay vì đoán mò qua tên file
        if os.path.exists(configured_path):
            target_filename = os.path.basename(launcher_name) if launcher_name else ""
            found_exe_path = None
            
            # Nếu có launcher name, quét tìm nó
            if target_filename:
                for root_dir, dirs, files in os.walk(configured_path):
                    if target_filename in files:
                        found_exe_path = os.path.join(root_dir, target_filename)
                        break
            
            # Nếu tìm thấy file exe
            if found_exe_path:
                try:
                    abs_config = os.path.abspath(configured_path)
                    abs_exe = os.path.abspath(found_exe_path)
                    
                    # Tính đường dẫn tương đối từ Config Path đến File Exe
                    # VD: Config="D:/Game", Exe="D:/Game/Bin/game.exe" -> Rel="Bin/game.exe"
                    rel_path = os.path.relpath(abs_exe, abs_config)
                    
                    if rel_path == os.path.basename(abs_exe):
                        # Trường hợp: File nằm ngay tại root (VD: D:/New folder/game.exe)
                        target_folder_to_delete = abs_config
                        is_root_install = True
                    else:
                        # Trường hợp: File nằm trong subfolder (VD: D:/New folder/GameData/game.exe)
                        # Lấy folder cấp 1 ngay dưới Config Path
                        top_subfolder = rel_path.split(os.sep)[0]
                        target_folder_to_delete = os.path.join(abs_config, top_subfolder)
                        is_root_install = False
                        
                except Exception as e:
                    print(f"Lỗi tính toán đường dẫn: {e}")

        # Nếu Bước 1 thất bại (không tìm thấy exe), thử dùng logic đoán tên folder (Bước 2 cũ)
        if not target_folder_to_delete and launcher_name:
            try:
                norm_launcher = os.path.normpath(launcher_name)
                parts = norm_launcher.split(os.sep)
                if len(parts) > 1:
                    potential_path = os.path.join(configured_path, parts[0])
                    if os.path.exists(potential_path) and os.path.isdir(potential_path):
                        target_folder_to_delete = potential_path
                        is_root_install = False
            except: pass

        # --- BƯỚC 2: THỰC HIỆN XÓA ---
        if target_folder_to_delete and os.path.isdir(target_folder_to_delete):
            folder_name = os.path.basename(target_folder_to_delete)
            
            # Cảnh báo khác nhau tùy trường hợp
            if is_root_install:
                # CẢNH BÁO MẠNH nếu xóa folder gốc (như D:/New folder)
                msg = (
                    f"⚠️ CẢNH BÁO QUAN TRỌNG ⚠️\n\n"
                    f"Tool phát hiện game được cài trực tiếp vào:\n{target_folder_to_delete}\n\n"
                    f"Bạn có chắc chắn muốn XÓA TOÀN BỘ thư mục này không?\n"
                    f"(Hãy kiểm tra kỹ xem trong đó có dữ liệu quan trọng khác không!)"
                )
                title = "Xác nhận Xóa (Root Folder)"
                icon_type = "warning"
            else:
                # Cảnh báo thường nếu xóa sub-folder
                msg = (
                    f"XÁC NHẬN GỠ CÀI ĐẶT '{game_name}'\n\n"
                    f"Sẽ xóa thư mục game:\n{folder_name}\n" 
                    f"(Tại: {os.path.dirname(target_folder_to_delete)})"
                )
                title = "Gỡ Cài Đặt"
                icon_type = "yesno" # Dùng logic dialog cũ

            # Sử dụng hộp thoại xác nhận
            should_delete = False
            if is_root_install:
                # Với root install, dùng askyesno kỹ hơn
                should_delete = custom_askyesno(title, msg)
            else:
                should_delete = custom_askyesno(title, msg)

            if should_delete:
                try:
                    import shutil
                    # Kiểm tra lần cuối: Không bao giờ xóa ổ đĩa gốc (C:\, D:\)
                    if len(target_folder_to_delete) <= 3:
                        custom_showerror("Nguy hiểm", "Không được phép xóa ổ đĩa gốc!")
                        return

                    shutil.rmtree(target_folder_to_delete)
                    cleanup_config_only(game_name) # Xóa khỏi config sau khi xóa file
                    custom_showinfo("Thành công", f"Đã xóa xong thư mục '{folder_name}'.")
                except Exception as e:
                    custom_showerror("Lỗi", f"Không thể xóa folder:\n{e}\n(Có thể file đang mở hoặc thiếu quyền).")

        # --- BƯỚC 3: TRƯỜNG HỢP KHÔNG TÌM THẤY GÌ (HOẶC FILE ĐÃ MẤT) ---
        else:
            # Hộp thoại tùy chọn mới: Cho phép xóa config
            dialog = tk.Toplevel(root)
            dialog.title("Không tìm thấy file")
            center_window_on_screen(dialog, 400, 220)
            dialog.transient(root)
            dialog.grab_set()
            
            ttk.Label(dialog, text="⚠️ Không tìm thấy thư mục game cụ thể.", font=("Segoe UI", 10, "bold"), foreground="#ffcc00").pack(pady=(15, 5))
            
            msg_text = (
                f"Tool không xác định được thư mục cần xóa tại:\n{configured_path}\n\n"
                "Bạn muốn làm gì?"
            )
            ttk.Label(dialog, text=msg_text, justify=tk.CENTER).pack(pady=5)

            btn_frame = ttk.Frame(dialog)
            btn_frame.pack(fill=tk.X, pady=15, padx=20)

            def on_open_folder():
                try: os.startfile(configured_path)
                except: pass
                dialog.destroy()

            def on_clean_list():
                if custom_askyesno("Xác nhận", f"Xóa '{game_name}' khỏi danh sách App (Config)?"):
                    cleanup_config_only(game_name)
                    dialog.destroy()
                    custom_showinfo("Xong", "Đã xóa game khỏi danh sách.")

            # Nút 1: Mở thư mục (Để xóa tay)
            ttk.Button(btn_frame, text="📂 Mở Thư Mục (Xóa tay)", command=on_open_folder).pack(fill=tk.X, pady=2)
            
            # Nút 2: Chỉ xóa khỏi danh sách (Fix cho trường hợp file đã xóa rồi)
            ttk.Button(btn_frame, text="🗑️ Chỉ xóa khỏi Danh Sách App", command=on_clean_list, style="Accent.TButton").pack(fill=tk.X, pady=2)
            
            # Nút 3: Hủy
            ttk.Button(btn_frame, text="Hủy bỏ", command=dialog.destroy).pack(fill=tk.X, pady=(10, 0))

    def cleanup_config_only(game_name):
        """Hàm phụ: Chỉ dọn dẹp config trong settings.json"""
        global local_config, g_all_mods_flat
        
        # 1. Xóa đường dẫn
        if 'game_paths' in local_config and game_name in local_config['game_paths']:
            del local_config['game_paths'][game_name]
        
        # 2. Xóa launcher
        if 'game_launchers' in local_config and game_name in local_config['game_launchers']:
            del local_config['game_launchers'][game_name]
        
        # 3. Xóa version đã cài
        if 'installed_versions' in local_config and 'g_all_mods_flat' in globals():
            keys_to_remove = []
            for mod_key, mod_data in g_all_mods_flat.items():
                if mod_data.get("game") == game_name:
                    keys_to_remove.append(mod_key)
            for k in keys_to_remove:
                if k in local_config['installed_versions']:
                    del local_config['installed_versions'][k]

        save_local_config(local_config)
        action_clear_game_search() # Refresh giao diện

    def action_clear_game_exe(game_key):
        """
        Xóa đường dẫn file khởi chạy (.exe) và CẬP NHẬT LẠI DANH SÁCH.
        """
        global local_config
        
        if custom_askyesno("Xác nhận", f"Bạn muốn xóa liên kết file chạy (.exe) của '{game_key}'?\n(Game sẽ chuyển về mục 'Chưa Cài Đặt')."):
            try:
                # 1. Xóa khỏi custom_games (nếu là game custom)
                if 'custom_games' in local_config and game_key in local_config['custom_games']:
                    local_config['custom_games'][game_key]['launch_path'] = "" 
                
                # 2. Xóa khỏi game_launchers (File chạy)
                if 'game_launchers' in local_config and game_key in local_config['game_launchers']:
                    del local_config['game_launchers'][game_key]

                # 3. [QUAN TRỌNG] Xóa khỏi game_paths (Đường dẫn thư mục)
                # Điều này giúp hàm 'is_game_installed' nhận biết là chưa cài
                if 'game_paths' in local_config and game_key in local_config['game_paths']:
                    del local_config['game_paths'][game_key]
                
                # 4. Lưu config
                save_local_config(local_config)
                
                # 5. [QUAN TRỌNG] LÀM MỚI GIAO DIỆN (REFRESH)
                # Gọi hàm này để nó phân loại lại game vào nhóm "Chưa Cài Đặt"
                if 'download_options' in globals():
                    populate_page_1_grid(download_options)
                else:
                    # Fallback nếu chưa tải xong dữ liệu
                    # (Ít khi xảy ra, nhưng giữ lại cho an toàn)
                    global g_show_steam_details
                    if g_current_game_name == game_key and g_show_steam_details:
                        g_show_steam_details(game_key)
                    
                custom_showinfo("Thành công", f"Đã xóa file chạy của '{game_key}'.")
                
            except Exception as e:
                custom_showerror("Lỗi", f"Không thể xóa file chạy: {e}")

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

    def action_change_resolution(game_key):
        """Mở popup chọn độ phân giải cho Custom Game."""
        # 1. Tạo cửa sổ
        dialog = tk.Toplevel(root)
        dialog.title(f"Resolution - {game_key}")
        center_window_on_screen(dialog, 350, 200)
        dialog.transient(root)
        dialog.grab_set()
        
        # Theme cho titlebar
        dialog.after(10, lambda: apply_theme_to_titlebar(dialog))

        ttk.Label(dialog, text="Chọn độ phân giải khởi động (16:9):", font=("Segoe UI", 10)).pack(pady=15)

        # 2. Danh sách Resolution 16:9 phổ biến
        res_options = [
            "Mặc định (Theo Game)",
            "1280x720  (HD)",
            "1366x768  (Laptop)",
            "1600x900  (HD+)",
            "1920x1080 (Full HD)",
            "2560x1440 (2K)",
            "3840x2160 (4K)"
        ]

        # Lấy giá trị hiện tại
        current_res = "Mặc định (Theo Game)"
        if 'custom_games' in local_config and game_key in local_config['custom_games']:
            saved_res = local_config['custom_games'][game_key].get('resolution', "")
            if saved_res:
                # Tìm text khớp với saved_res (ví dụ "1920x1080")
                for opt in res_options:
                    if saved_res in opt:
                        current_res = opt
                        break

        combo = ttk.Combobox(dialog, values=res_options, state="readonly", width=30)
        combo.pack(pady=5)
        combo.set(current_res)

        def on_save():
            selection = combo.get()
            
            # Trích xuất độ phân giải (VD: Lấy "1920x1080" từ "1920x1080 (Full HD)")
            res_val = ""
            if "x" in selection:
                res_val = selection.split(" ")[0] # Lấy phần đầu tiên trước dấu cách

            # Lưu vào config
            if 'custom_games' in local_config and game_key in local_config['custom_games']:
                local_config['custom_games'][game_key]['resolution'] = res_val
                save_local_config(local_config)
                
                if res_val:
                    custom_showinfo("Đã lưu", f"Game sẽ chạy ở độ phân giải: {res_val}\n(Lưu ý: Game phải hỗ trợ tham số dòng lệnh -screen-width / -w)")
                else:
                    custom_showinfo("Đã lưu", "Đã reset về mặc định của game.")
                    
                dialog.destroy()

        ttk.Button(dialog, text="Lưu Thiết Lập", command=on_save, style="Accent.TButton").pack(pady=20)

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

    def get_ctx_icon(name, color):
        """Tạo icon vector đơn giản cho Menu (Đã thêm Bánh răng)."""
        key = f"ctx_icon_{name}_{color}" # Thêm color vào key để cache đúng màu
        if key in root.cached_images: return root.cached_images[key]
        
        # Tạo ảnh trong suốt 20x20
        img = Image.new("RGBA", (20, 20), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        
        # Vẽ các hình tượng trưng đơn giản
        if name == "edit": # Bút chì
            draw.line((14, 4, 4, 14), fill=color, width=2)
            draw.polygon([(4, 14), (3, 17), (6, 15)], fill=color)
        elif name == "image": # Khung ảnh
            draw.rectangle((3, 4, 17, 16), outline=color, width=2)
            draw.polygon([(3, 16), (8, 11), (13, 16)], fill=color)
        elif name == "folder": # Thư mục
            draw.polygon([(2,4), (8,4), (10,6), (18,6), (18,16), (2,16)], outline=color, width=2)
        elif name == "screen": # Màn hình
            draw.rectangle((2, 4, 18, 14), outline=color, width=2)
            draw.line((10, 14, 10, 17), fill=color, width=2)
            draw.line((6, 17, 14, 17), fill=color, width=2)
        elif name == "delete": # Dấu X
            draw.line((5, 5, 15, 15), fill=color, width=3)
            draw.line((5, 15, 15, 5), fill=color, width=3)
        elif name == "restore": # Mũi tên quay lại
            draw.arc((5, 5, 15, 15), 20, 280, fill=color, width=2)
            draw.polygon([(5,5), (5,9), (1,5)], fill=color)
        
        elif name == "trash":
            # Thân thùng rác
            draw.rectangle((6, 7, 14, 17), outline=color, width=2)
            # Nắp
            draw.line((4, 5, 16, 5), fill=color, width=2)
            # Tay cầm
            draw.line((8, 3, 12, 3), fill=color, width=2)
            # Thanh giữa (tùy chọn)
            draw.line((10, 10, 10, 14), fill=color, width=1)
        # --- [MỚI] VẼ BÁNH RĂNG (GEAR) ---
        elif name == "gear":
            import math
            cx, cy = 10, 10 # Tâm ảnh
            
            # 1. Vẽ 8 răng cưa tỏa ra từ tâm
            for i in range(8):
                angle = math.radians(i * 45) # 360 / 8 = 45 độ
                
                # Tính điểm bắt đầu (sát tâm) và kết thúc (ngoài rìa)
                # R_in = 4, R_out = 9
                x1 = cx + 4 * math.cos(angle)
                y1 = cy + 4 * math.sin(angle)
                x2 = cx + 9 * math.cos(angle)
                y2 = cy + 9 * math.sin(angle)
                
                draw.line((x1, y1, x2, y2), fill=color, width=3)

            # 2. Vẽ vòng tròn thân ở giữa (đè lên chân các răng để làm mịn)
            # Bbox: (left, top, right, bottom) -> Vẽ vòng tròn bán kính ~5
            draw.ellipse((5, 5, 15, 15), outline=color, width=2)
        # ---------------------------------

        tk_img = ImageTk.PhotoImage(img)
        root.cached_images[key] = tk_img
        return tk_img

    def show_game_context_menu(target, game_key, is_custom):
        """
        Hiển thị menu ngữ cảnh (Đã thêm: Xóa file chạy).
        """
        menu = tk.Menu(root, tearoff=0)
        
        # --- 1. CÁC MỤC CƠ BẢN ---
        menu.add_command(
            label="Đổi Tên Game", 
            image=get_ctx_icon("edit", "#FFD700"), # Gold
            compound=tk.LEFT,
            command=lambda: action_rename_game(game_key)
        )
        
        menu.add_command(
            label="Đổi Ảnh (URL)", 
            image=get_ctx_icon("image", "#00FFFF"), # Cyan
            compound=tk.LEFT,
            command=lambda: action_change_game_image(game_key, is_custom)
        )
        
        # --- QUẢN LÝ FILE CHẠY ---
        menu.add_separator()
        
        # Chọn file
        menu.add_command(
            label="Chọn file khởi chạy",  # <-- Đã xóa chữ (.exe)
            image=get_ctx_icon("folder", "#F0E68C"),
            compound=tk.LEFT,
            command=action_set_game_path_from_page_2
        )

        # [MỚI] Xóa file
        menu.add_command(
            label="Xóa file chạy", 
            image=get_ctx_icon("delete", "#FFA500"), # Orange
            compound=tk.LEFT,
            command=lambda: action_clear_game_exe(game_key)
        )

        # --- KHÔI PHỤC ẢNH ---
        if not is_custom and game_key in local_config.get('theme_overrides', {}):
            menu.add_separator()
            menu.add_command(
                label="Khôi phục Ảnh Gốc", 
                image=get_ctx_icon("restore", "#FFFFFF"), 
                compound=tk.LEFT,
                command=lambda: action_remove_custom_image(game_key)
            )

        # --- MENU CHO CUSTOM GAME ---
        if is_custom:
            menu.add_separator()
            
            menu.add_command(
                label="Chỉnh Resolution (16:9)", 
                image=get_ctx_icon("screen", "#87CEFA"), # LightBlue
                compound=tk.LEFT,
                command=lambda: action_change_resolution(game_key)
            )
            
            menu.add_command(
                label="Xóa Game Khỏi List", 
                image=get_ctx_icon("delete", "#FF6347"), # Tomato (Đỏ)
                compound=tk.LEFT,
                command=lambda: action_delete_custom_game(game_key)
            )
            
        # Xử lý tọa độ (như cũ)
        try:
            x = target.x_root
            y = target.y_root
        except AttributeError:
            try:
                x = target.winfo_rootx()
                y = target.winfo_rooty() + target.winfo_height()
            except:
                x = root.winfo_pointerx()
                y = root.winfo_pointery()

        menu.post(x, y)

    def on_page_1_mouse_wheel(event):
        """Hàm cuộn CHUYÊN BIỆT cho Trang 1 (Tránh xung đột với Tab 2)."""
        global page_1_canvas
        try:
            if not page_1_canvas.winfo_exists(): return
            
            scroll_amount = 0
            if sys.platform == "win32":
                scroll_amount = int(-1 * (event.delta / 120))
            elif sys.platform == "darwin": # macOS
                scroll_amount = event.delta
            else: # Linux
                if event.num == 4: scroll_amount = -1
                elif event.num == 5: scroll_amount = 1
            
            page_1_canvas.yview_scroll(scroll_amount, "units")
        except Exception as e:
            pass

    def populate_page_1_grid(game_groups, search_term=""):
        """
        [STEAM UI CATEGORIZED] Giao diện chia 3 mục: MY GAMES, INSTALLED, LIBRARY.
        """
        global g_game_search_entry, page_1_canvas
        global g_steam_sidebar_frame, g_steam_detail_frame
        global g_selected_game_label 
        global path_entry, g_mod_buttons, g_current_selected_key, selected_option
        global g_launch_game_button 
        global g_auto_add_exclusion

        # --- 0. STYLE & CLEANUP ---
        style.configure("SteamPlay.TButton", background="#4cff00", foreground="black", font=("Segoe UI", 12, "bold"), padding=(20, 10))
        style.map("SteamPlay.TButton", background=[('active', '#66ff33'), ('disabled', '#3d4d3d')], foreground=[('disabled', '#888888')])
        style.configure("InstallMod.TButton", background="#0078d4", foreground="white", font=("Segoe UI", 11, "bold"))
        
        # Style cho Header danh mục (Mới)
        style.configure("Category.TLabel", background="#191919", foreground="#8a8a8a", font=("Segoe UI", 9, "bold"))
        style.configure("CategoryHover.TLabel", foreground="#ffffff")

        if 'g_tab1_loading_frame' in globals() and g_tab1_loading_frame:
            try: g_tab1_loading_frame.destroy()
            except: pass
        
        for widget in page_1_game_grid.winfo_children(): widget.destroy()

        # --- 1. LAYOUT CHÍNH (GRID 3:7) ---
        main_layout = tk.Frame(page_1_game_grid, bg="#191919")
        main_layout.pack(fill=tk.BOTH, expand=True)
        main_layout.columnconfigure(0, weight=3, uniform="group1") 
        main_layout.columnconfigure(1, weight=7, uniform="group1")
        main_layout.rowconfigure(0, weight=1)
        
        # === CỘT TRÁI: SIDEBAR ===
        sidebar_container = tk.Frame(main_layout, bg="#191919")
        sidebar_container.grid(row=0, column=0, sticky="nsew")

        # --- [CẬP NHẬT] FOOTER: NÚT GEMINI + STICKER ---
        sidebar_footer = tk.Frame(sidebar_container, bg="#191919", pady=10, padx=10)
        sidebar_footer.pack(side=tk.BOTTOM, fill=tk.X)

        # 1. Style cho nút (Giữ nguyên)
        style.configure("Gemini.TButton", 
                        font=("Segoe UI", 11, "bold"), 
                        foreground="#00FFFF") 
        style.map("Gemini.TButton",
                foreground=[('active', '#FFFFFF'), ('pressed', '#00CCCC')],
                background=[('active', '#333333')]) 

        # 2. Tạo nút
        gemini_full_btn = ttk.Button(
            sidebar_footer,
            text="✨Google Gemini Pro",
            command=action_open_gemini_pro,
            style="Gemini.TButton"
        )
        gemini_full_btn.pack(fill=tk.X, ipady=5)

        # 3. [MỚI] TẠO STICKER "MIỄN PHÍ"
        # Dùng tk.Label thường để dễ chỉnh màu nền (bg)
        badge = tk.Label(
            sidebar_footer,
            text="MIỄN PHÍ",
            bg="#FF3333",       # Màu đỏ tươi (Red Badge)
            fg="white",         # Chữ trắng
            font=("Segoe UI", 7, "bold"), # Font nhỏ, đậm
            padx=5, pady=0,     # Đệm bên trong cho đẹp
            bd=0                # Không viền
        )
        
        # Dùng place để "dán" đè lên góc phải trên của Footer
        # relx=1.0: Sát lề phải
        # rely=0.0: Sát lề trên
        # x=-5, y=0: Dịch vào trong một chút cho cân đối
        badge.place(relx=1.0, rely=0.0, anchor="ne", x=-2, y=2)

        # Quan trọng: Click vào sticker cũng kích hoạt lệnh mở Gemini
        badge.bind("<Button-1>", lambda e: action_open_gemini_pro())
        # Cho chuột biến hình bàn tay khi trỏ vào sticker
        badge.bind("<Enter>", lambda e: badge.config(cursor="hand2"))
        
        # ----------------------------------------------

        # --- FIX SCROLL SIDEBAR (CỘT TRÁI) ---
        def on_sidebar_scroll(event):
            scroll_amount = int(-1 * (event.delta / 120)) if sys.platform == "win32" else event.delta
            list_canvas.yview_scroll(scroll_amount, "units")

        def _bind_sidebar_scroll(event):
            list_canvas.bind_all("<MouseWheel>", on_sidebar_scroll)
            list_canvas.bind_all("<Button-4>", on_sidebar_scroll)
            list_canvas.bind_all("<Button-5>", on_sidebar_scroll)

        def _unbind_sidebar_scroll(event):
            list_canvas.unbind_all("<MouseWheel>")
            list_canvas.unbind_all("<Button-4>")
            list_canvas.unbind_all("<Button-5>")

        # Chỉ kích hoạt cuộn khi chuột nằm trong vùng Sidebar Container
        sidebar_container.bind("<Enter>", _bind_sidebar_scroll)
        sidebar_container.bind("<Leave>", _unbind_sidebar_scroll)

        # Search Bar
        # Tạo Frame nền đen đóng vai trò là viền của ô tìm kiếm
        search_frame = tk.Frame(sidebar_container, bg="#191919", pady=10, padx=8)
        search_frame.pack(fill=tk.X)

        # Container cho ô nhập liệu (Mô phỏng Input field có icon)
        # bg="#252526": Màu nền của ô input (xám hơn nền sidebar một chút)
        input_container = tk.Frame(search_frame, bg="#252526")
        input_container.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3) # ipady để tăng chiều cao

        # 1. Icon Search (🔍)
        # Dùng Label để hiện icon, đặt bên trái cùng
        lbl_search_icon = tk.Label(input_container, text="🔍", bg="#252526", fg="#8a8a8a", font=("Segoe UI", 10))
        lbl_search_icon.pack(side=tk.LEFT, padx=(5, 2))

        # 2. Ô Nhập Liệu
        # borderwidth=0 để bỏ viền mặc định, hòa nhập vào container
        g_game_search_entry = tk.Entry(input_container, bg="#252526", fg="white", 
                                    insertbackground="white", # Màu con trỏ nhấp nháy
                                    relief=tk.FLAT, font=("Segoe UI", 10))
        g_game_search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Bind phím Enter
        g_game_search_entry.bind("<Return>", on_game_search)
        if search_term: g_game_search_entry.insert(0, search_term)

        # 3. Nút Xóa (✖) - Chỉ hiện khi có text (hoặc luôn hiện để clear)
        if search_term:
            btn_clear = tk.Label(input_container, text="✖", bg="#252526", fg="#8a8a8a", cursor="hand2")
            btn_clear.pack(side=tk.RIGHT, padx=5)
            btn_clear.bind("<Button-1>", lambda e: action_clear_game_search())
            # Hiệu ứng hover cho nút X
            btn_clear.bind("<Enter>", lambda e: btn_clear.config(fg="white"))
            btn_clear.bind("<Leave>", lambda e: btn_clear.config(fg="#8a8a8a"))

        # Nút Thêm Game (+) nằm ngoài ô search
        add_btn = tk.Button(search_frame, text="➕", command=action_add_custom_game_popup,
                            bg="#191919", fg="#4cff00", bd=0, font=("Segoe UI", 14), cursor="hand2")
        add_btn.pack(side=tk.LEFT, padx=(5, 0))
        CreateToolTip(add_btn, "Thêm Game Ngoài")
        
        # List Canvas
        list_canvas = tk.Canvas(sidebar_container, bg="#191919", highlightthickness=0)
        list_scrollbar = ttk.Scrollbar(sidebar_container, orient="vertical", command=list_canvas.yview)
        g_steam_sidebar_frame = tk.Frame(list_canvas, bg="#191919")
        
        list_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        list_canvas.configure(yscrollcommand=list_scrollbar.set)
        list_canvas.create_window((0, 0), window=g_steam_sidebar_frame, anchor="nw", width=280)

        def on_sidebar_scroll(event):
            scroll_amount = int(-1 * (event.delta / 120)) if sys.platform == "win32" else event.delta
            list_canvas.yview_scroll(scroll_amount, "units")

        g_steam_sidebar_frame.bind("<Configure>", lambda e: list_canvas.configure(scrollregion=list_canvas.bbox("all")))
        list_canvas.bind("<Configure>", lambda e: list_canvas.itemconfig(list_canvas.find_all()[0], width=e.width))
        list_canvas.bind_all("<MouseWheel>", on_sidebar_scroll)

        # === CỘT PHẢI: MAIN CONTENT ===
        content_container = ttk.Frame(main_layout)
        content_container.grid(row=0, column=1, sticky="nsew")

        detail_canvas = tk.Canvas(content_container, highlightthickness=0, bg="#181818")
        detail_scrollbar = ttk.Scrollbar(content_container, orient="vertical", command=detail_canvas.yview)
        g_steam_detail_frame = tk.Frame(detail_canvas, bg="#181818")
        
        detail_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        detail_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        detail_canvas.configure(yscrollcommand=detail_scrollbar.set)
        detail_window_id = detail_canvas.create_window((0, 0), window=g_steam_detail_frame, anchor="nw")

        g_steam_detail_frame.bind("<Configure>", lambda e: detail_canvas.configure(scrollregion=detail_canvas.bbox("all")))
        detail_canvas.bind("<Configure>", lambda e: detail_canvas.itemconfig(detail_window_id, width=e.width))
        # --- FIX SCROLL DETAIL (CỘT PHẢI) ---
        def on_detail_scroll(event):
            # Hàm thực hiện cuộn Canvas bên phải
            try:
                scroll_amount = int(-1 * (event.delta / 120)) if sys.platform == "win32" else event.delta
                detail_canvas.yview_scroll(scroll_amount, "units")
            except: pass

        def _bind_detail_scroll(event):
            # Khi chuột VÀO vùng phải: Bắt sự kiện cuộn cho Canvas phải
            detail_canvas.bind_all("<MouseWheel>", on_detail_scroll)
            detail_canvas.bind_all("<Button-4>", on_detail_scroll)
            detail_canvas.bind_all("<Button-5>", on_detail_scroll)

        def _unbind_detail_scroll(event):
            # Khi chuột RA KHỎI vùng phải: Gỡ bỏ sự kiện (để nhường cho bên trái)
            detail_canvas.unbind_all("<MouseWheel>")
            detail_canvas.unbind_all("<Button-4>")
            detail_canvas.unbind_all("<Button-5>")

        # Gắn sự kiện: Chỉ khi chuột nằm trong content_container thì mới cuộn được
        content_container.bind("<Enter>", _bind_detail_scroll)
        content_container.bind("<Leave>", _unbind_detail_scroll)
        # --- 2. LOGIC HIỂN THỊ CHI TIẾT ---
        def show_steam_details(game_name):
            global g_current_game_name, local_config, path_entry
            global g_mod_buttons, g_current_selected_key, selected_option
            global g_launch_game_button 

            g_current_game_name = game_name
            local_config = load_local_config()
            g_mod_buttons = {}
            selected_option.set("") 

            for w in g_steam_detail_frame.winfo_children(): w.destroy()

            is_custom = game_name in local_config.get('custom_games', {})

            # Header Image
            raw_banner_pil = None
            override_path = local_config.get('theme_overrides', {}).get(game_name)
            if is_custom: override_path = local_config['custom_games'][game_name].get("image_local_path")
            
            if override_path and os.path.exists(override_path):
                try: raw_banner_pil = Image.open(override_path)
                except: pass
            if not raw_banner_pil:
                image_url = g_game_themes.get(game_name)
                if image_url:
                    try:
                        import hashlib
                        cache_key = f"{image_url}_460x215"
                        hashed_name = hashlib.sha256(cache_key.encode('utf-8')).hexdigest() + ".png"
                        cache_path = os.path.join(g_cache_dir, hashed_name)
                        if os.path.exists(cache_path): raw_banner_pil = Image.open(cache_path)
                    except: pass
            if not raw_banner_pil:
                try: raw_banner_pil = Image.open(resource_path("logo.png"))
                except: raw_banner_pil = Image.new('RGB', (800, 300), color='#181818')

            banner_frame = tk.Frame(g_steam_detail_frame, bg="#181818")
            banner_frame.pack(fill=tk.X, anchor="n")
            
            FIXED_BANNER_HEIGHT = 300
            hero_canvas = tk.Canvas(banner_frame, height=FIXED_BANNER_HEIGHT, bg="#181818", highlightthickness=0)
            hero_canvas.pack(fill=tk.X, expand=True)
            banner_img_id = hero_canvas.create_image(0, 0, anchor="nw")

            def resize_banner_image(event):
                new_width = event.width
                if new_width < 10 or not raw_banner_pil: return
                try:
                    img_w, img_h = raw_banner_pil.size
                    ratio = new_width / img_w
                    new_h = int(img_h * ratio)
                    resized_pil = raw_banner_pil.resize((new_width, new_h), Image.Resampling.LANCZOS)
                    if new_h > FIXED_BANNER_HEIGHT:
                        resized_pil = resized_pil.crop((0, 0, new_width, FIXED_BANNER_HEIGHT))
                    tk_img = ImageTk.PhotoImage(resized_pil)
                    hero_canvas.image = tk_img 
                    hero_canvas.itemconfig(banner_img_id, image=tk_img)
                    hero_canvas.tag_raise("text_layer")
                except: pass

            hero_canvas.bind("<Configure>", resize_banner_image)

            # display_name = local_config.get('display_name_overrides', {}).get(game_name, game_name)
            # hero_canvas.create_text(32, 242, text=display_name, font=("Segoe UI", 30, "bold"), fill="black", anchor="w", tags="text_layer")
            # hero_canvas.create_text(30, 240, text=display_name, font=("Segoe UI", 30, "bold"), fill="white", anchor="w", tags="text_layer")

            # Play Bar
            play_bar_frame = tk.Frame(g_steam_detail_frame, bg="#252526", height=80, padx=30, pady=15)
            play_bar_frame.pack(fill=tk.X)

            # Logic kiểm tra Path (Giữ nguyên)
            full_path_to_launch = None
            current_path_folder = local_config.get("game_paths", {}).get(game_name, "")
            if not current_path_folder: current_path_folder = local_config.get("last_used_folder", "")

            if is_custom:
                full_path_to_launch = local_config['custom_games'][game_name].get("launch_path")
            else:
                found_launch_file = local_config.get('game_launchers', {}).get(game_name)
                if not found_launch_file and 'download_options' in globals():
                    for _key, mod_data in game_groups.get(game_name, []):
                        if mod_data.get("launch_file"): found_launch_file = mod_data.get("launch_file"); break
                if found_launch_file and current_path_folder and os.path.isdir(current_path_folder):
                    full_path = os.path.join(current_path_folder, found_launch_file)
                    if os.path.exists(full_path): full_path_to_launch = full_path
            
            g_launch_game_button = ttk.Button(play_bar_frame, text="🚀 Chạy Game ", style="Big.Accent.TButton")
            g_launch_game_button.pack(side=tk.LEFT, ipady=5, ipadx=15)
            
            if full_path_to_launch:
                g_launch_game_button.config(state=tk.NORMAL, command=lambda: action_launch_game_from_page_1(full_path_to_launch, None))
                status_text = "Ready To Play"
            else:
                g_launch_game_button.config(state=tk.DISABLED, text="Chưa Cài Đặt")
                status_text = "Hãy chọn folder & cài đặt Game"
            

            gear_btn = ttk.Button(
                play_bar_frame, 
                image=get_ctx_icon("gear", "white"), # <-- GỌI HÀM VỪA SỬA
                text="",              
                width=3
            )
            
            # Cấu hình lệnh
            gear_btn.configure(command=lambda: show_game_context_menu(gear_btn, game_name, is_custom))
            
            gear_btn.pack(side=tk.RIGHT, padx=5)
            gear_btn = play_bar_frame.winfo_children()[-1]

            if full_path_to_launch or (current_path_folder and os.path.exists(current_path_folder)):
                
                uninstall_btn = ttk.Button(
                    play_bar_frame,
                    image=get_ctx_icon("trash", "#ff4d4d"), # Icon thùng rác màu đỏ
                    text="",
                    width=3,
                    style="TButton" # Style thường
                )
                
                uninstall_btn.configure(command=lambda: action_uninstall_game_logic(game_name))
                
                # Pack sang phải (nó sẽ nằm bên TRÁI của nút Gear vì Gear pack trước)
                uninstall_btn.pack(side=tk.RIGHT, padx=(0, 5))
                
                CreateToolTip(uninstall_btn, "Gỡ cài đặt game (Xóa thư mục game)")

            # Content (Path & Mod List)
            content_frame = tk.Frame(g_steam_detail_frame, bg="#181818", padx=30, pady=20)
            content_frame.pack(fill=tk.BOTH, expand=True)

            path_group = tk.LabelFrame(content_frame, text="📂 Vị Trí Cài Đặt", bg="#181818", fg="white", padx=10, pady=10)
            path_group.pack(fill=tk.X, pady=(0, 20))
            
            path_entry = ttk.Entry(path_group)
            path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            path_entry.insert(0, current_path_folder)
            
            ttk.Button(path_group, text="Chọn đường dẫn...", command=browse_for_folder).pack(side=tk.LEFT, padx=5)
            # ttk.Button(path_group, text="Cài file mở Game", command=action_set_game_path_from_page_2).pack(side=tk.LEFT)

            mod_group = tk.LabelFrame(content_frame, text="📦 Các bản Cài đặt / Mod", bg="#181818", fg="white", padx=10, pady=10)
            mod_group.pack(fill=tk.BOTH, expand=True)

            mod_list_data = download_options.get(game_name, [])
            
            if not mod_list_data:
                tk.Label(mod_group, text="Hiện không có cài đặt nào", bg="#181818", fg="gray").pack(pady=20)
            else:
                for i, (key, data) in enumerate(mod_list_data):
                    mod_name = data.get("name", key)
                    mod_ver = data.get("version", "v?")
                    installed_ver = local_config.get("installed_versions", {}).get(key, "Not installed")
                    
                    card = tk.Frame(mod_group, bg="#252526", pady=10, padx=10)
                    card.pack(fill=tk.X, pady=2)
                    
                    status_icon = "✔" if mod_ver == installed_ver else "⬇"
                    chk_btn = tk.Button(card, text=status_icon, bg="#252526", fg="white", width=4, bd=0, cursor="hand2")
                    chk_btn.pack(side=tk.LEFT, fill=tk.Y)
                    
                    info_frame = tk.Frame(card, bg="#252526", padx=10)
                    info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                    tk.Label(info_frame, text=mod_name, fg="white", bg="#252526", font=("Segoe UI", 11, "bold"), anchor="w").pack(fill=tk.X)
                    
                    ver_text = f"Version: {mod_ver}"
                    if installed_ver != "Not installed": ver_text += f" (Installed: {installed_ver})"
                    tk.Label(info_frame, text=ver_text, fg="#8b929a", bg="#252526", font=("Segoe UI", 9), anchor="w").pack(fill=tk.X)

                    g_mod_buttons[key] = (chk_btn, card)

                    def on_mod_click(k=key):
                        selected_option.set(k)
                        for mk, (mb, mc) in g_mod_buttons.items():
                            if mk == k:
                                mc.config(bg="#3d4450")
                                mb.config(bg="#4cff00", fg="black")
                            else:
                                mc.config(bg="#252526")
                                mb.config(bg="#3d4450", fg="white")

                    chk_btn.config(command=on_mod_click)
                    card.bind("<Button-1>", lambda e, k=key: on_mod_click(k))
                    info_frame.bind("<Button-1>", lambda e, k=key: on_mod_click(k))
                    for child in info_frame.winfo_children(): child.bind("<Button-1>", lambda e, k=key: on_mod_click(k))

                if mod_list_data:
                    g_mod_buttons[mod_list_data[0][0]][0].invoke()

            action_bar = tk.Frame(content_frame, bg="#181818", pady=20)
            action_bar.pack(fill=tk.X)
            
            if 'g_auto_add_exclusion' not in globals():
                global g_auto_add_exclusion
                g_auto_add_exclusion = tk.BooleanVar(value=False)

            def_chk = ttk.Checkbutton(action_bar, text="🛡️ Auto-Exclusion (Defender)", variable=g_auto_add_exclusion, style="Switch.TCheckbutton")
            def_chk.pack(side=tk.LEFT)
            CreateToolTip(def_chk, "Tự động thêm thư mục vào Exclusion Windows Defender (Tránh xóa file).")

            dl_btn = ttk.Button(action_bar, text="Bắt Đầu Tải Và Cài Đặt", style="Accent.TButton", command=start_download_thread)
            dl_btn.pack(side=tk.RIGHT, ipadx=20, ipady=5)

        global g_show_steam_details
        g_show_steam_details = show_steam_details
        # --- 3. LOGIC SIDEBAR & SELECTION ---
        g_selected_game_label = None
        
        def on_select_game(game_name, widget_frame):
            global g_selected_game_label
            if g_selected_game_label:
                try: g_selected_game_label.config(bg="#191919")
                except: pass
            widget_frame.config(bg="#3d4450")
            g_selected_game_label = widget_frame
            show_steam_details(game_name)

        # --- HELPER: VẼ 1 ITEM GAME (ICON 16:9) ---
        def render_sidebar_item(parent_frame, game_name, is_custom):
            icon_img = None
            
            # Kích thước mục tiêu: 16:9 (Rộng 64, Cao 36)
            TARGET_SIZE = (64, 36) 

            # 1. Thử lấy từ Cache Local
            try:
                override_path = local_config.get('theme_overrides', {}).get(game_name)
                if is_custom: override_path = custom_games_data[game_name].get("image_local_path")
                
                if override_path and os.path.exists(override_path):
                    # Tạo key cache riêng cho size 16:9
                    cache_key = f"wide_{override_path}"
                    
                    if cache_key in root.cached_images: 
                        icon_img = root.cached_images[cache_key]
                    else:
                        with Image.open(override_path) as img:
                            # Resize theo tỉ lệ 16:9
                            img_resized = img.resize(TARGET_SIZE, Image.Resampling.LANCZOS)
                            icon_img = ImageTk.PhotoImage(img_resized)
                            root.cached_images[cache_key] = icon_img
            except: pass
            
            # 2. Thử lấy từ URL Server
            if not icon_img and not is_custom:
                image_url = g_game_themes.get(game_name)
                if image_url: 
                    # Load từ URL với size 16:9
                    icon_img = load_image_from_url(image_url, size=TARGET_SIZE)

            # 3. Fallback (Nếu không có ảnh, vẫn phải resize ảnh default để thẳng hàng)
            if not icon_img: 
                # Resize ảnh default thành 16:9 để không bị lệch layout
                if "default_wide" not in root.cached_images:
                    try:
                        # Lấy ảnh gốc default (giả sử đã load ở đâu đó hoặc load lại)
                        def_pil = Image.open(resource_path("logo.png")) # Hoặc ảnh default của bạn
                        def_resized = def_pil.resize(TARGET_SIZE, Image.Resampling.LANCZOS)
                        root.cached_images["default_wide"] = ImageTk.PhotoImage(def_resized)
                    except: pass
                
                icon_img = root.cached_images.get("default_wide", root.default_game_icon_small)

            # --- VẼ UI ITEM ---
            item_frame = tk.Frame(parent_frame, bg="#191919", cursor="hand2", padx=5, pady=2) # Giảm padding chút cho gọn
            item_frame.pack(fill=tk.X)

            l_icon = tk.Label(item_frame, image=icon_img, bg="#191919", bd=0)
            l_icon.image = icon_img 
            l_icon.pack(side=tk.LEFT)

            display_name = local_config.get('display_name_overrides', {}).get(game_name, game_name)
            fg_col = "#a3cf06" if is_custom else "#bfbfbf"
            
            l_name = tk.Label(item_frame, text=display_name, bg="#191919", fg=fg_col, font=("Segoe UI", 10), anchor="w")
            l_name.pack(side=tk.LEFT, padx=(10,0), fill=tk.X, expand=True)

            # Bind Events
            cmd = lambda e, g=game_name, w=item_frame: on_select_game(g, w)
            item_frame.bind("<Button-1>", cmd)
            l_name.bind("<Button-1>", cmd)
            l_icon.bind("<Button-1>", cmd)
            item_frame.bind("<Enter>", lambda e, w=item_frame: w.config(bg="#2c2c2c") if w != g_selected_game_label else None)
            item_frame.bind("<Leave>", lambda e, w=item_frame: w.config(bg="#191919") if w != g_selected_game_label else None)
            
            return item_frame

        # --- HELPER: CHECK INSTALLED (CẬP NHẬT) ---
        def is_game_installed(g_name):
            # 1. Kiểm tra phiên bản mod đã cài (Logic cũ)
            mods = game_groups.get(g_name, [])
            for key, _ in mods:
                if key in local_config.get("installed_versions", {}):
                    return True
            
            # 2. [MỚI] Kiểm tra xem đã set đường dẫn .exe chưa
            # Nếu có đường dẫn trong config -> Coi như đã cài đặt
            if 'game_paths' in local_config:
                path = local_config['game_paths'].get(g_name)
                # Chỉ cần có đường dẫn và thư mục tồn tại là tính
                if path and os.path.exists(path):
                    return True
                    
            return False
        
        # --- MAIN LOOP: PHÂN LOẠI & VẼ ---
        server_games = sorted(game_groups.keys())
        custom_games_data = local_config.get('custom_games', {})
        
        # 1. Gom tất cả tên game
        all_raw_names = sorted(list(custom_games_data.keys()) + server_games)
        
        # 2. Lọc theo search
        if search_term:
            search_term = search_term.lower()
            filtered_names = [name for name in all_raw_names if search_term in name.lower()]
        else:
            filtered_names = all_raw_names

        # 3. Chia 3 nhóm
        list_custom = []
        list_installed = []
        list_uninstalled = []

        for name in filtered_names:
            if name in custom_games_data:
                list_custom.append(name)
            elif is_game_installed(name):
                list_installed.append(name)
            else:
                list_uninstalled.append(name)

        # 4. Hàm vẽ Header + List
        # --- LOGIC ĐÓNG MỞ (COLLAPSIBLE) ---
        def toggle_section(section_frame, content_frame, arrow_label):
            """Ẩn/hiện nội dung danh mục và đổi mũi tên."""
            if content_frame.winfo_viewable():
                # Đang mở -> Đóng lại
                content_frame.pack_forget()
                arrow_label.config(text="▶")
            else:
                # Đang đóng -> Mở ra
                content_frame.pack(fill=tk.X)
                arrow_label.config(text="▼")
        
        # --- HÀM VẼ CATEGORY (FIX LỖI VỊ TRÍ) ---
        def draw_section(title, game_list, is_custom_section=False):
            if not game_list: return
            
            # 1. Tạo Container ĐỘC LẬP cho Category này (Quan trọng!)
            # Frame này sẽ giữ chỗ cố định trên Sidebar, không bị chạy lung tung
            section_container = tk.Frame(g_steam_sidebar_frame, bg="#191919")
            section_container.pack(fill=tk.X, pady=0) # Pack container vào Sidebar chính

            # Thiết lập màu sắc phù hợp
            if title == "🌟 GAME NGOÀI":
                title_color = "#FFC300"  # Vàng Gold (Đặc biệt)
            elif title == "✅ ĐÃ CÀI ĐẶT":
                title_color = "#32CD32"  # Xanh Lá (Ready)
            elif title == "❌ CHƯA CÀI ĐẶT":
                title_color = "#4A90E2"  # Xanh Dương (Mặc định/Thư viện)
            else:
                title_color = "#8a8a8a"  # Màu xám mặc định

            # 2. Header Frame (Nằm trong Container)
            header_frame = tk.Frame(section_container, bg="#191919", pady=5, cursor="hand2")
            header_frame.pack(fill=tk.X)
            
            arrow_lbl = tk.Label(header_frame, text="▼", bg="#191919", fg=title_color, font=("Segoe UI", 8))
            arrow_lbl.pack(side=tk.LEFT, padx=(5, 2))
            
            title_lbl = tk.Label(header_frame, text=f"{title} ({len(game_list)})", bg="#191919", fg=title_color, font=("Segoe UI", 9, "bold"))
            title_lbl.pack(side=tk.LEFT)

            # 3. Content Frame (Nằm trong Container, ngay dưới Header)
            content_frame = tk.Frame(section_container, bg="#191919")
            content_frame.pack(fill=tk.X) 

            # Gắn sự kiện Toggle
            cmd_toggle = lambda e: toggle_section(header_frame, content_frame, arrow_lbl)
            header_frame.bind("<Button-1>", cmd_toggle)
            arrow_lbl.bind("<Button-1>", cmd_toggle)
            title_lbl.bind("<Button-1>", cmd_toggle)
            
            # Hover Effect
            def on_enter(e):
                title_lbl.config(fg="white")
                arrow_lbl.config(fg="white")
            def on_leave(e):
                title_lbl.config(fg=title_color)
                arrow_lbl.config(fg=title_color)
            
            header_frame.bind("<Enter>", on_enter)
            header_frame.bind("<Leave>", on_leave)

            # Render Items
            for game in game_list:
                render_sidebar_item(content_frame, game, is_custom_section)


        # 5. Thực hiện vẽ theo thứ tự
        draw_section("🌟 GAME NGOÀI", list_custom, is_custom_section=True)
        draw_section("✅ ĐÃ CÀI ĐẶT", list_installed, is_custom_section=False)
        draw_section("❌ CHƯA CÀI ĐẶT", list_uninstalled, is_custom_section=False)

        # 6. Auto Select (Ưu tiên: Custom -> Installed -> Uninstalled)
        target_game = None
        
        # [MỚI] Ưu tiên giữ lại game đang chọn (để không bị nhảy trang khi refresh)
        if g_current_game_name and g_current_game_name in filtered_names:
            target_game = g_current_game_name
        else:
            # Nếu không có (hoặc game đang chọn bị lọc mất), chọn cái đầu tiên
            if list_custom: target_game = list_custom[0]
            elif list_installed: target_game = list_installed[0]
            elif list_uninstalled: target_game = list_uninstalled[0]

        if target_game:
            # Gọi hàm hiển thị chi tiết
            show_steam_details(target_game)

        print("Steam UI Loaded (Categorized).")


    def show_page_2_for_game(game_name):
        """
        (INSTANT SWITCH) Chuyển trang ngay lập tức, đẩy việc load dữ liệu ra sau.
        """
        global g_current_game_name, g_game_image_label, page_2_back_button
        
        # 1. Cập nhật biến cơ bản
        g_current_game_name = game_name
        
        # 2. Reset UI cơ bản (Ẩn nút, đổi tên frame)
        if 'g_launch_game_button' in globals():
            g_launch_game_button.pack_forget()
        if 'g_set_path_button' in globals():
            try: g_set_path_button.pack_forget()
            except: pass
            
        page_2_back_button.pack(side=tk.LEFT)
        options_frame.config(text=f"Các mod cho: {game_name}")
        
        # Xóa ảnh cũ tạm thời (để tránh hiện ảnh game trước)
        g_game_image_label.pack_forget() 
        
        # 3. CHUYỂN TRANG NGAY LẬP TỨC (Không chờ load dữ liệu)
        show_page(page_2_mod_list)
        
        # 4. Hẹn giờ chạy logic nặng (Load Config, Load Ảnh, Vẽ Mod)
        # 10ms là đủ để UI kịp vẽ trang mới trước khi bắt đầu xử lý nặng
        root.after(10, lambda: _deferred_page_2_logic(game_name))

    def _deferred_page_2_logic(game_name):
        """Hàm phụ: Chạy sau khi giao diện đã chuyển xong."""
        global local_config, path_entry
        
        # 1. Load Config (Nặng)
        local_config = load_local_config()
        
        # 2. Điền đường dẫn
        path_entry.delete(0, tk.END)
        last_used_folder = local_config.get("last_used_folder", "")
        # Nếu game này có đường dẫn riêng đã lưu, ưu tiên dùng nó
        specific_path = local_config.get("game_paths", {}).get(game_name, "")
        path_entry.insert(0, specific_path if specific_path else last_used_folder)

        # 3. Bắt đầu tải ảnh (Thread ngầm)
        # (Copy lại logic thread load ảnh từ code cũ của bạn vào đây)
        def load_game_image_thread():
            icon_img = None
            current_config = load_local_config()
            custom_games = current_config.get('custom_games', {})
            theme_overrides = current_config.get('theme_overrides', {})
            
            local_path = None
            if game_name in custom_games:
                local_path = custom_games[game_name].get("image_local_path")
            elif game_name in theme_overrides:
                local_path = theme_overrides[game_name]
                
            if local_path and os.path.exists(local_path):
                try:
                    cache_key = f"local_big_{local_path}"
                    if cache_key in root.cached_images:
                        icon_img = root.cached_images[cache_key]
                    else:
                        with Image.open(local_path) as img:
                            img_resized = img.resize((460, 215), Image.Resampling.LANCZOS)
                            icon_img = ImageTk.PhotoImage(img_resized)
                            root.cached_images[cache_key] = icon_img
                except: pass

            if not icon_img:
                image_url = g_game_themes.get(game_name)
                if image_url:
                    icon_img = load_image_from_url(image_url, size=(460, 215))

            if not icon_img:
                icon_img = root.default_game_icon_large 

            progress_queue.put(("game_image_loaded", icon_img))

        threading.Thread(target=load_game_image_thread, daemon=True).start()
        
        # 4. Vẽ danh sách mod (Hàm tối ưu bên dưới)
        update_radio_buttons_text_for_game(game_name)

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
        """
        (ULTIMATE BATCH) Xóa cực nhanh và Vẽ theo lô.
        """
        global local_config, radio_buttons, g_mod_buttons, g_current_selected_key
        global content_frame, canvas

        # 1. Reset dữ liệu
        g_mod_buttons.clear()
        g_current_selected_key = None
        selected_option.set("") 
        radio_buttons = []

        style.configure("New.TLabel", foreground="red", font=('TkDefaultFont', 9, 'bold'))
        style.configure("Installed.TLabel", foreground="green")

        # --- KỸ THUẬT DỌN DẸP SIÊU TỐC ---
        # Mẹo: Ẩn frame đi trước khi destroy con của nó. 
        # Tkinter sẽ không tốn sức tính toán lại layout cho từng cái bị xóa.
        if content_frame.winfo_viewable():
            # Tạm thời gỡ khỏi canvas (chỉ là ẩn hiển thị, ko mất dữ liệu)
            # Lưu ý: content_frame nằm trong canvas window, ta dùng itemconfigure để ẩn
            canvas.itemconfigure(canvas_window_id, state='hidden')
        
        # Bây giờ xóa rất nhanh
        for widget in content_frame.winfo_children(): 
            widget.destroy()
            
        # Hiện lại frame (đang trống)
        canvas.itemconfigure(canvas_window_id, state='normal')
        # --------------------------------

        # Hiện Loading
        loading_label = ttk.Label(content_frame, text="⏳ Đang tải danh sách mod...", font=("Segoe UI", 10))
        loading_label.pack(pady=20)
        
        # Cập nhật UI ngay lập tức để người dùng thấy Loading
        content_frame.update_idletasks()

        # Chuẩn bị dữ liệu
        mod_list = download_options.get(game_name_to_show, [])
        first_key_holder = [None] 

        def create_click_handler(key_value):
            def handler(event=None):
                selected_option.set(key_value)
                update_guide_text()
                update_mod_button_states(key_value)
            return handler

        BATCH_SIZE = 8 # Vẽ 8 cái một lúc
        
        def process_mod_batch(start_index):
            end_index = min(start_index + BATCH_SIZE, len(mod_list))
            
            if start_index == 0 and loading_label.winfo_exists():
                loading_label.destroy()

            for i in range(start_index, end_index):
                key, data = mod_list[i]
                
                display_name = data.get("name", "LỖI: THIẾU TÊN")
                online_version = data.get("version")
                if not online_version: continue 

                installed_version = local_config.get("installed_versions", {}).get(key, "Chưa cài đặt")

                # Layout Row
                row_frame = ttk.Frame(content_frame, style="Card.TFrame", padding=(10, 5))
                row_frame.pack(fill=tk.X, pady=2) 
                
                # Checkbox
                checkmark_frame = ttk.Frame(row_frame)
                checkmark_frame.pack(side=tk.LEFT,padx=(0, 0))
                checkmark_button = ttk.Button(checkmark_frame, text="", style="Accent.TButton", state=tk.DISABLED)
                checkmark_button.pack(fill=tk.Y, expand=True)

                # Info
                left_frame = ttk.Frame(row_frame)
                left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
                left_frame.columnconfigure(0, weight=1) 

                right_frame = ttk.Frame(row_frame)
                right_frame.pack(side=tk.RIGHT, padx=(0, 0))

                name_label = ttk.Label(left_frame, text=display_name, font=("Segoe UI", 10, "bold"), anchor=tk.CENTER)
                name_label.grid(row=0, column=0, sticky="ew")

                all_widgets_to_bind = [row_frame, checkmark_frame, checkmark_button, left_frame, right_frame, name_label] 

                # Status
                if online_version == installed_version:
                    status_text = f"✓ Đã cài đặt ({online_version})"
                    status_label = ttk.Label(left_frame, text=status_text, style="Installed.TLabel", anchor=tk.CENTER) 
                    status_label.grid(row=1, column=0, sticky="ew", pady=(2, 0)) 
                    all_widgets_to_bind.append(status_label)
                else:
                    status_text = f"🔥 Cần cài đặt ({online_version})" if installed_version == "Chưa cài đặt" else f"🔥 Cập nhật ({online_version})"
                    new_label = ttk.Label(left_frame, text=status_text, style="New.TLabel", anchor=tk.CENTER)
                    new_label.grid(row=1, column=0, sticky="ew", pady=(2, 0))
                    all_widgets_to_bind.append(new_label)

                # Selection
                if first_key_holder[0] is None: first_key_holder[0] = key

                click_cmd = create_click_handler(key)
                select_button = ttk.Button(right_frame, text="Chọn", command=click_cmd)
                select_button.pack(fill=tk.Y, expand=True)
                
                g_mod_buttons[key] = (select_button, checkmark_button)
                all_widgets_to_bind.append(select_button)

                # Bindings
                for widget in all_widgets_to_bind:
                    try:
                        widget.bind("<MouseWheel>", on_mouse_wheel)
                        widget.bind("<Button-4>", on_mouse_wheel) 
                        widget.bind("<Button-5>", on_mouse_wheel)
                        if widget != select_button: widget.bind("<Button-1>", click_cmd)
                    except: pass

            if end_index < len(mod_list):
                root.after(5, lambda: process_mod_batch(end_index))
            else:
                content_frame.update_idletasks()
                canvas.configure(scrollregion=canvas.bbox("all"))
                
                # Auto select first
                if first_key_holder[0]:
                    selected_option.set(first_key_holder[0])
                    update_guide_text()
                    update_mod_button_states(first_key_holder[0])

        process_mod_batch(0)

        
    # def refresh_mod_list_ui():
    #     """
    #     (Hàm mới) Xóa và vẽ lại danh sách mod (Trang 2) 
    #     để cập nhật trạng thái (ví dụ: "Đã cài đặt").
    #     """
    #     global content_frame, g_current_game_name
        
    #     # Kiểm tra xem Trang 2 có đang hoạt động không
    #     if not g_current_game_name or not content_frame.winfo_exists():
    #         print("Lỗi: Không thể refresh mod list (UI không tồn tại).")
    #         return

    #     print(f"Đang làm mới danh sách mod cho: {g_current_game_name}")
        
    #     # 1. Xóa tất cả các nút mod cũ (ĐIỀU QUAN TRỌNG NHẤT)
    #     for widget in content_frame.winfo_children(): 
    #         widget.destroy()
            
    #     # 2. Gọi hàm vẽ lại các nút mod mới
    #     # (Hàm này sẽ đọc config mới và vẽ lại đúng trạng thái)
    #     update_radio_buttons_text_for_game(g_current_game_name)


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

    for widget in page_3_progress.winfo_children():
        widget.destroy()

    # 2. Spacer trên cùng (Đẩy nội dung xuống giữa)
    ttk.Frame(page_3_progress).pack(side=tk.TOP, expand=True)

    # 3. Ảnh GIF (Animation) - Đặt ở giữa màn hình
    g_gif_label = ttk.Label(page_3_progress, anchor=tk.CENTER)
    g_gif_label.pack(side=tk.TOP, pady=(0, 20))

    # 4. Tên Option đang tải (Ví dụ: Đang xử lý: Elden Ring...)
    option_label = ttk.Label(page_3_progress, text="Chuẩn bị...", anchor=tk.CENTER, style="White.TLabel", font=("Segoe UI", 11, "bold"))
    option_label.pack(side=tk.TOP, pady=(0, 15))

    # --- KHUNG CHỨA THANH TIẾN TRÌNH & THÔNG SỐ (GOM NHÓM) ---
    # Tạo một container để gom các thanh bar và text lại gần nhau
    progress_container = ttk.Frame(page_3_progress)
    progress_container.pack(side=tk.TOP, fill=tk.X, padx=100) # padx=100 để thanh bar không quá dài ra mép

    # A. Thanh File hiện tại
    progress_file_frame = ttk.Frame(progress_container)
    progress_file_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))
    
    lbl_file_progress = ttk.Label(progress_file_frame, text="Tiến độ File hiện tại:", style="secondary.TLabel")
    lbl_file_progress.pack(anchor=tk.W)
    
    progress_bar = ttk.Progressbar(progress_file_frame, orient="horizontal", length=100, mode="indeterminate")
    progress_bar.pack(fill=tk.X, pady=(2, 0))

    # B. Thanh Tiến độ chung (Parts)
    global overall_progress_bar, overall_status_label
    progress_overall_frame = ttk.Frame(progress_container)
    progress_overall_frame.pack(side=tk.TOP, fill=tk.X, pady=(5, 5))

    overall_status_label = ttk.Label(progress_overall_frame, text="Tiến độ chung: 0/0 Part", style="White.TLabel")
    overall_status_label.pack(anchor=tk.W)

    overall_progress_bar = ttk.Progressbar(progress_overall_frame, orient="horizontal", length=100, mode="determinate")
    overall_progress_bar.pack(fill=tk.X, pady=(2, 0))

    # C. Dòng trạng thái (%, Tốc độ, ETA) - Đặt ngay dưới thanh bar
    status_frame = ttk.Frame(progress_container)
    status_frame.pack(side=tk.TOP, fill=tk.X, pady=(5, 0))

    status_label = ttk.Label(status_frame, text="Sẵn sàng.", anchor=tk.W, style="White.TLabel")
    status_label.pack(side=tk.LEFT)
    
    eta_label = ttk.Label(status_frame, text="", style="secondary.TLabel", anchor=tk.E, width=12)
    eta_label.pack(side=tk.RIGHT)
    
    speed_label = ttk.Label(status_frame, text="", style="secondary.TLabel", anchor=tk.E, width=15)
    speed_label.pack(side=tk.RIGHT)

    # 5. Spacer dưới cùng (Cân bằng bố cục)
    ttk.Frame(page_3_progress).pack(side=tk.TOP, expand=True)
    # --- Hết Nội dung Tab 1 ---

    # --- SỬA: Tạo UI cho Tab 2 ("Upload Config") ---
    second_tab_frame = ttk.Frame(notebook, padding=(10, 10))
    notebook.add(second_tab_frame, text=" Quản Lý Option Tải ") # Đổi tên cho chuyên nghiệp

    # --- Variables ---
    current_config_data = {} 
    current_github_sha = None 
    g_currently_selected_id = None
    g_game_theme_sha = None
    g_master_game_list = []
    g_search_timer = None
    g_theme_manager_window = None

    # --- Layout Chính: Chia làm 2 cột (Trái: List, Phải: Form Editor) ---
    # PanedWindow giúp người dùng kéo thả kích thước 2 bên
    paned_window = ttk.PanedWindow(second_tab_frame, orient=tk.HORIZONTAL)
    paned_window.pack(fill=tk.BOTH, expand=True)

    # Khung Trái (Danh sách Option)
    left_pane = ttk.Frame(paned_window)
    paned_window.add(left_pane, weight=1)

    # Khung Phải (Form Nhập liệu)
    right_pane = ttk.Frame(paned_window)
    paned_window.add(right_pane, weight=2) # Form rộng hơn list

    # ==========================
    # 1. CỘT TRÁI: DANH SÁCH
    # ==========================
    
    # Toolbar trên cùng của cột trái
    left_toolbar = ttk.Frame(left_pane)
    left_toolbar.pack(fill=tk.X, pady=(0, 5))
    
    ttk.Label(left_toolbar, text="Danh sách Option", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)

    # Treeview
    tree_frame = ttk.Frame(left_pane)
    tree_frame.pack(fill=tk.BOTH, expand=True)

    tree_scrollbar = ttk.Scrollbar(tree_frame)
    tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Chỉ hiện Tên và Game để tiết kiệm diện tích, các thông tin khác xem bên phải
    cols = ("ID", "Name", "Game") 
    options_treeview = ttk.Treeview(tree_frame, columns=cols, show='headings', yscrollcommand=tree_scrollbar.set, selectmode="browse")
    options_treeview.pack(expand=True, fill=tk.BOTH)
    tree_scrollbar.config(command=options_treeview.yview)

    options_treeview.heading("ID", text="ID")
    options_treeview.heading("Name", text="Tên Option")
    options_treeview.heading("Game", text="Game")
    
    options_treeview.column("ID", width=40, anchor=tk.CENTER, stretch=tk.NO)
    options_treeview.column("Name", width=150, anchor=tk.W)
    options_treeview.column("Game", width=100, anchor=tk.W)

    # Nút Di chuyển (Floating nhỏ gọn bên dưới)
    move_btn_frame = ttk.Frame(left_pane)
    move_btn_frame.pack(fill=tk.X, pady=5)
    
    ttk.Button(move_btn_frame, text="▲", width=3, command=lambda: action_move_option("up")).pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
    ttk.Button(move_btn_frame, text="▼", width=3, command=lambda: action_move_option("down")).pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)

    # ==========================
    # 2. CỘT PHẢI: FORM EDITOR HIỆN ĐẠI
    # ==========================
    
    # Container cho Form (có scrollbar phòng khi màn hình bé)
    form_canvas = tk.Canvas(right_pane, highlightthickness=0)
    form_scrollbar = ttk.Scrollbar(right_pane, orient="vertical", command=form_canvas.yview)
    
    # Frame chứa nội dung thực sự
    edit_form_frame = ttk.Frame(form_canvas)

    form_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    form_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # --- [FIX QUAN TRỌNG] ---
    # Tạo window và LƯU ID lại để dùng sau
    form_window_id = form_canvas.create_window((0, 0), window=edit_form_frame, anchor="nw")

    # Hàm 1: Khi nội dung thay đổi chiều cao -> Cập nhật thanh cuộn dọc
    def on_frame_configure(event):
        form_canvas.configure(scrollregion=form_canvas.bbox("all"))

    # Hàm 2: Khi Canvas thay đổi chiều rộng -> Ép nội dung co giãn theo
    def on_canvas_configure(event):
        # Lấy chiều rộng hiện tại của canvas
        canvas_width = event.width
        # Set chiều rộng của edit_form_frame bằng chiều rộng canvas
        form_canvas.itemconfig(form_window_id, width=canvas_width)

    edit_form_frame.bind("<Configure>", on_frame_configure)
    form_canvas.bind("<Configure>", on_canvas_configure)

    # --- Header Form ---
    header_form_frame = ttk.Frame(edit_form_frame, padding=10)
    header_form_frame.pack(fill=tk.X)
    
    form_title_label = ttk.Label(header_form_frame, text="✨ Thêm / Sửa Option", font=("Segoe UI", 12, "bold"), foreground="#4cc2ff")
    form_title_label.pack(side=tk.LEFT)
    
    # [SỬA] Gán vào biến btn_clear_header
    btn_clear_header = ttk.Button(header_form_frame, text="Làm mới (Tạo mới)", command=lambda: clear_form())
    btn_clear_header.pack(side=tk.RIGHT)

    form_widgets = {}
    def action_move_option(direction):
        """Di chuyển thứ tự option lên/xuống."""
        global current_config_data
        selected_items = options_treeview.selection()
        if not selected_items: return

        selected_key = selected_items[0]
        items_list = list(current_config_data.items())
        
        # Tìm index hiện tại
        curr_idx = -1
        for i, (k, v) in enumerate(items_list):
            if k == selected_key:
                curr_idx = i
                break
        
        if curr_idx == -1: return

        # Tính index mới
        new_idx = curr_idx - 1 if direction == "up" else curr_idx + 1
        
        if 0 <= new_idx < len(items_list):
            # Hoán đổi
            items_list[curr_idx], items_list[new_idx] = items_list[new_idx], items_list[curr_idx]
            current_config_data = dict(items_list)
            
            # Refresh UI
            populate_treeview()
            options_treeview.selection_set(selected_key)
            options_treeview.see(selected_key)
            upload_status_label.config(text="Đã thay đổi thứ tự. Nhớ 'Upload Config' để lưu!", foreground="#ffcc00")

    def open_game_theme_manager():
        """Mở cửa sổ modal để Thêm/Xóa game theme."""
        global g_theme_manager_window, g_theme_listbox, g_theme_name_entry, g_theme_url_entry

        if g_theme_manager_window is not None:
            try: g_theme_manager_window.destroy()
            except: pass

        g_theme_manager_window = tk.Toplevel(root)
        g_theme_manager_window.title("Quản lý Game Theme")
        center_window_on_screen(g_theme_manager_window, 600, 400)
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

    def toggle_edit_form_state(enable=True):
        """Khóa hoặc Mở khóa toàn bộ form nhập liệu."""
        state = "normal" if enable else "disabled"
        
        # 1. Xử lý các widget nhập liệu (Entry, Combobox, Text)
        for widget in form_widgets.values():
            try:
                # Với Text widget, state='disabled' sẽ làm xám màu và chặn nhập liệu
                widget.config(state=state)
            except: pass

        # 2. Xử lý các nút bấm hành động
        try:
            add_update_button.config(state=state)
            delete_option_btn.config(state=state)
            # Nút "Thêm Game" nhỏ bên cạnh combobox
            btn_add_game_theme.config(state=state) 
            # Nút "Chọn từ Drive"
            btn_drive_picker.config(state=state) # (Lưu ý: Cần gán biến cho nút này ở Bước 2)
            # Nút "Làm mới/Tạo mới" ở header
            btn_clear_header.config(state=state) # (Lưu ý: Cần gán biến cho nút này ở Bước 2)
        except Exception as e:
            # Bỏ qua lỗi nếu nút chưa được khởi tạo (lần chạy đầu)
            pass

    def action_add_update_option():
        """Lấy dữ liệu từ Form và Lưu vào Config (Hỗ trợ Multi-URL)."""
        global current_config_data, g_currently_selected_id

        # 1. Lấy dữ liệu từ Form Widgets
        name = form_widgets["Option Name:"].get().strip()
        
        # --- [CẬP NHẬT] Lấy URL từ Text Widget ---
        raw_urls_text = form_widgets["URL:"].get("1.0", tk.END).strip()
        # Tách dòng và làm sạch
        url_list = [line.strip() for line in raw_urls_text.splitlines() if line.strip()]
        
        # Logic xử lý ID Google Drive (nếu người dùng chỉ nhập ID)
        final_url_list = []
        for u in url_list:
            if "drive.google.com" not in u and "/" not in u and len(u) > 15:
                # Giả sử là ID
                final_url_list.append(f"https://drive.google.com/uc?id={u}")
            else:
                final_url_list.append(u)
        # -----------------------------------------

        game = form_widgets["Game:"].get().strip()
        ver = form_widgets["Version:"].get().strip()
        f_type = form_widgets["Type:"].get()
        launch_file = form_widgets["Launch File:"].get().strip()
        pwd = form_widgets["Password:"].get().strip()
        
        guide = form_widgets["Path Guide:"].get("1.0", tk.END).strip()
        del_list_raw = form_widgets["Delete List:"].get("1.0", tk.END).strip()
        del_list = [line.strip() for line in del_list_raw.splitlines() if line.strip()]

        # Validate
        if not name:
            custom_showwarning("Thiếu Tên", "Vui lòng nhập Tên Option.")
            return
        if not game:
            custom_showwarning("Thiếu Game", "Vui lòng chọn hoặc nhập tên Game.")
            return
        if not final_url_list:
            custom_showwarning("Thiếu Link", "Vui lòng nhập ít nhất 1 đường dẫn tải.")
            return

        # Tạo dict data mới
        new_data = {
            "name": name,
            "urls": final_url_list, # Lưu Key mới là 'urls' (list)
            "version": ver,
            "game": game,
            "type": f_type,
            "password": pwd if pwd else None,
            "launch_file": launch_file if launch_file else None,
            "path_guide": guide if guide else None,
            "delete_before_extract": del_list
        }
        
        # Tương thích ngược: Lưu thêm key 'url' là link đầu tiên (để các bản tool cũ không bị crash)
        if final_url_list:
            new_data["url"] = final_url_list[0]

        # 2. Lưu vào dict chính
        target_key = None
        if g_currently_selected_id:
            target_key = g_currently_selected_id
            current_config_data[target_key] = new_data
            upload_status_label.config(text=f"Đã cập nhật: {name}", foreground="green")
        else:
            max_id = 0
            for k in current_config_data:
                if k.isdigit(): max_id = max(max_id, int(k))
            target_key = str(max_id + 1)
            current_config_data[target_key] = new_data
            upload_status_label.config(text=f"Đã thêm mới: {name} (ID: {target_key})", foreground="green")

        # 3. Refresh
        populate_treeview()
        options_treeview.selection_set(target_key)
        options_treeview.see(target_key)
    
    def action_delete_option():
        global current_config_data
        sel = options_treeview.selection()
        if not sel: return
        
        key = sel[0]
        name = current_config_data.get(key, {}).get("name", "Unknown")
        
        if custom_askyesno("Xóa Option", f"Bạn chắc chắn muốn xóa: {name}?"):
            del current_config_data[key]
            clear_form()
            populate_treeview()
            upload_status_label.config(text=f"Đã xóa: {name}", foreground="red")

    def action_load_from_github_wrapper():
        # Wrapper gọi hàm load logic chính (đã có ở phần tab 2 cũ)
        # Vì bạn đang thay thế UI, ta cần đảm bảo logic load vẫn chạy
        # Gọi lại hàm load_from_github_wrapper gốc hoặc viết lại logic gọi hàm load_json
        # Ở đây tôi viết lại logic kết nối UI mới:
        
        global current_config_data, current_github_sha
        repo = get_github_repo()
        if not repo: return
        
        content, sha = load_json_from_github_api(repo)
        if content:
            current_config_data = json.loads(content)
            current_github_sha = sha
            populate_treeview()
            clear_form()
            upload_status_label.config(text="Đã tải Config mới nhất từ GitHub.", foreground="#4cc2ff")
            toggle_edit_form_state(True)
            # Refresh cả game list cho combobox
            update_game_combobox_list()

    def action_upload_to_github_wrapper():
        global current_config_data, current_github_sha
        if not current_config_data: return
        
        repo = get_github_repo()
        if not repo: return
        
        # Hỏi PIN
        pin = custom_askstring("Bảo Mật", "Nhập mã PIN Admin để upload:", show="*")
        if pin != "2408": 
            custom_showerror("Sai PIN", "Sai mã PIN.")
            return

        success, new_sha = upload_json_to_github(repo, current_config_data, current_github_sha)
        if success:
            if new_sha: current_github_sha = new_sha
            upload_status_label.config(text="Upload thành công! Dữ liệu đã an toàn.", foreground="green")

    def update_game_combobox_list():
        """Cập nhật Dropdown Game từ cả 2 nguồn: Config Option và Config Theme."""
        global g_game_themes, current_config_data
        
        # 1. Lấy game từ các Option hiện có
        games = set()
        if current_config_data:
            for v in current_config_data.values():
                if isinstance(v, dict) and "game" in v: 
                    games.add(v["game"])

        # 2. [FIX QUAN TRỌNG] Gộp thêm game từ danh sách Theme (g_game_themes)
        # Đây là phần bị thiếu khiến danh sách của bạn bị ngắn
        if 'g_game_themes' in globals() and g_game_themes:
            games.update(g_game_themes.keys())

        # 3. Sắp xếp và cập nhật vào Widget
        sorted_games = sorted(list(games))
        
        if "Game:" in form_widgets:
            form_widgets["Game:"].config(values=sorted_games)
            
            # Nếu danh sách không rỗng và chưa chọn gì, chọn cái đầu tiên hoặc giữ nguyên
            current_val = form_widgets["Game:"].get()
            if not current_val and sorted_games:
                # form_widgets["Game:"].current(0) # Tùy chọn: Tự động chọn cái đầu
                pass

    # --- Hàm Helper tạo Input Group ---
    def create_modern_input(parent, label_text, widget_key, widget_type="Entry", options=None, height=1):
        frame = ttk.Frame(parent, padding=(10, 5))
        frame.pack(fill=tk.X)
        
        ttk.Label(frame, text=label_text, style="secondary.TLabel").pack(anchor=tk.W)
        
        widget = None
        if widget_type == "Entry":
            widget = ttk.Entry(frame)
        elif widget_type == "Combobox":
            widget = ttk.Combobox(frame, values=options, state="readonly")
            if options: widget.set(options[0])
        elif widget_type == "Text":
            widget = tk.Text(frame, height=height, wrap="word", relief=tk.FLAT, bg="#2b2b2b", fg="white", insertbackground="white", padx=5, pady=5)
            # Viền giả
            border_frame = ttk.Frame(frame, style="Card.TFrame") # Giả sử có style Card
            widget.pack(fill=tk.X, pady=2)
            
        if widget_type != "Text":
            widget.pack(fill=tk.X, pady=2)
            
        form_widgets[widget_key] = widget
        return frame, widget

    # --- NHÓM 1: THÔNG TIN CƠ BẢN (Card Layout) ---
    basic_info_frame = ttk.LabelFrame(edit_form_frame, text="📁 Thông tin File & Nguồn", padding=10)
    basic_info_frame.pack(fill=tk.X, padx=10, pady=5)

    # Hàng 1: URLS (Thay thế Entry bằng Text để nhập nhiều dòng)
    url_container = ttk.Frame(basic_info_frame)
    url_container.pack(fill=tk.X, pady=5)
    
    # Label hướng dẫn
    ttk.Label(url_container, text="URLs (Mỗi dòng 1 link - Ưu tiên link Drive/Gdown):", style="secondary.TLabel").pack(anchor=tk.W)
    
    # Khung chứa Text + Scrollbar
    text_frame = ttk.Frame(url_container)
    text_frame.pack(fill=tk.X, pady=2)
    
    url_scrollbar = ttk.Scrollbar(text_frame, orient="vertical")
    url_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Widget Text nhập nhiều dòng
    url_text_widget = tk.Text(text_frame, height=4, wrap="none", 
                              relief=tk.FLAT, bg="#2b2b2b", fg="white", 
                              insertbackground="white", padx=5, pady=5,
                              yscrollcommand=url_scrollbar.set)
    url_text_widget.pack(side=tk.LEFT, fill=tk.X, expand=True)
    url_scrollbar.config(command=url_text_widget.yview)
    
    # Lưu vào dict widget để dùng sau
    form_widgets["URL:"] = url_text_widget

    # Các nút công cụ (Paste / Chọn từ Drive)
    btn_row = ttk.Frame(url_container)
    btn_row.pack(fill=tk.X, pady=2)
    
    

    # --- GIỮ NGUYÊN HÀM NÀY ---
    def configure_gemini():
        """Thiết lập Gemini API"""
        if GEMINI_API_KEY and "DIEN_API_KEY" not in GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            return True
        return False

    # --- GIỮ NGUYÊN HÀM NÀY ---    
    def find_game_image_url_online(game_name):
        """
        (NÂNG CẤP) Tìm ảnh capsule nhỏ từ Steam Search (Tốt cho Sidebar).
        """
        try:
            # Bỏ qua các từ khóa gây nhiễu khi search
            clean_name = game_name.replace("Portable", "").replace("Repack", "").strip()
            
            import urllib.parse
            encoded_name = urllib.parse.quote(clean_name)
            search_url = f"https://store.steampowered.com/search/?term={encoded_name}"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            
            response = requests.get(search_url, headers=headers, timeout=3)
            if response.status_code == 200:
                html = response.text
                
                # Ưu tiên 1: Tìm ảnh capsule nhỏ (src="...capsule_sm_120.jpg")
                # Đây là ảnh hiện trong kết quả search, rất nhẹ và phù hợp làm icon
                match_small = re.search(r'src="([^"]+capsule_sm_120\.jpg[^"]*)"', html)
                if match_small:
                    return match_small.group(1)

                # Ưu tiên 2: Nếu không thấy, tìm App ID để suy ra ảnh Header
                match_id = re.search(r'data-ds-appid="(\d+)"', html)
                if match_id:
                    app_id = match_id.group(1)
                    return f"https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/header.jpg"
                    
        except Exception as e:
            print(f"Lỗi tìm ảnh '{game_name}': {e}")
        return None
    
    def analyze_filename_with_gemini(filename):
        """
        Gửi tên file cho Gemini để phân tích: Tên Game, Version, Nguồn, Password, VÀ FILE EXE.
        """
        if not configure_gemini():
            return None

        try:
            model = genai.GenerativeModel('gemini-2.5-flash')

            # Cập nhật Prompt: Yêu cầu đoán thêm "launch_file"
            prompt = f"""
            Analyze this filename carefully: "{filename}"

            You are an expert in game modification and installation.
            Your task is to deduce metadata, the likely extraction password, AND THE LIKELY LAUNCH EXECUTABLE (.exe).

            Rules:
            1. Password Deduction: 
            - "LinkNeverDie" -> "linkneverdie.com"
            - "khiphach" -> "khiphach.vn"
            - "daominhha" -> "daominhha.com"
            - "GOG" -> often empty or "gog.com"
            - Else -> empty.
            2. Launch File Deduction:
            - Based on the Game Name, predict the standard .exe file name.
            - Example: "Elden Ring" -> "eldenring.exe", "League of Legends" -> "LeagueClient.exe".
            - If unsure, guess based on the game title (e.g. "GameName.exe").

            Return ONLY a JSON object with these keys:
            {{
                "game_name": "Clean name of the game",
                "version": "The version string (e.g. v1.02)",
                "file_type": "zip, rar, or exe",
                "password": "The deduced password",
                "launch_file": "The predicted executable name (e.g. game.exe)"
            }}
            """

            response = model.generate_content(prompt)
            
            text_res = response.text.strip()
            if text_res.startswith("```"):
                text_res = text_res.replace("```json", "").replace("```", "")
            
            import json
            data = json.loads(text_res)
            return data

        except Exception as e:
            print(f"Lỗi Gemini: {e}")
            return None
    # --- SỬA LẠI PHẦN NÀY ---

    def apply_ui_update_from_thread(callback, *args):
        """Hàm helper để chuyển lệnh vẽ UI về luồng chính an toàn."""
        root.after(0, callback, *args)

    def _ui_update_gemini_results(ai_data, real_filename, file_id):
        """Hàm này CHẠY TRÊN LUỒNG CHÍNH để điền thông tin vào Form."""
        global g_game_themes, g_master_game_list
        
        try:
            # 1. Điền URL/ID (Đã sửa cho Widget Text)
            url_entry = form_widgets.get("URL:")
            if url_entry:
                url_entry.delete("1.0", tk.END) # Sửa 0 thành "1.0"
                url_entry.insert("1.0", file_id) # Sửa 0 thành "1.0"

            if not ai_data:
                custom_showwarning("Gemini Error", "Gemini không trả về kết quả hợp lệ.")
                return
            
            detected_game_name = ai_data.get("game_name")

            # --- LOGIC MỚI: TỰ ĐỘNG THÊM GAME NẾU THIẾU ---
            if detected_game_name:
                # Chuẩn hóa tên (bỏ khoảng trắng thừa)
                detected_game_name = detected_game_name.strip()
                
                # Lấy danh sách hiện tại
                combobox = form_widgets.get("Game:")
                current_games = list(combobox['values']) if combobox else []
                
                # Kiểm tra xem tên game đã có trong danh sách chưa (so sánh không phân biệt hoa thường)
                found = False
                best_match = ""
                
                # Tìm khớp tương đối
                for game in current_games:
                    if game == "Thêm Game...": continue
                    if detected_game_name.lower() == game.lower():
                        best_match = game
                        found = True
                        break
                
                # NẾU CHƯA CÓ -> TỰ ĐỘNG TÌM ẢNH VÀ THÊM VÀO
                if not found:
                    print(f"Game '{detected_game_name}' chưa có trong hệ thống. Đang tự động thêm...")
                    
                    # 1. Tìm URL ảnh
                    # Lưu ý: Hàm tìm ảnh nên chạy nhanh hoặc đã chạy ở thread trước. 
                    # Tuy nhiên để đơn giản ta gọi ở đây (sẽ làm UI khựng nhẹ 1s, chấp nhận được)
                    # Hoặc lý tưởng nhất là gọi nó trong process_smart_paste_background rồi truyền vào đây.
                    # Để an toàn cho UI, tôi sẽ dùng ảnh mặc định trước, rồi tìm ảnh sau nếu cần.
                    
                    # Cách tối ưu: Gọi tìm ảnh ngay tại đây (chấp nhận khựng xíu để có ảnh ngay)
                    new_image_url = find_game_image_url_online(detected_game_name)
                    
                    if new_image_url:
                        # 2. Thêm vào g_game_themes
                        g_game_themes[detected_game_name] = new_image_url
                        
                        # 3. Cập nhật danh sách tổng (g_master_game_list)
                        if 'g_master_game_list' in globals():
                            if detected_game_name not in g_master_game_list:
                                g_master_game_list.append(detected_game_name)
                                g_master_game_list.sort()
                        
                        # 4. Cập nhật Combobox
                        new_values = sorted(list(g_game_themes.keys())) + ["Thêm Game..."]
                        if combobox:
                            combobox['values'] = new_values
                            combobox.set(detected_game_name) # Chọn luôn game mới
                        
                        # 5. (Tùy chọn) Tự động Upload Theme lên GitHub để lưu lại
                        # threading.Thread(target=upload_theme_json_thread, args=(detected_game_name,), daemon=True).start()
                        print(f"Đã tự động thêm game mới: {detected_game_name}")
                        
                        best_match = detected_game_name
                    else:
                        # Nếu không tìm thấy ảnh, vẫn điền tên vào ô nhưng không thêm vào list chính thức
                        # để người dùng tự xử lý
                        if combobox: combobox.set(detected_game_name)
                
                else:
                    # Nếu đã có thì chọn luôn
                    if combobox: combobox.set(best_match)

            # --- CÁC PHẦN KHÁC GIỮ NGUYÊN ---

            # 3. Điền Tên Option
            opt_name = ai_data.get("game_name", "")
            if ai_data.get("version"):
                opt_name += f" {ai_data['version']}"
            
            entry_opt = form_widgets.get("Option Name:")
            if entry_opt:
                entry_opt.delete(0, tk.END)
                entry_opt.insert(0, opt_name)

            # 4. Điền Version
            entry_ver = form_widgets.get("Version:")
            if entry_ver:
                entry_ver.delete(0, tk.END)
                entry_ver.insert(0, ai_data.get("version", ""))

            # 5. Điền Loại File
            ext = ai_data.get("file_type", "zip").lower()
            combo_type = form_widgets.get("Type:")
            if combo_type:
                if "rar" in ext: combo_type.set("rar")
                elif "exe" in ext: combo_type.set("exe")
                else: combo_type.set("zip")

            # 6. Điền Mật Khẩu
            detected_pass = ai_data.get("password", "")
            entry_pass = form_widgets.get("Password:")
            if entry_pass:
                entry_pass.delete(0, tk.END)
                entry_pass.insert(0, detected_pass)

            # 7. Điền Launch File (File EXE)
            detected_launch = ai_data.get("launch_file", "")
            entry_launch = form_widgets.get("Launch File:")
            if entry_launch:
                entry_launch.delete(0, tk.END)
                entry_launch.insert(0, detected_launch)

            # 8. Thông báo
            msg = f"Gemini Xong!\nGame: {ai_data.get('game_name')}\nExe: {detected_launch}\nPass: {detected_pass}"
            custom_showinfo("Thành công", msg)

        except Exception as e:
            print(f"Lỗi khi update UI: {e}")

    def process_smart_paste_background(content):
        """
        Chạy ngầm: Chỉ gọi API, KHÔNG được chạm vào widget UI.
        """
        try:
            file_id = extract_gdrive_id_from_url(content)
            
            if not file_id:
                # Nếu lỗi, gửi lệnh về UI để hiện thông báo
                apply_ui_update_from_thread(lambda: custom_showwarning("Lỗi", "Không tìm thấy ID Google Drive hợp lệ."))
                return

            # Kiểm tra Drive Service
            global drive_service
            if not drive_service:
                apply_ui_update_from_thread(lambda: custom_showinfo("Yêu cầu", "Vui lòng Đăng nhập Drive ở Tab 3 để lấy tên file gốc."))
                return

            # 1. Lấy tên file gốc từ Drive (Mạng)
            try:
                file_meta = drive_service.files().get(
                    fileId=file_id,
                    fields='name, size, fileExtension'
                ).execute()
                
                real_filename = file_meta.get('name', 'Unknown')
                print(f"File gốc trên Drive: {real_filename}")
                
                # 2. Gọi GEMINI để phân tích (Mạng - Rất nặng)
                print(f"Đang gửi tên file cho Gemini phân tích: {real_filename}")
                
                ai_data = analyze_filename_with_gemini(real_filename)
                
                # 3. Đã có dữ liệu -> Gọi hàm vẽ UI trên luồng chính
                apply_ui_update_from_thread(_ui_update_gemini_results, ai_data, real_filename, file_id)

            except Exception as e:
                print(f"Lỗi Drive/Gemini: {e}")
                apply_ui_update_from_thread(lambda: custom_showerror("Lỗi API", f"Có lỗi khi gọi API: {e}"))

        except Exception as e:
            print(f"Lỗi chung: {e}")

    def action_smart_paste():
        """Hàm kích hoạt nút Paste (Đã sửa cho Widget Text)."""
        try:
            content = root.clipboard_get().strip()
        except:
            custom_showwarning("Lỗi", "Clipboard trống hoặc không đọc được.")
            return

        print("Đang bắt đầu xử lý Smart Paste...")
        
        # --- [SỬA LỖI] Dùng index "1.0" thay vì 0 ---
        if "URL:" in form_widgets:
            form_widgets["URL:"].delete("1.0", tk.END)
            form_widgets["URL:"].insert("1.0", "Đang xử lý AI...")

        # Chạy luồng ngầm
        threading.Thread(target=process_smart_paste_background, args=(content,), daemon=True).start()

    def open_drive_picker_modal():
        """Mở popup chọn file từ Drive (dùng dữ liệu cache từ Tab 3)."""
        if not hasattr(root, 'drive_icon_zip'): # Check nếu resource chưa load
             custom_showerror("Lỗi", "Vui lòng tải danh sách file ở Tab 3 trước.")
             return

        picker = tk.Toplevel(root)
        picker.title("Chọn File từ Drive")
        center_window_on_screen(picker, 500, 400)
        picker.transient(root)
        picker.grab_set()
        
        # Tiêu đề
        ttk.Label(picker, text="Click đúp vào file để chọn:", font=("Segoe UI", 10, "bold")).pack(pady=10)

        # Listbox
        list_frame = ttk.Frame(picker, padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        lb = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=("Segoe UI", 10))
        lb.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=lb.yview)

        file_map = {} # Map index -> file info

        def load_list():
            try:
                # Gọi API trực tiếp cho chắc ăn
                if not drive_service:
                    lb.insert(tk.END, "Lỗi: Chưa đăng nhập Drive (Tab 3).")
                    return

                files = drive_service.files().list(
                    q=f"'{GOOGLE_DRIVE_FOLDER_ID}' in parents and trashed = false",
                    fields='files(id, name)', orderBy='name').execute().get('files', [])
                
                for idx, f in enumerate(files):
                    lb.insert(tk.END, f"📄 {f['name']}")
                    file_map[idx] = f
            except Exception as e:
                lb.insert(tk.END, f"Lỗi tải: {e}")

        threading.Thread(target=load_list, daemon=True).start()

        def on_select(event=None):
            selection = lb.curselection()
            if not selection: return
            idx = selection[0]
            if idx in file_map:
                f = file_map[idx]
                
                # --- AUTO FILL LOGIC (ĐÃ SỬA LỖI) ---
                
                # 1. Fill ID vào ô Text Widget (Thông qua form_widgets)
                if "URL:" in form_widgets:
                    url_widget = form_widgets["URL:"]
                    url_widget.delete("1.0", tk.END)
                    url_widget.insert("1.0", f['id'])
                
                # 2. Fill Name (Auto Clean)
                if "Option Name:" in form_widgets:
                    clean_name = os.path.splitext(f['name'])[0] # Bỏ đuôi
                    clean_name = clean_name.replace("_", " ").replace("-", " ")
                    form_widgets["Option Name:"].delete(0, tk.END)
                    form_widgets["Option Name:"].insert(0, clean_name)
                
                # 3. Detect Type
                if "Type:" in form_widgets:
                    ext = os.path.splitext(f['name'])[1].lower()
                    if ".zip" in ext: form_widgets["Type:"].set("zip")
                    elif ".rar" in ext: form_widgets["Type:"].set("rar")
                    elif ".exe" in ext: form_widgets["Type:"].set("exe")
                
                picker.destroy()
                custom_showinfo("Auto-Fill", f"Đã điền thông tin từ file:\n{f['name']}")

        lb.bind("<Double-Button-1>", on_select)
        ttk.Button(picker, text="Chọn File Này", command=on_select, style="Accent.TButton").pack(pady=10)
    # (Giữ nguyên các nút chức năng cũ nhưng trỏ vào widget mới nếu cần)
    # ttk.Button(btn_row, text="📋 Paste", width=8, command=action_smart_paste).pack(side=tk.RIGHT, padx=2)
    btn_drive_picker = ttk.Button(btn_row, text="🔍 Chọn từ Drive", command=open_drive_picker_modal, style="Accent.TButton")
    btn_drive_picker.pack(side=tk.RIGHT, padx=2)
    # Hàng 2: Tên Option & Version
    row2 = ttk.Frame(basic_info_frame)
    row2.pack(fill=tk.X)
    
    # Tên Option (chiếm 70%)
    f_name, w_name = create_modern_input(row2, "Tên Hiển Thị (Option Name):", "Option Name:")
    f_name.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    # Version (chiếm 30%)
    f_ver, w_ver = create_modern_input(row2, "Version:", "Version:")
    f_ver.pack(side=tk.LEFT, fill=tk.X) # Không expand
    w_ver.config(width=10)

    # Hàng 3: Game & Type
    row3 = ttk.Frame(basic_info_frame)
    row3.pack(fill=tk.X)
    
    # --- Game Combobox (Kèm nút thêm nhanh) ---
    game_frame = ttk.Frame(row3, padding=(10, 5))
    game_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    ttk.Label(game_frame, text="Game:", style="secondary.TLabel").pack(anchor=tk.W)
    
    # Tạo một frame con để chứa Combobox và Nút nằm ngang hàng
    game_input_group = ttk.Frame(game_frame)
    game_input_group.pack(fill=tk.X, pady=2)

    global g_admin_game_combobox
    g_admin_game_combobox = ttk.Combobox(game_input_group, values=[], state="normal")
    g_admin_game_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    # Nút Thêm Game (+)
    btn_add_game_theme = ttk.Button(game_input_group, text="➕", width=3, 
                                  command=open_game_theme_manager, style="Accent.TButton")
    btn_add_game_theme.pack(side=tk.LEFT, padx=(5, 0))
    CreateToolTip(btn_add_game_theme, "Mở Quản lý Game (Thêm/Xóa tên Game trong danh sách)")

    # Bindings cho Combobox
    g_admin_game_combobox.bind("<<ComboboxSelected>>", lambda e: on_game_combobox_select(e))
    g_admin_game_combobox.bind("<KeyRelease>", lambda e: on_game_combobox_search(e))
    g_admin_game_combobox.bind("<FocusOut>", lambda e: on_game_combobox_validate(e))
    
    form_widgets["Game:"] = g_admin_game_combobox

    # --- Type Combobox ---
    f_type, w_type = create_modern_input(row3, "Loại File:", "Type:", "Combobox", options=["zip", "rar", "exe"])
    f_type.pack(side=tk.LEFT, padx=(5, 0))
    w_type.config(width=8)

    # --- NHÓM 2: CẤU HÌNH CÀI ĐẶT (Card Layout) ---
    install_config_frame = ttk.LabelFrame(edit_form_frame, text="⚙️ Cấu Hình Cài Đặt", padding=10)
    install_config_frame.pack(fill=tk.X, padx=10, pady=10)
    
    # Launch File & Password
    row4 = ttk.Frame(install_config_frame)
    row4.pack(fill=tk.X)
    
    f_launch, w_launch = create_modern_input(row4, "File Khởi Chạy (.exe):", "Launch File:")
    f_launch.pack(side=tk.LEFT, fill=tk.X, expand=True)
    CreateToolTip(w_launch, "Tên file exe game (vd: EldenRing.exe).\nDùng để kiểm tra và kích hoạt nút 'Chạy Game'.")

    f_pass, w_pass = create_modern_input(row4, "Mật khẩu giải nén (nếu có):", "Password:")
    f_pass.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))

    # Path Guide
    create_modern_input(install_config_frame, "Hướng dẫn (Hiện ở Tab 1):", "Path Guide:", "Text", height=2)

    # Delete List
    create_modern_input(install_config_frame, "Xóa file cũ trước khi cài (Mỗi dòng 1 file/folder):", "Delete List:", "Text", height=3)

    # --- ACTION BUTTONS ---
    action_btn_frame = ttk.Frame(edit_form_frame, padding=20)
    action_btn_frame.pack(fill=tk.X)

    add_update_button = ttk.Button(action_btn_frame, text="✅ Lưu / Cập Nhật Option", command=action_add_update_option, style="Accent.TButton")
    add_update_button.pack(side=tk.RIGHT, padx=5)
    
    delete_option_btn = ttk.Button(action_btn_frame, text="🗑️ Xóa Option", command=action_delete_option, style="Danger.TButton")
    delete_option_btn.pack(side=tk.RIGHT, padx=5)

    toggle_edit_form_state(False)

    # --- FOOTER: Status & Global Actions ---
    bottom_status_frame = ttk.Frame(second_tab_frame)
    bottom_status_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
    # Thanh trạng thái riêng cho Tab 2
    upload_status_label = ttk.Label(bottom_status_frame, text="Sẵn sàng.", anchor=tk.W)
    upload_status_label.pack(side=tk.BOTTOM, fill=tk.X, pady=5, padx=10)

    # Global Actions (Tải Config / Upload Config)
    # Tái sử dụng frame bottom_status_frame đã tạo ở ngoài
    global_actions_frame = ttk.Frame(bottom_status_frame)
    global_actions_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
    
    ttk.Button(global_actions_frame, text="☁️ Tải Config (GitHub)", command=action_load_from_github_wrapper).pack(side=tk.LEFT, padx=5)
    ttk.Button(global_actions_frame, text="💾 Upload Config (GitHub)", command=action_upload_to_github_wrapper, style="Accent.TButton").pack(side=tk.RIGHT, padx=5)
    
    # --- LOGIC GẮN KẾT TREEVIEW VÀ FORM (Giữ nguyên logic cũ nhưng cập nhật widget reference) ---
    def populate_treeview():
        options_treeview.delete(*options_treeview.get_children())
        if not current_config_data: return
        for key, data in current_config_data.items():
            if key == "updater": continue
            # Chỉ hiển thị ID, Tên, Game trong bảng
            options_treeview.insert("", tk.END, iid=key, values=(key, data.get("name", "??"), data.get("game", "Khác")))

    def on_treeview_select(event):
        """Điền dữ liệu vào Form Hiện Đại (Hỗ trợ Multi-URL)."""
        if current_config_data: 
             toggle_edit_form_state(True)
        selected_items = options_treeview.selection()
        if not selected_items:
            clear_form()
            return

        selected_key = selected_items[0]
        global g_currently_selected_id
        g_currently_selected_id = selected_key

        if selected_key in current_config_data:
            data = current_config_data[selected_key]
            
            # Cập nhật tiêu đề
            form_title_label.config(text=f"✏️ Đang sửa: {data.get('name')} (ID: {selected_key})")
            
            # Fill Basic Info
            form_widgets["Option Name:"].delete(0, tk.END)
            form_widgets["Option Name:"].insert(0, data.get("name") or "")

            # --- [CẬP NHẬT] URL Logic (Hỗ trợ List) ---
            url_widget = form_widgets["URL:"]
            url_widget.delete("1.0", tk.END) # Xóa nội dung cũ
            
            # 1. Kiểm tra list 'urls' trước
            urls_list = data.get("urls", [])
            
            # 2. Nếu không có list, kiểm tra single 'url' (backward compatibility)
            if not urls_list:
                single_url = data.get("url")
                if single_url:
                    urls_list = [single_url]
            
            # 3. Hiển thị lên Text widget (Mỗi link 1 dòng)
            if urls_list:
                # Xử lý prefix ID cũ nếu cần (tùy chọn, ở đây ta hiển thị full link cho dễ quản lý)
                display_text = "\n".join(urls_list)
                url_widget.insert("1.0", display_text)

            # ... (Các phần dưới giữ nguyên: Version, Game, Type...) ...
            form_widgets["Version:"].delete(0, tk.END)
            form_widgets["Version:"].insert(0, data.get("version") or "")
            
            form_widgets["Game:"].set("")
            form_widgets["Game:"].insert(0, data.get("game") or "Khác")
            
            form_widgets["Type:"].set(data.get("type", "zip"))
            
            form_widgets["Launch File:"].delete(0, tk.END)
            form_widgets["Launch File:"].insert(0, data.get("launch_file") or "")
            
            form_widgets["Password:"].delete(0, tk.END)
            form_widgets["Password:"].insert(0, data.get("password") or "")

            guide_widget = form_widgets["Path Guide:"]
            guide_widget.delete("1.0", tk.END)
            if data.get("path_guide"): guide_widget.insert("1.0", data.get("path_guide"))

            delete_list_widget = form_widgets["Delete List:"]
            delete_list_widget.delete("1.0", tk.END)
            delete_items = data.get("delete_before_extract", [])
            if delete_items: delete_list_widget.insert("1.0", "\n".join(delete_items))

    options_treeview.bind('<<TreeviewSelect>>', on_treeview_select)

    def clear_form():
        if "URL:" in form_widgets:
             form_widgets["URL:"].config(state="normal")
        if "Path Guide:" in form_widgets:
             form_widgets["Path Guide:"].config(state="normal")
        if "Delete List:" in form_widgets:
             form_widgets["Delete List:"].config(state="normal")
        global g_currently_selected_id
        g_currently_selected_id = None
        form_title_label.config(text="✨ Thêm Option Mới")
        
        # Xóa nội dung tất cả widget
        form_widgets["Option Name:"].delete(0, tk.END)
        
        # [CẬP NHẬT] Xóa Text widget
        form_widgets["URL:"].delete("1.0", tk.END)
        
        form_widgets["Version:"].delete(0, tk.END)
        form_widgets["Game:"].set("") 
        form_widgets["Type:"].set("zip")
        form_widgets["Launch File:"].delete(0, tk.END)
        form_widgets["Password:"].delete(0, tk.END)
        form_widgets["Path Guide:"].delete("1.0", tk.END)
        form_widgets["Delete List:"].delete("1.0", tk.END)
        
        if options_treeview.selection():
            options_treeview.selection_remove(options_treeview.selection())

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

    def update_user_ui_on_main_thread(name, email, avatar_bytes):
        """
        Cập nhật giao diện Titlebar.
        - Khi Login: Hiện Avatar + Tên.
        - Khi Logout: Reset về nút Đăng nhập mà KHÔNG TẮT APP.
        """
        global g_titlebar_google_frame, drive_service
        
        # Màu sắc
        BG_TITLEBAR = "#1c1c1c"
        BG_HOVER = "#333333"
        FG_TEXT = "#ffffff"
        
        # 1. Cập nhật Tab 3 (Trạng thái đã kết nối)
        if 'drive_auth_button' in globals():
            drive_auth_button.config(text="Đã kết nối Drive", style="Green.TButton")
            
        # 2. Cập nhật Title Bar
        if g_titlebar_google_frame:
            # Xóa hết nội dung cũ (Nút đăng nhập hoặc Avatar cũ)
            for widget in g_titlebar_google_frame.winfo_children():
                widget.destroy()
            
            # --- TẠO KHUNG PROFILE ---
            profile_frame = tk.Frame(g_titlebar_google_frame, bg=BG_TITLEBAR, cursor="hand2", padx=10, pady=2)
            profile_frame.pack(fill=tk.Y, side=tk.RIGHT)

            # Avatar
            if avatar_bytes:
                avatar_tk = make_circle_avatar(avatar_bytes, size=(24, 24))
                root.cached_images["auto_user_avatar"] = avatar_tk 
                lbl_avt = tk.Label(profile_frame, image=avatar_tk, bg=BG_TITLEBAR, bd=0)
                lbl_avt.pack(side=tk.LEFT, padx=(0, 8))
            else:
                lbl_avt = tk.Label(profile_frame, text="👤", bg=BG_TITLEBAR, fg=FG_TEXT, font=("Segoe UI", 12))
                lbl_avt.pack(side=tk.LEFT, padx=(0, 8))

            # Tên User
            lbl_name = tk.Label(profile_frame, text=name, bg=BG_TITLEBAR, fg=FG_TEXT, font=("Segoe UI", 9))
            lbl_name.pack(side=tk.LEFT)

            # --- LOGIC ĐĂNG XUẤT MỚI (KHÔNG TẮT APP) ---
            def perform_logout():
                # 1. Xóa file token
                token_path = resource_path('token.json')
                if os.path.exists(token_path):
                    try: os.remove(token_path)
                    except: pass
                
                # 2. Reset biến toàn cục
                drive_service = None
                
                # 3. Reset giao diện Tab 3
                if 'drive_auth_button' in globals():
                    drive_auth_button.config(text="Đăng nhập Google Drive", state=tk.NORMAL, style="Accent.TButton")
                if 'upload_files_button' in globals():
                    upload_files_button.config(state=tk.DISABLED)
                    
                # 4. Reset Title Bar (Vẽ lại nút Đăng Nhập)
                if g_titlebar_google_frame:
                    # Xóa Avatar hiện tại
                    for widget in g_titlebar_google_frame.winfo_children():
                        widget.destroy()
                    
                    # Tạo lại nút Đăng Nhập (Code copy từ setup_custom_titlebar)
                    btn_login = tk.Button(
                        g_titlebar_google_frame,
                        text=" Đăng nhập ", 
                        bg="#4285F4", fg="white",
                        font=("Segoe UI", 9, "bold"), bd=0,
                        cursor="hand2", command=action_drive_login, # Gọi lại hàm login
                        relief="flat"
                    )
                    btn_login.pack(ipady=4, pady=4)
                    
                    # Hiệu ứng hover cho nút mới
                    btn_login.bind("<Enter>", lambda e: btn_login.config(bg="#357ae8"))
                    btn_login.bind("<Leave>", lambda e: btn_login.config(bg="#4285F4"))

                custom_showinfo("Đăng xuất", "Đã đăng xuất thành công.")

            # --- MENU POPUP ---
            def show_user_menu(e):
                menu = tk.Menu(root, tearoff=0)
                menu.add_command(label=f"📧 {email}", state=tk.DISABLED)
                menu.add_separator()
                menu.add_command(label="Đăng xuất", command=perform_logout) # Gọi hàm logout mới
                
                x = profile_frame.winfo_rootx()
                y = profile_frame.winfo_rooty() + profile_frame.winfo_height()
                menu.post(x, y)

            # --- HIỆU ỨNG HOVER ---
            def on_enter(e):
                profile_frame.config(bg=BG_HOVER)
                lbl_avt.config(bg=BG_HOVER)
                lbl_name.config(bg=BG_HOVER)

            def on_leave(e):
                profile_frame.config(bg=BG_TITLEBAR)
                lbl_avt.config(bg=BG_TITLEBAR)
                lbl_name.config(bg=BG_TITLEBAR)

            for widget in [profile_frame, lbl_avt, lbl_name]:
                widget.bind("<Button-1>", show_user_menu)
                widget.bind("<Enter>", on_enter)
                widget.bind("<Leave>", on_leave)

    def try_auto_login_drive_thread():
        """(Chạy ngầm) Tự động đăng nhập, lấy User Info và cập nhật UI."""
        global drive_service
        
        token_path = resource_path('token.json')
        creds_path = resource_path('credentials.json')
        
        # Kiểm tra file tồn tại
        if not os.path.exists(creds_path) or not os.path.exists(token_path): 
            return 
        
        try:
            print("Auto-Login: Đang kiểm tra token...")
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            
            # Làm mới token nếu hết hạn
            if not creds.valid and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            
            if creds.valid:
                # 1. Khởi tạo Drive Service
                drive_service = build('drive', 'v3', credentials=creds)
                print("Auto-Login: Drive Service OK.")
                
                # 2. Lấy thông tin User (Profile & Avatar)
                try:
                    user_service = build('oauth2', 'v2', credentials=creds)
                    user_info = user_service.userinfo().get().execute()
                    
                    name = user_info.get('name', 'User')
                    email = user_info.get('email', '')
                    pic_url = user_info.get('picture', '')
                    
                    # Tải ảnh avatar (nếu có URL)
                    avatar_data = None
                    if pic_url:
                        try:
                            res = requests.get(pic_url, timeout=5)
                            if res.status_code == 200:
                                avatar_data = res.content
                        except: pass
                    
                    # 3. Cập nhật UI (Chuyển về luồng chính để an toàn)
                    # Dùng root.after để đảm bảo thread safe
                    root.after(0, lambda: update_user_ui_on_main_thread(name, email, avatar_data))
                    
                except Exception as e:
                    print(f"Auto-Login Warning: Không thể lấy info user ({e})")

                # 4. Tiếp tục các công việc tải dữ liệu khác
                root.after(0, action_refresh_drive_list) # Refresh list file ở Tab 3
                load_accounts_from_drive_thread() # Tải account game
                
            else:
                print("Auto-Login: Token không hợp lệ.")
                
        except Exception as e:
            print(f"Auto-Login Error: {e}")

    def action_drive_login():
        """Đăng nhập và gọi hàm update UI chuẩn để đồng bộ giao diện."""
        global drive_service
        
        # Cập nhật trạng thái nút
        if 'drive_auth_button' in globals():
            drive_auth_button.config(text="Đang kết nối Google...", state=tk.DISABLED)
        root.update_idletasks()
        
        # 1. Xác thực
        service = authenticate_google_drive() 
        
        if service:
            print("Đăng nhập thành công.")
            
            # Cập nhật Tab 3
            if 'drive_auth_button' in globals():
                drive_auth_button.config(text="Đã kết nối Drive", style="Green.TButton")
            if files_to_upload_list and 'upload_files_button' in globals():
                upload_files_button.config(state=tk.NORMAL)
            
            action_refresh_drive_list()

            # 2. Lấy thông tin User
            try:
                token_path = resource_path('token.json')
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)
                user_service = build('oauth2', 'v2', credentials=creds)
                user_info = user_service.userinfo().get().execute()
                
                name = user_info.get('name', 'User')
                email = user_info.get('email', '')
                pic_url = user_info.get('picture', '')

                # Tải ảnh avatar thành dạng bytes
                avatar_data = None
                if pic_url:
                    try:
                        res = requests.get(pic_url, timeout=5)
                        if res.status_code == 200:
                            avatar_data = res.content
                    except Exception as e:
                        print(f"Lỗi tải avatar: {e}")

                # 3. [QUAN TRỌNG] GỌI HÀM UPDATE UI CHUẨN (Thay vì tự vẽ)
                # Hàm này đã được chỉnh màu #1c1c1c nên sẽ đẹp ngay lập tức
                update_user_ui_on_main_thread(name, email, avatar_data)

            except Exception as e:
                print(f"Lỗi lấy info sau đăng nhập: {e}")
                # Nếu lỗi vẫn cập nhật UI mặc định
                update_user_ui_on_main_thread("User", "", None)

        else:
            if 'drive_auth_button' in globals():
                drive_auth_button.config(text="Đăng nhập Google Drive", state=tk.NORMAL)

    def show_login_selector_popup():
        """Hiển thị popup chọn phương thức đăng nhập."""
        popup = tk.Toplevel(root)
        popup.title("Đăng Nhập")
        
        # Kích thước & Căn giữa
        w, h = 350, 200
        center_window_on_screen(popup, w, h)
        popup.transient(root)
        popup.grab_set() # Chặn tương tác với cửa sổ chính
        
        # Áp dụng theme cho titlebar (nếu có)
        popup.after(10, lambda: apply_theme_to_titlebar(popup))

        # UI Content
        frame = ttk.Frame(popup, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Chọn tài khoản để tiếp tục:", font=("Segoe UI", 11)).pack(pady=(0, 20))
        
        # --- NÚT 1: GOOGLE DRIVE ---
        def on_google_click():
            popup.destroy() # Đóng popup trước
            action_drive_login() # Gọi hàm đăng nhập gốc (Tab 3)
            
        btn_google = ttk.Button(
            frame, 
            text="Google", 
            command=on_google_click, 
            style="Accent.TButton" # Nút xanh nổi bật
        )
        btn_google.pack(fill=tk.X, ipady=5, pady=5)
        
        # --- NÚT 2: (VÍ DỤ) API KEY RIÊNG ---
        # (Bạn có thể thêm nút nhập API Key thủ công ở đây sau này)
        # btn_apikey = ttk.Button(frame, text="🔑  Sử dụng API Key riêng", ...)
        # btn_apikey.pack(fill=tk.X, ipady=5, pady=5)

        # Nút Đóng
        ttk.Button(frame, text="Hủy bỏ", command=popup.destroy).pack(fill=tk.X, pady=(10, 0))

    # [QUAN TRỌNG] Gán hàm này vào biến toàn cục để Title Bar gọi được
    g_show_login_selector = show_login_selector_popup

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

    def action_browse_secret_zip(): # Đổi tên hàm cho đúng nghĩa
        """Thay thế kéo thả cho Secret Uploader (Chế độ ZIP)."""
        file_path = filedialog.askopenfilename(
            title="Chọn file Update đã nén (.zip)",
            filetypes=[("Zip Files", "*.zip")]
        )
        
        if file_path:
            secret_drop_listbox.delete(0, tk.END)
            secret_drop_listbox.insert(tk.END, file_path)

    def open_secret_uploader():
        """Mở cửa sổ upload bí mật (Giao diện mới cho --onedir)."""
        global secret_drop_listbox, secret_zip_id_entry, secret_window

        secret_window = tk.Toplevel(root)
        secret_window.title("Secret Updater (Onedir Mode)")
        secret_window.after(10, lambda: apply_theme_to_titlebar(secret_window))
        center_window_on_screen(secret_window, 500, 300)
        secret_window.transient(root)
        secret_window.grab_set()

        main_frame = ttk.Frame(secret_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Khung kéo thả
        drop_frame = ttk.LabelFrame(main_frame, text="1. Kéo file Update (.zip) vào đây")
        drop_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Nút chọn file
        ttk.Button(drop_frame, text="📂 Chọn File .zip", command=action_browse_secret_zip).pack(fill=tk.X, padx=5, pady=5)
        
        secret_drop_listbox = tk.Listbox(drop_frame, height=3)
        secret_drop_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        secret_drop_listbox.drop_target_register(DND_FILES)
        secret_drop_listbox.dnd_bind('<<Drop>>', handle_secret_drop)

        # 2. Khung config (Chỉ cần 1 ID)
        config_frame = ttk.LabelFrame(main_frame, text="2. Cấu hình Link Drive")
        config_frame.pack(fill=tk.X, pady=5)

        row2 = ttk.Frame(config_frame)
        row2.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(row2, text="File ID bản Update (.zip):", width=22).pack(side=tk.LEFT)

        secret_zip_id_entry = ttk.Entry(row2)
        secret_zip_id_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        # Load ID cũ từ config (nếu có)
        secret_zip_id_entry.insert(0, local_config.get("secret_zip_id", ""))

        # 3. Nút bắt đầu
        start_button = ttk.Button(main_frame, text="🚀 Upload Ngay", 
                                command=start_secret_upload, style="Accent.TButton")
        start_button.pack(pady=10)

    def handle_secret_drop(event):
        """Xử lý khi kéo file vào cửa sổ bí mật (Chỉ nhận .zip)."""
        secret_drop_listbox.delete(0, tk.END) # Chỉ cho phép 1 file
        raw_paths = root.tk.splitlist(event.data)

        if raw_paths:
            file_path = raw_paths[0] # Lấy file đầu tiên
            if os.path.exists(file_path) and os.path.isfile(file_path) and file_path.lower().endswith(".zip"):
                secret_drop_listbox.insert(tk.END, file_path)
            else:
                secret_drop_listbox.insert(tk.END, "Lỗi: Chỉ chấp nhận file .zip")

    def start_secret_upload():
        """Bắt đầu luồng upload bí mật."""
        global scan_loading_window # Tái sử dụng cửa sổ loading

        try:
            file_path = secret_drop_listbox.get(0)
        except tk.TclError:
            custom_showerror("Lỗi", "Chưa kéo file .zip vào.", parent=secret_window)
            return

        zip_id = secret_zip_id_entry.get().strip()

        # --- Lưu ID vào config ---
        global local_config
        local_config["secret_zip_id"] = zip_id
        save_local_config(local_config)

        if not file_path or not zip_id:
            custom_showerror("Lỗi", "Thiếu file hoặc File ID.", parent=secret_window)
            return

        if not file_path.lower().endswith(".zip"):
            custom_showerror("Lỗi", "File phải là .zip.", parent=secret_window)
            return

        # Hiển thị cửa sổ "Đang tải"
        scan_loading_window = tk.Toplevel(root)
        scan_loading_window.title("Đang Upload...")
        center_window_on_screen(scan_loading_window, 350, 100)
        scan_loading_window.transient(secret_window)
        scan_loading_window.grab_set()

        global secret_loading_label
        secret_loading_label = ttk.Label(scan_loading_window, text="Đang chuẩn bị...")
        secret_loading_label.pack(expand=True, padx=20, pady=20)

        # Chạy thread mới (gọn nhẹ hơn)
        threading.Thread(target=secret_upload_thread, 
                        args=(file_path, zip_id), 
                        daemon=True).start()

    def secret_upload_thread(file_path, zip_id):
        """(Chạy ngầm) Chỉ upload file .zip lên Drive."""
        try:
            # 1. Update file ZIP lên Drive
            progress_queue.put(("secret_status", f"Đang upload: {os.path.basename(file_path)}..."))
            
            # Gọi hàm helper có sẵn (nó sẽ tự xử lý Update hoặc Create nếu ID 404)
            _secret_update_file(file_path, zip_id)

            progress_queue.put(("secret_done", "Upload thành công!"))

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
    print("Đang kết nối Server Online...")
    threading.Thread(target=start_socket_service, daemon=True).start()
    root.after(1000, lambda: show_new_feature_banner(
        root, 
        "✨ TÍNH NĂNG MỚI: DỊCH GAME", 
        "Dịch trực tiếp mọi nội dung trên màn hình (Skill, Item, Cốt truyện) từ tiếng Anh sang tiếng Việt \n\nHãy mở tính năng này ở Cài Đặt & Credit.\n\n👉 Sau khi mở dùng phím tắt: Alt + ~ ", 
    ))
    root.mainloop()