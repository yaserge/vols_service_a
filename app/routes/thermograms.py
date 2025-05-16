from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.db.mongodb import mongodb
from app.models.schemas import ValueUpdate
import app.services.monitoring as monitor

router = APIRouter(prefix="/thermograms", tags=["thermograms"])


async def get_config(request: Request):
    return request.app.state.config


@router.get("/closest")
async def get_closest_thermogram(target_time: datetime = Query(..., description="Целевое время для поиска")):
    thermogram = await mongodb.get_closest_thermogram(target_time)
    if not thermogram:
        raise HTTPException(status_code=404, detail="No thermograms found")
    return thermogram


@router.get("/times", response_model=List[datetime])
async def get_all_thermogram_times():
    return await mongodb.get_all_thermogram_times()


# TODO: redo
@router.put("/thresholds")
async def update_threshold(value: ValueUpdate):
    monitor.event_handler.detector.threshold = value.value
    return {"message": "Threshold is updated", "new_value": value.value}


# @router.put("/hot_th")
# async def update_hot_th(value: ValueUpdate):
#     print(monitor.event_handler)
#     monitor.event_handler.detector.hot_th = value.value
#     return {"message": "Hot threshold is updated", "new_value": value.value}
#
#
# @router.put("/cold_th")
# async def update_cold_th(value: ValueUpdate):
#     monitor.event_handler.detector.cold_th = value.value
#     return {"message": "Cold threshold is updated", "new_value": value.value}
