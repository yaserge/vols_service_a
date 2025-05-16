import pickle
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import numpy as np
from bson import Binary, ObjectId
from pydantic import BaseModel, ConfigDict, Field
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema


@dataclass
class LeakMask:
    hot_leak: np.ndarray
    cold_leak: np.ndarray
    length: np.ndarray
    date_time: datetime

    @property
    def total_hot_leaks(self) -> int:
        """Общее количество горячих утечек"""
        return int(np.sum(self.hot_leak))

    @property
    def total_cold_leaks(self) -> int:
        """Общее количество холодных утечек"""
        return int(np.sum(self.cold_leak))

    @property
    def dx(self) -> float:
        """Шаг по длине (как в Thermogram)"""
        return np.abs(self.length[1] - self.length[0])

    def to_dict(self) -> dict:
        """Конвертация в словарь для MongoDB"""
        return {
            "hot_leak": Binary(pickle.dumps(self.hot_leak)),
            "cold_leak": Binary(pickle.dumps(self.cold_leak)),
            "length": Binary(pickle.dumps(self.length)),
            "date_time": self.date_time,
            "metadata": {"total_hot": self.total_hot_leaks, "total_cold": self.total_cold_leaks, "dx": self.dx},
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LeakMask":
        """Создание объекта из данных MongoDB"""
        return dict(
            hot_leak=pickle.loads(data["hot_leak"]).tolist(),
            cold_leak=pickle.loads(data["cold_leak"]).tolist(),
            length=pickle.loads(data["length"]).tolist(),
            date_time=data["date_time"],
        )


class LeakMaskInDB(BaseModel):
    id: str = Field(..., alias="_id")
    hot_leak: bytes
    cold_leak: bytes
    length: bytes
    date_time: datetime

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat(), ObjectId: str},
        arbitrary_types_allowed=True,
        populate_by_name=True,
    )
