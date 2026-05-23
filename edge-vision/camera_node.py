import cv2
import requests
from ultralytics import YOLO
import time

# USE THEIR VIDEO FILE
VIDEO_PATH = "project/videos/intersection1.mp4" 
SERVER_URL = "http://localhost:8000/api/alert"

print("📷 Edge Node Starting...")
model = YOLO('yolov8n.pt')
cap = cv2.VideoCapture(VIDEO_PATH)

alert_sent = False

while True:
    success, frame = cap.read()
    if not success: 
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0) # Loop video
        continue

    results = model(frame, stream=True)

    for r in results:
        boxes = r.boxes
        for box in boxes:
            cls = int(box.cls[0])
            label = model.names[cls]

            # Draw Box
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            color = (0, 0, 255) if label in ["truck", "bus", "car"] else (0, 255, 0)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            # TRIGGER! (Using 'car'/'truck' to test since video might not have ambulance)
            if label in ["truck", "bus"] and not alert_sent:
                print(f"🚀 EMERGENCY VEHICLE ({label}) DETECTED! Sending Signal...")
                try:
                    requests.post(SERVER_URL, json={"vehicle_type": "AMBULANCE_PRIORITY"})
                    alert_sent = True # Don't spam
                except: print("Server Offline")

    cv2.imshow("ResQRoute Edge Cam", frame)
    if cv2.waitKey(1) == ord('q'): break

cap.release()
cv2.destroyAllWindows()