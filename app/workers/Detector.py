import numpy as np
from app.models.thermogram import Thermogram
from typing import Dict


# TODO: check everywhere if dict iteration is fixed, maybe change to ordereddict
def create_range_mask(length, area_ranges):
    range_mask = np.zeros_like(length, dtype=int)
    for i in range(length.shape[0]):
        for (range_start, range_end,) in area_ranges:
            if range_start <= length[i] <= range_end:
                range_mask[i] = 1
    return range_mask


def create_ranges_mask(length, areas_ranges):
    ranges_mask = np.vstack([
        create_range_mask(length, areas_ranges[area])
        for area in areas_ranges
    ])
    return ranges_mask


class Detector:
    def __init__(self,
                 area_config: dict,
                 # hot_th: float, cold_th: float
                 ) -> None:
        self.area_config = area_config
        self.thresholds = {
            area_name: area_config[area_name]['threshold']
            for area_name in area_config.keys()
        }
        self.threshold_direction_sign = {
            area_name: area_config[area_name]['threshold_direction_sign']
            for area_name in area_config.keys()
        }

        self.ranges = {
            area_name: area_config[area_name]['ranges']
            for area_name in area_config.keys()
        }

        self.current_event_mask = None
        self.prev_event_mask = None

    # TODO: add threshold direction, range
    def detect_event(self, thermogram: Thermogram) -> None:
        print("starting detect_event")
        if self.current_event_mask is not None:
            self.prev_event_mask = self.current_event_mask
            print("prev_event_mask updated")

        print(f"thermogram.thermogram shape: {thermogram.thermogram.shape}")

        self.current_event_mask = ((
            (thermogram.thermogram
             * np.array(list(self.threshold_direction_sign.values()))[:, np.newaxis]
             ) > (
                np.array(list(self.thresholds.values()))[:, np.newaxis]
                * np.array(list(self.threshold_direction_sign.values()))[:, np.newaxis]
            )
        ))
        print("current_event_mask calculated")


        # print(f"self.current_event_mask shape: {self.current_event_mask.shape}")

        ranges_mask = create_ranges_mask(thermogram.length, self.ranges)
        # print(f"ranges_mask shape: {ranges_mask.shape}")

        self.current_event_mask = self.current_event_mask * ranges_mask
        # print(f"self.current_event_mask shape: {self.current_event_mask.shape}")
        print("current_event_mask and ranges_mask updated")


    def get_event_start(self) -> np.ndarray:
        if self.prev_event_mask is None:
            return np.array(self.current_event_mask, bool)
        print(self.current_event_mask.shape, self.prev_event_mask.shape)

        return self.current_event_mask > self.prev_event_mask

    def get_event_stop(self) -> np.ndarray:
        if self.prev_event_mask is None:
            return np.zeros_like(self.current_event_mask, dtype=bool)

        return self.current_event_mask < self.prev_event_mask
