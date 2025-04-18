from fastapi import FastAPI
from pathlib import Path
import uvicorn
from app.routes import thermograms, masks
from app.services.monitoring import start_monitoring, stop_monitoring
from app.workers.ParserInitFile import ParserInitFile
from app.routes import notifications
from app.db.mongodb import mongodb
import asyncio

app = FastAPI(title="Thermogram Processing API")
app.include_router(notifications.router)

init_parser = ParserInitFile(Path("INIT.yaml"))

app.state.config = {
    "monitoring_dir": init_parser.get_monitoring_path(),
    "hot_threshold": init_parser.get_hot_th(),
    "cold_threshold": init_parser.get_cold_th()
}

app.include_router(thermograms.router)
app.include_router(masks.router)

@app.on_event("startup")
async def startup_event():
    """Запускаем мониторинг папки при старте приложения"""
    loop = asyncio.get_running_loop()
    
    start_monitoring(
        monitoring_dir=app.state.config["monitoring_dir"],
        hot_th=app.state.config["hot_threshold"],
        cold_th=app.state.config["cold_threshold"],
        loop=loop
    )

@app.on_event("shutdown")
async def shutdown_event():
    """Останавливаем мониторинг при завершении работы"""
    stop_monitoring()

@app.on_event("startup")
async def startup_db_client():
    await mongodb.connect()

# @app.on_event("shutdown")
# async def shutdown_db_client():
#     await mongodb.connect()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)