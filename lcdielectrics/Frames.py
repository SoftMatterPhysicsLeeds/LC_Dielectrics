import numpy as np
import pyvisa
from qtpy.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QWidget,
)

## TODO: Need docs everywhere
## TODO: User could easily bypass maximum number of points -
#       need to check length of listboxes after population


class ValueSelectorWindow(QWidget):
    """
    Popout window that will allow the user to select a range of
    frequencies/voltages /temperatures to add to the relevant list.
    """

    def __init__(
        self,
        value_list: QListWidget,
        start_val: float,
        end_val: float,
        logspace: bool = True,
    ):
        super().__init__()
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
        self.points.editingFinished.connect(lambda: limits(self.points, 201, 10))

        layout.addWidget(QLabel("Start"), 2, 0, 1, 2)
        self.start = QLineEdit(f"{start_val}")
        layout.addWidget(self.start, 3, 0, 1, 2)
        self.start.editingFinished.connect(
            lambda: limits(self.start, start_val, start_val, False)
        )
        self.start.editingFinished.connect(
            lambda: limits(self.start, end_val, start_val)
        )

        layout.addWidget(QLabel("End"), 4, 0, 1, 2)
        self.end = QLineEdit(f"{end_val}")
        layout.addWidget(self.end, 5, 0, 1, 2)
        self.end.editingFinished.connect(
            lambda: limits(self.end, start_val, start_val, False)
        )
        self.end.editingFinished.connect(lambda: limits(self.end, end_val, start_val))

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
        start_val = float(self.start.text())
        end_val = float(self.end.text())
        points = float(self.points.text())

        if self.logspace:
            val_list = [
                f"{x:.2f}"
                for x in list(
                    np.logspace(np.log10(start_val), np.log10(end_val), int(points))
                )
            ]
        else:
            if self.combo.currentText() == "Number of Points":
                val_list = [
                    f"{x:.2f}"
                    for x in list(np.linspace(start_val, end_val, int(points)))
                ]
            else:
                if start_val <= end_val:
                    val_list = [
                        f"{x:.2f}"
                        for x in list(np.arange(start_val, end_val + points, points))
                    ]
                else:
                    val_list = [
                        f"{x:.2f}"
                        for x in list(np.arange(start_val, end_val - points, -points))
                    ]

        for val in val_list:
            addValuesToList(self.value_list, val)

        self.close()


def addValuesToList(list_widget: QListWidget, value: str) -> None:
    item = QListWidgetItem(value, list_widget)
    list_widget.setCurrentItem(item)


def removeValuesFromList(list_widget: QListWidget) -> None:
    items = list_widget.selectedItems()
    for item in items:
        list_widget.takeItem(list_widget.row(item))


def createMultiValueWindow(
    list_widget: QListWidget,
    min_val: float,
    max_val: float,
    logspace: bool = True,
) -> None:
    sw = ValueSelectorWindow(list_widget, min_val, max_val, logspace)
    sw.show()


def statusFrame() -> tuple[QFrame, QLabel, QLabel, QLabel]:
    status_frame = QFrame()
    layout = QGridLayout(status_frame)
    status_frame.setFrameStyle(QFrame.Box)

    layout.addWidget(QLabel("Measurement Status: "), 0, 0)
    measurement_status_label = QLabel("Idle")
    layout.addWidget(measurement_status_label, 0, 1)

    layout.addWidget(QLabel("Linkam Status: "), 1, 0)
    linkam_status_label = QLabel("Not Connected")
    layout.addWidget(linkam_status_label, 1, 1)

    layout.addWidget(QLabel("Agilent Status: "), 2, 0)
    agilent_status_label = QLabel("Not Connected")
    layout.addWidget(agilent_status_label, 2, 1)

    return (
        status_frame,
        measurement_status_label,
        linkam_status_label,
        agilent_status_label,
    )


def instrumentSettingsFrame() -> tuple[QFrame, QPushButton, QPushButton]:
    instrument_settings_frame = QFrame()
    layout = QGridLayout(instrument_settings_frame)
    instrument_settings_frame.setFrameStyle(QFrame.Box)

    layout.addWidget(QLabel("Linkam COM port: "), 0, 0)
    com_selector = QComboBox()

    layout.addWidget(com_selector, 0, 1)

    layout.addWidget(QLabel("Agilent USB port: "), 1, 0)
    usb_selector = QComboBox()
    layout.addWidget(usb_selector, 1, 1)

    # get all visa resources:
    rm = pyvisa.ResourceManager()
    resource_list = rm.list_resources()

    for resource in resource_list:
        if resource.split("::")[0][0:4] == "ASRL":
            com_selector.addItem(resource)
        elif resource.split("::")[0][0:3] == "USB":
            usb_selector.addItem(resource)
        else:
            print(f"Unknown resource: {resource} ")

    init_linkam_button = QPushButton("Initialise")
    layout.addWidget(init_linkam_button, 0, 2)

    init_agilent_button = QPushButton("Initialise")
    layout.addWidget(init_agilent_button, 1, 2)

    return instrument_settings_frame, init_linkam_button, init_agilent_button


def measurementSettingsFrame() -> tuple[QGroupBox, QComboBox, QLineEdit, QComboBox]:
    measurement_settings_frame = QGroupBox()
    layout = QGridLayout(measurement_settings_frame)
    measurement_settings_frame.setFrame = True  # type: ignore
    measurement_settings_frame.setTitle("Measurement Settings")

    layout.addWidget(QLabel("Meas. Time. Mode: "), 0, 0)
    time_selector = QComboBox()
    time_selector.addItem("SHOR")
    time_selector.addItem("MED")
    time_selector.addItem("LONG")
    layout.addWidget(time_selector, 0, 1)

    layout.addWidget(QLabel("Averaging Factor"), 0, 2)
    averaging_factor = QLineEdit("1")
    layout.addWidget(averaging_factor, 0, 3)
    averaging_factor.editingFinished.connect(lambda: limits(averaging_factor, 256, 1))

    layout.addWidget(QLabel("Bias Level (V)"), 0, 4)
    bias_voltage_selector = QComboBox()
    bias_voltage_selector.addItem("0")
    bias_voltage_selector.addItem("1.5")
    bias_voltage_selector.addItem("2")
    layout.addWidget(bias_voltage_selector, 0, 5)

    return (
        measurement_settings_frame,
        time_selector,
        averaging_factor,
        bias_voltage_selector,
    )


def populateVariableFrame(
    frame: QGroupBox,
    list_box: QListWidget,
    default_val: float,
    min_val: float,
    max_val: float,
    logspace: bool = True,
) -> QGridLayout:
    layout = QGridLayout(frame)

    frame.setFrame = True  # type: ignore

    list_box.setFixedWidth(150)
    layout.addWidget(list_box, 0, 0, 4, 1)
    list_box.setSelectionMode(QAbstractItemView.ExtendedSelection)
    QListWidgetItem(f"{default_val}", list_box)

    add_edit = QLineEdit(f"{default_val}")
    add_edit.setFixedWidth(100)
    layout.addWidget(add_edit, 0, 1)
    add_edit.editingFinished.connect(lambda: limits(add_edit, min_val, min_val, False))
    add_edit.editingFinished.connect(lambda: limits(add_edit, max_val, min_val))

    add_button = QPushButton("Add")
    add_button.setFixedWidth(100)
    layout.addWidget(add_button, 1, 1)
    add_button.clicked.connect(lambda: addValuesToList(list_box, add_edit.text()))

    multi_button = QPushButton("Add range")
    multi_button.setFixedWidth(100)
    layout.addWidget(multi_button, 2, 1)
    multi_button.clicked.connect(
        lambda: createMultiValueWindow(list_box, min_val, max_val, logspace)
    )

    delete_button = QPushButton("Delete")
    delete_button.setFixedWidth(100)
    layout.addWidget(delete_button, 3, 1)
    delete_button.clicked.connect(lambda: removeValuesFromList(list_box))

    return layout


def frequencySettingsFrame() -> tuple[QGroupBox, QListWidget]:
    freq_settings_frame = QGroupBox()
    freq_settings_frame.setTitle("Frequency List")
    freq_list_widget = QListWidget()

    populateVariableFrame(freq_settings_frame, freq_list_widget, 20, 20, 2e6)
    return freq_settings_frame, freq_list_widget


def voltageSettingsFrame() -> tuple[QGroupBox, QListWidget]:
    voltage_settings_frame = QGroupBox()
    voltage_settings_frame.setTitle("Voltage List")
    volt_list_widget = QListWidget()

    populateVariableFrame(voltage_settings_frame, volt_list_widget, 1, 0, 20, False)

    return voltage_settings_frame, volt_list_widget


def temperatureSettingsFrame() -> tuple[
    QGroupBox, QPushButton, QLineEdit, QLineEdit, QLineEdit
]:
    temperature_settings_frame = QGroupBox()
    temperature_settings_frame.setTitle("Temperature List (°C)")
    temp_list_widget = QListWidget()

    layout = populateVariableFrame(
        temperature_settings_frame,
        temp_list_widget,
        25,
        -40,
        350,
        False,
    )

    go_to_temp_button = QPushButton("Go to:")
    layout.addWidget(go_to_temp_button, 0, 2)

    go_to_temp = QLineEdit("25")
    layout.addWidget(go_to_temp, 0, 3)
    layout.addWidget(QLabel("°C"), 0, 4)

    layout.addWidget(QLabel("Rate (°C/min)"), 1, 2)
    temp_rate = QLineEdit("10")
    layout.addWidget(temp_rate, 1, 3)

    layout.addWidget(QLabel("Stab. Time (s)"), 2, 2)
    stab_time = QLineEdit("1")
    layout.addWidget(stab_time, 2, 3)

    return (
        temperature_settings_frame,
        go_to_temp_button,
        go_to_temp,
        temp_rate,
        stab_time,
    )


def outputDataSettingsFrame(window) -> None:
    window.output_settings_frame = QGroupBox()
    layout = QGridLayout(window.output_settings_frame)
    window.output_settings_frame.setFrame = True  # type: ignore
    window.output_settings_frame.setTitle("Output Data Settings")

    window.output_file_input = QLineEdit("results.json")
    layout.addWidget(window.output_file_input, 0, 0)

    window.add_file_button = QPushButton("Browse")
    layout.addWidget(window.add_file_button, 0, 1)
    window.add_file_button.clicked.connect(lambda: add_file_dialogue(window))


# def graphFrame(window) -> None:

#     window.graph_frame = QFrame()
#     layout = QGridLayout(window.graph_frame)

#     window.graphWidget_Cap = pg.PlotWidget()
#     layout.addWidget(window.graphWidget_Cap, 0, 0)
#     window.graphWidget_Cap.setBackground(None)
#     window.graphWidget_Cap.setLabel("left", "Capacitance", "F")
#     window.graphWidget_Cap.setLabel("bottom", "Frequency", "Hz")
#     window.graph_T = [window.current_T] * 100
#     window.graph_time = list(np.arange(0, 10, 0.1))
#     pen = pg.mkPen(color=(255, 0, 0))
#     window.data_line_cap = window.graphWidget_Cap.plot(
#         window.graph_time, window.graph_T, pen=pen
#     )

#     window.graphWidget_Dis = pg.PlotWidget()
#     layout.addWidget(window.graphWidget_Dis, 1, 0)
#     window.graphWidget_Dis.setBackground(None)
#     window.graphWidget_Dis.setLabel("left", "Dissipation", "F")
#     window.graphWidget_Dis.setLabel("bottom", "Frequency", "Hz")

#     window.data_line_dis = window.graphWidget_Dis.plot(
#         window.graph_time, window.graph_T, pen=pen
#     )

#     window.data_line_cap.setLogMode(True, False)
#     window.data_line_dis.setLogMode(True, False)


def add_file_dialogue(window) -> None:
    filename, _ = QFileDialog.getSaveFileName(
        window, "Output File", "", "JSON Files (*.json)"
    )
    window.output_file_input.setText(filename)


def limits(thing, limit: float, default: float, max_val=True) -> None:
    try:
        if thing.text() == "":
            pass
        elif (
            max_val is True
            and float(thing.text()) > limit
            or max_val is False
            and float(thing.text()) < limit
        ):
            thing.setText(f"{limit}")
    except ValueError:
        thing.setText(f"{default}")
