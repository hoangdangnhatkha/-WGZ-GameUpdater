# Đây là file updater.py (Một file Python riêng biệt)
import sys
import os
import requests
import time
import subprocess

# Cần cài đặt: pip install requests
# Build bằng: pyinstaller --onefile --console "updater.py"

def download_file(url, out_path):
    """Tải file với thanh tiến trình cơ bản trong console."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024 * 8
        
        print(f"Bắt đầu tải: {os.path.basename(out_path)}")
        with open(out_path, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=block_size):
                f.write(chunk)
                downloaded += len(chunk)
                
                percent = (downloaded / total_size) * 100 if total_size > 0 else 0
                progress_bar = '#' * int(percent / 2) + '-' * (50 - int(percent / 2))
                sys.stdout.write(f"\r[{progress_bar}] {percent:.1f}%")
                sys.stdout.flush()
        
        print("\nTải xong!")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"\nLỗi khi tải file: {e}")
        return False
    except IOError as e:
        print(f"\nLỗi khi ghi file: {e}")
        return False

def main():
    try:
        if len(sys.argv) != 3:
            print("Lỗi: Cần 2 tham số (download_url và main_app_path).")
            sys.exit(1)
            
        download_url = sys.argv[1] # Arg 1: Link tải .exe mới
        main_app_path = sys.argv[2] # Arg 2: Đường dẫn đến file .exe chính (cũ)
        
        print("--- Updater đang chạy ---")
        
        # 1. Đợi 2 giây để ứng dụng chính đóng hoàn toàn
        print("Đang đợi ứng dụng chính đóng...")
        time.sleep(2)
        
        # 2. Đặt tên file tạm
        new_app_path = main_app_path + ".new"
        
        # 3. Tải file mới
        if not download_file(download_url, new_app_path):
            raise Exception("Tải file thất bại.")
            
        # 4. Thay thế file cũ bằng file mới
        print(f"Đang thay thế {main_app_path}...")
        try:
            os.replace(new_app_path, main_app_path)
        except Exception:
            # Fallback nếu os.replace thất bại
            os.remove(main_app_path)
            os.rename(new_app_path, main_app_path)
        
        print("Cập nhật thành công!")

        # 5. Chạy lại ứng dụng chính
        print("Đang khởi động lại ứng dụng...")
        subprocess.Popen([main_app_path])
        
    except Exception as e:
        print(f"\n--- LỖI CẬP NHẬT ---")
        print(f"Lỗi: {e}")
        print("Vui lòng tải bản cập nhật thủ công.")
    
    print("Updater sẽ đóng sau 10 giây.")
    time.sleep(10)
    sys.exit()

if __name__ == "__main__":
    main()