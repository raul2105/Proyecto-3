import cv2
import numpy as np

class Diagnostics:
    
    @staticmethod
    def calculate_image_quality(image: np.ndarray):
        """
        Calculates basic image quality metrics:
        - Brightness: Mean pixel intensity
        - Blur: Variance of Laplacian (Higher is sharper)
        - Contrast: Standard deviation of pixel intensity
        """
        if image is None:
            return {"brightness": 0, "blur": 0, "contrast": 0}
            
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        brightness = np.mean(gray)
        contrast = np.std(gray)
        
        # Laplacan variance for blur detection
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        blur_score = laplacian.var()
        
        return {
            "brightness": float(brightness),
            "blur_score": float(blur_score),
            "contrast": float(contrast)
        }
