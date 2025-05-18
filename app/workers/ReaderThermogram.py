import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from app.models.thermogram import Thermogram
from time import sleep

class ReaderThermogram:
    def __init__(self) -> None:
        self.thermogram: np.ndarray | None = None
        self.length: np.ndarray | None = None

    def _get_line_value(self, fname: Path, line_num: int) -> str:
        """Читает строку с нужным номером и возвращает значение после '='."""
        with fname.open("r") as f:
            for i, line in enumerate(f):
                if i == line_num:
                    return line.strip().split("=")[1].strip()
        raise ValueError(f"Line {line_num} not found in file {fname}")

    def _get_thermogram(self, fname: Path) -> None:
        sleep(3)
        df = pd.read_csv(
            fname,
            sep=";",
            names=["L", "T"],
            decimal=".",
            skiprows=19,
        )
        print(df["L"].to_numpy().shape)
        print(df["T"].to_numpy().shape)
        self.length, self.thermogram = df["L"].to_numpy(), df["T"].to_numpy()

    def read_data(self, fname: Path) -> Thermogram:
        self._get_thermogram(fname)
        return Thermogram(
            thermogram=self.thermogram,
            length=self.length,
            date_time=datetime.strptime(self._get_line_value(fname, 7), "%Y-%m-%d %H:%M:%S"),
            temperature_ballast=float(self._get_line_value(fname, 8)),
            channel_num=int(self._get_line_value(fname, 9)),
            measure_time=float(self._get_line_value(fname, 10))
        )