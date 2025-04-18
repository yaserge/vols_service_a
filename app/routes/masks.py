from fastapi import APIRouter, Depends, HTTPException, Request, Query
from pathlib import Path
from typing import List
from app.models.mask import Mask
from app.db.mongodb import mongodb

from datetime import datetime

router = APIRouter(prefix="/masks", tags=["masks"])

@router.get("/closest")
async def get_closest_mask(
    target_time: datetime = Query(..., description="Целевое время для поиска")
):
    mask = await mongodb.get_closest_mask(target_time)
    if not mask:
        raise HTTPException(status_code=404, detail="No mask found")
    return mask

@router.get("/times", response_model=List[datetime])
async def get_all_mask_times():
    return await mongodb.get_all_mask_times()