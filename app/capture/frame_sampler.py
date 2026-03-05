import cv2
import numpy as np
from ..config import FRAME_INTERVAL_SECONDS


class FrameSampler:
    def __init__(self, source: str, interval: float = FRAME_INTERVAL_SECONDS):
        self.source = source
        self.interval = interval
        self.cap = cv2.VideoCapture(source)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
        self.step = int(self.fps * self.interval)
        self.idx = 0

    def __iter__(self):
        return self

    def __next__(self) -> np.ndarray:
        if not self.cap.isOpened():
            raise StopIteration
        while True:
            ret, frame = self.cap.read()
            if not ret:
                self.cap.release()
                raise StopIteration
            if self.idx % self.step == 0:
                self.idx += 1
                return frame
            self.idx += 1

    def close(self):
        if self.cap.isOpened():
            self.cap.release()


if __name__ == "__main__":
    # simple standalone test: open default camera and print frame shapes
    sampler = FrameSampler(0)
    try:
        for i, frame in enumerate(sampler):
            print(f"Captured frame {i}: shape {frame.shape}")
            if i >= 5:
                break
    except Exception as e:
        print(f"sampling error: {e}")
    finally:
        sampler.close()
