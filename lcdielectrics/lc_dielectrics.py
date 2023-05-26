import json
import sys
import time

import pyvisa
from qtpy import QtCore, QtGui
from qtpy.QtCore import QThread, Signal
from qtpy.QtWidgets import QApplication, QFileDialog, QMainWindow, QWidget

from lcdielectrics import icon_qrc
from lcdielectrics.excel_writer import make_excel
from lcdielectrics.instruments import AgilentSpectrometer, LinkamHotstage
from lcdielectrics.ui import generate_ui

# build command:
# pyinstaller -i .\LCD_icon.ico --onefile .\lc_dielectrics.py
# if you install modules/packages with conda ->
#    resulting file is 6x bigger (300mb) - best to use pip


class Sleepy(QtCore.QObject):
    finished = Signal()
    def __init__(self, sleep_time):
        super().__init__()
        self.sleep_time = sleep_time
    
    def sleep(self):
        time.sleep(self.sleep_time)
        self.finished.emit()


class Experiment(QtCore.QObject):
    finished = Signal()
    result = Signal(dict)

    def __init__(self, agilent: AgilentSpectrometer):
        super().__init__()
        self.agilent = agilent

    def run_spectrometer(self) -> None:
        result = dict()
        time.sleep(0.5)
        result["CPD"] = self.agilent.measure("CPD")
        time.sleep(0.5)
        result["GB"] = self.agilent.measure("GB")
        time.sleep(0.5)
        self.result.emit(result)
        self.finished.emit()


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle("LC Dielectrics")
        self.setWindowIcon(QtGui.QIcon(":LCD_icon.ico"))

        self.resultsDict = dict()

        self.current_T = 30.0
        self.linkam_action = "Idle"
        self.linkam_status = "Not Connected"
        self.agilent_status = "Not Connected"
        self.measurement_status = "Idle"
        self.t_stable_count = 0
        self.voltage_list_mode = False

        self.layout, self.widgets = generate_ui()

        self.widgets["init_linkam_button"].clicked.connect(self.init_linkam)
        self.widgets["init_agilent_button"].clicked.connect(self.init_agilent)
        self.widgets["add_file_button"].clicked.connect(self.add_file_dialogue)

        self.widgets["go_to_temp_button"].clicked.connect(
            lambda: self.linkam.set_temperature(
                float(self.widgets["go_to_temp"].text()), float(self.widgets["temp_rate"].text())
            )
        )

        self.widgets["go_button"].clicked.connect(self.start_measurement)
        self.widgets["stop_button"].clicked.connect(self.stop_measurement)

        # UI update loop
        self.timer = QtCore.QTimer()
        self.timer.setInterval(150)
        self.timer.timeout.connect(self.update_ui)
        self.timer.start()

        widget = QWidget()
        widget.setLayout(self.layout)
        self.setCentralWidget(widget)

    ###################### Control Logic ################################

    def init_agilent(self) -> None:
        self.agilent = AgilentSpectrometer(self.widgets["usb_selector"].currentText())
        self.agilent_status = "Connected"
        self.widgets["init_agilent_button"].setText("Connected")
        self.widgets["init_agilent_button"].setEnabled(False)
        self.update_ui()

    def init_linkam(self) -> None:
        self.linkam = LinkamHotstage(self.widgets["com_selector"].currentText())
        try:
            self.linkam.current_temperature()
            self.linkam_status = "Connected"
            self.widgets["init_linkam_button"].setText("Connected")
            self.widgets["init_linkam_button"].setEnabled(False)
        except pyvisa.errors.VisaIOError:
            self.linkam_status = self.linkam_status

        self.update_ui()

    def add_file_dialogue(self) -> None:
        filename, _ = QFileDialog.getSaveFileName(
            self, "Output File", "", "JSON Files (*.json)"
        )
        self.widgets["output_file_input"].setText(filename)

    def update_ui(self) -> None:
        self.widgets["agilent_status_label"].setText(self.agilent_status)

        # if Linkam is connected, show real-time temperature
        if self.linkam_status == "Connected":
            self.current_T, self.linkam_action = self.linkam.current_temperature()
            self.widgets["linkam_status_label"].setText(
                f"{self.linkam_status}, {self.linkam_action}, T: {self.current_T}"
            )
        else:
            self.widgets["linkam_status_label"].setText(f"{self.linkam_status}")

        # control measurement loop - see if this is better than threading?
        if self.measurement_status == "Idle":
            pass

        elif self.measurement_status == "Setting temperature" and (
            self.linkam_action == "Stopped" or self.linkam_action == "Holding"
        ):
            self.linkam.set_temperature(self.T_list[self.T_step], self.T_rate)
            
            self.measurement_status = f"Going to T: {self.T_list[self.T_step]}"

        elif (
            self.measurement_status == f"Going to T: {self.T_list[self.T_step]}"
            and self.linkam_action == "Holding"
        ):
            self.measurement_status = f"Stabilising temperature for {float(self.widgets['stab_time'].text())}s"
        elif (
            self.measurement_status == f"Stabilising temperature for {float(self.widgets['stab_time'].text())}s"
        ):
            self.t_stable_count += 1

            if self.t_stable_count * 0.15 >= float(self.widgets["stab_time"].text()):
                self.measurement_status = "Temperature Stabilised"
                self.t_stable_count = 0

        elif self.measurement_status == "Temperature Stabilised":
            self.measurement_status = "Collecting data"
            self.agilent.set_frequency(self.freq_list[self.freq_step])
            self.agilent.set_voltage(self.voltage_list[self.volt_step])
            ## insert wait time here!
            self.sleep_before_measurement()
            

        elif self.measurement_status == "Finished":
            self.linkam.stop()
            self.agilent.reset_and_clear()
            self.measurement_status = "Idle"

        self.widgets["measurement_status_label"].setText(self.measurement_status)

    def start_measurement(self) -> None:

        self.resultsDict = dict()
        self.freq_list = [
            float(self.widgets["freq_list_widget"].item(x).text())
            for x in range(self.widgets["freq_list_widget"].count())
        ]
        self.voltage_list = [
            float(self.widgets["volt_list_widget"].item(x).text())
            for x in range(self.widgets["volt_list_widget"].count())
        ]

        self.T_list = [
            float(self.widgets["temp_list_widget"].item(x).text())
            for x in range(self.widgets["temp_list_widget"].count())
        ]
        self.T_list = [round(x, 2) for x in self.T_list]

        self.agilent.set_aperture_mode(
            self.widgets["time_selector"].currentText(),
            int(self.widgets["averaging_factor"].text()),
        )

        if (
            self.widgets["bias_voltage_selector"].currentText() == "1.5"
            or self.widgets["bias_voltage_selector"].currentText() == "2"
        ):
            self.agilent.set_DC_bias(
                float(self.widgets["bias_voltage_selector"].currentText())
            )

        self.T_rate = float(self.widgets["temp_rate"].text())
        self.T_step = 0
        self.freq_step = 0
        self.volt_step = 0

        T = self.T_list[self.T_step]
        freq = self.freq_list[self.freq_step]
        
        self.resultsDict[self.T_list[self.T_step]] = dict()
        self.resultsDict[T][freq] = dict()
        self.resultsDict[T][freq]["volt"] = []
        self.resultsDict[T][freq]["Cp"] = []
        self.resultsDict[T][freq]["D"] = []
        self.resultsDict[T][freq]["G"] = []
        self.resultsDict[T][freq]["B"] = []



        self.measurement_status = "Setting temperature"

    def stop_measurement(self) -> None:
        self.linkam.stop()
        self.agilent.reset_and_clear()
        self.measurement_status = "Idle"

    def sleep_before_measurement(self):
        self.thread = QThread()
        self.worker = Sleepy(float(self.widgets["delay_time"].text()))
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.sleep)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.run_spectrometer)
        self.worker.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def run_spectrometer(self) -> None:

        self.thread = QThread()
        self.worker = Experiment(self.agilent)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run_spectrometer)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.result.connect(self.get_result)
        self.thread.start()

    def get_result(self, result: dict) -> None:
        self.parse_result(result)
    
        if (
            self.T_step == len(self.T_list) - 1
            and self.volt_step == len(self.voltage_list) - 1 and self.freq_step == len(self.freq_list) - 1
        ):
            self.measurement_status = "Finished"
            
            if len(self.voltage_list)==1: 
                make_excel(
                    self.resultsDict,
                    self.widgets["output_file_input"].text(),
                    True,
                )
            else:
                make_excel(
                    self.resultsDict,
                    self.widgets["output_file_input"].text(),
                    False,
                )

            with open(self.widgets["output_file_input"].text(), "w") as write_file:
                json.dump(self.resultsDict, write_file, indent=4)
        else:



            if self.volt_step == len(self.voltage_list) - 1 and self.freq_step == len(self.freq_list) - 1:
                self.T_step += 1
                self.freq_step = 0
                self.volt_step = 0
                
                T = self.T_list[self.T_step]
                freq = self.freq_list[self.freq_step]

                self.resultsDict[self.T_list[self.T_step]] = dict()
                self.resultsDict[T][freq] = dict()
                self.resultsDict[T][freq]["volt"] = []
                self.resultsDict[T][freq]["Cp"] = []
                self.resultsDict[T][freq]["D"] = []
                self.resultsDict[T][freq]["G"] = []
                self.resultsDict[T][freq]["B"] = []

                self.measurement_status = "Setting temperature"

            elif self.volt_step == len(self.voltage_list) - 1:
                self.freq_step+=1 
                self.volt_step=0
                
                T = self.T_list[self.T_step]
                freq = self.freq_list[self.freq_step]

                self.resultsDict[T][freq] = dict()
                self.resultsDict[T][freq]["volt"] = []
                self.resultsDict[T][freq]["Cp"] = []
                self.resultsDict[T][freq]["D"] = []
                self.resultsDict[T][freq]["G"] = []
                self.resultsDict[T][freq]["B"] = []

                self.measurement_status = "Temperature Stabilised"
            else:
                self.volt_step +=1
                self.measurement_status = "Temperature Stabilised"

    def parse_result(self, result: dict) -> None:

        T = self.T_list[self.T_step]
        freq = self.freq_list[self.freq_step]
        volt = self.voltage_list[self.volt_step]
        self.resultsDict[T][freq]["volt"].append(volt)
        self.resultsDict[T][freq]["Cp"].append(result["CPD"][0])
        self.resultsDict[T][freq]["D"].append(result["CPD"][1])
        self.resultsDict[T][freq]["G"].append(result["GB"][0])
        self.resultsDict[T][freq]["B"].append(result["GB"][1])
       

    ###################### END OF CONTROL LOGIC ###############################


def main() -> None:
    app = QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
