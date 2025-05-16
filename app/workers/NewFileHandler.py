import asyncio
import json
from datetime import datetime
from pathlib import Path

from app.db.mongodb import mongodb
from app.models.event_mask import EventMask
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
    async def send_event(event_type: str, length: float, time: str):
        await manager.broadcast(json.dumps({"event": event_type, "length": length, "time": time}))

    async def process_file(self, path):
        """Асинхронная обработка файла"""

        try:
            thermo = self.reader.read_data(path)
            self.detector.detect_event(thermo)

            event_start = self.detector.get_event_start()
            event_stop = self.detector.get_event_stop()
            thresholds = self.detector.thresholds


            mask = EventMask(
                event=event_start * 2
                + event_stop,  # 0 - ничего не произошло, 1 - утечка прошла, 2 - утечка началась
                length=thermo.length,
                date_time=thermo.date_time,
            )

            await mongodb.save_thermogram(thermo)
            await mongodb.save_mask(mask)
            print("Файл обработан")

            for i, length in enumerate(thermo.thermogram):
                event_code = event_start[i] * 2 + event_stop[i]

                event_map = {1: "event_stop", 2: "event_start"}

                if event_code in event_map:
                    await self.send_event(
                        # TODO: maybe separate?
                        event_map[event_code],
                        thermo.length[i],
                        datetime.strftime(thermo.date_time, "%Y-%m-%d %H:%M:%S.%f"),
                    )
                    continue  # исключаем возможность двойной отправки события

                # if cold_code in event_map:
                #     await self.send_event(
                #         event_map[cold_code],
                #         thermo.length[i],
                #         datetime.strftime(thermo.date_time, "%Y-%m-%d %H:%M:%S.%f"),
                #     )

        except Exception as e:
            await manager.broadcast(json.dumps({"event": "error", "message": str(e)}))
