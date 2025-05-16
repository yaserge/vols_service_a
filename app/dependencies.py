from pathlib import Path
from fastapi import Depends
from app.workers.ReaderThermogram import ReaderThermogram
from app.workers.Detector import Detector
from app.workers.ParserInitFile import ParserInitFile


def get_config_parser():
    return ParserInitFile(Path("INIT.yaml"))


# TODO: fix
def get_detector(parser: ParserInitFile = Depends(get_config_parser)):
    return Detector(parser.get_event_thresholds(), parser.get_area_config())


def get_reader():
    return ReaderThermogram()
    