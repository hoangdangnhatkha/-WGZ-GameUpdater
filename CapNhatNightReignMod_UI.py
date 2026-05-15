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
from PIL import Image, ImageTk, ImageDraw, ImageFont
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
from io import BytesIO
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
from PIL import Image, ImageTk, ImageGrab, ImageDraw, ImageOps
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
g_loaded_images = {}

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

def set_appwindow(root):
    """
    Hàm này ép cửa sổ Tkinter hiện dưới Taskbar khi dùng overrideredirect(True).
    """
    GWL_EXSTYLE = -20
    WS_EX_APPWINDOW = 0x00040000
    WS_EX_TOOLWINDOW = 0x00000080

    hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
    style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    
    # Thêm style AppWindow và xóa style ToolWindow
    style = style | WS_EX_APPWINDOW
    style = style & ~WS_EX_TOOLWINDOW
    
    ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
    
    # Cập nhật lại giao diện để Windows nhận thay đổi
    root.wm_withdraw()
    root.after(10, lambda: root.wm_deiconify())


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

def format_size(size_bytes):
    if not size_bytes:
        return "Unknown"
    # Chuyển đổi bytes sang B, KB, MB, GB
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def show_smart_download_confirm(parent, game_name, version, stats, is_space_ok, failed_links, on_confirm, on_cancel):
    """
    Popup xác nhận tải Modern UI - Có hiển thị danh sách Link lỗi.
    """
    popup = tk.Toplevel(parent)
    popup.title("Xác nhận tải xuống")
    
    # Tự động điều chỉnh độ cao nếu có link lỗi
    base_height = 470
    if failed_links and len(failed_links) > 0:
        base_height += 150 # Dài thêm để chứa khung lỗi
        
    popup.geometry(f"500x{base_height}") # Rộng hơn chút (450->500)
    popup.resizable(False, False)
    popup.configure(bg="#1e1e1e")
    
    # Căn giữa màn hình
    try:
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - 250
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (base_height // 2)
        popup.geometry(f"+{x}+{y}")
    except:
        popup.geometry("+300+300")

    # Khóa nút X
    popup.protocol("WM_DELETE_WINDOW", lambda: None) 

    # --- HEADER ---
    header_bg = "#c0392b" if not is_space_ok or failed_links else "#2d3436"
    header_frame = tk.Frame(popup, bg=header_bg, pady=15)
    header_frame.pack(fill="x")
    
    # Logic icon: Nếu thiếu chỗ hoặc có link lỗi thì hiện cảnh báo
    if not is_space_ok:
        icon_text = "⚠️" 
        title_text = "CẢNH BÁO DUNG LƯỢNG"
    elif failed_links:
        icon_text = "🔗"
        title_text = "LINK TẢI CÓ VẤN ĐỀ"
    else:
        icon_text = "☁️"
        title_text = "SẴN SÀNG TẢI XUỐNG"

    tk.Label(header_frame, text=icon_text, font=("Segoe UI Emoji", 30), bg=header_bg, fg="white").pack()
    tk.Label(header_frame, text=title_text, font=("Segoe UI", 12, "bold"), bg=header_bg, fg="white").pack(pady=(5,0))

    # --- BODY INFO ---
    body_frame = tk.Frame(popup, bg="#1e1e1e", padx=20, pady=10)
    body_frame.pack(fill="both", expand=True)

    tk.Label(body_frame, text=game_name, font=("Segoe UI", 14, "bold"), fg="#00cec9", bg="#1e1e1e").pack(pady=5)
    
    # --- [MỚI] KHUNG HIỂN THỊ LINK LỖI (NẾU CÓ) ---
    if failed_links:
        error_frame = tk.Frame(body_frame, bg="#2d3436", padx=10, pady=5)
        error_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(error_frame, text=f"⚠️ Có {len(failed_links)} link không thể kiểm tra (Có thể bị hỏng):", 
                 font=("Segoe UI", 9, "bold"), fg="#ff7675", bg="#2d3436").pack(anchor="w")
        
        # Textbox để hiện link (cho phép scroll và copy)
        txt_links = tk.Text(error_frame, height=4, font=("Consolas", 8), bg="#1e1e1e", fg="#fab1a0", bd=0)
        txt_links.pack(fill="x", pady=5)
        
        # Chèn link vào
        for link in failed_links:
            txt_links.insert("end", f"• {link}\n")
        
        # Khóa lại để không cho sửa, nhưng vẫn copy được
        txt_links.config(state="disabled")
    # ---------------------------------------------

    # --- BẢNG THÔNG SỐ ---
    stats_frame = tk.Frame(body_frame, bg="#2d3436", padx=10, pady=10)
    stats_frame.pack(fill="x", pady=5)
    
    def create_stat_row(p, label, value, color="white", row=0):
        tk.Label(p, text=label, font=("Segoe UI", 10), fg="#dfe6e9", bg="#2d3436").grid(row=row, column=0, sticky="w", pady=2)
        tk.Label(p, text=value, font=("Segoe UI", 10, "bold"), fg=color, bg="#2d3436").grid(row=row, column=1, sticky="e", pady=2)
        p.grid_columnconfigure(1, weight=1)

    create_stat_row(stats_frame, "📥 Tải về:", stats.get('down', 'Unknown'), "#0984e3", 0)
    create_stat_row(stats_frame, "📦 Giải nén (Est):", stats.get('extract', 'Unknown'), "#a29bfe", 1)
    
    tk.Frame(stats_frame, height=1, bg="#636e72").grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)
    
    total_color = "#e17055" if not is_space_ok else "#00b894"
    create_stat_row(stats_frame, "💾 Tổng cần thiết:", stats.get('total', 'Unknown'), total_color, 3)
    create_stat_row(stats_frame, "💿 Ổ cứng trống:", stats.get('free', 'Unknown'), "white", 4)

    # --- KẾT LUẬN ---
    conclusion_frame = tk.Frame(body_frame, bg="#1e1e1e", pady=5)
    conclusion_frame.pack(fill="x")

    if not is_space_ok:
        msg_text = "❌ KHÔNG ĐỦ DUNG LƯỢNG!"
        msg_color = "#ff7675"
    elif failed_links:
        msg_text = "⚠️ CẢNH BÁO: Link tải có thể bị lỗi!"
        msg_color = "#fab1a0" # Cam nhạt
    else:
        msg_text = "✅ ĐỦ DUNG LƯỢNG! An toàn để tải."
        msg_color = "#00b894"

    tk.Label(conclusion_frame, text=msg_text, font=("Segoe UI", 11, "bold"), fg=msg_color, bg="#1e1e1e").pack()

    # --- BUTTONS ---
    btn_frame = tk.Frame(popup, bg="#1e1e1e", pady=20)
    btn_frame.pack(side="bottom", fill="x")

    def on_click_cancel():
        popup.destroy()
        if on_cancel: on_cancel()

    def on_click_confirm():
        popup.destroy()
        if on_confirm: on_confirm()

    tk.Button(btn_frame, text="Hủy bỏ", font=("Segoe UI", 10), bg="#2d3436", fg="white", 
              bd=0, padx=20, pady=8, cursor="hand2", command=on_click_cancel).pack(side="left", padx=30)

    # Logic nút tải: Nếu có link lỗi, đổi màu nút tải thành màu Cam (Cảnh giác)
    if failed_links:
        confirm_text = "VẪN TẢI THỬ"
        confirm_bg = "#e67e22" # Màu cam
    elif not is_space_ok:
        confirm_text = "VẪN TẢI (Rủi ro)"
        confirm_bg = "#d63031" # Màu đỏ
    else:
        confirm_text = "TẢI NGAY 🚀"
        confirm_bg = "#0984e3" # Màu xanh
    
    tk.Button(btn_frame, text=confirm_text, font=("Segoe UI", 10, "bold"), bg=confirm_bg, fg="white", 
              bd=0, padx=30, pady=8, cursor="hand2", command=on_click_confirm).pack(side="right", padx=30)

    popup.transient(parent)
    popup.grab_set()


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
g_slideshow_job = None      # Để lưu ID của timer (dùng để hủy khi chuyển game)
g_slideshow_urls = [] 
g_pil_image_cache = {}
g_image_cache = {}      # Danh sách URL hiện tại
g_slideshow_index = 0       # Chỉ số ảnh đang hiệ
global g_mod_buttons
g_mod_buttons = {}
global g_current_selected_key
g_current_selected_key = None
CURRENT_VERSION = "1.4.3"
EXPECTED_UPDATER_HASH = "6F5E4FDB65D1BFFE174DE56908614C44EB5C87D5178AF1BEE99931B05140D79D"
GIF_URL = "https://media3.giphy.com/media/v1.Y2lkPTZjMDliOTUyNmQ4bGtzOW15aDhqcGYzbmx2bjVwdzBxMzNtcDB6aG9oZDBpejdpcyZlcD12MV9zdGlja2Vyc19zZWFyY2gmY3Q9cw/MZ7yrimhG3DThJqHjl/200w.gif"
ROCKET_GIF_URL = "https://media.tenor.com/ike6N7DwCa0AAAAM/%D8%B1%D9%8A%D8%A7%D9%84-%D9%85%D8%AF%D8%B1%D9%8A%D8%AF.gif"
DEFAULT_HERO_IMAGE = "https://c4.wallpaperflare.com/wallpaper/792/639/808/pattern-monochrome-dark-background-texture-wallpaper-preview.jpg"
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
    """
    (NÂNG CẤP) Trích xuất File ID từ mọi loại link Google Drive.
    Hỗ trợ:
    - .../uc?id=XXX
    - .../file/d/XXX/view
    - .../open?id=XXX
    """
    if not isinstance(url, str): return None
    
    # 1. Tìm theo pattern: id=XXX (cho link uc?, open?)
    match = re.search(r'[?&]id=([a-zA-Z0-9_-]+)', url)
    if match: return match.group(1)

    # 2. Tìm theo pattern: /d/XXX (cho link view, preview)
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
    if match: return match.group(1)

    # 3. Nếu người dùng nhập thẳng ID (không phải link)
    # Điều kiện: Không chứa tên miền, không chứa gạch chéo, độ dài > 20
    if "drive.google.com" not in url and "/" not in url and len(url) > 20:
        return url.strip()

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

def get_thumbnail_from_theme(theme_data):
    """
    Hàm bóc tách link ảnh từ dữ liệu theme (Dict hoặc String).
    """
    if not theme_data: return ""
    
    # 1. Nếu là Dictionary (Cấu trúc mới: {'slideshow': [...], 'image': ...})
    if isinstance(theme_data, dict):
        # Ưu tiên 1: Lấy key 'image' nếu có (ảnh đại diện riêng)
        if theme_data.get("image"):
            return theme_data["image"]
        
        # Ưu tiên 2: Lấy ảnh đầu tiên trong 'slideshow'
        slides = theme_data.get("slideshow")
        if slides and isinstance(slides, list) and len(slides) > 0:
            return slides[0]
            
    # 2. Nếu là String (Cấu trúc cũ: "http://...")
    elif isinstance(theme_data, str):
        print(theme_data)
        return theme_data
        
    return ""

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
    (HYBRID MODE) 
    1. Nếu đã đăng nhập: Tải bằng API (để lấy quyền ghi).
    2. Nếu CHƯA đăng nhập: Tải bằng 'requests' qua link công khai (Chỉ đọc).
    """
    global drive_service, g_user_accounts_data, g_user_accounts_file_id
    global g_accounts_loaded

    if g_accounts_loaded:
        progress_queue.put(("accounts_loaded", None))
        return

    # --- CÁCH 1: DÙNG API (NẾU ĐÃ ĐĂNG NHẬP) ---
    token_path = resource_path('token.json')
    if os.path.exists(token_path) and drive_service:
        try:
            print("Đã đăng nhập. Đang tải Account bằng API (Full Quyền)...")
            
            # Tìm file
            query = f"name = '{ACCOUNT_CONFIG_FILENAME}' and '{GOOGLE_DRIVE_FOLDER_ID}' in parents and trashed = false"
            response = drive_service.files().list(q=query, fields='files(id, name)').execute()
            files = response.get('files', [])
            
            if files:
                g_user_accounts_file_id = files[0]['id']
                # Tải nội dung
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)
                authed_session = AuthorizedSession(creds)
                download_url = f"https://www.googleapis.com/drive/v3/files/{g_user_accounts_file_id}?alt=media"
                response = authed_session.get(download_url)
                
                if response.status_code == 200:
                    g_user_accounts_data = json.loads(response.content.decode('utf-8'))
                    print("Tải API thành công.")
                    g_accounts_loaded = True
                    progress_queue.put(("accounts_loaded", None))
                    return
        except Exception as e:
            print(f"Lỗi API: {e}. Chuyển sang tải Public...")

    # --- CÁCH 2: DÙNG REQUESTS (CHẾ ĐỘ KHÁCH / PUBLIC) ---
    print("Chưa đăng nhập (hoặc lỗi). Đang tải chế độ Public (Read-Only)...")
    
    if PUBLIC_ACCOUNT_FILE_ID == "HÃY_DÁN_ID_FILE_JSON_VÀO_ĐÂY":
        print("Lỗi: Chưa cấu hình PUBLIC_ACCOUNT_FILE_ID trong code.")
        progress_queue.put(("accounts_load_failed", "Chưa cấu hình ID File Public"))
        return

    try:
        # Link tải trực tiếp từ Google Drive (không cần đăng nhập nếu file là Public)
        url = f"https://drive.google.com/uc?export=download&id={PUBLIC_ACCOUNT_FILE_ID}"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            try:
                g_user_accounts_data = response.json()
                # Lưu ID lại để dùng cho logic hiển thị, nhưng lưu ý là chưa có quyền ghi
                g_user_accounts_file_id = PUBLIC_ACCOUNT_FILE_ID 
                
                print("Tải Public thành công.")
                g_accounts_loaded = True
                progress_queue.put(("accounts_loaded", None))
            except json.JSONDecodeError:
                progress_queue.put(("accounts_load_failed", "File JSON lỗi"))
        else:
            print(f"Không thể tải file Public. Code: {response.status_code}")
            progress_queue.put(("accounts_load_failed", "Không tải được file"))

    except Exception as e:
        print(f"Lỗi tải Public: {e}")
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
PUBLIC_ACCOUNT_FILE_ID = "1LNEwzPoelziUIR9Nvum-zRQE3hku_q1l"
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
def get_remote_file_size(url):
    """
    Lấy kích thước file từ xa.
    Cải tiến: Sử dụng stream=True để follow redirect chính xác hơn.
    """
    global drive_service
    
    # 1. ƯU TIÊN: Google Drive API (Nếu có cấu hình)
    # Đây là cách DUY NHẤT chính xác 100% với file Google Drive > 100MB
    file_id = extract_gdrive_id_from_url(url)
    if file_id and 'drive_service' in globals() and drive_service:
        try:
            meta = drive_service.files().get(fileId=file_id, fields="size").execute()
            print(f"Lấy size từ Drive API: {meta.get('size')}")
            return int(meta.get('size', 0))
        except Exception as e:
            print(f"Drive API lỗi hoặc chưa login: {e}")

    # 2. DỰ PHÒNG: HTTP Request (Stream)
    try:
        # stream=True: Kết nối nhưng KHÔNG tải body -> Giống HEAD nhưng server ít chặn hơn
        # allow_redirects=True: Bắt buộc để xử lý link rút gọn hoặc link redirect Google
        with requests.get(url, stream=True, allow_redirects=True, timeout=5) as response:
            
            # Lấy Content-Length
            size = response.headers.get('Content-Length')
            
            # --- LOGIC XỬ LÝ GOOGLE DRIVE SCAN WARNING ---
            # Nếu là link Google Drive mà trả về "text/html", nghĩa là dính trang cảnh báo virus.
            # Lúc này size nhận được là size của trang web, không phải file.
            content_type = response.headers.get('Content-Type', '').lower()
            if "drive.google.com" in url and "text/html" in content_type:
                print("URL là trang cảnh báo virus Google Drive -> Không thể lấy size qua HTTP.")
                return 0
            # ---------------------------------------------

            if size:
                return int(size)
    except Exception as e:
        print(f"Lỗi lấy size qua HTTP: {e}")
        
    return 0

def download_and_extract_logic():
    """
    (FIX V7 - PRE-CHECK SIZE)
    Kiểm tra dung lượng file và dung lượng ổ cứng trước khi tải.
    """
    global local_config, g_current_game_name

    progress_queue.put(("status", "DISABLE_BUTTONS"))

    selected_key = selected_option.get()
    if selected_key not in g_all_mods_flat:
        progress_queue.put(("status", "Lỗi: Không tìm thấy thông tin mod."))
        progress_queue.put(("status", "ENABLE_BUTTONS"))
        return

    mod_data = g_all_mods_flat[selected_key]
    mod_display_name = mod_data.get("name", selected_key)
    option_label.configure(text="Đang xử lý: " + mod_display_name, style="White.TLabel")

    # Lấy danh sách URL
    url_list = mod_data.get("urls", [])
    if not url_list:
        single_url = mod_data.get("url")
        if single_url: url_list = [single_url]

    if not url_list:
        progress_queue.put(("download_complete", {"success": False, "title": "Lỗi Config", "message": "Không tìm thấy link tải."}))
        progress_queue.put(("status", "ENABLE_BUTTONS"))
        return

    version = mod_data.get("version", "")
    file_type = mod_data.get("type", "zip")
    password = mod_data.get("password", None)
    delete_list = mod_data.get("delete_before_extract", [])
    destination_folder = path_entry.get()

    # 1. Tạo folder đích
    if not os.path.exists(destination_folder):
        try: os.makedirs(destination_folder, exist_ok=True)
        except Exception as e:
            progress_queue.put(("download_complete", {"success": False, "title": "Lỗi", "message": f"Lỗi tạo folder: {e}"}))
            progress_queue.put(("status", "ENABLE_BUTTONS"))
            return

    # --- [MỚI] BƯỚC KIỂM TRA DUNG LƯỢNG (PRE-CHECK) ---
    progress_queue.put(("status", "Đang tính toán dung lượng..."))
    
    total_download_size = 0
    failed_url_list = []
    unknown_size_count = 0
    
    # Tính tổng dung lượng cần tải
    for url in url_list:
        size = get_remote_file_size(url)
        if size > 0:
            total_download_size += size
        else:
            failed_url_list.append(url)
            unknown_size_count += 1
            
    # Kiểm tra dung lượng trống ổ đĩa
    try:
        total_disk, used_disk, free_disk = shutil.disk_usage(destination_folder)
    except Exception as e:
        print(f"Lỗi check ổ đĩa: {e}")
        free_disk = 999999999999 # Bỏ qua nếu lỗi

    # --- TÍNH TOÁN DUNG LƯỢNG GIẢI NÉN (ƯỚC TÍNH) ---
    # Giả sử tỉ lệ nén trung bình là 1:2 (1GB tải về nở ra thành 2GB)
    # Tổng cần thiết = File Tải (1) + File Giải Nén (2) = 3 lần
    # Đây là mức "An toàn" để đảm bảo không bị đầy ổ giữa chừng.
    estimated_extract_size = (total_download_size * 1.2)
    total_required_space = total_download_size + estimated_extract_size

    stats_data = {
        "down": format_bytes(total_download_size),
        "extract": format_bytes(estimated_extract_size),
        "total": format_bytes(total_required_space),
        "free": format_bytes(free_disk)
    }
    
    if unknown_size_count > 0:
        stats_data["down"] += f" (+{unknown_size_count} file chưa rõ)"

    # Kiểm tra đủ chỗ không
    is_space_ok = True
    if total_download_size > 0 and free_disk < total_required_space:
        is_space_ok = False

    # --- [PHẦN SỬA ĐỔI QUAN TRỌNG: GỌI UI VÀ ĐỢI PHẢN HỒI] ---
    
    # 1. Tạo biến cờ để đồng bộ giữa Thread và UI
    download_event = threading.Event()
    user_decision = {"proceed": False}

    def on_ui_confirm():
        user_decision["proceed"] = True
        download_event.set()

    def on_ui_cancel():
        user_decision["proceed"] = False
        download_event.set()
        
        # --- [MỚI] LOGIC QUAY VỀ TRANG CHỦ TAB 1 ---
        # Chạy trên luồng chính UI để tránh lỗi thread
        def back_to_home():
            try:
                # 1. Chuyển về Tab đầu tiên (Index 0)
                # Giả sử tên biến Notebook của bạn là 'notebook' hoặc 'main_notebook'
                if 'notebook' in globals():
                    notebook.select(0)
                
                # 2. Gọi hàm quay lại danh sách (Mô phỏng bấm nút Back)
                # Nếu bạn có hàm 'on_back_click' hoặc 'show_mod_list', hãy gọi nó
                if 'on_back_click' in globals():
                    on_back_click()
                
                # Reset trạng thái nút (nếu đang bị disable)
                progress_queue.put(("status", "ENABLE_BUTTONS"))
                option_label.configure(text="Đã hủy tải xuống.", style="White.TLabel")
                
            except Exception as e:
                print(f"Lỗi khi quay về trang chủ: {e}")

        root.after(100, back_to_home)
        # ---------------------------------------------

    def trigger_ui_thread_safe():
        show_smart_download_confirm(
            parent=root,
            game_name=mod_display_name,
            version=version,
            stats=stats_data,
            is_space_ok=is_space_ok,
            failed_links=failed_url_list, 
            on_confirm=on_ui_confirm,
            on_cancel=on_ui_cancel
        )

    root.after(0, trigger_ui_thread_safe)

    # 5. [QUAN TRỌNG] Thread đứng lại ở đây chờ người dùng bấm nút
    # Code sẽ không chạy xuống dưới cho đến khi download_event.set() được gọi
    print("Đang chờ người dùng xác nhận...")
    download_event.wait() 

    # 6. Kiểm tra kết quả sau khi chờ
    if not user_decision["proceed"]:
        progress_queue.put(("status", "Đã hủy tải xuống."))
        progress_queue.put(("status", "ENABLE_BUTTONS"))
        progress_queue.put(("cancel_and_return_home", None))
        return

    # --- NẾU NGƯỜI DÙNG ĐỒNG Ý, TIẾP TỤC TẢI ---
    progress_queue.put(("status", f"Bắt đầu tải {mod_display_name}..."))

    # 2. Lưu config đường dẫn (Tiếp tục code cũ)
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

def action_refresh_data():
    """
    Smart Refresh: Chỉ tải lại Config Text, giữ nguyên ảnh cũ để tiết kiệm băng thông.
    """
    # Disable nút tạm thời để tránh bấm liên tục
    if 'btn_refresh_data' in globals() and btn_refresh_data.winfo_exists():
        btn_refresh_data.configure(state="disabled", text="⏳ Đang tải...")
        
    if 'status_label' in globals() and status_label.winfo_exists():
        status_label.configure(text="Đang đồng bộ dữ liệu mới...", style="White.TLabel")

    # Chạy luồng xử lý riêng
    threading.Thread(target=smart_refresh_thread, daemon=True).start()

def smart_refresh_thread():
    global config_data, g_all_mods_flat, g_loaded_images
    global GLOBAL_CONFIG_URL 
    
    # [FIX AN TOÀN] Nếu biến chưa tồn tại thì tạo mới để tránh crash
    if 'g_loaded_images' not in globals():
        g_loaded_images = {}

    try:
        print("[Smart Refresh] Bắt đầu tải JSON mới...")
        
        # --- 1. TÌM URL ---
        url = "https://raw.githubusercontent.com/hoangdangnhatkha/-WGZ-GameUpdater/refs/heads/main/CapNhatNightReignMod.json"
        if local_config and "config_url" in local_config:
            url = local_config["config_url"]
        if not url and 'GLOBAL_CONFIG_URL' in globals():
            url = GLOBAL_CONFIG_URL
        if not url:
            print("⚠️ Cảnh báo: Chưa tìm thấy URL. Đang dùng URL dự phòng...")
            url = "https://raw.githubusercontent.com/hoangdangnhatkha/-WGZ-GameUpdater/refs/heads/main/CapNhatNightReignMod.json"

        # --- 2. TẢI DATA ---
        import time
        anti_cache_url = f"{url}?t={int(time.time())}"
        
        print(f"Đang tải từ: {anti_cache_url}")
        response = requests.get(anti_cache_url, timeout=10)
        response.raise_for_status()
        config_data = response.json()
        
        # --- 3. TÁI TẠO DỮ LIỆU PHẲNG (PARSE ĐÚNG CẤU TRÚC JSON) ---
        temp_flat = {}
        for key, value in config_data.items():
            if key in ["updater", "themes", "motd"]: continue
            if isinstance(value, dict):
                temp_flat[key] = value
                
        g_all_mods_flat = temp_flat 
        print(f"[Smart Refresh] Tìm thấy {len(g_all_mods_flat)} mục game/mod.")

        # --- 4. KIỂM TRA ẢNH (Chỉ tải cái còn thiếu) ---
        print("[Smart Refresh] Đang kiểm tra ảnh mới...")
        
        for game_id, game_info in g_all_mods_flat.items():
            # Code cũ bị lỗi ở đây do g_loaded_images chưa có
            # Code mới đã an toàn nhờ dòng [FIX AN TOÀN] ở đầu hàm
            if game_id not in g_loaded_images:
                img_url = game_info.get("image_url", "") or game_info.get("image", "")

                if img_url:
                    try:
                        print(f"-> Tải ảnh mới cho ID {game_id}...")
                        res = requests.get(img_url, timeout=5)
                        img_bytes = io.BytesIO(res.content)
                        pil_img = Image.open(img_bytes)
                        pil_img = pil_img.resize((140, 200), Image.LANCZOS)
                        g_loaded_images[game_id] = ImageTk.PhotoImage(pil_img)
                    except Exception as e:
                        print(f"Lỗi tải ảnh {game_id}: {e}")
            else:
                pass # Đã có ảnh -> Bỏ qua để tiết kiệm

        print("[Smart Refresh] Hoàn tất. Đang vẽ lại UI...")
        root.after(0, finish_smart_refresh)

    except Exception as e:
        print(f"Lỗi Smart Refresh: {e}")
        import traceback
        traceback.print_exc()
        root.after(0, lambda: btn_refresh_data.configure(state="normal", text="🔄 Làm Mới Dữ Liệu"))
        
def finish_smart_refresh():
    """Hàm chạy trên UI Thread để vẽ lại Grid - ĐÃ SỬA LỖI SCROLL CHÍNH XÁC"""
    global g_all_mods_flat, download_options
    # Sử dụng biến g_steam_sidebar_frame có sẵn trong code của bạn
    global g_steam_sidebar_frame 
    
    try:
        print("[Refresh] Đang gom nhóm dữ liệu để vẽ lại...")

        # 1. GOM NHÓM DATA
        new_grouped_data = {}
        if g_all_mods_flat:
            for key, data in g_all_mods_flat.items():
                if key == "updater": continue
                game_name = data.get("game", "Khác")
                if game_name not in new_grouped_data:
                    new_grouped_data[game_name] = []
                new_grouped_data[game_name].append( (key, data) )
        
        download_options = new_grouped_data

        # 2. VẼ LẠI GIAO DIỆN
        if 'populate_page_1_grid' in globals():
            populate_page_1_grid(download_options)
        
        # --- [FIX LỖI SCROLL] ---
        # Lấy lại tiêu điểm vào vùng danh sách game
        try:
            # Code của bạn dùng g_steam_sidebar_frame nằm trong Canvas
            # Nên .master của nó chính là cái Canvas chúng ta cần focus
            if 'g_steam_sidebar_frame' in globals() and g_steam_sidebar_frame:
                canvas_widget = g_steam_sidebar_frame.master
                canvas_widget.focus_set()
                # Giả lập chuột đi vào để kích hoạt binding cuộn
                canvas_widget.event_generate("<Enter>") 
            else:
                # Dự phòng: Focus vào cửa sổ chính
                root.focus_set()
        except Exception as e:
            print(f"Lỗi set focus: {e}")
        # ------------------------

        if 'status_label' in globals() and status_label.winfo_exists():
            status_label.configure(text="Dữ liệu đã được cập nhật!", style="White.TLabel")
            
    except Exception as e:
        print(f"Lỗi vẽ UI: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if 'btn_refresh_data' in globals() and btn_refresh_data.winfo_exists():
            btn_refresh_data.configure(state="normal", text="🔄 Làm Mới Dữ Liệu")

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
        elif message_type == "cancel_and_return_home":
            print("Người dùng hủy tải. Quay về trang chủ...")
            
            # 1. Reset trạng thái các nút
            start_button.config(state=tk.NORMAL)
            browse_button.config(state=tk.NORMAL)
            
            # 2. Dọn dẹp giao diện Page 3 (để lần sau vào nó sạch sẽ)
            status_label.configure(text="Sẵn sàng.", style="White.TLabel")
            progress_bar['value'] = 0
            speed_label.config(text="")
            eta_label.config(text="")
            
            if 'overall_progress_bar' in globals():
                overall_progress_bar['value'] = 0
            if 'overall_status_label' in globals():
                overall_status_label.config(text="")
            if 'option_label' in globals():
                option_label.config(text="...")

            # 3. CHUYỂN VỀ PAGE 1 (LƯỚI GAME)
            show_page(page_1_game_grid)
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
                # if g_current_page == page_3_progress:
                #     show_page(page_2_mod_list)

                # # Xử lý nếu đang ở trang 1
                # elif not g_current_game_name: 
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
            # --- [FIX] RELOAD ICON TRONG MAIN THREAD ---
            # Ảnh tạo trong thread sẽ bị lỗi hiển thị, cần load lại trong luồng chính
            # (Lúc này ảnh đã có trong cache nên load sẽ rất nhanh)
            try:
                url_steam = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Steam_icon_logo.svg/512px-Steam_icon_logo.svg.png"
                url_riot = "https://static.wikia.nocookie.net/leagueoflegends/images/5/53/Riot_Games_logo_icon.png/revision/latest?cb=20220302144707"
                
                # Nạp lại icon Steam
                s_small = load_image_from_url(url_steam, size=(64, 64))
                if s_small: root.steam_icon_small = s_small
                
                s_tiny = load_image_from_url(url_steam, size=(24, 24))
                if s_tiny: root.steam_icon_tiny = s_tiny
                
                # Nạp lại icon Riot
                r_small = load_image_from_url(url_riot, size=(64, 64))
                if r_small: root.riot_icon_small = r_small
                
                r_tiny = load_image_from_url(url_riot, size=(24, 24))
                if r_tiny: root.riot_icon_tiny = r_tiny
                
                print("Đã nạp lại icon Steam/Riot trong Main Thread.")
            except Exception as e:
                print(f"Lỗi nạp lại icon: {e}")
            # -------------------------------------------

            g_images_preloaded = True
            print("Tất cả ảnh đã được tải trước. Đang hiển thị Lưới Game (Tab 1)...")
            mod_config_dict = message_value # Đây là g_all_mods_flat được truyền qua

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
            if 'g_theme_url_text' in globals() and g_theme_url_text.winfo_exists():
                g_theme_url_text.delete("1.0", tk.END)

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
    btn_max = create_sys_btn("◻", None) 
    
    # Chuyển trạng thái sang DISABLED và chỉnh màu xám tối để người dùng biết là bị khóa
    btn_max.config(state=tk.DISABLED, fg="#444444", cursor="arrow") 
    
    # QUAN TRỌNG: Gỡ bỏ sự kiện Hover (rê chuột) để nút không sáng lên
    btn_max.unbind("<Enter>")
    btn_max.unbind("<Leave>")

    # Nút Minimize (─)
    def minimize_win():
        root.overrideredirect(False) # Trả lại viền để Windows cho phép minimize
        root.iconify()
        
    def on_map(event):
        # Khi cửa sổ được mở lên lại (Map event)
        if event.widget == root_window and root_window.state() == 'normal':
            # Kiểm tra nếu cửa sổ đang có viền (do lúc minimize ta đã set False)
            if not root_window.overrideredirect():
                # 1. Xóa viền đi để trở lại giao diện Custom
                root_window.overrideredirect(True)
                
                # 2. [QUAN TRỌNG] Gọi hàm này để ép icon hiện lại dưới Taskbar
                # Nếu thiếu dòng này, app sẽ biến mất khỏi taskbar
                set_appwindow(root_window) 

    root_window.bind('<Map>', on_map)
    
    # --- ĐÂY LÀ DÒNG TẠO NÚT (BẠN ĐÃ BỊ THIẾU DÒNG NÀY) ---
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
def _run_webview_process(url, title):
    """
    Hàm này chạy trong một tiến trình riêng biệt (OS Process).
    Nó tạo cửa sổ trình duyệt để phát video.
    """
    # Cấu hình cửa sổ trailer
    webview.create_window(
        title, 
        url, 
        width=1024, 
        height=576, 
        resizable=True,
        confirm_close=True,
        text_select=False
    )
    # start() ở đây sẽ chặn tiến trình con này, nhưng không ảnh hưởng App chính
    webview.start()

def _convert_to_embed_url(url):
    """Chuyển link YouTube thường sang link Embed để nhẹ hơn"""
    if "youtube.com/watch?v=" in url:
        # Tách lấy ID video: v=dQw4w9WgXcQ
        try:
            video_id = url.split("v=")[1].split("&")[0]
            return f"https://www.youtube.com/embed/{video_id}?autoplay=1"
        except:
            return url
    elif "youtu.be/" in url:
        try:
            video_id = url.split("youtu.be/")[1].split("?")[0]
            return f"https://www.youtube.com/embed/{video_id}?autoplay=1"
        except:
            return url
    return url

class TrailerManager:
    def __init__(self):
        self.process = None

    def play(self, url, title="Game Trailer"):
        # 1. Nếu có trailer cũ đang chạy, tắt nó đi
        self.stop()
        
        # 2. Xử lý link
        embed_url = _convert_to_embed_url(url)
        if not embed_url: return

        # 3. Tạo tiến trình mới (Multiprocessing)
        self.process = multiprocessing.Process(
            target=_run_webview_process,
            args=(embed_url, title)
        )
        self.process.start()

    def stop(self):
        if self.process and self.process.is_alive():
            self.process.terminate()
            self.process.join() # Đợi tiến trình kết thúc hẳn
            self.process = None

def on_closing_app():
    try:
        # Tắt trailer nếu đang chạy
        if 'trailer_manager' in globals():
            trailer_manager.stop()
    except:
        pass
        
    # Gọi các logic tắt app cũ của bạn (nếu có)
    # Ví dụ: save_config() 
    
    root.destroy()
    sys.exit()
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
    print("Khởi tạo tài nguyên hình ảnh mặc định...")
    root.cached_game_icons_small = {}
    
    try:
        # Tạo một ảnh màu xám mặc định (Fallback image)
        # Kích thước 64x64 (hoặc tùy chỉnh)
        _img_temp = Image.new('RGB', (64, 64), color="#2d2d2d")
        _draw = ImageDraw.Draw(_img_temp)
        # Vẽ chữ giả nếu muốn
        # _draw.text((10, 20), "IMG", fill="gray") 
        root.default_game_icon_small = ImageTk.PhotoImage(_img_temp)
        
        # Tạo thêm các icon tiny nếu cần (để tránh lỗi AttributeError khác)
        root.steam_icon_tiny = root.default_game_icon_small 
        root.riot_icon_tiny = root.default_game_icon_small
    except Exception as e:
        print(f"Lỗi khởi tạo ảnh mặc định: {e}")
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
    app_height = 1000

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
    trailer_manager = TrailerManager()
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
        (ĐÃ SỬA: FIX LỖI MẤT ẢNH DO GARBAGE COLLECTION)
        """
        global g_acct_grid_container, g_acct_page_1_grid
        global g_game_themes, g_user_accounts_data 
        global g_acct_has_unsaved_changes 

        # Xóa loading frame nếu còn
        try:
            loading_frame = g_acct_page_1_grid.nametowidget("tab2_loading_frame")
            if loading_frame: loading_frame.destroy()
        except KeyError: pass
        
        if 'g_acct_login_prompt_label' in globals():
            try: g_acct_login_prompt_label.pack_forget()
            except: pass

        # --- KIỂM TRA QUYỀN GHI ---
        is_guest_mode = (drive_service is None)

        if 'g_acct_page_2_add_btn' in globals():
            if is_guest_mode:
                g_acct_page_2_add_btn.config(state=tk.DISABLED, text="Đăng nhập để Thêm")
            else:
                g_acct_page_2_add_btn.config(state=tk.NORMAL, text="➕ Thêm Account Mới")
        
        # --- [FIX LỖI NÚT LƯU] ---
        if 'g_acct_page_2_save_btn' in globals():
            if is_guest_mode:
                g_acct_page_2_save_btn.config(state=tk.DISABLED)
            else:
                if g_acct_has_unsaved_changes:
                    g_acct_page_2_save_btn.config(state=tk.NORMAL)
                else:
                    g_acct_page_2_save_btn.config(state=tk.DISABLED)
        # -------------------------

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

        # HIỂN THỊ THÔNG BÁO NẾU KHÔNG CÓ DỮ LIỆU
        if not g_user_accounts_data:
            msg_frame = ttk.Frame(g_acct_grid_container, padding=20)
            msg_frame.pack(fill=tk.BOTH, expand=True)
            
            error_msg = "Chưa tải được dữ liệu."
            if PUBLIC_ACCOUNT_FILE_ID == "HÃY_DÁN_ID_FILE_JSON_VÀO_ĐÂY":
                error_msg = "LỖI CODE: Bạn chưa điền 'PUBLIC_ACCOUNT_FILE_ID' trong mã nguồn."
            
            ttk.Label(msg_frame, text="⚠️ DANH SÁCH TRỐNG", font=("Segoe UI", 14, "bold"), foreground="#ffcc00").pack(pady=5)
            ttk.Label(msg_frame, text=error_msg, style="secondary.TLabel").pack(pady=5)
            ttk.Button(msg_frame, text="Thử tải lại", command=lambda: threading.Thread(target=load_accounts_from_drive_thread, daemon=True).start()).pack(pady=10)
            return

        # 3. Lấy danh sách game CÓ account
        user_accounts_data = g_user_accounts_data 
        game_names_with_accounts = sorted(user_accounts_data.keys())

        # 4. Vẽ lưới game
        MAX_COLS = 5    
        col = 0
        row = 0
        
        for game_name in game_names_with_accounts:
            icon_img = None 
            
            # Xử lý icon đặc biệt
            if game_name == "Steam":
                icon_img = root.steam_icon_small
            elif game_name == "Riot":
                icon_img = root.riot_icon_small
            
            # Nếu chưa có icon, tải từ Theme
            if not icon_img:
                # 1. Lấy dữ liệu thô
                raw_theme_data = g_game_themes.get(game_name)
                
                # 2. Dùng hàm bóc tách để lấy Link ảnh sạch (Fix lỗi Dict/List)
                image_url = get_thumbnail_from_theme(raw_theme_data)
                
                # 3. Tải ảnh
                if image_url:
                    try:
                        icon_img = load_image_from_url(image_url, size=(192, 89))
                    except Exception as e:
                        print(f"Lỗi tải ảnh {game_name}: {e}")
            
            # Fallback icon mặc định
            if not icon_img:
                icon_img = root.default_game_icon_small
            
            # --- VẼ CARD ---
            card_frame = ttk.Frame(g_acct_grid_container, style="Card.TFrame", cursor="hand2")
            card_frame.grid(row=row, column=col, padx=10, pady=10, sticky="ew")
            card_frame.columnconfigure(0, weight=1)

            # Hiển thị Ảnh
            if icon_img:
                img_label = ttk.Label(card_frame, image=icon_img, cursor="hand2")
                
                # [QUAN TRỌNG] GIỮ THAM CHIẾU ĐỂ KHÔNG MẤT ẢNH
                img_label.image = icon_img 
                
                img_label.grid(row=0, column=0, pady=(10, 5), padx=10)
            else:
                img_label = ttk.Label(card_frame, text="[No Image]", style="secondary.TLabel", cursor="hand2")
                img_label.grid(row=0, column=0, pady=(10, 5), padx=10)

            # Hiển thị Tên Game
            name_label = ttk.Label(card_frame, text=game_name, anchor=tk.CENTER, cursor="hand2", font=("Segoe UI", 10, "bold"))
            name_label.grid(row=1, column=0, pady=(0, 10), padx=10, sticky="ew")

            # Sự kiện Click
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
        (ĐÃ VIẾT LẠI & SỬA LỖI)
        1. Fix lỗi Crash do thiếu root.default_game_icon_small
        2. Fix lỗi mất ảnh thumbnail (Garbage Collection)
        """
        global g_user_accounts_data, g_acct_list_container, g_acct_current_game, g_dynamic_account_buttons
        
        g_acct_current_game = game_name 
        
        # Cập nhật tiêu đề frame (nếu biến g_acct_list_frame tồn tại)
        if 'g_acct_list_frame' in globals() and g_acct_list_frame:
            g_acct_list_frame.config(text=f"Accounts đã lưu cho: {game_name}")

        # Xóa widget cũ
        for widget in g_acct_list_container.winfo_children():
            widget.destroy()
            
        g_dynamic_account_buttons.clear()
        
        game_accounts = g_user_accounts_data.get(game_name, [])
        
        if not game_accounts:
            ttk.Label(g_acct_list_container, 
                    text="Không có tài khoản nào được lưu cho dịch vụ này.", 
                    style="secondary.TLabel").pack(pady=10)

        # --- LẤY ICON DỊCH VỤ ---
        service_icon_img = None 
        if g_acct_current_game == "Steam":
            service_icon_img = root.steam_icon_small
        elif g_acct_current_game == "Riot":
            service_icon_img = root.riot_icon_small
        else:
            service_icon_img = root.cached_game_icons_small.get(g_acct_current_game, root.default_game_icon_small)

        # --- Kiểm tra chế độ Guest ---
        is_guest_mode = (drive_service is None)
        state_for_edit = tk.DISABLED if is_guest_mode else tk.NORMAL

        widgets_to_bind = [g_acct_list_container]

        # --- Vẽ các Card mới ---
        for i, acc_info in enumerate(game_accounts):
            
            # 1. Tạo Card
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
            print(getattr(root, 'riot_icon_tiny', None))
            login_btn = ttk.Button(
                left_frame, 
                text="Đăng nhập", 
                image=btn_icon,    
                compound=tk.BOTTOM, # Ảnh nằm dưới chữ
                style="Accent.TButton",
                command=lambda index=i: action_login_by_index(index)
            )
            login_btn.pack(expand=True, fill=tk.BOTH)
            
            # [QUAN TRỌNG] Giữ tham chiếu ảnh cho nút này
            login_btn.image = btn_icon 
            
            g_dynamic_account_buttons.append(login_btn)
            widgets_to_bind.append(login_btn)

            # 3. Frame ở giữa (Thông tin)
            mid_frame = ttk.Frame(card)
            mid_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
            widgets_to_bind.append(mid_frame)

            nickname = acc_info.get('nickname', 'N/A')
            acc_type_str = acc_info.get('type', 'N/A').capitalize() # Đổi tên biến tránh trùng
            game_display_tag = acc_info.get('game', None) 
            
            # --- XỬ LÝ ẢNH THUMBNAIL ---
            icon_to_use = None
            if game_display_tag:
                # Ưu tiên lấy từ cache
                if game_display_tag in root.cached_game_icons_small:
                    icon_to_use = root.cached_game_icons_small[game_display_tag]
                else:
                    # Nếu chưa có, tải mới
                    raw_theme_data = g_game_themes.get(game_display_tag)
                    image_url = get_thumbnail_from_theme(raw_theme_data)
                    
                    if image_url:
                        try:
                            icon_to_use = load_image_from_url(image_url, size=(192, 89))
                        except Exception as e:
                            print(f"Lỗi tải ảnh {game_display_tag}: {e}")
            
            if not icon_to_use: 
                icon_to_use = service_icon_img

            if icon_to_use:
                img_label = ttk.Label(mid_frame, image=icon_to_use)
                
                # --- [FIX 2] QUAN TRỌNG: GIỮ THAM CHIẾU ẢNH ---
                img_label.image = icon_to_use 
                # ----------------------------------------------
                
                img_label.grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky=tk.W)
                widgets_to_bind.append(img_label)

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
            v3 = ttk.Label(mid_frame, text=acc_type_str)
            v3.grid(row=3, column=1, sticky=tk.W, padx=5)
            
            widgets_to_bind.extend([l1, v1, l2, v2, l3, v3])

            # 4. Frame bên phải (Nút Sửa/Xóa)
            right_frame = ttk.Frame(card)
            right_frame.pack(side=tk.RIGHT, fill=tk.Y)
            widgets_to_bind.append(right_frame)

            edit_btn = tk.Button(
                right_frame, 
                text="Sửa",
                width=10,         
                fg="white",                 
                activeforeground="white",   
                relief='groove',
                borderwidth=1,              
                highlightthickness=0,              
                cursor="hand2" if not is_guest_mode else "arrow", 
                state=state_for_edit, 
                command=lambda index=i: open_add_edit_account_popup(index)
            )
            edit_btn.pack(pady=(0, 5))
            
            delete_btn = tk.Button(
                right_frame, 
                text="Xóa", 
                width=10,
                bg="#c94e4e",               
                fg="white",                 
                activebackground="#a13e3e", 
                activeforeground="white",   
                relief='groove',              
                borderwidth=1,              
                highlightthickness=0,
                cursor="hand2" if not is_guest_mode else "arrow",             
                state=state_for_edit, 
                command=lambda index=i: delete_selected_account_by_index(index)
            )
            delete_btn.pack()
            
            g_dynamic_account_buttons.append(edit_btn)
            g_dynamic_account_buttons.append(delete_btn)
            widgets_to_bind.extend([edit_btn, delete_btn])

        # --- GẮN (BIND) SCROLL ---
        for widget in widgets_to_bind:
            try:
                widget.bind("<MouseWheel>", on_acct_list_mouse_wheel)
                widget.bind("<Button-4>", on_acct_list_mouse_wheel)
                widget.bind("<Button-5>", on_acct_list_mouse_wheel)
            except: pass
        
        # Đảm bảo canvas tồn tại trước khi bind
        if 'g_acct_list_canvas' in globals() and g_acct_list_canvas:
            g_acct_list_canvas.bind("<MouseWheel>", on_acct_list_mouse_wheel)
            g_acct_list_canvas.bind("<Button-4>", on_acct_list_mouse_wheel)
            g_acct_list_canvas.bind("<Button-5>", on_acct_list_mouse_wheel)

        # Chuyển trang (nếu hàm switch_account_page tồn tại)
        if 'switch_account_page' in globals() and 'g_acct_page_2_list' in globals():
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
    def load_image_from_url(url, size=(192, 89), only_cache=False):
        """
        [FIXED] Thêm Headers để tránh bị server chặn (Lỗi 403).
        Hiển thị chi tiết lỗi nếu tải thất bại.
        """
        global g_cache_dir
        
        # 1. Bóc tách link
        if isinstance(url, dict):
            url = get_thumbnail_from_theme(url)
            
        if not url or not isinstance(url, str):
            return None

        # 2. Tạo đường dẫn Cache
        try:
            import hashlib
            # Thêm size vào key để tránh lấy nhầm ảnh to/nhỏ
            cache_key = f"{url}_{size[0]}x{size[1]}" 
            hashed_name = hashlib.sha256(cache_key.encode('utf-8')).hexdigest() + ".png"
            
            if not os.path.exists(g_cache_dir):
                os.makedirs(g_cache_dir)
                
            local_path = os.path.join(g_cache_dir, hashed_name)

            # 3. ƯU TIÊN 1: LẤY TỪ CACHE Ổ CỨNG
            if os.path.exists(local_path):
                try:
                    img = Image.open(local_path)
                    return ImageTk.PhotoImage(img)
                except Exception as e:
                    print(f"Lỗi đọc cache {local_path}: {e}")
                    # Nếu file lỗi, xóa đi để tải lại
                    os.remove(local_path)

            # 4. ƯU TIÊN 2: TẢI TỪ INTERNET
            if url.startswith("http"):
                # [QUAN TRỌNG] Giả lập trình duyệt để không bị chặn
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                # Tải về
                response = requests.get(url, headers=headers, timeout=5)
                response.raise_for_status() # Nếu lỗi 403/404 sẽ nhảy xuống except
                
                img_data = response.content
                
                with Image.open(io.BytesIO(img_data)) as img:
                    # Resize (Dùng LANCZOS cho đẹp)
                    img_resized = img.resize(size, Image.Resampling.LANCZOS)
                    
                    # Lưu vào cache ngay lập tức
                    try:
                        # Chuyển mode về RGBA nếu cần để giữ trong suốt
                        if img_resized.mode != 'RGBA':
                            img_resized = img_resized.convert('RGBA')
                        img_resized.save(local_path, "PNG")
                    except Exception as save_err:
                        print(f"Không thể lưu cache: {save_err}")
                    
                    if only_cache:
                        return None
                    
                    return ImageTk.PhotoImage(img_resized)
                    
        except Exception as e:
            # [DEBUG] In ra lỗi để biết tại sao không hiện ảnh
            print(f"Lỗi tải ảnh ({url}): {e}")
            return None
            
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
        if 'custom_games' in local_config and game_name in local_config['custom_games']:
            custom_showwarning("Bảo Vệ", 
                f"'{game_name}' là game được thêm từ ngoài vào.\n"
                "Tool sẽ KHÔNG xóa file của game này để đảm bảo an toàn.\n\n"
                "Nếu bạn muốn bỏ nó khỏi Tool, hãy dùng nút 'Xóa khỏi List'.")
            return
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
