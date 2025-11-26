import tkinter as tk
import tkinter.font
import pyautogui
import threading
import numpy as np
import win32gui
import win32con
# Thêm ImageMath vào dòng import PIL
from PIL import Image, ImageTk, ImageOps, ImageFilter, ImageEnhance, ImageChops
from rapidocr_onnxruntime import RapidOCR
from groq import Groq
from pynput import mouse, keyboard as pynput_k
import ctypes
import os
import sys
import traceback # Thư viện để in chi tiết lỗi
import re
import google.generativeai as genai

try:
    # Giúp tool nhận diện đúng độ phân giải màn hình, cắt ảnh chuẩn xác hơn
    ctypes.windll.user32.SetProcessDPIAware()
except:
    pass
# --- CẤU HÌNH ---
try:
    from key_secrets import GROQ_API_KEYS, GEMINI_API_KEY
except ImportError:
    # Xử lý trường hợp người dùng tải về nhưng chưa tạo file key_secrets.py
    print("Cảnh báo: Không tìm thấy file 'key_secrets.py'.")
    print("Vui lòng tạo file này hoặc nhập Key thủ công.")
    # Đặt danh sách rỗng để không crash ngay lập tức
    GROQ_API_KEYS = []
    GEMINI_API_KEY = ""
     
HOTKEY = "<alt>+`"

# Khai báo biến toàn cục (Chưa khởi tạo vội để tránh lỗi khi import)
ocr_engine = None
client = None
current_key_index = 0
# --- PROMPT DỊCH ---
ROGUELIKE_PROMPT = """
[Nhiệm vụ: Dịch text game (từ OCR) sang Tiếng Việt theo ngữ cảnh RPG/Roguelike.

YÊU CẦU ĐẶC BIỆT (RICH TEXT):
- Hãy giữ nguyên các từ khóa quan trọng (Tên kỹ năng, Chỉ số, Hiệu ứng, Thuật Ngữ Game) ở dạng Tiếng Anh và BAO QUANH CHÚNG BẰNG DẤU SAO (*).
- Ví dụ: "Apply *Burn* to enemies" -> "Áp dụng *Thiêu đốt* lên kẻ địch".

QUY TẮC DỊCH:
1. Sửa lỗi chính tả OCR.
2. OUTPUT ONLY: Chỉ trả về kết quả dịch, TUYỆT ĐỐI KHÔNG GIẢI THÍCH HAY NÓI GÌ THÊM.
3. Văn phong: Tooltip game, súc tích.]
"""
# (VÍ DỤ:
# In: 
# "Fireba1l
# DeaI **5O0** **fire**
# damge."
# Out: 
# Fireball
# Gây *500* sát thương *Lửa*.)
def enforce_admin():
    """Tự động khởi động lại với quyền Admin"""
    try:
        if not ctypes.windll.shell32.IsUserAnAdmin():
            print("⚠️ Đang yêu cầu quyền Admin...")
            
            # Lấy đường dẫn tuyệt đối
            script_path = os.path.abspath(sys.argv[0])
            
            # Gọi UAC
            # Dùng sys.executable để đảm bảo chạy đúng môi trường Python hiện tại
            ret = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{script_path}"', None, 1
            )
            
            # Nếu người dùng bấm Yes hoặc đã chạy xong lệnh
            sys.exit() 
    except Exception as e:
        print(f"❌ Lỗi khi xin quyền: {e}")
        input("Bấm Enter để xem lỗi...")

def clean_translation_output(text):
    """Dọn dẹp các câu dẫn dắt thừa (Tiếng Anh & Tiếng Việt)"""
    patterns = [
        # Tiếng Anh
        r"^Here is.*?:", 
        r"^Translation:", 
        r"^Sure.*?:", 
        r"^Output:",
        
        # Tiếng Việt (Các câu nó hay nói nhảm)
        r"^Dưới đây là.*?:",
        r"^Đây là bản dịch.*?:",
        r"^Bản dịch.*?:",
        r"^Kết quả dịch.*?:",
        r"^Nội dung dịch.*?:",
        r"^Sau đây là.*?:",
        
        # Các trường hợp không có dấu hai chấm
        r"^Dưới đây là bản nội dung cần dịch",
        r"^Đây là kết quả",
    ]
    
    cleaned_text = text
    for pattern in patterns:
        # re.DOTALL để dấu chấm (.) ăn luôn cả xuống dòng nếu nó nói nhiều dòng
        cleaned_text = re.sub(pattern, "", cleaned_text, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)
        
    return cleaned_text.strip().strip('"').strip("'")

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
        print(f"Lỗi config Gemini: {e}")

def call_gemini_vision(image):
    """Gửi ảnh cho Gemini: Prompt ngăn chặn việc gộp dòng Tiêu đề vào Body"""
    if not gemini_model:
        return None
    try:
        system_prompt = """
        Bạn là Game Localizer chuyên nghiệp. Nhiệm vụ: Dịch text trong ảnh sang Tiếng Việt.
        
        QUY TẮC CẤU TRÚC (BẮT BUỘC TUÂN THỦ 100%):
        
        1. XỬ LÝ TIÊU ĐỀ (Dòng chữ to nhất/trên cùng):
           - Bắt buộc thêm dấu thăng (#) vào đầu dòng tiêu đề.
           - [TUYỆT ĐỐI CẤM] Không được viết nối nội dung mô tả vào ngay sau tiêu đề.
           - Sau tiêu đề PHẢI xuống dòng ngay lập tức.
           
           🚫 SAI: #Fireball Gây 500 sát thương lửa. (Gộp chung dòng -> CẤM)
           ✅ ĐÚNG: 
              #*Fireball*
              Gây *500* sát thương *Fire*. (Tách dòng riêng -> CHUẨN)

        2. GIỮ NGUYÊN THUẬT NGỮ (Hybrid):
           - Giữ nguyên tiếng Anh cho: Tên Skill, Item, Boss, Stats, Effect, Damage Type.
           - Bọc các từ tiếng Anh này trong dấu sao (*).
           
        3. NỘI DUNG:
           - Dịch phần mô tả sang tiếng Việt.
           - [QUAN TRỌNG] VIẾT LIỀN MẠCH, KHÔNG TỰ Ý XUỐNG DÒNG GIỮA CÂU.
           - Chỉ xuống dòng khi hết một đoạn văn hoặc bắt đầu một mục mới hoặc tiêu đề.
           - Giữ nguyên số lượng dòng của ảnh gốc.

        HÃY KIỂM TRA LẠI KẾT QUẢ TRƯỚC KHI TRẢ VỀ: LIỆU TIÊU ĐỀ ĐÃ NẰM RIÊNG 1 DÒNG CHƯA?
        """
        
        response = gemini_model.generate_content([system_prompt, image])
        print(f"Gemini Result: {response.text.strip()}")
        return response.text.strip()
    except Exception as e:
        print(f"❌ Lỗi Gemini: {e}")
        return None

def call_groq_with_rotation(prompt):
    global current_key_index
    
    # Thử tối đa số lần bằng số lượng key đang có
    max_attempts = len(GROQ_API_KEYS)
    
    for attempt in range(max_attempts):
        try:
            # 1. Lấy key hiện tại
            api_key = GROQ_API_KEYS[current_key_index]
            client = Groq(api_key=api_key)
            
            # 2. Gọi API
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                temperature=0.1,
            )
            # Nếu thành công -> Trả về kết quả ngay
            return chat_completion.choices[0].message.content.strip()

        except Exception as e:
            err_msg = str(e)
            # 3. Nếu gặp lỗi 429 (Rate Limit) -> Đổi Key
            if "429" in err_msg:
                print(f"⚠️ Key số {current_key_index + 1} bị giới hạn (429). Đang đổi key...")
                
                # Chuyển sang key tiếp theo (xoay vòng)
                current_key_index = (current_key_index + 1) % len(GROQ_API_KEYS)
                print(f"👉 Đã chuyển sang Key số {current_key_index + 1}")
                
                # Tiếp tục vòng lặp để thử key mới ngay lập tức
                continue
            else:
                # Nếu là lỗi khác (mạng, server sập) -> Ném lỗi ra ngoài luôn
                raise e
    
    raise Exception("Tất cả các Key đều đã hết hạn mức!")

class TooltipTranslator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.result_windows = []
        self.is_selecting = False
        self.listeners = []
        self.font_size = 11
        # Lắng nghe phím tắt (Global)
        with pynput_k.GlobalHotKeys({HOTKEY: self.start_selection}) as h:
            self.hotkey_listener = h
            threading.Thread(target=h.join, daemon=True).start()
            print(f"✅ Đã khởi động xong! Vào game và bấm Ctrl+Q để dịch.")
            self.root.mainloop()

    def start_selection(self):
        # LOGIC MỚI: Toggle (Bật/Tắt)
        
        # 1. Nếu đang trong chế độ chọn (is_selecting = True)
        # -> Bấm lần nữa sẽ HỦY chọn (Tắt overlay)
        if self.is_selecting: 
            print("🔄 Đã hủy chọn vùng (Toggle OFF).")
            # Gọi qua after để đảm bảo an toàn luồng UI
            self.root.after(0, self.close_selection)
            return
        
        # 2. Nếu chưa chọn -> Bắt đầu chế độ chọn
        print("📸 Bắt đầu chụp màn hình...")
        self.is_selecting = True 
        
        # Chỉ gửi tín hiệu để main thread mở overlay. 
        # KHÔNG chụp màn hình ở đây nữa (để hàm _show_overlay lo)
        self.root.after(0, self._show_overlay)

    def process_quality_path(self, image, label_widget, btn_widget):
        try:
            # Gọi API (Lúc này mới thực sự tốn tiền/token)
            translated = call_gemini_vision(image)
            
            if translated:
                print(f"Gemini Result: {translated}")
                
                # Cập nhật giao diện Text
                self.root.after(0, lambda: self.update_text_safe(label_widget, translated, "#00ff00", "✨ Gemini AI"))
                
                # Cập nhật lại cái nút báo thành công
                def update_button_done():
                    if btn_widget.winfo_exists():
                        btn_widget.config(text="✔ Hoàn tất", bg="#1c1c1c", fg="#00ff00", cursor="arrow")
                
                self.root.after(0, update_button_done)
                
        except Exception as e:
            print(f"Lỗi Quality Path: {e}")
            # Nếu lỗi thì báo lên nút
            self.root.after(0, lambda: btn_widget.config(text="❌ Lỗi", fg="red"))

    def update_text_safe(self, widget, text, color="white", status_text=""):
        try:
            widget.config(state=tk.NORMAL)
            widget.delete("1.0", tk.END)
            widget.config(fg=color)
            
            # --- [MỚI] CẬP NHẬT TRẠNG THÁI ---
            if hasattr(widget, 'status_label'):
                widget.status_label.config(text=status_text)
                # Nếu là màu xanh (Gemini hoàn tất), đổi màu status cho nổi
                if color == "#00ff00": 
                    widget.status_label.config(fg="#00ff00")
                else:
                    widget.status_label.config(fg="gray")
            # ---------------------------------

            # 1. Get the Fixed Window Dimensions
            top = widget.winfo_toplevel()
            target_height = top.winfo_height()
            
            # ... (GIỮ NGUYÊN ĐOẠN LOOP TÍNH FONT SIZE - KHÔNG ĐỔI GÌ Ở GIỮA) ...
            
            # Copy lại đoạn Loop 1 và Loop 2 từ code cũ của bạn vào đây
            # (Tôi rút gọn để dễ nhìn, bạn giữ nguyên logic tính font size cũ nhé)
            widget.pack_configure(fill='both', expand=True)
            start_size = getattr(self, 'font_size', 14)
            final_size = start_size
            text_pixel_height = 0
            
            for size in range(start_size, 7, -1):
                # ... (Code cũ của bạn về logic render text) ...
                # Chú ý: Đảm bảo bạn copy đủ logic render text vào đây
                body_font = ("Segoe UI", int(self.font_size * 0.95), "bold")
                title_font = ("Segoe UI", -int(self.font_size * 1.1), "bold")
                
                widget.tag_config("body_text", font=body_font)
                widget.tag_config("title_text", font=title_font, justify='center', spacing3=5)
                widget.tag_config("highlight_body", font=body_font, foreground="#FFD700") 
                widget.tag_config("highlight_title", font=title_font, foreground="#FFD700")

                widget.delete("1.0", tk.END)
                clean_text = clean_translation_output(text)
                lines = clean_text.split('\n')
                
                for line in lines:
                    is_title = line.strip().startswith('#')
                    if is_title: line = line.strip().lstrip('#').strip()
                    base_tag = "title_text" if is_title else "body_text"
                    high_tag = "highlight_title" if is_title else "highlight_body"
                    parts = line.split('*')
                    for i, part in enumerate(parts):
                        if i % 2 == 0: widget.insert(tk.END, part, base_tag)
                        else: widget.insert(tk.END, part, high_tag)
                    widget.insert(tk.END, "\n")
                
                widget.update_idletasks()
                bbox = widget.bbox("end-1c")
                if bbox:
                    current_text_height = bbox[1] + bbox[3]
                    if current_text_height <= target_height:
                        final_size = self.font_size
                        text_pixel_height = current_text_height
                        break 
            
            self.current_font_size = final_size
            
            # Loop 2: Vertical Centering
            gap = target_height - text_pixel_height
            if gap > 0:
                top_padding = gap // 2
                # widget.tag_config("v_center_push", spacing1=top_padding)
                widget.tag_add("v_center_push", "1.0", "1.end")
            
            widget.config(state=tk.DISABLED)
            
        except Exception as e:
            print(f"Lỗi update UI: {e}")
            traceback.print_exc()

    def trigger_optimization(self, event):
        btn = event.widget
        
        # Kiểm tra xem nút đã có ảnh chưa (để tránh lỗi)
        if hasattr(btn, 'target_image') and btn.target_image:
            print("🚀 Bắt đầu gọi Gemini theo yêu cầu...")
            
            # 1. Đổi giao diện nút để báo đang làm việc
            btn.config(text="⏳ Đang xử lý...", bg="#333", fg="gray", cursor="watch")
            
            # 2. Hủy sự kiện click (để không bị bấm spam nhiều lần)
            btn.unbind("<Button-1>")
            
            # 3. Chạy luồng xử lý (truyền cả cái nút vào để hàm kia update lại khi xong)
            threading.Thread(target=self.process_quality_path, 
                             args=(btn.target_image, btn.original_widget, btn)).start()
            
            # Ngăn sự kiện lan truyền (nếu cần)
            return "break"

    def _show_overlay(self):
        # Bảo vệ kép: Nếu cửa sổ chọn đã tồn tại thì không tạo nữa
        if hasattr(self, 'sel_win') and self.sel_win and self.sel_win.winfo_exists():
            return

        # Xóa sạch các cửa sổ cũ (nếu có sót)
        self.close_all_windows()

        self.root.update()

        import time 
        time.sleep(0.1)
        # --- CHỤP ẢNH (Di chuyển vào đây để an toàn luồng UI) ---
        try:
            self.frozen_img = pyautogui.screenshot()
            self.tk_frozen = ImageTk.PhotoImage(self.frozen_img)
        except Exception as e:
            print(f"Lỗi chụp màn hình: {e}")
            self.is_selecting = False # Nhả khóa nếu lỗi
            return
        # -------------------------------------------------------

        # (Phần tạo cửa sổ bên dưới GIỮ NGUYÊN)
        self.sel_win = tk.Toplevel(self.root)
        self.sel_win.attributes('-fullscreen', True)
        self.sel_win.attributes('-topmost', True)
        self.sel_win.focus_force()
        self.sel_win.grab_set()

        self.canvas = tk.Canvas(self.sel_win, cursor="cross", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(0, 0, image=self.tk_frozen, anchor="nw")
        
        self.canvas.create_rectangle(0, 0, self.frozen_img.width, self.frozen_img.height, 
                                     fill="black", stipple="gray50")

        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.sel_win.bind("<Escape>", lambda e: self.close_selection())

    def close_selection(self):
        if hasattr(self, 'sel_win') and self.sel_win:
            try:
                self.sel_win.grab_release()
                self.sel_win.destroy()
            except: pass
            
        # Xóa ảnh để giải phóng RAM
        if hasattr(self, 'frozen_img'): del self.frozen_img
        if hasattr(self, 'tk_frozen'): del self.tk_frozen
        
        # [QUAN TRỌNG] Nhả khóa để cho phép bấm lần sau
        self.is_selecting = False

    def close_all_windows(self):
        for win in self.result_windows:
            try: win.destroy()
            except: pass
        self.result_windows.clear()
        for listener in self.listeners:
            try: listener.stop()
            except: pass
        self.listeners.clear()

    def on_mouse_down(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, 1, 1, outline='#00FF00', width=2)

    def on_mouse_drag(self, event):
        self.cur_x, self.cur_y = (event.x, event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, self.cur_x, self.cur_y)

    def on_mouse_up(self, event):
        # 1. Tính toán vùng chọn gốc
        x1, y1 = min(self.start_x, self.cur_x), min(self.start_y, self.cur_y)
        x2, y2 = max(self.start_x, self.cur_x), max(self.start_y, self.cur_y)
        
        w = x2 - x1
        h = y2 - y1
        screen_x, screen_y = x1, y1
        
        # --- [SỬA LỖI: KHÔNG GỌI close_selection() Ở ĐÂY NỮA] ---
        # (Code cũ gọi ở đây nên nó xóa mất self.frozen_img)

        if w > 10 and h > 10:
            try:
                # --- LOGIC CẮT ẢNH (Thực hiện khi ảnh gốc vẫn còn) ---
                
                pad = 0
                
                img_w, img_h = self.frozen_img.size # Lấy kích thước ảnh gốc
                
                # Các dòng tính toán crop giữ nguyên
                crop_x1 = max(0, x1 - pad)
                crop_y1 = max(0, y1 - pad)
                crop_x2 = min(img_w, x2 + pad)
                crop_y2 = min(img_h, y2 + pad)
                
                # Cắt ảnh
                cropped_img = self.frozen_img.crop((crop_x1, crop_y1, crop_x2, crop_y2))
                
                self.close_selection() 

                # Hiện khung kết quả
                win, label = self.create_result_window(screen_x, screen_y, w, h)
                self.update_text_safe(label, "🔍 Đang đọc...", "#FFFF00")
                # --- [MỚI] GẮN ẢNH VÀO NÚT ĐỂ DÙNG SAU ---
                # Chúng ta cần truy cập vào cái nút opt_btn đã tạo trong create_result_window
                if hasattr(self, 'opt_btn'):
                    self.opt_btn.target_image = cropped_img # Lưu ảnh vào nút
                # -----------------------------------------

                self.enable_auto_close()
                
                # Chỉ chạy OCR (Groq) tự động
                threading.Thread(target=self.process_image, args=(cropped_img, label)).start()
                
                # --- [QUAN TRỌNG] ĐÃ XÓA DÒNG GỌI GEMINI TỰ ĐỘNG Ở ĐÂY ---
                # (Không còn threading.Thread(target=self.process_quality_path...) nữa)

            except Exception as e:
                print(f"Lỗi cắt ảnh: {e}")
                self.close_selection()
        else:
            self.close_selection()

    def create_result_window(self, x, y, w, h):
        win = tk.Toplevel(self.root)
        win.geometry(f"{w}x{h}+{x}+{y}")
        win.pack_propagate(False) 
        win.grid_propagate(False)
        
        win.overrideredirect(True)
        win.attributes('-topmost', True)
        win.config(bg='#1c1c1c')
        win.attributes('-alpha', 0.9)

        # Widget Text
        text_widget = tk.Text(win, bg='#1c1c1c', fg="white", 
                              font=("Segoe UI", 11, "bold"), 
                              wrap=tk.WORD, bd=0, highlightthickness=0)
        text_widget.pack(fill="both", expand=True, padx=5, pady=5)
        
        # --- [QUAN TRỌNG: XÓA DÒNG BIND NÀY ĐI] ---
        # text_widget.bind("<Button-1>", lambda e: self.close_all_windows())  <-- XÓA HOẶC COMMENT
        # ------------------------------------------
        
        text_widget.tag_configure("center", justify='center')
        text_widget.tag_config("highlight", foreground="#FFD700")

        # Nút tối ưu
        self.opt_btn = tk.Label(win, text="✨ Tối ưu", bg='#007acc', fg='white', 
                                font=("Segoe UI", 9), padx=5, pady=2, cursor="hand2")
        self.opt_btn.place(relx=1.0, rely=1.0, anchor='se', x=-2, y=-2)
        
        self.opt_btn.original_widget = text_widget # Lưu widget chữ để lát nữa ghi đè
        self.opt_btn.target_image = None # Chỗ giữ ảnh (sẽ được gán ở on_mouse_up)

        # Gán sự kiện click: Gọi hàm kích hoạt
        self.opt_btn.bind("<Button-1>", self.trigger_optimization)
        
        # Hiệu ứng hover cho đẹp
        self.opt_btn.bind("<Enter>", lambda e: e.widget.config(bg="#005f9e"))
        self.opt_btn.bind("<Leave>", lambda e: e.widget.config(bg="#007acc"))

        self.result_windows.append(win)
        return win, text_widget

    def set_click_through(self, win):
        try:
            hwnd = win.winfo_id()
            win.update_idletasks()
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(hwnd)
            if hwnd == 0: hwnd = win.winfo_id()
            ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_LAYERED)
        except: pass

    def enable_auto_close(self):
        # Hàm kiểm tra click chuột
        def on_click(x, y, button, pressed):
            # Chỉ xử lý khi nhấn xuống (pressed=True)
            if pressed:
                is_click_inside = False
                
                # Duyệt qua tất cả các cửa sổ kết quả đang mở
                for win in self.result_windows:
                    try:
                        if win.winfo_exists():
                            # Lấy tọa độ và kích thước cửa sổ
                            win_x = win.winfo_rootx()
                            win_y = win.winfo_rooty()
                            win_w = win.winfo_width()
                            win_h = win.winfo_height()
                            
                            # Kiểm tra xem chuột có nằm trong hình chữ nhật cửa sổ không
                            if (win_x <= x <= win_x + win_w) and (win_y <= y <= win_y + win_h):
                                is_click_inside = True
                                break # Đã tìm thấy click bên trong, dừng kiểm tra
                    except:
                        pass
                
                # LOGIC QUAN TRỌNG:
                # Nếu click KHÔNG nằm trong cửa sổ nào -> Đóng tất cả
                if not is_click_inside:
                    self.root.after(0, self.close_all_windows)
                # Ngược lại (click bên trong) -> Không làm gì cả (để Tkinter xử lý nút bấm)

        # Lắng nghe chuột toàn cục
        m_listener = mouse.Listener(on_click=on_click)
        m_listener.start()
        self.listeners.append(m_listener)
        
        # Vẫn giữ phím ESC để đóng khẩn cấp
        def on_key_release(key):
            if key == pynput_k.Key.esc:
                self.root.after(0, self.close_all_windows)
                
        k_listener = pynput_k.Listener(on_release=on_key_release)
        k_listener.start()
        self.listeners.append(k_listener)

    def process_image(self, image, label_widget):
        global ocr_engine
        try:
            # --- CHIẾN THUẬT "THỬ SAI" (MULTI-PASS OCR) ---
            scale = 3
            # Hàm con để xử lý ảnh và chạy OCR
            def try_ocr(img_input, contrast_factor=2.0, threshold=140, invert=True):
                # 1. Xử lý
                gray = img_input.convert('L')
                enhancer = ImageEnhance.Contrast(gray)
                high_contrast = enhancer.enhance(contrast_factor)
                
                # Threshold
                bw = high_contrast.point(lambda x: 0 if x < threshold else 255, '1')
                
                # Upscale
                
                new_w, new_h = int(bw.width * scale), int(bw.height * scale)
                upscaled = bw.resize((new_w, new_h), Image.Resampling.LANCZOS)
                
                # Sharpen
                sharp = upscaled.filter(ImageFilter.SHARPEN)
                
                # Invert (Tùy chọn)
                final = ImageOps.invert(sharp.convert('L')) if invert else sharp.convert('L')
                
                # 2. Chạy OCR
                result, _ = ocr_engine(np.array(final))
                return result

            # --- THỬ LẦN 1: Cấu hình chuẩn (Tốt cho text body) ---
            result = try_ocr(image, contrast_factor=2.0, threshold=128, invert=True)
            
            # Kiểm tra xem đã đọc được dòng tiêu đề chưa?
            # (Thường dòng tiêu đề nằm ở trên cùng, y < 50)
            has_title = False
            if result:
                # Thuật toán gom dòng thông minh (TOLERANCE)
                TOLERANCE = 35 # Dung sai cho phép lệch dòng
                
                # 1. Chuyển dữ liệu
                word_blocks = []
                for line in result:
                    box = line[0]
                    text = line[1]
                    y_min = min(p[1] for p in box)
                    y_max = max(p[1] for p in box)
                    y_center = (y_min + y_max) / 2
                    
                    word_blocks.append({
                        'text': text,
                        'y_center': y_center,
                        'height': y_max - y_min,
                        'x': min(p[0] for p in box),
                        'raw_h': abs(box[3][1] - box[0][1])
                    })

                # 2. Sắp xếp theo Y
                word_blocks.sort(key=lambda b: b['y_center'])
                
                lines = []
                current_line = []
                
                # 3. Gom nhóm
                for block in word_blocks:
                    if not current_line:
                        current_line.append(block)
                        continue
                    
                    ref = current_line[0]
                    # Nếu tâm nằm trong khoảng dung sai của dòng trước
                    if abs(block['y_center'] - ref['y_center']) < TOLERANCE:
                        current_line.append(block)
                    else:
                        lines.append(current_line)
                        current_line = [block]
                if current_line: lines.append(current_line)
                
                # 4. Nối chuỗi và tính chiều cao
                final_lines = []
                total_h = 0
                count = 0
                
                for line in lines:
                    line.sort(key=lambda b: b['x']) # Sort trái -> phải
                    line_text = " ".join([b['text'] for b in line])
                    final_lines.append(line_text)
                    
                    for b in line:
                        # Bây giờ biến 'scale' đã được định nghĩa -> Không lỗi nữa
                        total_h += (b['raw_h'] / scale)
                        count += 1

                if count > 0: avg_h_orig = total_h / count
                raw_text = "\n".join(final_lines)
                print(f"OCR Result:\n{raw_text}")

            # --- THỬ LẦN 2: Cấu hình cho Tiêu đề (Nền sáng/Chữ to) ---
            # Nếu chưa đọc được gì hoặc nghi ngờ thiếu
            if not result or not has_title:
                print("Thử lại với cấu hình Tiêu đề...")
                # Không invert, threshold cao hơn để lọc nền vàng
                result_v2 = try_ocr(image, contrast_factor=1.5, threshold=180, invert=False)
                
                if result_v2:
                    if not result: 
                        result = result_v2
                    else:
                        # Gộp kết quả: Lấy những dòng mà lần 1 chưa đọc được
                        # (Logic đơn giản: Nếu lần 2 đọc được nhiều dòng hơn thì lấy lần 2)
                        if len(result_v2) > len(result):
                            result = result_v2

            # --- (PHẦN CÒN LẠI GIỮ NGUYÊN: Sắp xếp, Nối dòng...) ---
            raw_text = ""
            avg_h_orig = 20
            
            if result:
                # --- [THUẬT TOÁN GOM DÒNG THÔNG MINH V2: CENTER Y] ---
                
                # 1. Chuyển đổi dữ liệu để dễ xử lý: [ {y_center, height, x, text}, ... ]
                word_blocks = []
                for line in result:
                    box = line[0]
                    text = line[1]
                    
                    # Tính Y trung tâm và Chiều cao
                    y_min = min(p[1] for p in box)
                    y_max = max(p[1] for p in box)
                    y_center = (y_min + y_max) / 2
                    height = y_max - y_min
                    x_min = min(p[0] for p in box)
                    
                    word_blocks.append({
                        'text': text,
                        'y_center': y_center,
                        'height': height,
                        'x': x_min,
                        'raw_h': abs(box[3][1] - box[0][1]) # Để tính font size
                    })

                # 2. Sắp xếp sơ bộ theo Y để duyệt từ trên xuống
                word_blocks.sort(key=lambda b: b['y_center'])
                
                lines = []
                current_line = []
                
                # 3. Duyệt và gom nhóm
                for block in word_blocks:
                    if not current_line:
                        current_line.append(block)
                        continue
                    
                    # Lấy block đầu tiên của dòng hiện tại làm chuẩn
                    ref_block = current_line[0]
                    
                    # Logic: Nếu tâm của block mới nằm trong phạm vi chiều cao của dòng hiện tại
                    # (Cho phép sai số 50% chiều cao dòng)
                    vertical_threshold = ref_block['height'] * 0.5
                    
                    if abs(block['y_center'] - ref_block['y_center']) < vertical_threshold:
                        # Cùng dòng
                        current_line.append(block)
                    else:
                        # Khác dòng -> Lưu dòng cũ, bắt đầu dòng mới
                        lines.append(current_line)
                        current_line = [block]
                
                # Lưu dòng cuối
                if current_line:
                    lines.append(current_line)
                
                # 4. Sắp xếp X trong từng dòng và nối chuỗi
                final_text_lines = []
                total_h = 0
                count = 0
                
                for line in lines:
                    # Sort từ trái qua phải
                    line.sort(key=lambda b: b['x'])
                    
                    # Nối các từ
                    line_text = " ".join([b['text'] for b in line])
                    final_text_lines.append(line_text)
                    
                    # Tính toán chiều cao trung bình
                    for b in line:
                        total_h += (b['raw_h'] / scale)
                        count += 1

                if count > 0: avg_h_orig = total_h / count
                
                # Kết quả cuối cùng
                raw_text = "\n".join(final_text_lines)

            # ... (Phần Fallback, Tính font size, Gọi Groq... GIỮ NGUYÊN) ...
            # (Copy y nguyên phần dưới từ code cũ vào)
            
            if not raw_text.strip():
                # Fallback
                res_retry, _ = ocr_engine(np.array(image))
                if res_retry: raw_text = "\n".join([r[1] for r in res_retry])
            
            if not raw_text.strip():
                self.update_text_safe(label_widget, "Không thấy chữ", "gray")
                return

            # Font Size
            font_size = max(11, min(int(avg_h_orig * 0.85), 40))
            self.font_size = font_size
            dynamic_font = ("Segoe UI", font_size, "bold")
            label_widget.config(font=dynamic_font)
            label_widget.tag_config("highlight", foreground="#FFD700", font=dynamic_font)

            # Groq
            final_input = f"{ROGUELIKE_PROMPT}\n\n(NỘI DUNG CẦN DỊCH:\n\n'{raw_text}')"
            translated_text = call_groq_with_rotation(final_input)
            clean_text = clean_translation_output(translated_text)
            self.root.after(0, lambda: self.update_text_safe(label_widget, clean_text, "white", "⏳ Đang tối ưu..."))
            # Display
            label_widget.config(state=tk.NORMAL)
            label_widget.delete("1.0", tk.END)
            label_widget.config(fg="#00ff00")
            
            parts = clean_text.split('*')
            for i, part in enumerate(parts):
                if i % 2 == 0: label_widget.insert(tk.END, part)
                else: label_widget.insert(tk.END, part, "highlight")
            
            # Auto-fit
            label_widget.update_idletasks()
            count_res = label_widget.count("1.0", "end", "displaylines")
            num_lines = count_res[0] if count_res else 1
            label_widget.config(height=num_lines)
            label_widget.pack_configure(fill='x', expand=True, anchor='center')
            label_widget.config(state=tk.DISABLED)
                
        except Exception as e:
            print(f"Lỗi xử lý: {e}")
            self.update_text_safe(label_widget, "Lỗi dịch", "red")



# --- HÀM MAIN AN TOÀN (CHỐNG CRASH) ---
def main():
    global ocr_engine, client
    
    # 1. Xin quyền Admin trước
    # enforce_admin()
    
   # 2. Khởi tạo thư viện nặng
    print("--- Đang khởi tạo RapidOCR... ---")
    # Để trống tham số để nó tự động (tránh lỗi model_path)
    ocr_engine = RapidOCR() 
    
    print("--- Đang mở giao diện... ---")
    TooltipTranslator()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # NẾU CÓ LỖI, MÀN HÌNH SẼ DỪNG LẠI ĐỂ BẠN ĐỌC
        print("\n" + "="*40)
        print("❌ CHƯƠNG TRÌNH GẶP LỖI NGHIÊM TRỌNG:")
        traceback.print_exc() # In chi tiết lỗi ra
        print("="*40 + "\n")
        input("👉 Bấm Enter để thoát...")