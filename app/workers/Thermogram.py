from dataclasses import dataclass
from datetime import datetime

import numpy as np

@dataclass
class Thermogram:
    thermogram: np.ndarray[float]
    length: np.ndarray[float]
    date_time: datetime
    temperature_ballast: float
    channel_num: int
    measure_time: float
          
    @property
    def dx(self) -> float:
        return np.abs(self.length[1] - self.length[0])
