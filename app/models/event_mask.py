import pickle
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import numpy as np
from bson import Binary, ObjectId
from itertools import groupby
from pydantic import BaseModel, ConfigDict, Field
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema


def collapse_events_row(row):
    groups = [list(g) for _, g in groupby(row)]
    output_vector = [sum(1 for x in groups[:i] for _ in x) + len(x) // 2 for i, x in enumerate(groups)]
    collapsed_row_mask = np.zeros_like(row)
    np.put(collapsed_row_mask, output_vector, 1)
    return row * collapsed_row_mask


def collapse_events(arr):
    return np.apply_along_axis(collapse_events_row, 1, arr)


@dataclass
class EventMask:
    event: np.ndarray
    length: np.ndarray
    date_time: datetime
    named_dict: dict

    @property
    def total_events(self) -> int:
        """Общее количество событий"""
        return int(np.sum(self.event))

    @property
    def dx(self) -> float:
        """Шаг по длине (как в Thermogram)"""
        return np.abs(self.length[1] - self.length[0])

    def to_dict(self) -> dict:
        """Конвертация в словарь для MongoDB"""
        return {
            "event": Binary(pickle.dumps(self.event)),
            "length": Binary(pickle.dumps(self.length)),
            "date_time": self.date_time,
            "metadata": {"total_event": self.total_events, "dx": self.dx},
        }

    # def to_dict(self) -> dict:
    #     """Конвертация в словарь для MongoDB"""
    #     return_dict = {
    #         "length": Binary(pickle.dumps(self.length)),
    #         "date_time": self.date_time,
    #         "metadata": {"total_event": self.total_events, "dx": self.dx},
    #     }
    #     return_dict.update({event_name: Binary(pickle.dumps(list(event_topic))) for event_name, event_topic in zip(
    #         named_dict.keys(),
    #         self.event
    #     )})
    #
    #     return return_dict

    @classmethod
    def from_dict(cls, data: dict) -> dict:
        """Создание объекта из данных MongoDB"""
        return dict(
            event=pickle.loads(data["event"]).tolist(),
            length=pickle.loads(data["length"]).tolist(),
            date_time=data["date_time"],
        )

    @classmethod
    def expanded_from_dict(cls, data: dict, named_dict: dict,) -> dict:
        """Создание объекта из данных MongoDB"""
        event_arr = pickle.loads(data["event"])
        event_arr = collapse_events(event_arr)
        print(event_arr.shape)
        return_dict = dict(
            # event=pickle.loads(data["event"]).tolist(),
            length=pickle.loads(data["length"]).tolist(),
            date_time=data["date_time"],
        )
        print(named_dict.keys())
        print(list(event_arr))
        print(event_arr.tolist())
        return_dict.update({event_name: event_mask for event_name, event_mask in zip(
            named_dict.keys(),
            # event_arr
            event_arr.tolist()
        )})
        return return_dict


class MaskInDB(BaseModel):
    id: str = Field(..., alias="_id")
    event: bytes
    length: bytes
    date_time: datetime

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat(), ObjectId: str},
        arbitrary_types_allowed=True,
        populate_by_name=True,
    )
