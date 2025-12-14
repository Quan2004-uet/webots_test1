import cv2
import mediapipe as mp
import socket

# --- Mediapipe ---
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# --- Socket ---
HOST = '127.0.0.1'
PORT = 65432
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen()
print("[Server] Đang chờ robot kết nối...")
conn, addr = server_socket.accept()
print(f"[Server] Robot đã kết nối từ {addr}")

# --- Camera ---
cap = cv2.VideoCapture(0)
tip_ids = [4, 8, 12, 16, 20]

# --- States ---
STATE_IDLE = 1
STATE_WAIT_HAND_DOWN = 2
STATE_WAIT_WAVE = 3

state = STATE_IDLE
state_str = "IDLE (5 ngón = STOP)"

while cap.isOpened() and conn:
    ret, image = cap.read()
    if not ret:
        continue

    image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
    results = hands.process(image)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    finger_count = 0

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            fingers = []
            fingers.append(
                1 if hand_landmarks.landmark[4].x <
                hand_landmarks.landmark[3].x else 0
            )
            for i in range(1, 5):
                fingers.append(
                    1 if hand_landmarks.landmark[tip_ids[i]].y <
                    hand_landmarks.landmark[tip_ids[i] - 2].y else 0
                )
            finger_count = sum(fingers)

    try:
        if state == STATE_IDLE and finger_count == 5:
            conn.sendall(b'STOP')
            print("[Server] Gửi STOP")
            state = STATE_WAIT_HAND_DOWN
            state_str = "WAIT_HAND_DOWN"

        elif state == STATE_WAIT_HAND_DOWN and finger_count < 5:
            state = STATE_WAIT_WAVE
            state_str = "WAIT_WAVE (5 ngón = WAVE)"

        elif state == STATE_WAIT_WAVE and finger_count == 5:
            conn.sendall(b'WAVE')
            print("[Server] Gửi WAVE")
            state = STATE_WAIT_HAND_DOWN
            state_str = "WAIT_HAND_DOWN"

    except Exception as e:
        print("Lỗi socket:", e)
        break

    cv2.putText(image, f'Fingers: {finger_count}', (10, 70),
                cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 255), 2)
    cv2.putText(image, f'State: {state_str}', (10, 120),
                cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)

    cv2.imshow("Hand Detection", image)
    if cv2.waitKey(5) & 0xFF == 27:
        break

cap.release()
conn.close()
server_socket.close()
cv2.destroyAllWindows()
