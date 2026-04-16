import numpy as np
import cv2
from scipy.ndimage import gaussian_filter

class HeatmapGenerator:
    """Generates and processes density heatmaps for crowd visualization."""

    def __init__(self, sigma: float = 25.0):
        self.sigma = sigma

    def generate(self, boxes: list, frame_shape: tuple) -> np.ndarray:
        """Plot centroids, apply Gaussian blur, and normalize.
        
        Args:
            boxes: List of bounding boxes [x1, y1, x2, y2].
            frame_shape: (height, width, channels) or (height, width).
            
        Returns:
            Normalized float32 heatmap array (0 to 1).
        """
        h, w = frame_shape[:2]
        heatmap = np.zeros((h, w), dtype=np.float32)

        for box in boxes:
            x1, y1, x2, y2 = box
            # Calculate centroid
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)
            
            # Bounds check and increment count at centroid
            if 0 <= cx < w and 0 <= cy < h:
                heatmap[cy, cx] += 1.0

        # Apply spatial smoothing
        heatmap = gaussian_filter(heatmap, sigma=self.sigma)

        # Rescale to [0, 1]
        max_val = np.max(heatmap)
        if max_val > 0:
            heatmap = heatmap / max_val

        return heatmap

    def to_overlay(self, heatmap: np.ndarray, frame_shape: tuple = None) -> np.ndarray:
        """Convert normalized heatmap to colored BGR overlay, sized to match frame.
        
        Args:
            heatmap: Normalized float32 heatmap (0 to 1).
            frame_shape: Optional (height, width) to ensure output matches frame.
            
        Returns:
            BGR array matching frame dimensions.
        """
        # Ensure heatmap matches target frame size
        if frame_shape is not None:
            h, w = frame_shape[:2]
            if heatmap.shape != (h, w):
                heatmap = cv2.resize(heatmap, (w, h))
        
        # 1. Scale to grayscale uint8 for colormap
        h_uint8 = (heatmap * 255).astype(np.uint8)
        
        # 2. Apply JET colormap (returns BGR with proper size)
        color_map = cv2.applyColorMap(h_uint8, cv2.COLORMAP_JET)
        
        return color_map

    def generate_full(self, boxes: list, frame_shape: tuple) -> tuple:
        """Plot centroids, apply blur, normalize, and return (raw_matrix, colored_frame)."""
        heatmap_raw = self.generate(boxes, frame_shape)
        heatmap_frame = self.to_overlay(heatmap_raw, frame_shape)
        return heatmap_raw, heatmap_frame
