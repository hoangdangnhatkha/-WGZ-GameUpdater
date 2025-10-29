# Đây là file updater.py (Phiên bản dùng gdown)
import sys
import os
import time
import subprocess
import shutil
import gdown # Cần cài đặt: pip install gdown

# Build bằng: pyinstaller --onefile --console updater.py

# --- Hàm tải file bằng gdown ---
def download_file_gdown(url, out_path):
    """Tải file từ Google Drive (hoặc link trực tiếp) bằng gdown."""
    try:
        print(f"Bắt đầu tải: {os.path.basename(out_path)} từ {url}")
        # gdown tự động xử lý link Google Drive và hiển thị tiến trình
        gdown.download(url, out_path, quiet=False, fuzzy=True)
        print("\nTải xong!")
        return True
    except Exception as e:
        print(f"\nLỗi khi tải file bằng gdown: {e}")
        # Cố gắng dọn dẹp file tạm nếu tải lỗi
        try:
            if os.path.exists(out_path):
                os.remove(out_path)
        except Exception as remove_e:
            print(f"Lỗi khi xóa file tạm bị lỗi: {remove_e}")
        return False

# --- Hàm main (logic chính của updater) ---
def main():
    try:
        if len(sys.argv) != 3:
            print("Lỗi: Cần 2 tham số (download_url và main_app_path).")
            sys.exit(1)

        download_url = sys.argv[1]
        main_app_path = sys.argv[2]
        # download_url = "https://drive.google.com/uc?export=download&id=1xLitheCe9ygKSajQl9LbwxYskikYSG1J"
        # main_app_path = r"C:\Users\Dang\Desktop\Exe File\[WGZ]GameUpdaterProject\WGZGameUpdater\dist\WGZGameUpdater.exe"
        print("--- Updater đang chạy (gdown Mode) ---")

        # 1. Đợi ứng dụng chính đóng
        print("Đang đợi ứng dụng chính đóng...")
        time.sleep(3) # Giữ nguyên thời gian chờ này

        # 2. Đặt tên file tạm
        new_app_path = main_app_path + ".new"
        old_app_path_temp = main_app_path + ".old"

        # 2.5 Dọn dẹp file tạm cũ nếu có
        print("Dọn dẹp file tạm cũ (.new, .old) nếu có...")
        try:
            if os.path.exists(new_app_path): os.remove(new_app_path)
            if os.path.exists(old_app_path_temp): os.remove(old_app_path_temp)
            print("Dọn dẹp xong.")
        except Exception as cleanup_e:
            print(f"Cảnh báo: Không thể dọn dẹp file tạm cũ: {cleanup_e}")


        # 3. Tải file mới bằng gdown
        if not download_file_gdown(download_url, new_app_path):
            raise Exception("Tải file thất bại.")

        # 4. Thay thế file cũ (Logic này giữ nguyên)
        print(f"Đang thay thế {main_app_path}...")
        max_retries = 5
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                # 1. Cố gắng đổi tên file CŨ -> .old
                if os.path.exists(main_app_path):
                    print(f"Lần thử {attempt + 1}: Đổi tên file cũ thành .old...")
                    shutil.move(main_app_path, old_app_path_temp)
                    time.sleep(0.5)
                else:
                    print(f"Lần thử {attempt + 1}: File cũ không tồn tại, tiếp tục...")

                # 2. Cố gắng đổi tên file MỚI (.new) -> tên file chính
                print(f"Lần thử {attempt + 1}: Đổi tên file mới thành tên chính...")
                shutil.move(new_app_path, main_app_path)
                print("Cập nhật thành công!")

                # 3. Cố gắng xóa file .old
                try:
                    if os.path.exists(old_app_path_temp):
                        os.remove(old_app_path_temp)
                        print("Đã xóa file .old.")
                except Exception as remove_old_e:
                    print(f"Cảnh báo: Không thể xóa file .old: {remove_old_e}")
                break
            except (PermissionError, OSError) as e:
                print(f"Lần thử {attempt + 1}/{max_retries}: Vẫn bị khóa hoặc lỗi ({e}). Đang chờ {retry_delay} giây...")
                try:
                    if os.path.exists(old_app_path_temp) and not os.path.exists(main_app_path):
                        print("Khôi phục file cũ từ .old...")
                        shutil.move(old_app_path_temp, main_app_path)
                except Exception as restore_e:
                    print(f"Lỗi khi khôi phục file cũ: {restore_e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise e
            except Exception as e:
                print(f"Lỗi không mong muốn khi thay thế: {e}")
                raise e

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