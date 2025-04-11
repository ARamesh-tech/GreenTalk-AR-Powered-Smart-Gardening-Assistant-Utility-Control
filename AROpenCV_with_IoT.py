import cv2
import mediapipe as mp
import requests
import speech_recognition as sr
import threading
import time

# Blynk API URLs
BLYNK_AUTH = "oqVvTjuTCSu7gj4_mOiyvl1ToIfarOtb"  # Replace with your Blynk token
LED_ON_URL = f"https://blynk.cloud/external/api/update?token={BLYNK_AUTH}&v0=1"
LED_OFF_URL = f"https://blynk.cloud/external/api/update?token={BLYNK_AUTH}&v0=0"
MOISTURE_URL = f"https://blynk.cloud/external/api/get?token={BLYNK_AUTH}&v1"  # Virtual pin V1 for moisture
LDR_URL = f"https://blynk.cloud/external/api/get?token={BLYNK_AUTH}&v2"  # Virtual pin V2 for LDR

# Initialize MediaPipe Hand tracking
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# Open webcam
cap = cv2.VideoCapture(0)
led_on = False

# Initialize Speech Recognizer
recognizer = sr.Recognizer()

# Set FPS limit
FPS = 10  # Desired FPS
frame_time = 1.0 / FPS

def recognize_speech():
    global led_on
    while True:
        with sr.Microphone() as source:
            print("Listening for voice commands...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            try:
                audio = recognizer.listen(source, timeout=10, phrase_time_limit=5)
                command = recognizer.recognize_google(audio).lower()
                print(f"Recognized: {command}")
                
                if "turn on" in command and not led_on:
                    print("Turning LED ON via Blynk (Voice)")
                    requests.get(LED_ON_URL)
                    led_on = True
                elif "turn off" in command and led_on:
                    print("Turning LED OFF via Blynk (Voice)")
                    requests.get(LED_OFF_URL)
                    led_on = False
            except sr.WaitTimeoutError:
                print("Listening timed out. No speech detected, retrying...")
            except sr.UnknownValueError:
                print("Could not understand the command")
            except sr.RequestError:
                print("Could not request results, check your internet connection")

# Run speech recognition in a separate thread
speech_thread = threading.Thread(target=recognize_speech, daemon=True)
speech_thread.start()

while cap.isOpened():
    start_time = time.time()
    
    ret, frame = cap.read()
    if not ret:
        continue

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    # Fetch soil moisture data from Blynk
    try:
        response = requests.get(MOISTURE_URL)
        moisture_level = response.text if response.status_code == 200 else "N/A"
    except:
        moisture_level = "Error"

    # Fetch LDR sensor data from Blynk
    try:
        response = requests.get(LDR_URL)
        ldr_value = response.text if response.status_code == 200 else "N/A"
    except:
        ldr_value = "Error"

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            x, y = int(index_finger_tip.x * frame.shape[1]), int(index_finger_tip.y * frame.shape[0])
            cv2.circle(frame, (x, y), 10, (0, 255, 0), -1)
            
            # Define ON/OFF button areas
            on_area = (50, 100, 150, 200)
            off_area = (250, 100, 350, 200)
            
            if on_area[0] < x < on_area[2] and on_area[1] < y < off_area[3] and not led_on:
                print("Turning LED ON via Blynk (Gesture)")
                requests.get(LED_ON_URL)
                led_on = True
            elif off_area[0] < x < off_area[2] and off_area[1] < y < off_area[3] and led_on:
                print("Turning LED OFF via Blynk (Gesture)")
                requests.get(LED_OFF_URL)
                led_on = False

    # Draw ON/OFF button areas
    cv2.rectangle(frame, (50, 100), (150, 200), (0, 255, 0), 2)
    cv2.putText(frame, "ON", (75, 175), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.rectangle(frame, (250, 100), (350, 200), (0, 0, 255), 2)
    cv2.putText(frame, "OFF", (275, 175), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    # Display soil moisture reading
    cv2.putText(frame, f"Moisture: {moisture_level}%", (400, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    # Display LDR sensor reading and environment status
    if ldr_value == "0":
        ldr_text = "Bright Environment - Sufficient Sunlight"
        ldr_color = (0, 255, 0)  # Green
    elif ldr_value == "1":
        ldr_text = "Dark Environment - Needs Sunlight"
        ldr_color = (0, 0, 255)  # Red
    else:
        ldr_text = "LDR Sensor Error"
        ldr_color = (0, 255, 255)  # Yellow

    cv2.putText(frame, ldr_text, (400, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, ldr_color, 2)

    cv2.imshow("AR Application - Multimodal interaction", frame)

    # FPS control
    elapsed_time = time.time() - start_time
    if elapsed_time < frame_time:
        time.sleep(frame_time - elapsed_time)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
