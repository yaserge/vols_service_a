import yaml
from pathlib import Path

class ParserInitFile:
    def __init__(self, init_file: Path):
        self.init_file = init_file

    def get_hot_th(self) -> float:
        return float(yaml.load(self.init_file.open("r"), Loader=yaml.Loader)["hot_threshold"])
        
    def get_cold_th(self) -> float:
        return float(yaml.load(self.init_file.open("r"), Loader=yaml.Loader)["cold_threshold"])
    
    def get_monitoring_path(self) -> Path:
        return Path(yaml.load(self.init_file.open("r"), Loader=yaml.Loader)["path"])