from qtpy.QtWidgets import (QMainWindow, QWidget, QGridLayout, QApplication, QPushButton)
from qtpy import QtCore, QtGui
from qtpy.QtCore import QThread
from PyQt5.QtCore import pyqtSignal
import sys
import numpy as np
import pyvisa
import json
import time

from Instruments import LinkamHotstage, AgilentSpectrometer
from Frames import * #type: ignore
from Excel_writer import make_excel #type: ignore
import icon_qrc #type:ignore

class Experiment(QtCore.QObject):
    finished = pyqtSignal()
    result = pyqtSignal(dict)

    def __init__(self, agilent: AgilentSpectrometer):
        super().__init__()
        self.agilent = agilent

    def run_spectrometer(self) -> None:
        result = dict()
        result["CPD"] = self.agilent.measure("CPD")
        time.sleep(0.5)
        result["GB"] = self.agilent.measure("GB")
        self.result.emit(result)
        self.finished.emit()


class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle("LC Dielectrics")
        self.setWindowIcon(QtGui.QIcon(':LCD_icon.ico'))

        self.resultsDict = dict()

        self.current_T = 30.0
        self.linkam_action = "Idle"
        self.linkam_status = "Not Connected"
        self.agilent_status = "Not Connected"
        self.measurement_status = "Idle"
        self.t_stable_count = 0
        self.voltage_list_mode = False

        self.layout = QGridLayout()

        # initialise frames
        statusFrame(self) #type: ignore
        instrumentSettingsFrame(self) #type: ignore
        measurementSettingsFrame(self) #type: ignore
        frequencySettingsFrame(self) #type: ignore
        voltageSettingsFrame(self) #type: ignore
        temperatureSettingsFrame(self) #type: ignore
        outputDataSettingsFrame(self) #type: ignore
        graphFrame(self) #type: ignore


        # initialise layout
        self.layout.addWidget(self.status_frame, 0, 0, 1, 2)
        self.layout.addWidget(self.instrument_settings_frame, 1, 0, 1, 2)
        self.layout.addWidget(self.measurement_settings_frame, 2, 0, 1, 2)
        self.layout.addWidget(self.freq_settings_frame, 3, 0)
        self.layout.addWidget(self.voltage_settings_frame, 3, 1)
        self.layout.addWidget(self.temperature_settings_frame, 4, 0, 1, 2)
        self.layout.addWidget(self.output_settings_frame, 5, 0, 1, 2)
        self.layout.addWidget(self.graph_frame, 0, 2, 7, 1)

        self.go_button = QPushButton("Start")
        self.layout.addWidget(self.go_button, 6, 0, 1, 1)
        self.go_button.clicked.connect(self.start_measurement)
        self.set_button_style(self.go_button, "green")

        self.stop_button = QPushButton("Stop")
        self.layout.addWidget(self.stop_button, 6, 1, 1, 1)
        self.stop_button.clicked.connect(self.stop_measurement)
        self.set_button_style(self.stop_button, "red")

        # UI update loop
        self.timer = QtCore.QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_ui)
        self.timer.start()

        widget = QWidget()
        widget.setLayout(self.layout)
        self.setCentralWidget(widget)

    def set_button_style(self, button: QPushButton, bg_colour: str, fixed_width: bool = False) -> None:
    # button.setFixedWidth(250)
        button.setFixedHeight(40)

        if fixed_width:
            button.setFixedWidth(100)

        button.setStyleSheet(
            "\
            QPushButton { \
            color: white;\
            /*font-family: 'helvetica';*/ \
            /*font-size: 20px;*/ \
            border-radius: 5px; \
            padding: 2px 0; \
            margin-top: 2px; \
            " + "background-color:" + bg_colour + "; \
            } \
            QPushButton:hover { \
                background-color: black;\
                color: white;\
            }\
         ")


    ###################### Control Logic ################################

    def init_agilent(self) -> None:
        self.agilent = AgilentSpectrometer(self.usb_selector.currentText())
        self.agilent_status = "Connected"
        self.init_agilent_button.setText("Connected")
        self.init_agilent_button.setEnabled(False)
        self.update_ui()

    def init_linkam(self) -> None:
        self.linkam = LinkamHotstage(self.com_selector.currentText())
        try:
            self.linkam.current_temperature()
            self.linkam_status = "Connected"
            self.init_linkam_button.setText("Connected")
            self.init_linkam_button.setEnabled(False)
        except pyvisa.errors.VisaIOError:
            self.linkam_status = self.linkam_status

        self.update_ui()

    def voltage_toggle(self) -> None:
        if self.voltage_checkbox.isChecked():
            self.voltage_step.setEnabled(False)
            self.voltage_max.setEnabled(False)
            self.voltage_min_label.setText("Voltage")
            self.voltage_list_mode = False

        else:
            self.voltage_step.setEnabled(True)
            self.voltage_max.setEnabled(True)
            self.voltage_min_label.setText("Min Voltage")
            self.voltage_list_mode = True

    def update_ui(self) -> None:
        self.agilent_status_label.setText(self.agilent_status)

        # if Linkam is connected, show real-time temperature
        if self.linkam_status == "Connected":
            self.current_T, self.linkam_action = self.linkam.current_temperature()
            self.linkam_status_label.setText(
                f"{self.linkam_status}, {self.linkam_action}, T: {self.current_T}")
        else:
            self.linkam_status_label.setText(f"{self.linkam_status}")

        # control measurement loop - see if this is better than threading?
        if self.measurement_status == "Idle":
            pass

        elif self.measurement_status == "Setting temperature" and (self.linkam_action == "Stopped" or self.linkam_action == "Holding"):
            self.linkam.set_temperature(self.T_list[self.T_step], self.T_rate)
            if self.voltage_list_mode:
                self.agilent.set_frequency(self.freq_list[self.freq_step])
                if self.freq_step != 0:
                    self.measurement_status = "Temperature Stabilised"
                else:
                    self.measurement_status = f"Going to T: {self.T_list[self.T_step]}"
            else:
                self.measurement_status = f"Going to T: {self.T_list[self.T_step]}"

        elif self.measurement_status == f"Going to T: {self.T_list[self.T_step]}" and self.linkam_action == "Holding":
            self.resultsDict[self.T_list[self.T_step]] = dict()
            self.measurement_status = f"Stabilising temperature for {float(self.stab_time.text())}s"

        elif self.measurement_status == f"Stabilising temperature for {float(self.stab_time.text())}s":
            self.t_stable_count += 1

            if self.t_stable_count*0.1 >= float(self.stab_time.text()):
                self.measurement_status = "Temperature Stabilised"
                self.t_stable_count = 0

        elif self.measurement_status == "Temperature Stabilised":
            self.measurement_status = "Collecting data"
            self.run_spectrometer()

        elif self.measurement_status == "Finished":
            self.linkam.stop()
            self.agilent.reset_and_clear()
            self.measurement_status = "Idle"

        self.measurement_status_label.setText(self.measurement_status)

    def start_measurement(self) -> None:

        self.resultsDict = dict()

        voltage_min = float(self.voltage_min.text())
        voltage_max = float(self.voltage_max.text())
        voltage_step = float(self.voltage_step.text())

        self.freq_list = [float(self.freq_list_widget.item(x).text()) for x in range(self.freq_list_widget.count())]

        # self.freq_list = list(np.logspace(
        #     np.log10(freq_min), np.log10(freq_max), freq_points))

        if self.voltage_list_mode:
            self.voltage_list = list(
                np.arange(voltage_min, voltage_max+voltage_step, voltage_step))
            self.agilent.set_volt_list(self.voltage_list)
            self.agilent.set_frequency(self.freq_list[0])
        else:
            self.resultsDict["volt"] = voltage_min
            self.agilent.set_voltage(voltage_min)
            self.agilent.set_freq_list(self.freq_list)

        self.agilent.set_aperture_mode(
            self.time_selector.currentText(), int(self.averaging_factor.text()))

        if self.bias_voltage_selector.currentText() == "1.5" or self.bias_voltage_selector.currentText() == "2":
            self.agilent.set_DC_bias(
                float(self.bias_voltage_selector.currentText()))
        # calculate T list
        T_start = round(float(self.temp_start.text()),2)
        T_end = round(float(self.temp_end.text()),2)
        T_inc = round(float(self.temp_step.text()),2)
        self.T_rate = float(self.temp_rate.text())

        if T_start == T_end:
            self.T_list = np.array([T_start])
        elif T_start > T_end and T_inc > 0:
            self.T_list = np.arange(T_start, T_end-T_inc, -T_inc)
        else:
            self.T_list = np.arange(T_start, T_end + T_inc, T_inc)

        #round T_list to 2 decimal places
        self.T_list = [round(x,2) for x in self.T_list]


        self.T_step = 0
        self.freq_step = 0
        self.measurement_status = "Setting temperature"

    def stop_measurement(self) -> None:
        self.linkam.stop()
        self.agilent.reset_and_clear()
        self.measurement_status = "Idle"

    def run_spectrometer(self) -> None:

        self.thread = QThread()
        self.worker = Experiment(self.agilent)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run_spectrometer)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.result.connect(self.get_result)
        self.thread.start()

    def get_result(self, result: list) -> None:
        self.parse_result(result)

        if self.voltage_list_mode:
            self.data_line_cap.setData(self.resultsDict[self.T_list[self.T_step]][self.freq_list[self.freq_step]]
                                       ["volt"], self.resultsDict[self.T_list[self.T_step]][self.freq_list[self.freq_step]]["Cp"])
            self.data_line_dis.setData(self.resultsDict[self.T_list[self.T_step]][self.freq_list[self.freq_step]]
                                       ["volt"], self.resultsDict[self.T_list[self.T_step]][self.freq_list[self.freq_step]]["D"])

            if self.T_step == len(self.T_list) - 1 and self.freq_step == len(self.freq_list) - 1:
                self.measurement_status = "Finished"
                make_excel(self.resultsDict, self.output_file_input.text(), self.voltage_list_mode)
                with open(self.output_file_input.text(), "w") as write_file:
                    json.dump(self.resultsDict, write_file, indent=4)
            else:
                if self.freq_step == len(self.freq_list) - 1:
                    self.T_step += 1
                    self.freq_step = 0
                    self.measurement_status = "Setting temperature"

                else:
                    self.freq_step += 1
                    self.measurement_status = "Setting temperature"
        else:
            self.data_line_cap.setData(
                self.resultsDict[self.T_list[self.T_step]]["freq"], self.resultsDict[self.T_list[self.T_step]]["Cp"])
            self.data_line_dis.setData(
                self.resultsDict[self.T_list[self.T_step]]["freq"], self.resultsDict[self.T_list[self.T_step]]["D"])

            if self.T_step == len(self.T_list) - 1:
                self.measurement_status = "Finished"
                make_excel(self.resultsDict, self.output_file_input.text(), self.voltage_list_mode)
                with open(self.output_file_input.text(), "w") as write_file:
                    json.dump(self.resultsDict, write_file, indent=4)

                
            else:
                self.T_step += 1
                self.measurement_status = "Setting temperature"

    def parse_result(self, result: dict) -> None:

        T = self.T_list[self.T_step]
        
        if self.voltage_list_mode:
            freq = self.freq_list[self.freq_step]

            self.resultsDict[T][freq] = dict()

            self.resultsDict[T][freq]["Cp"] = []
            self.resultsDict[T][freq]["D"] = []
            self.resultsDict[T][freq]["volt"] = []
            self.resultsDict[T][freq]["G"] = []
            self.resultsDict[T][freq]["B"] = []
        

            for i, volt in enumerate(self.voltage_list):
                increment = i+(3*i)
                self.resultsDict[T][freq]["volt"].append(volt)
                self.resultsDict[T][freq]["Cp"].append(result["CPD"][increment])
                self.resultsDict[T][freq]["D"].append(result["CPD"][increment + 1])
                self.resultsDict[T][freq]["G"].append(result["GB"][increment])
                self.resultsDict[T][freq]["B"].append(result["GB"][increment + 1])
        else:

            self.resultsDict[T]["Cp"] = []
            self.resultsDict[T]["D"] = []
            self.resultsDict[T]["freq"] = []
            self.resultsDict[T]["G"] = []
            self.resultsDict[T]["B"] = []
            
            for i, freq in enumerate(self.freq_list):
                increment = i+(3*i)
                self.resultsDict[T]["freq"].append(freq)
                self.resultsDict[T]["Cp"].append(result["CPD"][increment])
                self.resultsDict[T]["D"].append(result["CPD"][increment + 1])
                self.resultsDict[T]["G"].append(result["GB"][increment])
                self.resultsDict[T]["B"].append(result["GB"][increment + 1])

    ###################### END OF CONTROL LOGIC ###############################


def main():
    app = QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
    
