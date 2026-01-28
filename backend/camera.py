import cv2
import numpy as np
import platform

class CameraService:
    def __init__(self):
        self.cap = None
        self.current_camera_id = None

    def _open_capture(self, camera_id: int):
        if platform.system().lower().startswith("win"):
            cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
            if cap.isOpened():
                return cap
            cap.release()
            cap = cv2.VideoCapture(camera_id, cv2.CAP_MSMF)
            if cap.isOpened():
                return cap
            cap.release()
            return cv2.VideoCapture(camera_id)
        return cv2.VideoCapture(camera_id)

    def _probe_capture(self, camera_id: int):
        if platform.system().lower().startswith("win"):
            return cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
        return cv2.VideoCapture(camera_id)

    def list_cameras(self):
        """
        Scans for available cameras.
        Note: OpenCV doesn't natively list devices reliably on all OSs without probing.
        We will probe the first 5 indices.
        """
        available_cameras = []
        # Add a Virtual Camera for testing logic without hardware
        available_cameras.append({"id": -1, "name": "Virtual Test Camera"})

        for i in range(5):
            cap = self._probe_capture(i)
            if cap.isOpened():
                available_cameras.append({"id": i, "name": f"Camera {i}"})
                cap.release()
        return available_cameras

    def connect(self, camera_id: int, fallback_to_virtual: bool = True):
        """
        Connect to camera with optional fallback to virtual camera
        
        Args:
            camera_id: Camera index to connect (-1 for virtual)
            fallback_to_virtual: If True, switch to virtual camera if real camera fails
        
        Returns:
            dict with connection status and actual camera used
        """
        if self.cap is not None and isinstance(self.cap, cv2.VideoCapture):
            self.cap.release()
        
        self.current_camera_id = camera_id
        
        # Virtual camera requested
        if camera_id == -1:
            self.cap = "VIRTUAL"
            return {
                "success": True,
                "camera_id": -1,
                "camera_name": "Virtual Test Camera",
                "message": "Connected to Virtual Camera"
            }
        
        # Try to open real camera
        self.cap = self._open_capture(camera_id)
        
        # If failed and fallback enabled, switch to virtual
        if not self.cap.isOpened():
            if fallback_to_virtual:
                self.cap = "VIRTUAL"
                self.current_camera_id = -1
                return {
                    "success": True,
                    "camera_id": -1,
                    "camera_name": "Virtual Test Camera (Fallback)",
                    "warning": f"Could not open camera {camera_id}, switched to Virtual Camera"
                }
            else:
                raise Exception(f"Could not open camera {camera_id}")

        # Set default resolution (can be parameterized later)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        return {
            "success": True,
            "camera_id": camera_id,
            "camera_name": f"Camera {camera_id}",
            "message": "Connected to real camera"
        }

    def get_frame(self):
        if self.cap == "VIRTUAL":
            # Generate a test pattern
            img = np.zeros((720, 1280, 3), dtype=np.uint8)
            # Draw some moving graphics based on time (mock)
            import time
            t = time.time()
            cv2.putText(img, f"Virtual Camera Test {t:.2f}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            # Moving rectangle
            x = int((t * 100) % 1200)
            cv2.rectangle(img, (x, 200), (x+100, 300), (0, 255, 0), -1)
            return img

        if self.cap is None or (isinstance(self.cap, cv2.VideoCapture) and not self.cap.isOpened()):
             raise Exception("Camera not connected")
        
        ret, frame = self.cap.read()
        if not ret:
            raise Exception("Failed to read frame")
        return frame

    def set_settings(self, exposure=None, gain=None):
        if self.cap is None or self.cap == "VIRTUAL":
            return
        
        # Note: exposure mapping depends on camera driver
        if exposure is not None:
             try:
                self.cap.set(cv2.CAP_PROP_EXPOSURE, exposure)
             except:
                 pass
        
        if gain is not None:
             try:
                self.cap.set(cv2.CAP_PROP_GAIN, gain)
             except:
                 pass

    def release(self):
        if self.cap is not None and isinstance(self.cap, cv2.VideoCapture):
            self.cap.release()
        self.cap = None
