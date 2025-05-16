from pathlib import Path
from typing import Optional
from watchdog.observers import Observer
from app.workers.NewFileHandler import NewFileHandler
from app.workers.Detector import Detector
from app.workers.ReaderThermogram import ReaderThermogram

_observer: Optional[Observer] = None
event_handler = None

def start_monitoring(monitoring_dir: Path, thresholds: dict, area_config:dict, loop):
    """Запуск мониторинга папки"""
    global _observer
    global event_handler 

    if not monitoring_dir.exists():
        monitoring_dir.mkdir(parents=True, exist_ok=True)
    
    detector = Detector(thresholds, area_config)
    reader = ReaderThermogram()
    
    event_handler = NewFileHandler(monitoring_dir, reader, detector, loop)
    _observer = Observer()
    _observer.schedule(event_handler, str(monitoring_dir), recursive=False)
    _observer.start()

    print(f"Monitoring directory: {monitoring_dir.resolve()}")

def stop_monitoring():
    """Остановка мониторинга"""
    global _observer
    if _observer is not None:
        _observer.stop()
        _observer.join()