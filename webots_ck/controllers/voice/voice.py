from controller import Robot, Motion
import socket
import os

robot = Robot()
time_step = int(robot.getBasicTimeStep())

# Load motion
webots_home = os.environ.get("WEBOTS_HOME")
motion_folder = os.path.join(
    webots_home, "projects", "robots", "softbank", "nao", "motions"
)
wave_motion = Motion(os.path.join(motion_folder, "HandWave.motion"))

# SOCKET SERVER
HOST = '127.0.0.1'
PORT = 65432

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(1)
server_socket.setblocking(False)

print("[Robot] Server mở, chờ client...")

conn = None

STATE_IDLE = 1
STATE_WAVING = 2
state = STATE_IDLE

while robot.step(time_step) != -1:

    # 🔹 Accept client
    if conn is None:
        try:
            conn, addr = server_socket.accept()
            conn.setblocking(False)
            print("[Robot] Client đã kết nối:", addr)
        except BlockingIOError:
            continue

    # 🔹 Nhận dữ liệu
    try:
        data = conn.recv(1024)
    except BlockingIOError:
        data = None

    if state == STATE_IDLE and data == b'WAVE':
        print("[Robot] WAVE")
        wave_motion.play()
        state = STATE_WAVING

    elif state == STATE_WAVING and wave_motion.isOver():
        print("[Robot] Xong, chờ lệnh")
        state = STATE_IDLE
