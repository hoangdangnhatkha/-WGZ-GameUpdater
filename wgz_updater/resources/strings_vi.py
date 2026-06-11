"""Centralized Vietnamese UI strings. Keep keys ASCII-friendly."""

APP_TITLE = "WGZ Game Updater"

NAV_LIBRARY = "Thư Viện"
NAV_ACCOUNTS = "Share Acc Game"
NAV_SETTINGS = "Cài Đặt"
NAV_MANAGER = "Quản Lý"

LIBRARY_HEADER_NAME = "Tên"
LIBRARY_HEADER_GAME = "Game"
LIBRARY_HEADER_VERSION = "Phiên bản"
LIBRARY_HEADER_STATUS = "Trạng thái"
LIBRARY_HEADER_ACTION = "Thao tác"

STATUS_INSTALLED = "Đã cài"
STATUS_UPDATE = "Cần cập nhật"
STATUS_NOT_INSTALLED = "Chưa cài"
STATUS_DOWNLOADING = "Đang tải..."
STATUS_EXTRACTING = "Đang giải nén..."

ACTION_DOWNLOAD = "Tải về"
ACTION_UPDATE = "Cập nhật"
ACTION_OPEN = "Mở"
ACTION_LAUNCH = "Chạy"
ACTION_PAUSE = "Tạm dừng"
ACTION_RESUME = "Tiếp tục"
ACTION_CANCEL = "Hủy"
ACTION_REFRESH = "Làm mới"
ACTION_BROWSE = "Chọn thư mục..."
ACTION_AUTO_LOGIN = "Đăng nhập tự động"

DIALOG_CONFIRM_DELETE_TITLE = "Xác nhận xóa"
DIALOG_NEED_PATH_TITLE = "Chọn đường dẫn"
DIALOG_ERROR_TITLE = "Lỗi"
DIALOG_INFO_TITLE = "Thông báo"
DIALOG_OK = "Đồng ý"
DIALOG_CANCEL = "Hủy"

DOWNLOAD_SPEED_FMT = "{speed} • {percent}% • còn {eta}"
DOWNLOAD_DONE = "Hoàn tất"

ERR_NETWORK = "Lỗi mạng. Vui lòng kiểm tra kết nối."
ERR_NO_DOWNLOAD_URL = "Không tìm thấy link tải."
ERR_EXTRACT = "Lỗi giải nén tệp tin."

SETTINGS_INSTALL_PATH = "Đường dẫn cài đặt"
SETTINGS_GITHUB_TOKEN = "GitHub Token"
SETTINGS_RESET_CACHE = "Xóa cache"
SETTINGS_OPEN_LOG = "Mở thư mục log"
SETTINGS_VERSION = "Phiên bản"
SETTINGS_CHECK_UPDATE = "Kiểm tra cập nhật"

SPLASH_BOOTING = "Đang khởi động..."
SPLASH_CHECKING_VERSION = "Đang kiểm tra phiên bản..."
SPLASH_DOWNLOADING = "Đang tải xuống... {percent}%"
SPLASH_EXTRACTING = "Đang giải nén dữ liệu..."
SPLASH_DONE = "Cập nhật hoàn tất!"
SPLASH_OFFLINE = "Lỗi mạng. Đang chạy chế độ offline..."

# Library grid + detail page
ACTION_LAUNCH_GAME = "🚀 Chạy Game"
ACTION_BACK = "← Quay lại"
LABEL_INSTALL_PATH = "Thư mục cài đặt:"
LABEL_PATH_GUIDE = "Hướng dẫn cài đặt:"
LABEL_MOD_SELECT = "Chọn bản cài:"
LABEL_PART_OF = "Phần {current}/{total}"
STATUS_READY = "Sẵn sàng"
STATUS_CANCELLED = "Đã hủy"

# Accounts
ACTION_SAVE_DRIVE = "Lưu lên Server"
ACTION_LOAD_DRIVE = "Tải từ Server"
ACTION_ADD_ACCOUNT = "Thêm tài khoản"
LABEL_SERVICE = "Dịch vụ:"
LABEL_NICKNAME = "Tên hiển thị:"
LABEL_GAME_TAG = "Game:"
LABEL_ACCOUNTS_COUNT = "{count} tài khoản"
MSG_ACCOUNTS_SAVED = "Đã lưu tài khoản lên Server thành công."
MSG_ACCOUNTS_LOADED = "Đã tải tài khoản từ Server."
MSG_DRIVE_ERROR = "Lỗi Server: {error}"

# Download confirm
DIALOG_DOWNLOAD_CONFIRM = "Xác nhận tải về"
MSG_DOWNLOAD_CONFIRM = "Tải {name} ({parts} phần)?\nDung lượng trống: {free:.1f} GB"

# Windows Defender exclusion (game detail page)
DEFENDER_CHECKBOX = "Thêm thư mục cài đặt vào Defender Exclusion"
DEFENDER_TOOLTIP = (
    "Bỏ qua quét real-time của Windows Defender cho thư mục này → "
    "giải nén + chạy game nhanh hơn. Yêu cầu quyền Quản trị viên."
)
DEFENDER_ALREADY_COVERED = "Thư mục đã nằm trong Defender Exclusion, bỏ qua."
DEFENDER_ADDED = "Đã thêm thư mục vào Defender Exclusion."
DEFENDER_ADD_FAILED = "Không thêm được vào Defender Exclusion: {error}"

# Launcher picker (game detail page)
ACTION_SET_LAUNCHER = "Đổi launcher game"
DIALOG_PICK_LAUNCHER = "Chọn file launcher"
LAUNCHER_PICK_FILTER = "Executable (*.exe *.bat *.lnk);;Tất cả (*)"
LAUNCHER_OUTSIDE_INSTALL = (
    "File launcher phải nằm trong thư mục cài đặt:\n{install_path}"
)
LAUNCHER_NEED_INSTALL_PATH = (
    "Chọn thư mục cài đặt trước khi đổi launcher."
)
LAUNCHER_SAVED = "Đã đổi launcher: {file}"

# Remote support (RustDesk + Discord)
SUPPORT_TOOLTIP = "Gọi hỗ trợ từ xa"
SUPPORT_DIALOG_TITLE = "Gọi hỗ trợ từ xa"
SUPPORT_DIALOG_BODY = (
    "Hệ thống sẽ mở RustDesk và gửi thông tin kết nối tới đội hỗ trợ.\n"
    "Vui lòng giữ RustDesk mở cho đến khi kỹ thuật viên kết nối."
)
SUPPORT_CONFIRM_SEND = "Mở RustDesk"
SUPPORT_CALLING = "Đang chuẩn bị phiên hỗ trợ..."
SUPPORT_INSTALL_TITLE = "Cài đặt RustDesk"
SUPPORT_INSTALL_BODY = (
    "Lần đầu sử dụng cần cài đặt RustDesk service (chạy 1 lần duy nhất).\n\n"
    "Windows sẽ hỏi quyền Quản trị viên (UAC). "
    "Sau khi cài xong, mật khẩu hỗ trợ sẽ tự động hiện ra."
)
SUPPORT_INSTALL_CONFIRM = "Cài đặt"
SUPPORT_INSTALLING = "Đang cài đặt RustDesk service..."
SUPPORT_INSTALL_FAILED = "Cài đặt RustDesk thất bại: {error}"
SUPPORT_INSTALL_CANCELLED = "Bạn đã hủy yêu cầu cấp quyền Quản trị viên."
SUPPORT_INSTALL_TIMEOUT = "Cài đặt RustDesk quá thời gian. Vui lòng thử lại."

SUPPORT_OTP_PROMPT_TITLE = "Lấy mật khẩu từ RustDesk"
SUPPORT_OTP_PROMPT_BODY = (
    "RustDesk đã mở. ID của bạn là: <b>{id}</b><br/><br/>"
    "Trong cửa sổ RustDesk, ở khung <b>Your Desktop</b>:<br/>"
    "1. Nhấn nút <b>↻</b> (refresh) cạnh dòng <b>One-time password</b><br/>"
    "2. Copy mật khẩu vừa tạo<br/>"
    "3. Dán vào ô bên dưới và bấm <b>Gửi</b>"
)
SUPPORT_OTP_PLACEHOLDER = "Dán mật khẩu RustDesk vào đây"
SUPPORT_OTP_SEND = "Gửi tới đội hỗ trợ"
SUPPORT_OTP_EMPTY = "Vui lòng nhập mật khẩu RustDesk."
SUPPORT_SENT_OK = (
    "Đã gửi yêu cầu hỗ trợ.\n"
    "RustDesk đang mở — vui lòng chờ kỹ thuật viên kết nối.\n\n"
    "ID: {id}\nMật khẩu: {password}"
)
SUPPORT_SENT_FAIL = (
    "Không gửi được yêu cầu hỗ trợ tới Discord.\n"
    "Bạn có thể gửi thủ công các thông tin sau cho đội hỗ trợ:\n\n"
    "ID: {id}\nMật khẩu: {password}\n\nLỗi: {error}"
)
SUPPORT_NO_CONFIG = "Tính năng hỗ trợ chưa được cấu hình. Vui lòng liên hệ quản trị."
SUPPORT_NO_RUSTDESK = (
    "Không tìm thấy RustDesk đi kèm. "
    "Vui lòng cài đặt lại ứng dụng hoặc liên hệ quản trị."
)
SUPPORT_NO_CREDENTIALS = (
    "Không đọc được ID/mật khẩu RustDesk. "
    "Vui lòng thử lại sau vài giây."
)
