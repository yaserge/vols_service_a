from pydantic import BaseModel

class ThermogramResponse(BaseModel):
    name: str
    path: str

class TemperatureStats(BaseModel):
    max: float
    min: float
    mean: float

class DetectionResult(BaseModel):
    filename: str
    hot_leaks_count: int
    cold_leaks_count: int
    temperature_stats: TemperatureStats
    
class ValueUpdate(BaseModel):
    value: float