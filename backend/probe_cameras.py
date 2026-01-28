import cv2

print("Scanning for cameras...")
found = False
for i in range(10):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f"Found camera at index {i}")
        found = True
        cap.release()
print(f"Scan complete. Found any? {found}")
