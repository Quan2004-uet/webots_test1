import cv2
import mediapipe as mp
import socket
import threading
import time
import whisper
import sounddevice as sd
import numpy as np

# ================= SOCKET =================
HOST = '127.0.0.1'
PORT = 65432

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

print("[Client] Đang chờ Webots kết nối...")
while True:
    try:
        sock.connect((HOST, PORT))
        print("[Client] Đã kết nối robot")
        break
    except ConnectionRefusedError:
        time.sleep(1)

# ================= WHISPER =================
model = whisper.load_model("base")
SAMPLE_RATE = 16000
RECORD_TIME = 3
last_voice_cmd = 0

def listen_voice():
    global last_voice_cmd
    WAVE_KEYWORDS = ["wave", "hello", "hi", "bye", "bai"]

    while True:
        audio = sd.rec(
            int(RECORD_TIME * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype=np.float32
        )
        sd.wait()

        result = model.transcribe(audio.flatten(), language="en")
        text = result["text"].lower().strip()
        print("[Voice]", text)

        now = time.time()
        if now - last_voice_cmd < 3:
            continue

        # --- STOP ---
        if "stop" in text:
            sock.sendall(b"STOP")
            print("[Voice] Gửi STOP")
            last_voice_cmd = now

        # --- WAVE ---
        elif any(word in text for word in WAVE_KEYWORDS):
            sock.sendall(b"WAVE")
            print("[Voice] Gửi WAVE")
            last_voice_cmd = now


# ================= HAND DETECTION =================
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils
tip_ids = [4, 8, 12, 16, 20]

STATE_IDLE = 1
STATE_WAIT_HAND_DOWN = 2
STATE_WAIT_WAVE = 3
state = STATE_IDLE

last_hand_cmd = 0

cap = cv2.VideoCapture(0)

# ================= START VOICE THREAD =================
threading.Thread(target=listen_voice, daemon=True).start()

# ================= MAIN LOOP =================
while cap.isOpened():
    ret, img = cap.read()
    if not ret:
        continue

    img = cv2.flip(img, 1)
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    finger_count = 0
    if results.multi_hand_landmarks:
        for hand in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(img, hand, mp_hands.HAND_CONNECTIONS)

            fingers = []
            fingers.append(1 if hand.landmark[4].x < hand.landmark[3].x else 0)
            for i in range(1, 5):
                fingers.append(
                    1 if hand.landmark[tip_ids[i]].y <
                    hand.landmark[tip_ids[i] - 2].y else 0
                )
            finger_count = sum(fingers)

    now = time.time()
    if now - last_hand_cmd > 2:
        if state == STATE_IDLE and finger_count == 5:
            sock.sendall(b"STOP")
            print("[Hand] STOP")
            state = STATE_WAIT_HAND_DOWN
            last_hand_cmd = now

        elif state == STATE_WAIT_HAND_DOWN and finger_count < 5:
            state = STATE_WAIT_WAVE

        elif state == STATE_WAIT_WAVE and finger_count == 5:
            sock.sendall(b"WAVE")
            print("[Hand] WAVE")
            state = STATE_WAIT_HAND_DOWN
            last_hand_cmd = now

    cv2.putText(img, f"Fingers: {finger_count}", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)

    cv2.imshow("Hand + Voice Control", img)
    if cv2.waitKey(5) & 0xFF == 27:
        break

cap.release()
sock.close()
cv2.destroyAllWindows()
