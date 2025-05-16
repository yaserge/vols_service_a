import numpy as np
from app.models.thermogram import Thermogram
from typing import Dict

class Detector:
    def __init__(self,
                 thresholds: Dict[str, float],
                 area_config: dict,
                 # hot_th: float, cold_th: float
                 ) -> None:
        self.area_config = area_config
        self.thresholds = {
            area_name: area_config[area_name]['threshold']
            for area_name in area_config.keys()
        }
        self.threshold_direction_is_up = {
            area_name: area_config[area_name]['threshold_direction_is_up']
            for area_name in area_config.keys()
        }

        self.current_event_mask = None
        self.prev_event_mask = None

    # TODO: add threshold direction, range
    def detect_event(self, thermogram: Thermogram) -> None:
        print("starting detect_event")
        if self.current_event_mask is not None:
            self.prev_event_mask = self.current_event_mask
        print(f"thermogram.thermogram shape: {thermogram.thermogram.shape}")
        self.current_event_mask = thermogram.thermogram > np.array(list(self.thresholds.values()))[:, np.newaxis]
        print(f"self.current_event_mask shape: {self.current_event_mask.shape}")

    def get_event_start(self) -> np.ndarray:
        if self.prev_event_mask is None:
            return np.array(self.current_event_mask, bool)

        return self.current_event_mask > self.prev_event_mask

    def get_event_stop(self) -> np.ndarray:
        if self.prev_event_mask is None:
            return np.zeros_like(self.current_event_mask, dtype=bool)

        return self.current_event_mask < self.prev_event_mask
