from controller import Robot
import socket
import json
import time

robot = Robot()
timestep = int(robot.getBasicTimeStep())

# ================== DEVICES ==================
def motor(name):
    m = robot.getDevice(name)
    m.setVelocity(1.5)
    return m

shoulder = motor("LShoulderPitch")
head_pitch = motor("HeadPitch")
head_yaw = motor("HeadYaw")
led = robot.getDevice("ChestBoard/Led")

# ================== ACTION STATE ==================
is_busy = False
last_action_time = 0
ACTION_DELAY = 5.0  # seconds

# ================== ACTIONS ==================
def stop_all():
    global is_busy
    shoulder.setPosition(0.0)
    head_pitch.setPosition(0.0)
    head_yaw.setPosition(0.0)
    led.set(0)
    is_busy = False
    print("🛑 STOP - Robot idle")

def wave():
    shoulder.setPosition(-0.8)

def nod():
    head_pitch.setPosition(0.4)

def shake():
    head_yaw.setPosition(0.6)

def led_on():
    led.set(1)

COMMANDS = {
    "WAVE": wave,
    "NOD": nod,
    "SHAKE": shake,
    "LED_ON": led_on,
    "STOP": stop_all
}

# ================== SOCKET ==================
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("0.0.0.0", 65432))
server.listen(1)
server.setblocking(False)

print("🤖 NAO Controller Ready")

while robot.step(timestep) != -1:
    now = time.time()

    # ---------- AUTO UNLOCK ----------
    if is_busy and (now - last_action_time) >= ACTION_DELAY:
        is_busy = False
        print("✅ Action finished, ready for next")

    try:
        conn, _ = server.accept()
        data = json.loads(conn.recv(1024).decode())
        cmd = data.get("command")
        conn.close()

        print("📥", cmd)

        # ---------- STOP ALWAYS PRIORITY ----------
        if cmd == "STOP":
            stop_all()
            continue

        # ---------- BLOCK IF BUSY ----------
        if is_busy:
            print("⏳ Robot busy, command ignored")
            continue

        # ---------- EXECUTE ----------
        if cmd in COMMANDS:
            COMMANDS[cmd]()
            is_busy = True
            last_action_time = time.time()
            print(f"▶ Executing {cmd}, locked for {ACTION_DELAY}s")

    except:
        pass
