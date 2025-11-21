from flask import Flask, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_wgz_key'
# cors_allowed_origins='*' để cho phép Tool từ máy người dùng kết nối vào
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

@app.route('/')
def index():
    return "WGZ Quick Drop Server is Running!"

@socketio.on('connect')
def handle_connect():
    print('Một người dùng đã kết nối!')

@socketio.on('client_uploaded_file')
def handle_upload_event(data):
    """
    Khi Client A upload xong lên Drive, nó gửi tín hiệu này.
    Server nhận và hét to lên cho tất cả Client khác biết.
    """
    print(f"Nhận tín hiệu file mới: {data}")
    
    # Broadcast=True: Gửi cho TẤT CẢ mọi người đang kết nối (trừ người gửi nếu muốn, nhưng ở đây gửi hết)
    emit('server_new_file_alert', data, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)