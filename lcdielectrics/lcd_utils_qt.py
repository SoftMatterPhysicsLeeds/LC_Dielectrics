from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal, Slot, QThread

@dataclass
class DataPoint:
    frequency: float
    voltage: float
    temperature: float

@dataclass
class Result:
    pass

class SinglePointWorker(QObject):
    temperature_reached = Signal(float)
    measurement_complete = Signal(dict)