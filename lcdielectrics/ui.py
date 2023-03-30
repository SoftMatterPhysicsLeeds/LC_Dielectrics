import numpy as np
import pyvisa
from qtpy.QtWidgets import (QAbstractItemView, QComboBox, QFrame, QGridLayout,
                            QGroupBox, QLabel, QLineEdit, QListWidget,
                            QListWidgetItem, QPushButton, QWidget)

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


def set_button_style(
    button: QPushButton, bg_colour: str, fixed_width: bool = False
) -> None:
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
            "
        + "background-color:"
        + bg_colour
        + "; \
            } \
            QPushButton:hover { \
                background-color: black;\
                color: white;\
            }\
         "
    )


def generate_ui():
    layout = QGridLayout()
    widgets = {}
    # initialise frames
    (
        status_frame,
        measurement_status_label,
    ) = statusFrame()

    (
        instrument_settings_frame,
        com_selector,
        usb_selector,
        init_linkam_button,
        init_agilent_button,
        linkam_status_label,
        agilent_status_label,
    ) = instrumentSettingsFrame()

    (
        measurement_settings_frame,
        time_selector,
        averaging_factor,
        bias_voltage_selector,
    ) = measurementSettingsFrame()

    freq_settings_frame, freq_list_widget = frequencySettingsFrame()
    voltage_settings_frame, volt_list_widget = voltageSettingsFrame()
    (
        temperature_settings_frame,
        go_to_temp_button,
        go_to_temp,
        temp_rate,
        stab_time,
        temp_list_widget,
    ) = temperatureSettingsFrame()

    (
        output_settings_frame,
        output_file_input,
        add_file_button,
    ) = outputDataSettingsFrame()

    layout.addWidget(status_frame, 0, 0, 1, 2)
    layout.addWidget(instrument_settings_frame, 1, 0, 1, 2)
    layout.addWidget(measurement_settings_frame, 2, 0, 1, 2)
    layout.addWidget(freq_settings_frame, 3, 0)
    layout.addWidget(voltage_settings_frame, 3, 1)
    layout.addWidget(temperature_settings_frame, 4, 0, 1, 2)
    layout.addWidget(output_settings_frame, 5, 0, 1, 2)

    go_button = QPushButton("Start")
    layout.addWidget(go_button, 6, 0, 1, 1)
    set_button_style(go_button, "green")

    stop_button = QPushButton("Stop")
    layout.addWidget(stop_button, 6, 1, 1, 1)
    set_button_style(stop_button, "red")

    widgets.update(
        {
            "measurement_status_label": measurement_status_label,
            "linkam_status_label"     : linkam_status_label,
            "agilent_status_label"    : agilent_status_label,
            "com_selector"            : com_selector,
            "usb_selector"            : usb_selector,
            "init_linkam_button"      : init_linkam_button,
            "init_agilent_button"     : init_agilent_button,
            "time_selector"           : time_selector,
            "averaging_factor"        : averaging_factor,
            "bias_voltage_selector"   : bias_voltage_selector,
            "go_to_temp_button"       : go_to_temp_button,
            "go_to_temp"              : go_to_temp,
            "temp_rate"               : temp_rate,
            "stab_time"               : stab_time,
            "output_file_input"       : output_file_input,
            "add_file_button"         : add_file_button,
            "go_button"               : go_button,
            "stop_button"             : stop_button,
            "freq_list_widget"        : freq_list_widget,
            "volt_list_widget"        : volt_list_widget,
            "temp_list_widget"        : temp_list_widget,
        }
    )

    return layout, widgets


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


def statusFrame() -> tuple[QFrame, QLabel]:
    status_frame = QFrame()
    layout = QGridLayout(status_frame)
    status_frame.setFrameStyle(QFrame.Box)

    style = """ QLabel { 
        font-size: 20pt;
     }"""

    measurement_status = QLabel("Measurement Status: ")
    measurement_status.setStyleSheet(style)
    layout.addWidget(measurement_status, 0, 0)
    measurement_status_label = QLabel("Idle")
    measurement_status_label.setStyleSheet(style)
    layout.addWidget(measurement_status_label, 0, 1)

    return (
        status_frame,
        measurement_status_label,
    )


def instrumentSettingsFrame() -> tuple[
    QFrame, QComboBox, QComboBox, QPushButton, QPushButton, QLabel, QLabel
]:
    instrument_settings_frame = QFrame()
    layout = QGridLayout(instrument_settings_frame)
    instrument_settings_frame.setFrameStyle(QFrame.Box)

    layout.addWidget(QLabel("Linkam Status: "), 0, 0)
    linkam_status_label = QLabel("Not Connected")
    layout.addWidget(linkam_status_label, 0, 1)
    com_selector = QComboBox()
    layout.addWidget(com_selector, 0, 2)

    layout.addWidget(QLabel("Agilent Status: "), 1, 0)
    usb_selector = QComboBox()
    agilent_status_label = QLabel("Not Connected")
    layout.addWidget(agilent_status_label, 1, 1)
    layout.addWidget(usb_selector, 1, 2)

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
    layout.addWidget(init_linkam_button, 0, 3)

    init_agilent_button = QPushButton("Initialise")
    layout.addWidget(init_agilent_button, 1, 3)

    return (
        instrument_settings_frame,
        com_selector,
        usb_selector,
        init_linkam_button,
        init_agilent_button,
        linkam_status_label,
        agilent_status_label,
    )


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
    QGroupBox, QPushButton, QLineEdit, QLineEdit, QLineEdit, QListWidget
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
        temp_list_widget,
    )


def outputDataSettingsFrame() -> tuple[QGroupBox, QLineEdit, QPushButton]:
    output_settings_frame = QGroupBox()
    layout = QGridLayout(output_settings_frame)
    output_settings_frame.setFrame = True  # type: ignore
    output_settings_frame.setTitle("Output Data Settings")

    output_file_input = QLineEdit("results.json")
    layout.addWidget(output_file_input, 0, 0)

    add_file_button = QPushButton("Browse")
    layout.addWidget(add_file_button, 0, 1)

    return (output_settings_frame, output_file_input, add_file_button)


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
