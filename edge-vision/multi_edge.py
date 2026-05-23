import cv2
import requests
from ultralytics import YOLO
import time
import csv  # Added for CSV support

# USE THEIR VIDEO FILE
VIDEO_PATH = "project/videos/node2.mp4" 
SERVER_URL = "http://localhost:8000/api/alert"
CSV_FILE = "detection_results.csv"  # File name for storage

print("📷 Edge Node Starting...")
model = YOLO('yolov8n.pt')
cap = cv2.VideoCapture(VIDEO_PATH)

# Initialize CSV File and Header
with open(CSV_FILE, mode='w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["frame_id", "timestamp", "class_name", "confidence", "x1", "y1", "x2", "y2"])

alert_sent = False
frame_count = 0  # To track frame_id

while True:
    success, frame = cap.read()
    if not success: 
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0) # Loop video
        continue

    frame_count += 1
    # Calculate timestamp based on 20 frames = 1 second (0.05s per frame)
    timestamp = round(frame_count * 0.05, 2) 

    results = model(frame, stream=True)

    # Open CSV in append mode to log detections for this frame
    with open(CSV_FILE, mode='a', newline='') as f:
        writer = csv.writer(f)
        
        for r in results:
            boxes = r.boxes
            for box in boxes:
                cls = int(box.cls[0])
                label = model.names[cls]
                conf = round(float(box.conf[0]), 2)
                x1, y1, x2, y2 = map(int, box.xyxy[0])

                # LOG TO CSV
                writer.writerow([frame_count, timestamp, label, conf, x1, y1, x2, y2])

                # Draw Box (Rest of your code remains the same)
                color = (0, 0, 255) if label in ["truck", "bus", "car"] else (0, 255, 0)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

                # TRIGGER! 
                if label in ["truck", "bus"] and not alert_sent:
                    print(f"🚀 EMERGENCY VEHICLE ({label}) DETECTED! Sending Signal...")
                    try:
                        requests.post(SERVER_URL, json={"vehicle_type": "AMBULANCE_PRIORITY"})
                        alert_sent = True 
                    except: print("Server Offline")

    cv2.imshow("ResQRoute Edge Cam", frame)
    if cv2.waitKey(1) == ord('q'): break

cap.release()
cv2.destroyAllWindows()