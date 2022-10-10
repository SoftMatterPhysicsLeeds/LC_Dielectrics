from qtpy.QtWidgets import QMainWindow, QGridLayout, QFrame, QLabel, QComboBox, QPushButton, QGroupBox, QLineEdit, QCheckBox, QFileDialog
import pyvisa
import pyqtgraph as pg
import numpy as np


def statusFrame(window: QMainWindow) -> None:
    window.status_frame = QFrame()
    layout = QGridLayout(window.status_frame)
    window.status_frame.setFrameStyle(QFrame.Box)

    layout.addWidget(QLabel("Measurement Status: "), 0, 0)
    window.measurement_status_label = QLabel(f"{window.measurement_status}")
    layout.addWidget(window.measurement_status_label, 0, 1)

    layout.addWidget(QLabel("Linkam Status: "), 1, 0)
    window.linkam_status_label = QLabel(f"{window.linkam_status}")
    layout.addWidget(window.linkam_status_label, 1, 1)

    layout.addWidget(QLabel("Agilent Status: "), 2, 0)
    window.agilent_status_label = QLabel(f"{window.agilent_status}")
    layout.addWidget(window.agilent_status_label, 2, 1)


def instrumentSettingsFrame(window) -> None:
    window.instrument_settings_frame = QFrame()
    layout = QGridLayout(window.instrument_settings_frame)
    window.instrument_settings_frame.setFrameStyle(QFrame.Box)

    layout.addWidget(QLabel("Linkam COM port: "), 0, 0)
    window.com_selector = QComboBox()

    layout.addWidget(window.com_selector, 0, 1)

    layout.addWidget(QLabel("Agilent USB port: "), 1, 0)
    window.usb_selector = QComboBox()
    layout.addWidget(window.usb_selector, 1, 1)

    # get all visa resources:
    rm = pyvisa.ResourceManager()
    resource_list = rm.list_resources()

    for resource in resource_list:
        if resource.split("::")[0][0:4] == "ASRL":
            window.com_selector.addItem(resource)
        elif resource.split("::")[0][0:3] == "USB":
            window.usb_selector.addItem(resource)
        else:
            print(f"Unknown resource: {resource} ")

    window.init_linkam_button = QPushButton("Initialise")
    layout.addWidget(window.init_linkam_button, 0, 2)
    window.init_linkam_button.clicked.connect(window.init_linkam)

    window.init_agilent_button = QPushButton("Initialise")
    layout.addWidget(window.init_agilent_button, 1, 2)
    window.init_agilent_button.clicked.connect(window.init_agilent)


def measurementSettingsFrame(window) -> None:
    window.measurement_settings_frame = QGroupBox()
    layout = QGridLayout(window.measurement_settings_frame)
    window.measurement_settings_frame.setFrame = True
    window.measurement_settings_frame.setTitle("Measurement Settings")

    layout.addWidget(QLabel("Meas. Time. Mode: "), 0, 0)
    window.time_selector = QComboBox()
    window.time_selector.addItem("SHOR")
    window.time_selector.addItem("MED")
    window.time_selector.addItem("LONG")
    layout.addWidget(window.time_selector, 0, 1)

    layout.addWidget(QLabel("Averaging Factor"), 0, 2)
    window.averaging_factor = QLineEdit("1")
    layout.addWidget(window.averaging_factor, 0, 3)
    window.averaging_factor.editingFinished.connect(
        lambda: limits(window, window.averaging_factor, 256, 1))

    layout.addWidget(QLabel("Bias Level (V)"), 0, 4)
    window.bias_voltage_selector = QComboBox()
    window.bias_voltage_selector.addItem("0")
    window.bias_voltage_selector.addItem("1.5")
    window.bias_voltage_selector.addItem("2")
    layout.addWidget(window.bias_voltage_selector, 0, 5)


def frequencySettingsFrame(window) -> None:
    window.freq_settings_frame = QGroupBox()
    layout = QGridLayout(window.freq_settings_frame)

    window.freq_settings_frame.setFrame = True
    window.freq_settings_frame.setTitle("Frequency Settings")

    layout.addWidget(QLabel("Number of Data Points"), 0, 0)
    window.freq_points = QLineEdit("10")
    layout.addWidget(window.freq_points, 1, 0)
    window.freq_points.editingFinished.connect(
        lambda: limits(window, window.freq_points, 201, 10))

    layout.addWidget(QLabel("Min Frequency"), 2, 0)
    window.freq_min = QLineEdit("20")
    layout.addWidget(window.freq_min, 3, 0)
    window.freq_min.editingFinished.connect(
        lambda: limits(window, window.freq_min, 20, 20, False))
    window.freq_min.editingFinished.connect(
        lambda: limits(window, window.freq_min, 2e6, 20))

    layout.addWidget(QLabel("Max Frequency"), 4, 0)
    window.freq_max = QLineEdit("2e6")
    layout.addWidget(window.freq_max, 5, 0)
    window.freq_max.editingFinished.connect(
        lambda: limits(window, window.freq_max, 20, 20, False))
    window.freq_max.editingFinished.connect(
        lambda: limits(window, window.freq_max, 2e6, 20))


def voltageSettingsFrame(window) -> None:
    window.voltage_settings_frame = QGroupBox()
    layout = QGridLayout(window.voltage_settings_frame)
    window.voltage_settings_frame.setFrame = True
    window.voltage_settings_frame.setTitle("Voltage Settings")

    window.voltage_min_label = QLabel("Voltage")
    layout.addWidget(window.voltage_min_label, 0, 0)
    window.voltage_min = QLineEdit("1")
    layout.addWidget(window.voltage_min, 1, 0)
    window.voltage_min.editingFinished.connect(
        lambda: limits(window, window.voltage_min, 0, 1, False))
    window.voltage_min.editingFinished.connect(
        lambda: limits(window, window.voltage_min, 20, 1))

    layout.addWidget(QLabel("Max Voltage"), 2, 0)
    window.voltage_max = QLineEdit("1")
    layout.addWidget(window.voltage_max, 3, 0)
    window.voltage_max.editingFinished.connect(
        lambda: limits(window, window.voltage_max, 0, 1, False))
    window.voltage_max.editingFinished.connect(
        lambda: limits(window, window.voltage_max, 20, 1))

    layout.addWidget(QLabel("Step Size"), 4, 0)
    window.voltage_step = QLineEdit("1")
    layout.addWidget(window.voltage_step, 5, 0)
    window.voltage_step.editingFinished.connect(
        lambda: limits(window, window.voltage_step, 0.001, 0.1, False))
    window.voltage_step.editingFinished.connect(
        lambda: limits(window, window.voltage_step, 20, 0.1))

    layout.addWidget(QLabel("Single Voltage?"), 0, 1)
    window.voltage_checkbox = QCheckBox()
    layout.addWidget(window.voltage_checkbox, 1, 1)
    window.voltage_checkbox.stateChanged.connect(window.voltage_toggle)
    window.voltage_checkbox.setChecked(True)


def temperatureSettingsFrame(window) -> None:
    window.temperature_settings_frame = QGroupBox()
    layout = QGridLayout(window.temperature_settings_frame)
    window.temperature_settings_frame.setFrame = True
    window.temperature_settings_frame.setTitle("Temperature Settings")

    layout.addWidget(QLabel("Start Temp."), 0, 0)
    window.temp_start = QLineEdit("25")
    layout.addWidget(window.temp_start, 1, 0)

    layout.addWidget(QLabel("End Temp."), 2, 0)
    window.temp_end = QLineEdit("30")
    layout.addWidget(window.temp_end, 3, 0)

    layout.addWidget(QLabel("Temp Step."), 4, 0)
    window.temp_step = QLineEdit("1")
    layout.addWidget(window.temp_step, 5, 0)

    layout.addWidget(QLabel("Rate."), 0, 1)
    window.temp_rate = QLineEdit("10")
    layout.addWidget(window.temp_rate, 1, 1)

    layout.addWidget(QLabel("Stab. Time (s)"), 2, 1)
    window.stab_time = QLineEdit("1")
    layout.addWidget(window.stab_time, 3, 1)


def outputDataSettingsFrame(window) -> None:
    window.output_settings_frame = QGroupBox()
    layout = QGridLayout(window.output_settings_frame)
    window.output_settings_frame.setFrame = True
    window.output_settings_frame.setTitle("Output Data Settings")

    window.output_file_input = QLineEdit("results.json")
    layout.addWidget(window.output_file_input, 0, 0)

    window.add_file_button = QPushButton("Browse")
    layout.addWidget(window.add_file_button, 0, 1)
    window.add_file_button.clicked.connect(add_file_dialogue)


def graphFrame(window) -> None:

    window.graph_frame = QFrame()
    layout = QGridLayout(window.graph_frame)

    window.graphWidget_Cap = pg.PlotWidget()
    layout.addWidget(window.graphWidget_Cap, 0, 0)
    window.graphWidget_Cap.setBackground(None)
    window.graphWidget_Cap.setLabel('left', 'Capacitance', 'F')
    window.graphWidget_Cap.setLabel('bottom', 'Frequency', 'Hz')
    window.graph_T = [window.current_T] * 100
    window.graph_time = list(np.arange(0, 10, 0.1))
    pen = pg.mkPen(color=(255, 0, 0))
    window.data_line_cap = window.graphWidget_Cap.plot(
        window.graph_time, window.graph_T, pen=pen)

    window.graphWidget_Dis = pg.PlotWidget()
    layout.addWidget(window.graphWidget_Dis, 1, 0)
    window.graphWidget_Dis.setBackground(None)
    window.graphWidget_Dis.setLabel('left', 'Dissipation', 'F')
    window.graphWidget_Dis.setLabel('bottom', 'Frequency', 'Hz')

    window.data_line_dis = window.graphWidget_Dis.plot(
        window.graph_time, window.graph_T, pen=pen)

    window.data_line_cap.setLogMode(True, False)
    window.data_line_dis.setLogMode(True, False)


def add_file_dialogue(window) -> None:
    filename, _ = QFileDialog.getSaveFileName(
        window, "Output File", "", "JSON Files (*.json)")
    window.output_file_input.setText(filename)


def limits(window, thing, limit: float, default: float, max_val=True) -> None:
    try:
        if thing.text() == "":
            pass
        elif max_val == True and float(thing.text()) > limit or max_val == False and float(thing.text()) < limit:
            thing.setText(f"{limit}")
    except ValueError:
        thing.setText(f"{default}")