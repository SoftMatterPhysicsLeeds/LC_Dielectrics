from dataclasses import dataclass
from lcdielectrics.lcd_dataclasses import lcd_instruments
import time

from PySide6.QtCore import QObject, Signal, Slot, QThread

@dataclass
class DataPoint:
    frequency: float
    voltage: float
    temperature: float
    rate: float


class SinglePointWorker(QObject):
    temperature_reached = Signal()
    measurement_complete = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, datapoint: DataPoint, instruments: lcd_instruments, stabilisation_time: float):
        super().__init__()
        self.datapoint = datapoint
        self.stabilisation_time = stabilisation_time

    def run_experiment(self):
        # Go to temperature
        success = self.go_to_temperature()
        if not success:
            self.error_occurred.emit("Failed to set temperature")
            return
        
        
    def go_to_temperature(self):

        self.instruments.linkam.set_temperature(self.datapoint.temperature, self.datapoint.rate)

        # Wait for temperature to stabilise i.e. within 0.1 degrees of target for stabilisation time
        start_time = time.time()
        while True:
            current_temp = self.instruments.linkam.current_temperature()
            if abs(current_temp - self.datapoint.temperature) < 0.1 and time.time() - start_time > self.stabilisation_time:
                break
        self.temperature_reached.emit()
        return True