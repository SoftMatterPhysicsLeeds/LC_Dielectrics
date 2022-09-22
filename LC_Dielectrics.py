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
        self.layout.addWidget(self.status_frame, 0, 0 ,1, 2)
        

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
        self.layout.addWidget(self.graph_frame,0,2,6,1)

        widget = QWidget()

        widget.setLayout(self.layout)
        self.setCentralWidget(widget)

    def statusFrame(self) -> None:
        self.status_frame = QFrame()
        layout = QGridLayout(self.status_frame)
        self.status_frame.setFrameStyle(QFrame.Box)

        layout.addWidget(QLabel("Linkam Status: "), 0, 0)
        layout.addWidget(
            QLabel(f"{self.linkam_status}"), 0, 1)

        layout.addWidget(QLabel("Agilent Status: "), 1, 0)
        layout.addWidget(QLabel(f"{self.agilent_status}"), 1, 1)

        # self.status_frame.setStyleSheet(
        #     "QFrame {border: 1px solid rgb(100,100,100)}")

    def instrumentSettingsFrame(self) -> None:
        self.instrument_settings_frame = QFrame()
        layout = QGridLayout(self.instrument_settings_frame)
        self.instrument_settings_frame.setFrameStyle(QFrame.Box)
        layout.addWidget(QLabel("Linkam COM port: "), 0, 0)
        self.com_selector = QComboBox()
        self.com_selector.addItem("ASRL1::INSTR")
        self.com_selector.addItem("ASRL2::INSTR")
        self.com_selector.addItem("ASRL3::INSTR")
        layout.addWidget(self.com_selector, 0, 1)

        layout.addWidget(QLabel("Agilent USB port: "), 1, 0)
        self.usb_selector = QComboBox()
        self.usb_selector.addItem("USB0::0x0957::0x0909::MY46412852::INSTR")
        layout.addWidget(self.usb_selector, 1, 1)


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

if __name__ == "__main__":

    app = QApplication(sys.argv)
    if len(sys.argv) > 1:
        main = MainWindow(sys.argv[1])
    else:
        main = MainWindow()

    # main.setGeometry(200,100,800,480)

    main.show()
    sys.exit(app.exec_())
