import cv2
import numpy as np

class Inspector:
    def __init__(self):
        # ORB detector for feature matching
        self.orb = cv2.ORB_create(nfeatures=5000)
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        self.last_registration_ok = True
        self.last_match_count = 0
        self.last_transform = {}

    def align_images(self, master: np.ndarray, live: np.ndarray):
        """
        Aligns the live image to the master image using feature matching.
        """
        # Convert to grayscale
        gray_master = cv2.cvtColor(master, cv2.COLOR_BGR2GRAY)
        gray_live = cv2.cvtColor(live, cv2.COLOR_BGR2GRAY)

        # Detect keypoints and descriptors
        kp1, des1 = self.orb.detectAndCompute(gray_master, None)
        kp2, des2 = self.orb.detectAndCompute(gray_live, None)

        if des1 is None or des2 is None:
            print("Warning: No features found")
            self.last_registration_ok = False
            self.last_match_count = 0
            height, width, _ = master.shape
            aligned_live = cv2.resize(live, (width, height)) if live.shape[:2] != (height, width) else live
            return aligned_live, {"matches": 0, "dx": 0.0, "dy": 0.0, "rotation_deg": 0.0, "scale_x": 1.0, "scale_y": 1.0}

        # Match descriptors
        matches = self.matcher.match(des1, des2)
        matches = sorted(matches, key=lambda x: x.distance)

        # Keep top matches
        num_matches = int(len(matches) * 0.15)
        matches = matches[:num_matches]
        self.last_match_count = len(matches)

        if len(matches) < 4:
            print("Warning: Not enough matches for homography")
            self.last_registration_ok = False
            height, width, _ = master.shape
            aligned_live = cv2.resize(live, (width, height)) if live.shape[:2] != (height, width) else live
            return aligned_live, {"matches": len(matches), "dx": 0.0, "dy": 0.0, "rotation_deg": 0.0, "scale_x": 1.0, "scale_y": 1.0}

        # Extract location of good matches
        points1 = np.zeros((len(matches), 2), dtype=np.float32)
        points2 = np.zeros((len(matches), 2), dtype=np.float32)

        for i, match in enumerate(matches):
            points1[i, :] = kp1[match.queryIdx].pt
            points2[i, :] = kp2[match.trainIdx].pt

        # Find Homography
        h, mask = cv2.findHomography(points2, points1, cv2.RANSAC)

        if h is None:
            self.last_registration_ok = False
            height, width, _ = master.shape
            aligned_live = cv2.resize(live, (width, height)) if live.shape[:2] != (height, width) else live
            return aligned_live, {"matches": len(matches), "dx": 0.0, "dy": 0.0, "rotation_deg": 0.0, "scale_x": 1.0, "scale_y": 1.0}

        self.last_registration_ok = True
        dx = float(h[0, 2])
        dy = float(h[1, 2])
        rotation_deg = float(np.degrees(np.arctan2(h[1, 0], h[0, 0])))
        scale_x = float(np.sqrt(h[0, 0] ** 2 + h[1, 0] ** 2))
        scale_y = float(np.sqrt(h[0, 1] ** 2 + h[1, 1] ** 2))
        self.last_transform = {
            "matches": len(matches),
            "dx": dx,
            "dy": dy,
            "rotation_deg": rotation_deg,
            "scale_x": scale_x,
            "scale_y": scale_y
        }

        # Warps live image to match master
        height, width, channels = master.shape
        aligned_live = cv2.warpPerspective(live, h, (width, height))

        return aligned_live, self.last_transform

    def compare_images(self, master: np.ndarray, aligned_live: np.ndarray, diff_threshold: int = 30, min_blob_area: int = 50):
        """
        Compares two aligned images and returns the difference map and defect list.
        """
        if master.shape[:2] != aligned_live.shape[:2]:
            aligned_live = cv2.resize(aligned_live, (master.shape[1], master.shape[0]))
        # Absolute difference
        diff = cv2.absdiff(master, aligned_live)
        
        # Convert to grayscale
        gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        
        # Threshold to separate defect from noise
        _, thresh = cv2.threshold(gray_diff, diff_threshold, 255, cv2.THRESH_BINARY)
        
        # Morphological operations to clean up noise
        kernel = np.ones((5,5), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        
        # Generate Heatmap (JET colormap on difference)
        # Normalize diff for visualization
        norm_diff = cv2.normalize(gray_diff, None, 0, 255, cv2.NORM_MINMAX)
        heatmap = cv2.applyColorMap(norm_diff, cv2.COLORMAP_JET)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        defects = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > min_blob_area: # Minimum defect size
                x, y, w, h = cv2.boundingRect(cnt)
                defects.append({"x": x, "y": y, "w": w, "h": h, "area": area})
                
        return diff, thresh, heatmap, defects
