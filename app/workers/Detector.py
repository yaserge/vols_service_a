import numpy as np
from app.models.thermogram import Thermogram

class Detector:
    def __init__(self, hot_th: float, cold_th: float) -> None:
        self.hot_th = hot_th
        self.cold_th = cold_th

        self.current_hot_mask = None
        self.prev_hot_mask = None

        self.current_cold_mask = None
        self.prev_cold_mask = None

    def detect_hot_leak(self, termogram: Thermogram) -> None:
        if self.current_hot_mask is not None:
            self.prev_hot_mask = self.current_hot_mask    
        self.current_hot_mask = termogram.thermogram > self.hot_th
        
    def detect_cold_leak(self, termogram: Thermogram) -> None:
        if self.current_cold_mask is not None:
            self.prev_cold_mask = self.current_cold_mask    
        self.current_cold_mask = termogram.thermogram < self.cold_th
        
    def get_hot_leak_start(self) -> np.ndarray:
        if self.prev_hot_mask is None:
            return np.array(self.current_hot_mask, bool)
        
        return self.current_hot_mask > self.prev_hot_mask

    def get_hot_leak_stop(self) -> np.ndarray:
        if self.prev_hot_mask is None:
            return np.zeros_like(self.current_hot_mask, dtype=bool)
        
        return self.current_hot_mask < self.prev_hot_mask

    def get_cold_leak_start(self) -> np.ndarray:
        if self.prev_cold_mask is None:
            return self.current_cold_mask
        
        return self.current_cold_mask > self.prev_cold_mask

    def get_cold_leak_stop(self) -> np.ndarray:
        if self.prev_cold_mask is None:
            return np.zeros_like(self.current_cold_mask, dtype=bool)
        
        return self.current_cold_mask < self.prev_cold_mask
