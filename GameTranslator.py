import tkinter as tk
import pyautogui
import threading
import numpy as np
import win32gui
import win32con
from PIL import Image, ImageTk 
from rapidocr_onnxruntime import RapidOCR
from groq import Groq
from pynput import mouse, keyboard as pynput_k
import ctypes
import os
import sys
import traceback # Thư viện để in chi tiết lỗi
import re

try:
    # Giúp tool nhận diện đúng độ phân giải màn hình, cắt ảnh chuẩn xác hơn
    ctypes.windll.user32.SetProcessDPIAware()
except:
    pass
# --- CẤU HÌNH ---
try:
    from key_secrets import GROQ_API_KEYS
except ImportError:
    # Xử lý trường hợp người dùng tải về nhưng chưa tạo file key_secrets.py
    print("Cảnh báo: Không tìm thấy file 'key_secrets.py'.")
    print("Vui lòng tạo file này hoặc nhập Key thủ công.")
    # Đặt danh sách rỗng để không crash ngay lập tức
    GROQ_API_KEYS = []
    
HOTKEY = "<alt>+<caps_lock>"

# Khai báo biến toàn cục (Chưa khởi tạo vội để tránh lỗi khi import)
ocr_engine = None
client = None
current_key_index = 0
# --- PROMPT DỊCH ---
ROGUELIKE_PROMPT = """
Bạn là chuyên gia ngôn ngữ game. Nhiệm vụ: Dịch văn bản game (được trích xuất từ OCR) sang Tiếng Việt.

QUY TẮC CỐT LÕI (BẮT BUỘC TUÂN THỦ):
1. ⛔ KHÔNG bao giờ được thêm câu dẫn dắt như: "Đây là bản dịch", "Sure", "Here is the result", "Dịch:", "Output:".
2. ⛔ KHÔNG giải thích, KHÔNG ghi chú thêm.
3. CHỈ TRẢ VỀ DUY NHẤT KẾT QUẢ DỊCH. Nếu đầu vào là "Fireball", đầu ra phải là "Cầu Lửa" (không có dấu chấm, không có ngoặc kép bao quanh).

⚠️ LƯU Ý QUAN TRỌNG: Dữ liệu đầu vào là từ OCR (quét ảnh) nên thường bị lỗi chính tả (Ví dụ: 'Damag' -> 'Damage', 'Hcalth' -> 'Health', 'l00%' -> '100%').
👉 HÃY TỰ ĐỘNG SUY LUẬN VÀ SỬA LỖI CHÍNH TẢ DỰA TRÊN NGỮ CẢNH GAME TRƯỚC KHI DỊCH.

HƯỚNG DẪN DỊCH THUẬT:
1. Tên Riêng (Skill, Item, Monster): GIỮ NGUYÊN Tiếng Anh.
2. Chỉ số (HP, MP, Crit): Giữ nguyên.
3. Văn phong: Ngắn gọn, súc tích, kiểu tooltip game RPG.

VÍ DỤ XỬ LÝ LỖI NGẮT DÒNG:
- Input: 
  "Attacks deal 50% more"
  "damage to enemies."
  "Crit Rate +10%"
- Output:
  Attacks deal 50% more damage to enemies.
  Crit Rate +10%
- Bản Dịch:
  Đòn đánh gây thêm 50% sát thương lên kẻ địch.
  Tỉ lệ chí mạng +10%
"""

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

        # Lắng nghe phím tắt (Global)
        with pynput_k.GlobalHotKeys({HOTKEY: self.start_selection}) as h:
            self.hotkey_listener = h
            threading.Thread(target=h.join, daemon=True).start()
            print(f"✅ Đã khởi động xong! Vào game và bấm Ctrl+Q để dịch.")
            self.root.mainloop()

    def start_selection(self):
        if self.is_selecting: return
        
        # 1. ĐÓNG BĂNG MÀN HÌNH
        try:
            self.frozen_img = pyautogui.screenshot()
            self.tk_frozen = ImageTk.PhotoImage(self.frozen_img)
            self.root.after(0, self._show_overlay)
        except Exception as e:
            print(f"Lỗi chụp màn hình: {e}")

    def _show_overlay(self):
        self.is_selecting = True
        self.close_all_windows()

        self.sel_win = tk.Toplevel(self.root)
        self.sel_win.attributes('-fullscreen', True)
        self.sel_win.attributes('-topmost', True)
        self.sel_win.focus_force()
        self.sel_win.grab_set()

        self.canvas = tk.Canvas(self.sel_win, cursor="cross", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(0, 0, image=self.tk_frozen, anchor="nw")
        
        # Lớp phủ tối
        self.canvas.create_rectangle(0, 0, self.frozen_img.width, self.frozen_img.height, 
                                     fill="black", stipple="gray50")

        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.sel_win.bind("<Escape>", lambda e: self.close_selection())

    def close_selection(self):
        if hasattr(self, 'sel_win') and self.sel_win:
            self.sel_win.grab_release()
            self.sel_win.destroy()
        self.is_selecting = False
        if hasattr(self, 'frozen_img'): del self.frozen_img
        if hasattr(self, 'tk_frozen'): del self.tk_frozen

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
                
                pad = 5
                
                img_w, img_h = self.frozen_img.size # Lấy kích thước ảnh gốc
                
                # Các dòng tính toán crop giữ nguyên
                crop_x1 = max(0, x1 - pad)
                crop_y1 = max(0, y1 - pad)
                crop_x2 = min(img_w, x2 + pad)
                crop_y2 = min(img_h, y2 + pad)
                
                # Cắt ảnh
                cropped_img = self.frozen_img.crop((crop_x1, crop_y1, crop_x2, crop_y2))
                
                # --- [SỬA LỖI: ĐÓNG SAU KHI ĐÃ CẮT XONG] ---
                self.close_selection() 
                # -------------------------------------------

                # Hiện khung kết quả
                win, label = self.create_result_window(screen_x, screen_y, w, h)
                label.config(text="Đang đọc...", fg="yellow")
                
                self.enable_auto_close()
                
                threading.Thread(target=self.process_image, args=(cropped_img, label)).start()
            except Exception as e:
                print(f"Lỗi cắt ảnh: {e}")
                self.close_selection() # Đóng nếu có lỗi
        else:
            # Nếu vùng chọn quá bé (click nhầm), đóng luôn
            self.close_selection()

    def create_result_window(self, x, y, w, h):
        win = tk.Toplevel(self.root)
        
        # --- [SỬA ĐỔI QUAN TRỌNG] ---
        # 1. Chỉ đặt vị trí (x, y), KHÔNG đặt kích thước cố định ở đây nữa
        win.geometry(f"+{x}+{y}")
        
        # 2. Đặt kích thước tối thiểu (minsize) bằng đúng vùng chọn
        # Giúp đảm bảo luôn che hết chữ gốc, nhưng vẫn có thể to ra nếu cần
        win.minsize(w, h)
        # ----------------------------

        win.overrideredirect(True)
        win.attributes('-topmost', True)
        win.config(bg='#1c1c1c')
        win.attributes('-alpha', 0.9)

        # 3. Cấu hình Label để tự xuống dòng (Wrap)
        # wraplength=w: Nếu chữ dài hơn chiều ngang vùng chọn, nó sẽ tự xuống dòng
        label = tk.Label(win, text="", fg="white", bg='#1c1c1c', 
                         font=("Segoe UI", 11, "bold"), 
                         wraplength=w, # Tự động xuống dòng theo chiều rộng
                         justify="left")
        
        label.pack(fill="both", expand=True, padx=2, pady=2)
        
        self.set_click_through(win)
        self.result_windows.append(win)
        return win, label

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
        def on_any_action(*args):
            self.root.after(0, self.close_all_windows)
            return False
        
        m_listener = mouse.Listener(on_click=on_any_action)
        m_listener.start()
        self.listeners.append(m_listener)
        
        k_listener = pynput_k.Listener(on_press=on_any_action)
        k_listener.start()
        self.listeners.append(k_listener)

    def process_image(self, image, label_widget):
        try:
            # --- [BƯỚC 1: NÂNG CẤP ẢNH ĐỂ OCR CHUẨN HƠN] ---
            
            # 1. Chuyển sang đen trắng (Grayscale)
            # Giúp loại bỏ nhiễu màu nền của game (lửa, băng, mây...)
            processed_img = image.convert('L')
            
            # 2. Phóng to ảnh lên gấp 3 lần (Upscale)
            # Chữ to ra -> OCR đọc nét hơn hẳn
            scale_factor = 3 
            new_w = int(processed_img.width * scale_factor)
            new_h = int(processed_img.height * scale_factor)
            processed_img = processed_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            # 3. (Tùy chọn) Tăng độ tương phản cực đại (Binarization)
            # Biến ảnh thành chỉ có Đen và Trắng tuyệt đối
            # threshold = 140
            # processed_img = processed_img.point(lambda x: 0 if x < threshold else 255, '1')

            # Lưu ảnh ra để debug nếu cần (bỏ comment dòng dưới để xem ảnh mà máy đọc được)
            # processed_img.save("debug_ocr_input.png") 

            # Chuyển sang dạng mảng số (Numpy) cho RapidOCR
            img_np = np.array(processed_img)
            
            # --- [BƯỚC 2: CHẠY OCR] ---
            result, _ = ocr_engine(img_np)
            
            raw_text = ""
            # Biến tính chiều cao trung bình của chữ GỐC (trước khi phóng to)
            avg_height_original = 20 
            
            if result:
                total_height = 0
                count = 0
                for line in result:
                    box = line[0]
                    text = line[1]
                    
                    # --- SỬA NHẸ: Thêm khoảng trắng thay vì xuống dòng cứng ---
                    # Logic: Chỉ xuống dòng nếu dòng đó kết thúc bằng dấu câu hoặc số
                    # Tuy nhiên, để AI tự lo là tốt nhất.
                    # Ta chỉ cần đảm bảo text gửi đi sạch sẽ.
                    raw_text += text + "\n"
                    
                    # Tính chiều cao chữ trên ảnh ĐÃ PHÓNG TO
                    h_scaled = abs(box[3][1] - box[0][1])
                    
                    # Chia lại cho scale_factor để ra kích thước thật trên màn hình
                    h_real = h_scaled / scale_factor
                    
                    total_height += h_real
                    count += 1
                
                if count > 0: 
                    avg_height_original = total_height / count

            # Kiểm tra lại lần cuối
            if not raw_text.strip():
                # Fallback: Nếu xử lý ảnh kỹ quá mà vẫn không ra, thử đọc ảnh gốc màu
                # Đôi khi màu sắc lại giúp phân biệt chữ tốt hơn
                print("Ảnh đen trắng thất bại, thử lại với ảnh gốc...")
                result_retry, _ = ocr_engine(np.array(image))
                if result_retry:
                    raw_text = "" # Reset text
                    for line in result_retry:
                        raw_text += line[1] + "\n"
            
            # Nếu vẫn không có chữ
            if not raw_text.strip():
                label_widget.config(text="Không tìm thấy chữ", fg="gray")
                return

            # --- [BƯỚC 3: TÍNH FONT SIZE ĐỘNG] ---
            font_size = int(avg_height_original * 0.9) # Nhân 0.9 cho gọn
            final_font_size = max(11, min(font_size, 40)) # Giới hạn an toàn
            dynamic_font = ("Segoe UI", -final_font_size, "bold")

            # --- [BƯỚC 4: GỌI GROQ DỊCH] ---
            final_input = f"{ROGUELIKE_PROMPT}\n\nNỘI DUNG CẦN DỊCH:\n{raw_text}"
            print(final_input)
            translated_text = call_groq_with_rotation(final_input)
            
            clean_text = clean_translation_output(translated_text)
            label_widget.config(text=clean_text, fg="#00ff00", font=dynamic_font)
            
        except Exception as e:
            print(f"Lỗi xử lý: {e}")
            try: label_widget.config(text="Lỗi", fg="red")
            except: pass

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