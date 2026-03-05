import cv2
import numpy as np


def resize_frame(frame: np.ndarray, width: int) -> np.ndarray:
    """Resize maintaining aspect ratio based on target width."""
    h, w = frame.shape[:2]
    if w == width:
        return frame
    ratio = width / float(w)
    dim = (width, int(h * ratio))
    return cv2.resize(frame, dim)


def blur_faces(frame: np.ndarray) -> np.ndarray:
    """Placeholder for face blurring logic; returns frame unchanged for now."""
    # TODO: integrate face detector and apply gaussian blur per face region
    return frame


def basic_noise_reduction(frame: np.ndarray) -> np.ndarray:
    """Apply simple noise reduction using Gaussian blur."""
    return cv2.GaussianBlur(frame, (5, 5), 0)
