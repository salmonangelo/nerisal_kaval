import numpy as np
from typing import List, Tuple, Dict

def compute_grid_density(boxes: List[Tuple], frame_shape: Tuple[int, int], grid_size: Tuple[int, int] = (5, 5)) -> Dict:
    """Computes density of people across an NxM grid.
    
    Args:
        boxes: List of bounding boxes [x1, y1, x2, y2]
        frame_shape: (height, width) or (height, width, channels) of the frame
        grid_size: (rows, cols)
        
    Returns:
        Dict:
            - grid_counts: 2D numpy array of counts
            - max_density_cell: max count in any single cell
            - total_count: int
            - hotspots: List of (row, col) with max density
    """
    rows, cols = grid_size
    height, width = frame_shape[:2]
    
    grid = np.zeros((rows, cols), dtype=np.int32)
    
    if not boxes:
        return {
            "grid_counts": grid.tolist(),
            "max_density_cell": 0,
            "total_count": 0,
            "hotspots": []
        }
        
    for box in boxes:
        x1, y1, x2, y2 = box
        # use bottom-center point
        bx = (x1 + x2) / 2.0
        by = y2
        
        # calculate cell indices
        col_idx = int((bx / width) * cols)
        row_idx = int((by / height) * rows)
        
        # clamp to max index
        col_idx = max(0, min(cols - 1, col_idx))
        row_idx = max(0, min(rows - 1, row_idx))
        
        grid[row_idx, col_idx] += 1
        
    max_density = int(np.max(grid))
    hotspots = []
    if max_density > 0:
        hotspots_coords = np.argwhere(grid == max_density)
        hotspots = [(int(r), int(c)) for r, c in hotspots_coords]
        
    return {
        "grid_counts": grid.tolist(),
        "max_density_cell": max_density,
        "total_count": len(boxes),
        "hotspots": hotspots
    }
