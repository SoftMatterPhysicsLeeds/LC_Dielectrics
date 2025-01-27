from PySide6.QtCore import QObject, Signal, Slot, QThread
from enum import Enum
import time

class ExperimentStage(Enum):
    TEMP_STABILIZATION = 1
    FIELD_RAMP = 2
    MEASUREMENT = 3
    CLEANUP = 4

class ExperimentWorker(QObject):
    # Signals for different stages
    temperature_reached = Signal(float)  # Emits actual temperature
    field_ready = Signal(float)         # Emits actual field
    measurement_complete = Signal(dict)  # Emits measurement results
    experiment_finished = Signal()
    error_occurred = Signal(str)        # Emits error message

    def __init__(self, parameters):
        super().__init__()
        self.parameters = parameters
        self.should_stop = False

    @Slot()
    def run_experiment(self):
        try:
            # Temperature stabilization
            success = self.go_to_temperature(self.parameters['target_temp'])
            if not success:
                return
            
            # Field ramping
            if self.should_stop:
                return
            success = self.ramp_field(self.parameters['target_field'])
            if not success:
                return

            # Measurement
            if self.should_stop:
                return
            results = self.perform_measurement()
            if results:
                self.measurement_complete.emit(results)

            self.experiment_finished.emit()

        except Exception as e:
            self.error_occurred.emit(str(e))

    def go_to_temperature(self, target_temp):
        """Simulate temperature control"""
        # In reality, you'd communicate with your temperature controller here
        time.sleep(2)  # Simulate temperature stabilization
        current_temp = target_temp + 0.1  # Simulate slight offset
        self.temperature_reached.emit(current_temp)
        return True

    def ramp_field(self, target_field):
        """Simulate field ramping"""
        # In reality, you'd communicate with your field controller here
        time.sleep(1)  # Simulate field ramping
        actual_field = target_field - 0.05  # Simulate slight offset
        self.field_ready.emit(actual_field)
        return True

    def perform_measurement(self):
        """Simulate measurement"""
        # In reality, you'd communicate with your measurement equipment here
        time.sleep(3)  # Simulate measurement time
        return {"voltage": 1.23, "current": 0.45}

    @Slot()
    def stop_experiment(self):
        self.should_stop = True


class ExperimentController(QObject):
    start_experiment = Signal()
    
    def __init__(self, parameters):
        super().__init__()
        self.parameters = parameters
        
        # Create worker and thread
        self.worker = ExperimentWorker(parameters)
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        
        # Connect signals
        self.start_experiment.connect(self.worker.run_experiment)
        self.worker.temperature_reached.connect(self.on_temperature_reached)
        self.worker.field_ready.connect(self.on_field_ready)
        self.worker.measurement_complete.connect(self.on_measurement_complete)
        self.worker.experiment_finished.connect(self.on_experiment_finished)
        self.worker.error_occurred.connect(self.on_error)
        
        # Start thread
        self.thread.start()

    def begin_experiment(self):
        self.start_experiment.emit()

    @Slot(float)
    def on_temperature_reached(self, actual_temp):
        print(f"Temperature stabilized at {actual_temp}K")

    @Slot(float)
    def on_field_ready(self, actual_field):
        print(f"Field stabilized at {actual_field}T")

    @Slot(dict)
    def on_measurement_complete(self, results):
        print(f"Measurement complete: {results}")

    @Slot()
    def on_experiment_finished(self):
        print("Experiment finished successfully")
        self.cleanup()

    @Slot(str)
    def on_error(self, error_msg):
        print(f"Error occurred: {error_msg}")
        self.cleanup()

    def cleanup(self):
        self.thread.quit()
        self.thread.wait()


# Example usage in your main window
class MainWindow:
    def __init__(self):
        self.parameters = {
            'target_temp': 4.2,
            'target_field': 1.0,
            # Add other parameters as needed
        }
        
        self.experiment = ExperimentController(self.parameters)

    def start_button_clicked(self):
        self.experiment.begin_experiment()