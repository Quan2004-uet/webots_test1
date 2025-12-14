"""
Robot NAO – KHÔNG DI CHUYỂN
Nhận STOP -> đứng yên
Nhận WAVE -> vẫy tay
"""

from controller import Robot, Motion
import os
import socket

robot = Robot()
time_step = int(robot.getBasicTimeStep())

# --- Load Motion ---
webots_home = os.environ.get("WEBOTS_HOME")
motion_folder = os.path.join(
    webots_home, "projects", "robots", "softbank", "nao", "motions"
)

wave_motion = Motion(os.path.join(motion_folder, "HandWave.motion"))

# --- Socket ---
HOST = '127.0.0.1'
PORT = 65432
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))
client_socket.setblocking(False)
print("[Robot] Đã kết nối server")

# --- States ---
STATE_IDLE = 1
STATE_WAVING = 2
state = STATE_IDLE

print("[Robot] Đang chờ lệnh...")

while robot.step(time_step) != -1:
    received = None
    try:
        received = client_socket.recv(1024)
    except BlockingIOError:
        pass

    if state == STATE_IDLE:
        if received == b'STOP':
            print("[Robot] STOP (đứng yên)")

        elif received == b'WAVE':
            print("[Robot] WAVE")
            wave_motion.play()
            state = STATE_WAVING

    elif state == STATE_WAVING:
        if wave_motion.isOver():
            print("[Robot] Vẫy xong, quay lại chờ")
            state = STATE_IDLE

client_socket.close()
print("[Robot] Kết thúc")
