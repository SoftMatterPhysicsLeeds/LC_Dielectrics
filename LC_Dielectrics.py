from qtpy.QtWidgets import (QMainWindow, QWidget, QGridLayout, QApplication, QFrame,
                            QLabel, QLineEdit, 
                            QCheckBox, QHBoxLayout,QVBoxLayout, 
                            QPushButton, QFileDialog, QComboBox, QGroupBox)
from qtpy import QtGui, QtCore
import pyqtgraph as pg
import sys
import numpy as np
from LinkamHotstage import LinkamHotstage
from Agilent_E4890A import AgilentSpectrometer
import pyvisa


class MainWindow(QMainWindow):

    def __init__(self, testing="false"):
        super(MainWindow, self).__init__()

        self.testing = testing

        if self.testing == "false":
            self.testing = False
        else:
            self.testing = True

        self.setWindowTitle("LC Dielectrics")
      
        self.current_T = 30.0
        self.linkam_status = "Not Connected"
        self.agilent_status = "Not Connected"

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
        self.layout.addWidget(self.go_button,6, 0,1,2)
        self.go_button.clicked.connect(self.start_measurement)

        widget = QWidget()

        widget.setLayout(self.layout)
        self.setCentralWidget(widget)

    ####### GUI LOGIC (all frames etc)


    def statusFrame(self) -> None:
        self.status_frame = QFrame()
        layout = QGridLayout(self.status_frame)
        self.status_frame.setFrameStyle(QFrame.Box)

        layout.addWidget(QLabel("Linkam Status: "), 0, 0)
        self.linkam_status_label = QLabel(f"{self.linkam_status}")
        layout.addWidget(self.linkam_status_label, 0, 1)

        layout.addWidget(QLabel("Agilent Status: "), 1, 0)
        self.agilent_status_label = QLabel(f"{self.agilent_status}")
        layout.addWidget(self.agilent_status_label , 1, 1)

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
        
        self.init_agilent_button = QPushButton("Initialise")
        layout.addWidget(self.init_agilent_button,0,2)
        self.init_agilent_button.clicked.connect(self.init_agilent)

        self.init_linkam_button = QPushButton("Initialise")
        layout.addWidget(self.init_linkam_button,1,2)
        self.init_linkam_button.clicked.connect(self.init_linkam)


    def measurementSettingsFrame(self) -> None:
        self.measurement_settings_frame = QGroupBox()
        layout =  QHBoxLayout(self.measurement_settings_frame)
        self.measurement_settings_frame.setFrame = True
        self.measurement_settings_frame.setTitle("Measurement Settings")
        
        
        layout.addWidget(QLabel("Averaging Factor"),0)
        self.averaging_factor = QLineEdit("10")
        layout.addWidget(self.averaging_factor,1)

        
        layout.addWidget(QLabel("Bias Level (V)"),2)
        self.bias_voltage = QLineEdit("0")
        layout.addWidget(self.bias_voltage,3)

    def frequencySettingsFrame(self) -> None:
        self.freq_settings_frame = QGroupBox()
        layout = QVBoxLayout(self.freq_settings_frame)
        # self.freq_settings_frame.setFrameStyle(QFrame.Box)
        # self.freq_settings_frame.setStyleSheet("QGroupBox#self.freq_settings_frame \
        # {border: 2px solid-gray;\
        # font: Fira Code}")
        self.freq_settings_frame.setFrame = True
        self.freq_settings_frame.setTitle("Frequency Settings")

        layout.addWidget(QLabel("Number of Data Points"),0)
        self.freq_points = QLineEdit("100")
        layout.addWidget(self.freq_points,1)

        layout.addWidget(QLabel("Min Frequency"),2)
        self.freq_min = QLineEdit("20")
        layout.addWidget(self.freq_min,3)

        layout.addWidget(QLabel("Max Frequency"),4)
        self.freq_max = QLineEdit("2e6")
        layout.addWidget(self.freq_max,5)
        
    def voltageSettingsFrame(self) -> None:
        self.voltage_settings_frame = QGroupBox()
        layout = QVBoxLayout(self.voltage_settings_frame)
        self.voltage_settings_frame.setFrame = True
        self.voltage_settings_frame.setTitle("Voltage Settings")
        

        layout.addWidget(QLabel("Number of Data Points"),0)
        self.voltage_points = QLineEdit("1")
        layout.addWidget(self.voltage_points,1)

        layout.addWidget(QLabel("Min Voltage"),2)
        self.voltage_min = QLineEdit("1")
        layout.addWidget(self.voltage_min,3)

        layout.addWidget(QLabel("Max Voltage"),4)
        self.voltage_max = QLineEdit("1")
        layout.addWidget(self.voltage_max,5)

    def temperatureSettingsFrame(self) -> None:
        self.temperature_settings_frame = QGroupBox()
        layout = QGridLayout(self.temperature_settings_frame)
        self.temperature_settings_frame.setFrame = True
        self.temperature_settings_frame.setTitle("Temperature Settings")

        layout.addWidget(QLabel("Start Temp."),0,0)
        self.temp_start = QLineEdit("25")
        layout.addWidget(self.temp_start,1,0)
        
        layout.addWidget(QLabel("End Temp."),2,0)
        self.temp_end = QLineEdit("25")
        layout.addWidget(self.temp_end,3,0)

        layout.addWidget(QLabel("Temp Step."),4,0)
        self.temp_step = QLineEdit("1")
        layout.addWidget(self.temp_step,5,0)

        layout.addWidget(QLabel("Rate."),0,1)
        self.temp_rate = QLineEdit("10")
        layout.addWidget(self.temp_rate,1,1)

        layout.addWidget(QLabel("Stab. Time (s)"),2,1)
        self.temp_rate = QLineEdit("60")
        layout.addWidget(self.temp_rate,3,1)

    def outputDataSettingsFrame(self) -> None:
        self.output_settings_frame = QGroupBox()
        layout = QVBoxLayout(self.output_settings_frame)
        self.output_settings_frame.setFrame = True
        self.output_settings_frame.setTitle("Output Data Settings")

        layout.addWidget(QLabel("Output data file: "),0)
        self.output_file_input = QLineEdit(r"C:\something\dan")
        layout.addWidget(self.output_file_input,1)

    def graphFrame(self) -> None:

        self.graph_frame = QFrame()
        layout = QVBoxLayout(self.graph_frame)

        self.graphWidget_Cap = pg.PlotWidget()
        layout.addWidget(self.graphWidget_Cap, 0)
        self.graphWidget_Cap.setBackground(None)
        self.graphWidget_Cap.setLabel('left', 'Capacitance', 'F')
        self.graphWidget_Cap.setLabel('bottom', 'Frequency', 'Hz')
        self.graph_T = [self.current_T] * 100
        self.graph_time = list(np.arange(0, 10, 0.1))
        pen = pg.mkPen(color=(255, 0, 0))
        self.data_line_cap = self.graphWidget_Cap.plot(
            self.graph_time, self.graph_T, pen=pen)

        self.graphWidget_Dis = pg.PlotWidget()
        layout.addWidget(self.graphWidget_Dis, 1)
        self.graphWidget_Dis.setBackground(None)
        self.graphWidget_Dis.setLabel('left', 'Dissipation', 'F')
        self.graphWidget_Dis.setLabel('bottom', 'Frequency', 'Hz')

        self.data_line_dis = self.graphWidget_Dis.plot(
            self.graph_time, self.graph_T, pen=pen)

    ###################### END OF GUI LOGIC #############################

    ###################### Control Logic ################################

    def init_agilent(self) -> None:
        self.agilent = AgilentSpectrometer(self.usb_selector.currentText())
        self.agilent_status = "Connected"
        self.update_ui()
    
    def init_linkam(self) -> None:
        self.linkam = LinkamHotstage(self.com_selector.currentText())
        self.linkam_status = "Connected"
        self.update_ui()

    def update_ui(self) -> None:
        self.agilent_status_label.setText(self.agilent_status)
        self.linkam_status_label.setText(self.linkam_status)

    def start_measurement(self) -> None: 
        print("Measurement Started!")

    


if __name__ == "__main__":

    app = QApplication(sys.argv)
    if len(sys.argv) > 1:
        main = MainWindow(sys.argv[1])
    else:
        main = MainWindow()

    # main.setGeometry(200,100,800,480)

    main.show()
    sys.exit(app.exec_())
