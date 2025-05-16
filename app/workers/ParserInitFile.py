import yaml
from pathlib import Path

class ParserInitFile:
    def __init__(self, init_file: Path):
        self.init_file = init_file

    # TODO: set thresholds to iterable or dict
    def get_event_thresholds(self) -> dict:
        return dict(yaml.load(self.init_file.open("r"), Loader=yaml.Loader)["thresholds"])

    def get_area_config(self) -> dict:
        return dict(yaml.load(self.init_file.open("r"), Loader=yaml.Loader)["area_config"])

    def get_monitoring_path(self) -> Path:
        return Path(yaml.load(self.init_file.open("r"), Loader=yaml.Loader)["path"])