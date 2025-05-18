import asyncio
import json
from datetime import datetime
from pathlib import Path
from itertools import groupby


from app.db.mongodb import mongodb
from app.models.event_mask import EventMask
from app.routes.notifications import manager
from app.workers.Detector import Detector
from app.workers.ReaderThermogram import ReaderThermogram
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from app.models.event_mask import collapse_events


def get_centers_of_sequence(a):
    groups = [list(g) for _, g in groupby(a)]
    output_vector = [(x[0], sum(1 for x in groups[:i] for _ in x) + len(x) // 2) for i, x in enumerate(groups)]
    return output_vector


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
                named_dict=thresholds,
            )

            await mongodb.save_thermogram(thermo)
            await mongodb.save_mask(mask)
            print("Файл обработан")

            for name, row in zip(thresholds.keys(), list(event_stop)):
                for value, center in get_centers_of_sequence(row):
                    if value != 0:
                        print(f"event {name} ended on {thermo.length[center]}m at {thermo.date_time}")

            for name, row in zip(thresholds.keys(), list(event_start)):
                for value, center in get_centers_of_sequence(row):
                    if value != 0:
                        print(f"event {name} started on {thermo.length[center]}m at {thermo.date_time}")
                        with open("event_output_path.txt", "a") as f:
                            # f.write(f"{name}")
                            if name == 'cold_leak':
                                f.write(f"{thermo.date_time}, {thermo.length[center]}, 1\n")
                            if name == 'hot_leak':
                                f.write(f"{thermo.date_time}, {thermo.length[center]}, 2\n")

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
