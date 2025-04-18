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
class Thermogram:
    thermogram: np.ndarray
    length: np.ndarray
    date_time: datetime
    temperature_ballast: float
    channel_num: int
    measure_time: float

    @property
    def dx(self) -> float:
        return np.abs(self.length[1] - self.length[0])

    def to_dict(self) -> dict:
        """Конвертация в словарь для MongoDB"""
        return {
            "thermogram": Binary(pickle.dumps(self.thermogram)),
            "length": Binary(pickle.dumps(self.length)),
            "date_time": self.date_time,
            "temperature_ballast": self.temperature_ballast,
            "channel_num": self.channel_num,
            "measure_time": self.measure_time,
            "dx": self.dx,  # Сохраняем вычисляемое свойство
        }

    @classmethod
    def from_dict(cls, data: dict) -> dict:
        """Создание объекта из данных MongoDB"""
        return dict(
            thermogram=pickle.loads(data["thermogram"]).tolist(),
            length=pickle.loads(data["length"]).tolist(),
            date_time=data["date_time"],
            temperature_ballast=data["temperature_ballast"],
            channel_num=data["channel_num"],
            measure_time=data["measure_time"],
        )


class PyObjectId(str):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):
        return core_schema.no_info_after_validator_function(
            cls.validate,
            core_schema.str_schema(),
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)


class ThermogramInDB(BaseModel):
    id: str = Field(..., alias="_id")
    thermogram: bytes
    length: bytes
    date_time: datetime
    temperature_ballast: float
    channel_num: int
    measure_time: float
    dx: float

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat(), ObjectId: str},
        arbitrary_types_allowed=True,
        populate_by_name=True,
    )

    @classmethod
    def from_mongo(cls, data: dict):
        """Конвертирует данные из MongoDB в модель"""
        if not data:
            return None
        data["id"] = str(data["_id"])  # Конвертируем ObjectId в строку
        return cls(**data)
