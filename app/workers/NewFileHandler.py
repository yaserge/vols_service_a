import asyncio
import json
from datetime import datetime
from pathlib import Path

from app.db.mongodb import mongodb
from app.models.mask import Mask
from app.routes.notifications import manager
from app.workers.Detector import Detector
from app.workers.ReaderThermogram import ReaderThermogram
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class NewFileHandler(FileSystemEventHandler):
    def __init__(self, folder: Path, reader: ReaderThermogram, detector: Detector, loop):
        self.folder = folder
        self.reader = reader
        self.detector = detector
        self.loop = loop

    def on_created(self, event):
        path = Path(event.src_path)
        if path.is_file() and path.suffix == ".csv" and path.name.startswith("Therm"):
            print(f"Обрабатываю файл: {path.name}")

            # Запускаем асинхронную обработку в существующем loop
            asyncio.run_coroutine_threadsafe(self.process_file(path), self.loop)

    @staticmethod
    async def send_leak_event(event_type: str, length: float, time: str):
        await manager.broadcast(json.dumps({"event": event_type, "length": length, "time": time}))

    async def process_file(self, path):
        """Асинхронная обработка файла"""

        try:
            thermo = self.reader.read_data(path)
            self.detector.detect_hot_leak(thermo)
            self.detector.detect_cold_leak(thermo)

            hot_leak_start = self.detector.get_hot_leak_start()
            hot_leak_stop = self.detector.get_hot_leak_stop()

            cold_leak_start = self.detector.get_cold_leak_start()
            cold_leak_stop = self.detector.get_cold_leak_stop()

            mask = Mask(
                hot_leak=hot_leak_start * 2
                + hot_leak_stop,  # 0 - ничего не произошло, 1 - утечка прошла, 2 - утечка началась
                cold_leak=cold_leak_start * 2 + cold_leak_stop,
                length=thermo.length,
                date_time=thermo.date_time,
            )

            await mongodb.save_thermogram(thermo)
            await mongodb.save_mask(mask)
            print("Файл обработан")

            for i, length in enumerate(thermo.thermogram):
                hot_code = hot_leak_start[i] * 2 + hot_leak_stop[i]
                cold_code = cold_leak_start[i] * 2 + cold_leak_stop[i]

                event_map = {1: "hot_leak_stop", 2: "hot_leak_start"}

                if hot_code in event_map:
                    await self.send_leak_event(
                        event_map[hot_code],
                        thermo.length[i],
                        datetime.strftime(thermo.date_time, "%Y-%m-%d %H:%M:%S.%f"),
                    )
                    continue  # исключаем возможность двойной отправки события

                event_map = {1: "cold_leak_stop", 2: "cold_leak_start"}

                if cold_code in event_map:
                    await self.send_leak_event(
                        event_map[cold_code],
                        thermo.length[i],
                        datetime.strftime(thermo.date_time, "%Y-%m-%d %H:%M:%S.%f"),
                    )

        except Exception as e:
            await manager.broadcast(json.dumps({"event": "error", "message": str(e)}))
