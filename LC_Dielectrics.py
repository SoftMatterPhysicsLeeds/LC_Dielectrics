from qtpy.QtWidgets import (QMainWindow, QWidget, QGridLayout, QApplication, QFrame,
                            QLabel, QLineEdit, 
                            QCheckBox, QHBoxLayout,QVBoxLayout, 
                            QPushButton, QFileDialog, QComboBox, QGroupBox)
from qtpy import QtCore
from qtpy.QtCore import QThread
from PyQt5.QtCore import pyqtSignal
import pyqtgraph as pg
import sys
import numpy as np
from LinkamHotstage import LinkamHotstage  #type: ignore
from Agilent_E4890A import AgilentSpectrometer  #type: ignore
import pyvisa
import json


class Experiment(QtCore.QObject):
    finished = pyqtSignal()
    result = pyqtSignal(list)

    def __init__(self, agilent: AgilentSpectrometer):
        super().__init__()
        self.agilent = agilent
        

    def run_spectrometer(self) -> None:
        result = self.agilent.measure()
        self.result.emit(result)
        self.finished.emit()


class MainWindow(QMainWindow):

    def __init__(self, testing="false"):
        super(MainWindow, self).__init__()
        

        self.testing = testing

        if self.testing == "false":
            self.testing = False
        else:
            self.testing = True

        self.setWindowTitle("LC Dielectrics")

        self.resultsDict = dict()
      
        self.current_T = 30.0
        self.linkam_action = "Idle"
        self.linkam_status = "Not Connected"
        self.agilent_status = "Not Connected"
        self.measurement_status = "Idle"
        self.t_stable_count = 0
        self.voltage_list_mode = False

        self.layout = QGridLayout()
        self.statusFrame()

        self.instrumentSettingsFrame()
        self.layout.addWidget(self.instrument_settings_frame, 1, 0, 1, 2)

        self.measurementSettingsFrame()
        self.layout.addWidget(self.measurement_settings_frame,2,0,1,2)

        self.frequencySettingsFrame()
        self.layout.addWidget(self.freq_settings_frame, 3,0)

        self.voltageSettingsFrame()
        self.layout.addWidget(self.voltage_settings_frame,3,1)

        self.temperatureSettingsFrame()
        self.layout.addWidget(self.temperature_settings_frame,4,0,1,2)

        self.outputDataSettingsFrame()
        self.layout.addWidget(self.output_settings_frame,5,0,1,2)

        self.graphFrame()
        self.layout.addWidget(self.graph_frame,0,2,7,1)

        self.go_button = QPushButton("Start")
        self.layout.addWidget(self.go_button,6, 0,1,1)
        self.go_button.clicked.connect(self.start_measurement)
        self.set_button_style(self.go_button,"green")

        self.stop_button = QPushButton("Stop")
        self.layout.addWidget(self.stop_button,6, 1,1,1)
        self.stop_button.clicked.connect(self.stop_measurement)
        self.set_button_style(self.stop_button,"red")

        #EVENT LOOP
        self.timer = QtCore.QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_ui)
        self.timer.start()

        widget = QWidget()

        widget.setLayout(self.layout)
        self.setCentralWidget(widget)

    ####### GUI LOGIC (all frames etc)


    def set_button_style(self, button: QPushButton, bg_colour: str, fixed_width: bool = False) -> None:
        #button.setFixedWidth(250)
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
        
    


    def statusFrame(self) -> None:
        self.status_frame = QFrame()
        layout = QGridLayout(self.status_frame)
        self.status_frame.setFrameStyle(QFrame.Box)

        layout.addWidget(QLabel("Measurement Status: "), 0,0)
        self.measurement_status_label = QLabel(f"{self.measurement_status}")
        layout.addWidget(self.measurement_status_label, 0, 1)
        
        layout.addWidget(QLabel("Linkam Status: "), 1, 0)
        self.linkam_status_label = QLabel(f"{self.linkam_status}")
        layout.addWidget(self.linkam_status_label, 1, 1)

        layout.addWidget(QLabel("Agilent Status: "), 2, 0)
        self.agilent_status_label = QLabel(f"{self.agilent_status}")
        layout.addWidget(self.agilent_status_label , 2, 1)

        self.layout.addWidget(self.status_frame, 0, 0 ,1, 2)

        # self.status_frame.setStyleSheet(
        #     "QFrame {border: 1px solid rgb(100,100,100)}")

    def instrumentSettingsFrame(self) -> None:
        self.instrument_settings_frame = QFrame()
        layout = QGridLayout(self.instrument_settings_frame)
        self.instrument_settings_frame.setFrameStyle(QFrame.Box)

        layout.addWidget(QLabel("Linkam COM port: "), 0, 0)
        self.com_selector = QComboBox()

        layout.addWidget(self.com_selector, 0, 1)

        layout.addWidget(QLabel("Agilent USB port: "), 1, 0)
        self.usb_selector = QComboBox()
        layout.addWidget(self.usb_selector, 1, 1)

         # get all visa resources: 
        rm = pyvisa.ResourceManager()
        resource_list = rm.list_resources()

        for resource in resource_list:
            if resource.split("::")[0][0:4] == "ASRL":
                self.com_selector.addItem(resource)
            elif resource.split("::")[0][0:3] == "USB":
                self.usb_selector.addItem(resource)
            else:
                print(f"Unknown resource: {resource} ")
        
        
        self.init_linkam_button = QPushButton("Initialise")
        layout.addWidget(self.init_linkam_button,0,2)
        self.init_linkam_button.clicked.connect(self.init_linkam)
        
        self.init_agilent_button = QPushButton("Initialise")
        layout.addWidget(self.init_agilent_button,1,2)
        self.init_agilent_button.clicked.connect(self.init_agilent)



    def measurementSettingsFrame(self) -> None:
        self.measurement_settings_frame = QGroupBox()
        layout =  QGridLayout(self.measurement_settings_frame)
        self.measurement_settings_frame.setFrame = True
        self.measurement_settings_frame.setTitle("Measurement Settings")
        

        layout.addWidget(QLabel("Meas. Time. Mode: "), 0,0)
        self.time_selector = QComboBox()    
        self.time_selector.addItem("SHOR")
        self.time_selector.addItem("MED")
        self.time_selector.addItem("LONG")
        layout.addWidget(self.time_selector,0,1)
        
        layout.addWidget(QLabel("Averaging Factor"),0,2)
        self.averaging_factor = QLineEdit("1")
        layout.addWidget(self.averaging_factor,0,3)

        
        layout.addWidget(QLabel("Bias Level (V)"),0,4)
        self.bias_voltage = QLineEdit("0")
        layout.addWidget(self.bias_voltage,0,5)

    def frequencySettingsFrame(self) -> None:
        self.freq_settings_frame = QGroupBox()
        layout = QGridLayout(self.freq_settings_frame)

        self.freq_settings_frame.setFrame = True
        self.freq_settings_frame.setTitle("Frequency Settings")

        layout.addWidget(QLabel("Number of Data Points"),0,0)
        self.freq_points = QLineEdit("10")
        layout.addWidget(self.freq_points,1,0)

        layout.addWidget(QLabel("Min Frequency"),2,0)
        self.freq_min = QLineEdit("20")
        layout.addWidget(self.freq_min,3,0)

        layout.addWidget(QLabel("Max Frequency"),4,0)
        self.freq_max = QLineEdit("2e6")
        layout.addWidget(self.freq_max,5,0)
        
    def voltageSettingsFrame(self) -> None:
        self.voltage_settings_frame = QGroupBox()
        layout = QGridLayout(self.voltage_settings_frame)
        self.voltage_settings_frame.setFrame = True
        self.voltage_settings_frame.setTitle("Voltage Settings")
        
      

        layout.addWidget(QLabel("Number of Data Points"),0,0)
        self.voltage_points = QLineEdit("1")
        layout.addWidget(self.voltage_points,1,0)

        self.voltage_min_label = QLabel("Voltage")
        layout.addWidget(self.voltage_min_label,2,0)
        self.voltage_min = QLineEdit("1")
        layout.addWidget(self.voltage_min,3,0)

        layout.addWidget(QLabel("Max Voltage"),4,0)
        self.voltage_max = QLineEdit("1")
        layout.addWidget(self.voltage_max,5,0)

          
        layout.addWidget(QLabel("Single Voltage?"),0,1)
        self.voltage_checkbox = QCheckBox()
        layout.addWidget(self.voltage_checkbox,1,1)
        self.voltage_checkbox.stateChanged.connect(self.voltage_toggle)
        self.voltage_checkbox.setChecked(True)

    def voltage_toggle(self) -> None:
        if self.voltage_checkbox.isChecked():
            self.voltage_points.setEnabled(False)
            self.voltage_max.setEnabled(False)
            self.voltage_min_label.setText("Voltage")
            self.voltage_list_mode = False

        else:
            self.voltage_points.setEnabled(True)
            self.voltage_max.setEnabled(True)
            self.voltage_min_label.setText("Min Voltage")
            self.voltage_list_mode = True



    def temperatureSettingsFrame(self) -> None:
        self.temperature_settings_frame = QGroupBox()
        layout = QGridLayout(self.temperature_settings_frame)
        self.temperature_settings_frame.setFrame = True
        self.temperature_settings_frame.setTitle("Temperature Settings")

        layout.addWidget(QLabel("Start Temp."),0,0)
        self.temp_start = QLineEdit("25")
        layout.addWidget(self.temp_start,1,0)
        
        layout.addWidget(QLabel("End Temp."),2,0)
        self.temp_end = QLineEdit("30")
        layout.addWidget(self.temp_end,3,0)

        layout.addWidget(QLabel("Temp Step."),4,0)
        self.temp_step = QLineEdit("1")
        layout.addWidget(self.temp_step,5,0)

        layout.addWidget(QLabel("Rate."),0,1)
        self.temp_rate = QLineEdit("10")
        layout.addWidget(self.temp_rate,1,1)

        layout.addWidget(QLabel("Stab. Time (s)"),2,1)
        self.stab_time = QLineEdit("1")
        layout.addWidget(self.stab_time,3,1)

    def outputDataSettingsFrame(self) -> None:
        self.output_settings_frame = QGroupBox()
        layout = QGridLayout(self.output_settings_frame)
        self.output_settings_frame.setFrame = True
        self.output_settings_frame.setTitle("Output Data Settings")

        self.output_file_input = QLineEdit("results.json")
        layout.addWidget(self.output_file_input,0,0)

        self.add_file_button = QPushButton("Browse")
        layout.addWidget(self.add_file_button,0,1)
        self.add_file_button.clicked.connect(self.add_file_dialogue)
        # self.set_button_style(self.add_file_button, "blue", True)

    def add_file_dialogue(self) -> None:
        filename, _ = QFileDialog.getSaveFileName(self, "Output File","","JSON Files (*.json)")
        self.output_file_input.setText(filename)

    def graphFrame(self) -> None:

        self.graph_frame = QFrame()
        layout = QGridLayout(self.graph_frame)

        self.graphWidget_Cap = pg.PlotWidget()
        layout.addWidget(self.graphWidget_Cap, 0,0)
        self.graphWidget_Cap.setBackground(None)
        self.graphWidget_Cap.setLabel('left', 'Capacitance', 'F')
        self.graphWidget_Cap.setLabel('bottom', 'Frequency', 'Hz')
        self.graph_T = [self.current_T] * 100
        self.graph_time = list(np.arange(0, 10, 0.1))
        pen = pg.mkPen(color=(255, 0, 0))
        self.data_line_cap = self.graphWidget_Cap.plot(
            self.graph_time, self.graph_T, pen=pen)

        self.graphWidget_Dis = pg.PlotWidget()
        layout.addWidget(self.graphWidget_Dis, 1,0)
        self.graphWidget_Dis.setBackground(None)
        self.graphWidget_Dis.setLabel('left', 'Dissipation', 'F')
        self.graphWidget_Dis.setLabel('bottom', 'Frequency', 'Hz')

        self.data_line_dis = self.graphWidget_Dis.plot(
            self.graph_time, self.graph_T, pen=pen)

        self.data_line_cap.setLogMode(True,False)  
        self.data_line_dis.setLogMode(True,False)  
    ###################### END OF GUI LOGIC #############################

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

    def update_ui(self) -> None:
        self.agilent_status_label.setText(self.agilent_status)
        
        # if Linkam is connected, show real-time temperature
        if self.linkam_status == "Connected":
            self.current_T, self.linkam_action = self.linkam.current_temperature()
            self.linkam_status_label.setText(f"{self.linkam_status}, {self.linkam_action}, T: {self.current_T}")
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
            self.t_stable_count+=1

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

        # else: 
        #     #print(f"{self.linkam_action}")
        #     print(f"You haven't handled this status: {self.measurement_status}")

        self.measurement_status_label.setText(self.measurement_status)



    def start_measurement(self) -> None: 

        freq_min = float(self.freq_min.text())
        freq_max = float(self.freq_max.text())
        freq_points = int(self.freq_points.text())

        voltage_min = float(self.voltage_min.text())
        voltage_max = float(self.voltage_max.text())
        voltage_points = int(self.voltage_points.text())

        self.freq_list = list(np.logspace(np.log10(freq_min), np.log10(freq_max), freq_points))
       

        if  self.voltage_list_mode:
            self.voltage_list = list(np.linspace(voltage_min, voltage_max, voltage_points))
            self.agilent.set_volt_list(self.voltage_list)
            self.agilent.set_frequency(self.freq_list[0])
        else:
            self.resultsDict["volt"] = voltage_min
            self.agilent.set_voltage(voltage_min)
            self.agilent.set_freq_list(self.freq_list)
        
        self.agilent.set_aperture_mode(self.time_selector.currentText(), int(self.averaging_factor.text()))

        #calculate T list 
        T_start = float(self.temp_start.text())
        T_end = float(self.temp_end.text())
        T_inc = float(self.temp_step.text())
        self.T_rate = float(self.temp_rate.text())

        if T_start == T_end:
            self.T_list = np.array([T_start])
        elif T_start > T_end and T_inc > 0: 
            self.T_list = np.arange(T_start,T_end-T_inc, -T_inc)
        else:
            self.T_list = np.arange(T_start, T_end + T_inc, T_inc)

        self.T_step = 0
        self.freq_step = 0
        self.measurement_status = "Setting temperature"

        
    def stop_measurement(self) -> None:
        self.linkam.stop()
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
        
    def get_result(self,result: list) -> None:
        self.parse_result(result)
        
        if self.voltage_list_mode:
            self.data_line_cap.setData(self.resultsDict[self.T_list[self.T_step]][self.freq_list[self.freq_step]]["volt"],self.resultsDict[self.T_list[self.T_step]][self.freq_list[self.freq_step]]["Cp"])        
            self.data_line_dis.setData(self.resultsDict[self.T_list[self.T_step]][self.freq_list[self.freq_step]]["volt"],self.resultsDict[self.T_list[self.T_step]][self.freq_list[self.freq_step]]["D"])      
            
            if self.T_step == len(self.T_list) - 1 and self.freq_step == len(self.freq_list) - 1:
                self.measurement_status = "Finished"
                with open(self.output_file_input.text(), "w") as write_file:
                    json.dump(self.resultsDict, write_file, indent=4)
            else:
                if self.freq_step == len(self.freq_list) - 1:
                    self.T_step+=1
                    self.freq_step = 0
                    self.measurement_status = "Setting temperature"
                
                else:
                    self.freq_step+=1
                    self.measurement_status = "Setting temperature"
        else:
            self.data_line_cap.setData(self.resultsDict[self.T_list[self.T_step]]["freq"],self.resultsDict[self.T_list[self.T_step]]["Cp"])        
            self.data_line_dis.setData(self.resultsDict[self.T_list[self.T_step]]["freq"],self.resultsDict[self.T_list[self.T_step]]["D"])
            
            if self.T_step == len(self.T_list) - 1:
                self.measurement_status = "Finished"
                with open(self.output_file_input.text(), "w") as write_file:
                    json.dump(self.resultsDict, write_file, indent=4)
            else:
                self.T_step+=1
                self.measurement_status = "Setting temperature"
     

    def parse_result(self, result: list) -> list:

        T = self.T_list[self.T_step]   
        #self.resultsDict[T] = dict()
        if self.voltage_list_mode:
            freq = self.freq_list[self.freq_step]
            
            self.resultsDict[T][freq] = dict()

            self.resultsDict[T][freq]["Cp"] = []
            self.resultsDict[T][freq]["D"] = []
            self.resultsDict[T][freq]["volt"] = []

            for i,volt in enumerate(self.voltage_list):
                increment = i+(3*i)
                self.resultsDict[T][freq]["volt"].append(volt)
                self.resultsDict[T][freq]["Cp"].append(result[increment])
                self.resultsDict[T][freq]["D"].append(result[increment + 1])
        else:

            
            self.resultsDict[T]["Cp"] = []
            self.resultsDict[T]["D"] = []
            self.resultsDict[T]["freq"] = []
            for i,freq in enumerate(self.freq_list):
                increment = i+(3*i)
                self.resultsDict[T]["freq"].append(freq)
                self.resultsDict[T]["Cp"].append(result[increment])
                self.resultsDict[T]["D"].append(result[increment + 1])


    # 0...4...8...12
    # 0...3...6...9
    # 0...1...2...3
    # i+(3*i)

        

    

    
    ###################### END OF CONTROL LOGIC ###############################

if __name__ == "__main__":

    app = QApplication(sys.argv)
    if len(sys.argv) > 1:
        main = MainWindow(sys.argv[1])
    else:
        main = MainWindow()

    # main.setGeometry(200,100,800,480)

    main.show()
    sys.exit(app.exec_())
