import cv2
import numpy as np
import random

class DefectSimulator:
    def __init__(self):
        pass

    def add_defects(self, image: np.ndarray, count=3) -> np.ndarray:
        """
        Adds synthetic defects (blobs/lines) to the image.
        :param image: Source image (OpenCV format)
        :param count: Number of defects to add
        :return: Image with defects
        """
        defective_image = image.copy()
        h, w, _ = defective_image.shape

        for _ in range(count):
            defect_type = random.choice(['blob', 'line'])
            
            # Random color (usually dark like ink or paper white)
            color = (0, 0, 255) if random.random() > 0.5 else (0, 0, 0) # BGR
            
            x = random.randint(0, w-1)
            y = random.randint(0, h-1)

            if defect_type == 'blob':
                radius = random.randint(5, 20)
                cv2.circle(defective_image, (x, y), radius, color, -1)
            elif defect_type == 'line':
                x2 = x + random.randint(-50, 50)
                y2 = y + random.randint(-50, 50)
                thickness = random.randint(2, 5)
                cv2.line(defective_image, (x, y), (x2, y2), color, thickness)
                
        return defective_image
