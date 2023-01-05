from qtpy.QtWidgets import QWidget,  QMainWindow, QGridLayout, QFrame, QLabel, QComboBox, QPushButton, QGroupBox, QLineEdit, QCheckBox, QFileDialog, QListWidget, QListWidgetItem, QAbstractItemView
import pyvisa
import pyqtgraph as pg
import numpy as np

class ValueSelectorWindow(QWidget):
    """
    Popout window that will allow the user to select a range of frequencies/voltages/temperatures to add to the relevant list.
    """
    def __init__(self, main_window: QMainWindow, value_list: QListWidget, min_val: float, max_val: float, logspace: bool = True):
        super().__init__()
        self.main_window_ref = main_window
        self.value_list = value_list
        self.logspace = logspace
        self.setWindowTitle("Add values")

        layout = QGridLayout()

        if logspace:
            layout.addWidget(QLabel("Number of Points"), 0, 0, 1, 2)
            self.points = QLineEdit("10")
        else:
            self.combo = QComboBox()
            self.points = QLineEdit("0.1")
            self.combo.currentIndexChanged.connect(self.comboChanged)
            layout.addWidget(self.combo, 0, 0, 1, 2)
            self.combo.addItem("Step Size")
            self.combo.addItem("Number of Points")
            
        layout.addWidget(self.points, 1, 0, 1, 2)
        self.points.editingFinished.connect(
            lambda: limits(self, self.points, 201, 10))

        layout.addWidget(QLabel("Minimum"), 2, 0, 1, 2)
        self.min = QLineEdit(f"{min_val}")
        layout.addWidget(self.min, 3, 0, 1, 2)
        self.min.editingFinished.connect(
            lambda: limits(self, self.min, min_val, min_val, False))
        self.min.editingFinished.connect(
            lambda: limits(self, self.min, max_val, min_val))

        layout.addWidget(QLabel("Maximum"), 4, 0, 1, 2)
        self.max = QLineEdit(f"{max_val}")
        layout.addWidget(self.max, 5, 0, 1, 2)
        self.max.editingFinished.connect(
            lambda: limits(self, self.max, min_val, min_val, False))
        self.max.editingFinished.connect(
            lambda: limits(self, self.max, max_val, min_val))

        self.add_button = QPushButton("Append")
        layout.addWidget(self.add_button, 6, 0)
        self.add_button.clicked.connect(self.append)
        
        self.add_button = QPushButton("Replace")
        layout.addWidget(self.add_button, 6, 1)
        self.add_button.clicked.connect(self.replace)

        self.setLayout(layout)

    def comboChanged(self):
        if self.combo.currentText() == "Number of Points":
            self.points.setText("10")
        else: 
            self.points.setText("0.1")


    def replace(self):
        self.value_list.clear()
        self.append()


    def append(self):
        min_val = float(self.min.text())
        max_val = float(self.max.text())
        points = float(self.points.text())
        
        if self.logspace:
            val_list = [f"{x:.2f}" for x in list(np.logspace(
                np.log10(min_val), np.log10(max_val), points))]
        else:
            if self.combo.currentText() == "Number of Points":
                val_list = [f"{x:.2f}" for x in list(np.linspace(
                    min_val, max_val, points))]
            else: 
                val_list = [f"{x:.2f}" for x in list(np.arange(
                    min_val, max_val, points))]
        
        for val in val_list:
            addValuesToList(self.value_list,val)

        self.close()


def addValuesToList(list_widget: QListWidget, value: str) -> None:
    item = QListWidgetItem(value,list_widget)
    list_widget.setCurrentItem(item)

def removeValuesFromList(list_widget: QListWidget) -> None:
    items = list_widget.selectedItems()
    for item in items:
        list_widget.takeItem(list_widget.row(item))



def createMultiValueWindow(window: QMainWindow, list_widget: QListWidget, min_val: float,  max_val: float, logspace: bool = True) -> None:
    window.sw = ValueSelectorWindow(window, list_widget, min_val, max_val, logspace)
    window.sw.show()


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
    window.freq_settings_frame.setTitle("Frequency List")

    window.freq_list_widget = QListWidget()
    layout.addWidget(window.freq_list_widget, 0, 0, 4 ,1 )
    window.freq_list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
    QListWidgetItem("20",window.freq_list_widget)

    add_freq_edit = QLineEdit("20")
    layout.addWidget(add_freq_edit, 0, 1)
    add_freq_edit.editingFinished.connect(
            lambda: limits(window, add_freq_edit, 20, 20, False))
    add_freq_edit.editingFinished.connect(
            lambda: limits(window, add_freq_edit, 2e6, 20))


    add_freq_button = QPushButton("Add")
    layout.addWidget(add_freq_button, 1, 1)
    add_freq_button.clicked.connect(lambda: addValuesToList(window.freq_list_widget, add_freq_edit.text()))
    
    delete_freq_button = QPushButton("Delete")
    layout.addWidget(delete_freq_button, 2, 1)
    delete_freq_button.clicked.connect(lambda: removeValuesFromList(window.freq_list_widget))

    multi_freq_button  = QPushButton("Add range")
    layout.addWidget(multi_freq_button, 3, 1)
    multi_freq_button.clicked.connect(lambda: createMultiValueWindow(window, window.freq_list_widget, 20, 2e6))


def voltageSettingsFrame(window) -> None:
    window.voltage_settings_frame = QGroupBox()
    layout = QGridLayout(window.voltage_settings_frame)
    window.voltage_settings_frame.setFrame = True
    window.voltage_settings_frame.setTitle("Voltage List")

    
    window.volt_list_widget = QListWidget()
    layout.addWidget(window.volt_list_widget, 0, 0, 4 ,1 )
    window.volt_list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
    QListWidgetItem("1",window.volt_list_widget)

    add_volt_edit = QLineEdit("1")
    layout.addWidget(add_volt_edit, 0, 1)
    add_volt_edit.editingFinished.connect(
            lambda: limits(window, add_volt_edit, 20, 20, False))
    add_volt_edit.editingFinished.connect(
            lambda: limits(window, add_volt_edit, 2e6, 20))


    add_volt_button = QPushButton("Add")
    layout.addWidget(add_volt_button, 1, 1)
    add_volt_button.clicked.connect(lambda: addValuesToList(window.volt_list_widget, add_volt_edit.text()))
    
    delete_volt_button = QPushButton("Delete")
    layout.addWidget(delete_volt_button, 2, 1)
    delete_volt_button.clicked.connect(lambda: removeValuesFromList(window.volt_list_widget))

    multi_volt_button  = QPushButton("Add range")
    layout.addWidget(multi_volt_button, 3, 1)
    multi_volt_button.clicked.connect(lambda: createMultiValueWindow(window, window.volt_list_widget, 0, 20, False))



def temperatureSettingsFrame(window) -> None:
    window.temperature_settings_frame = QGroupBox()
    layout = QGridLayout(window.temperature_settings_frame)
    window.temperature_settings_frame.setFrame = True
    window.temperature_settings_frame.setTitle("Temperature List (°C)")


    window.temp_list_widget = QListWidget()
    layout.addWidget(window.temp_list_widget, 0, 0, 4 ,1 )
    window.temp_list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
    QListWidgetItem("25",window.temp_list_widget)

    add_temp_edit = QLineEdit("25")
    layout.addWidget(add_temp_edit, 0, 1)
    add_temp_edit.editingFinished.connect(
            lambda: limits(window, add_temp_edit, -40, -40, False))
    add_temp_edit.editingFinished.connect(
            lambda: limits(window, add_temp_edit, 150, -40))


    add_temp_button = QPushButton("Add")
    layout.addWidget(add_temp_button, 1, 1)
    add_temp_button.clicked.connect(lambda: addValuesToList(window.temp_list_widget, add_temp_edit.text()))
    
    delete_temp_button = QPushButton("Delete")
    layout.addWidget(delete_temp_button, 2, 1)
    delete_temp_button.clicked.connect(lambda: removeValuesFromList(window.temp_list_widget))

    multi_temp_button  = QPushButton("Add range")
    layout.addWidget(multi_temp_button, 3, 1)
    multi_temp_button.clicked.connect(lambda: createMultiValueWindow(window, window.temp_list_widget, -40, 150, False))

    # layout.addWidget(QLabel("Start Temp."), 0, 0)
    # window.temp_start = QLineEdit("25")
    # layout.addWidget(window.temp_start, 1, 0)

    # layout.addWidget(QLabel("End Temp."), 2, 0)
    # window.temp_end = QLineEdit("30")
    # layout.addWidget(window.temp_end, 3, 0)

    # layout.addWidget(QLabel("Temp Step."), 4, 0)
    # window.temp_step = QLineEdit("1")
    # layout.addWidget(window.temp_step, 5, 0)
    layout.addWidget(QLabel("Rate."), 4, 0)
    window.temp_rate = QLineEdit("10")
    layout.addWidget(window.temp_rate, 4, 1)

    layout.addWidget(QLabel("Stab. Time (s)"), 5, 0)
    window.stab_time = QLineEdit("1")
    layout.addWidget(window.stab_time, 5, 1)


def outputDataSettingsFrame(window) -> None:
    window.output_settings_frame = QGroupBox()
    layout = QGridLayout(window.output_settings_frame)
    window.output_settings_frame.setFrame = True
    window.output_settings_frame.setTitle("Output Data Settings")

    window.output_file_input = QLineEdit("results.json")
    layout.addWidget(window.output_file_input, 0, 0)

    window.add_file_button = QPushButton("Browse")
    layout.addWidget(window.add_file_button, 0, 1)
    window.add_file_button.clicked.connect(lambda: add_file_dialogue(window))


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
