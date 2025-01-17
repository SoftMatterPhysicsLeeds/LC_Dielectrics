from PySide6.QtWidgets import (
    QMainWindow,
    QGridLayout,
    QLabel,
    QWidget,
    QPushButton,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QGroupBox,
    QListWidget,
    QDialog,
    QVBoxLayout,
    QDialogButtonBox,
    QSplitter,  # Add QSplitter import
)
from PySide6.QtCore import Qt, QSettings  # Add QSettings import

import pyqtgraph as pg


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LC Dielectrics")
        self.setGeometry(100, 100, 1280, 850)
        self.settings = QSettings("SMPLeeds", "LC_Dielectrics")  # Initialize QSettings
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()

        central_widget.setStyleSheet("QSplitter::handle { background-color: #d3d3d3;};")

        self.setCentralWidget(central_widget)

        layout = QGridLayout(central_widget)

        self.splitter = QSplitter()  # Create a QSplitter
        self.splitter.setHandleWidth(5)  # Set the handle width to make it more visible
        layout.addWidget(self.splitter)

        left_widget = QWidget()
        left_layout = QGridLayout(left_widget)
        self.splitter.addWidget(left_widget)

        right_widget = QWidget()
        right_layout = QGridLayout(right_widget)
        self.splitter.addWidget(right_widget)

        self.status_window = StatusWindow()
        left_layout.addWidget(self.status_window, 0, 0, 1, 2)

        self.measurement_settings_window = MeasurementSettings()
        left_layout.addWidget(self.measurement_settings_window, 1, 0, 1, 2)

        self.frequency_list_window = ValueListWidget("Frequency", 20, 2e6)
        left_layout.addWidget(self.frequency_list_window, 2, 0)

        self.voltage_list_window = ValueListWidget("Voltage", 0, 20)
        left_layout.addWidget(self.voltage_list_window, 2, 1)

        self.temperature_list_window = ValueListWidget("Temperature", -150, 300)
        left_layout.addWidget(self.temperature_list_window, 3, 0, 1, 2)

        self.start_stop_buttons = StartStopButtons()
        left_layout.addWidget(self.start_stop_buttons, 4, 0, 1, 2)

        self.right_splitter = QSplitter()  # Create another QSplitter for the right layout
        self.right_splitter.setOrientation(Qt.Vertical)  # Set orientation to vertical
        self.right_splitter.setHandleWidth(5)  # Set the handle width to make it more visible
        right_layout.addWidget(self.right_splitter)

        self.results_window = ResultsWindow()
        self.right_splitter.addWidget(self.results_window)

        self.results_window2 = ResultsWindow()
        self.right_splitter.addWidget(self.results_window2)

        self.splitter.setStretchFactor(0, 1)  # Set stretch factor for left widget
        self.splitter.setStretchFactor(1, 3)  # Set stretch factor for right widget

        self.right_splitter.setStretchFactor(0, 1)  # Set stretch factor for first results window
        self.right_splitter.setStretchFactor(1, 1)  # Set stretch factor for second results window

        self.restore_splitter_sizes()  # Restore splitter sizes

    def closeEvent(self, event):
        self.save_splitter_sizes()  # Save splitter sizes on close
        super().closeEvent(event)

    def save_splitter_sizes(self):
        self.settings.setValue("main_splitter_sizes", self.splitter.saveState())
        self.settings.setValue("right_splitter_sizes", self.right_splitter.saveState())

    def restore_splitter_sizes(self):
        main_splitter_sizes = self.settings.value("main_splitter_sizes")
        if main_splitter_sizes:
            self.splitter.restoreState(main_splitter_sizes)
        right_splitter_sizes = self.settings.value("right_splitter_sizes")
        if right_splitter_sizes:
            self.right_splitter.restoreState(right_splitter_sizes)


class ResultsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.layout: QGridLayout = QGridLayout()
        self.setLayout(self.layout)

        group_box = QGroupBox()
        group_layout = QGridLayout()
        group_box.setLayout(group_layout)

        self.plot_widget = pg.PlotWidget()
        group_layout.addWidget(self.plot_widget)

        self.x = [1, 2, 3, 4, 5]
        self.y = [1, 2, 3, 4, 5]

        self.plot_widget.plot(self.x, self.y, pen="b")
        self.plot_widget.setLabel("left", "Value", units="V")
        self.plot_widget.setLabel("bottom", "Time", units="s")
        self.plot_widget.showGrid(x=True, y=True)

        self.layout.addWidget(group_box)


class StatusWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.layout: QGridLayout = QGridLayout()
        self.setLayout(self.layout)

        group_box = QGroupBox()
        group_layout = QGridLayout()
        group_box.setLayout(group_layout)

        group_layout.addWidget(QLabel("Status: "), 0, 0)

        # Add status label; we'll update this to reflect the current status
        self.status_label = QLabel("Idle")
        group_layout.addWidget(self.status_label, 0, 1)

        group_layout.addWidget(QLabel("Linkam: "), 1, 0)
        self.linkam_status_label = QLabel("Not Connected")
        group_layout.addWidget(self.linkam_status_label, 1, 1)
        self.linkam_init_button = QPushButton("Initialise")
        group_layout.addWidget(self.linkam_init_button, 1, 2)

        group_layout.addWidget(QLabel("Agilent: "), 2, 0)
        self.agilent_status_label = QLabel("Not Connected")
        group_layout.addWidget(self.agilent_status_label, 2, 1)
        self.agilent_init_button = QPushButton("Initialise")
        group_layout.addWidget(self.agilent_init_button, 2, 2)

        group_layout.addWidget(QLabel("Oscilloscope: "), 3, 0)
        self.oscilloscope_status_label = QLabel("Not Connected")
        group_layout.addWidget(self.oscilloscope_status_label, 3, 1)
        self.oscilloscope_init_button = QPushButton("Initialise")
        group_layout.addWidget(self.oscilloscope_init_button, 3, 2)

        self.layout.addWidget(group_box)


class MeasurementSettings(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QGridLayout()
        self.setLayout(self.layout)

        # Create a QGroupBox with title
        group_box = QGroupBox("Measurement Settings")
        group_layout = QGridLayout()
        group_box.setLayout(group_layout)

        # Add widgets to group layout instead of main layout
        group_layout.addWidget(QLabel("Delay Time (s): "), 0, 0)

        self.delay_time_selector = QDoubleSpinBox()
        self.delay_time_selector.setRange(0, 10000)
        self.delay_time_selector.setDecimals(1)
        self.delay_time_selector.setValue(0.5)
        group_layout.addWidget(self.delay_time_selector, 0, 1)

        group_layout.addWidget(QLabel("Averaging Factor: "), 1, 0)
        self.averaging_factor_selector = QSpinBox()
        self.averaging_factor_selector.setRange(1, 10000)
        self.averaging_factor_selector.setValue(1)
        group_layout.addWidget(self.averaging_factor_selector, 1, 1)

        group_layout.addWidget(QLabel("Meas. Time Mode: "), 0, 2)
        self.measure_time_mode_combo = QComboBox()
        self.measure_time_mode_combo.addItems(["SHOR", "MED", "LONG"])
        self.measure_time_mode_combo.setCurrentIndex(0)
        group_layout.addWidget(self.measure_time_mode_combo, 0, 3)

        group_layout.addWidget(QLabel("Bias Level (V): "), 1, 2)
        self.bias_level_combo = QComboBox()
        self.bias_level_combo.addItems(["0", "1.5", "2"])
        self.bias_level_combo.setCurrentIndex(0)
        group_layout.addWidget(self.bias_level_combo, 1, 3)

        # Add the group box to the main layout
        self.layout.addWidget(group_box)


class StartStopButtons(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        group_box = QGroupBox()
        group_layout = QGridLayout()
        group_box.setLayout(group_layout)

        self.start_button = QPushButton("Start")
        group_layout.addWidget(self.start_button, 0, 0)

        self.stop_button = QPushButton("Stop")
        group_layout.addWidget(self.stop_button, 0, 1)

        self.layout.addWidget(group_box)


class ValueListWidget(QWidget):
    def __init__(self, variable_name="Frequency", min_value=20, max_value=2e6):
        super().__init__()
        self.main_layout = QGridLayout()
        self.setLayout(self.main_layout)

        self.min_value = min_value
        self.max_value = max_value

        group_box = QGroupBox(variable_name + " List")
        self.layout = QGridLayout()
        group_box.setLayout(self.layout)

        self.setup_ui()
        self.setup_connections()

        self.main_layout.addWidget(group_box)

    def setup_ui(self):
        self.value_list = QListWidget()
        self.value_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.layout.addWidget(self.value_list, 0, 0, 4, 1)

        self.value_spinner = QDoubleSpinBox()
        self.value_spinner.setRange(self.min_value, self.max_value)
        self.value_spinner.setDecimals(3)
        self.value_spinner.setValue(self.min_value)
        self.layout.addWidget(self.value_spinner, 0, 1)

        self.add_button = QPushButton("Add")
        self.layout.addWidget(self.add_button, 1, 1)

        self.delete_button = QPushButton("Delete")
        self.layout.addWidget(self.delete_button, 2, 1)

        self.range_button = QPushButton("Range...")
        self.layout.addWidget(self.range_button, 3, 1)

    def setup_connections(self):
        self.add_button.clicked.connect(self.add_value)
        self.delete_button.clicked.connect(self.delete_selected)
        self.range_button.clicked.connect(self.show_range_dialog)

    def add_value(self):
        value = self.value_spinner.value()
        next_index = self.value_list.count() + 1
        self.value_list.addItem(f"{next_index}: {value}")

    def delete_selected(self):
        # Get all selected items
        selected_items = self.value_list.selectedItems()

        # Remove the selected items
        for item in selected_items:
            self.value_list.takeItem(self.value_list.row(item))

        # Renumber remaining items
        self.renumber_items()

    def renumber_items(self):
        # Go through all items and renumber them
        for i in range(self.value_list.count()):
            item = self.value_list.item(i)
            # Get the value part after the colon
            old_text = item.text()
            value = old_text.split(": ")[1]
            # Set new numbered text
            item.setText(f"{i + 1}: {value}")

    def get_values(self):
        """Returns a list of just the values without the numbering"""
        values = []
        for i in range(self.value_list.count()):
            item = self.value_list.item(i)
            value = float(item.text().split(": ")[1])
            values.append(value)
        return values

    def show_range_dialog(self):
        dialog = RangeDialog(self)
        if dialog.exec() == QDialog.Accepted:
            min_val, max_val, step = dialog.get_values()
            current = min_val
            while current <= max_val:
                next_index = self.value_list.count() + 1
                self.value_list.addItem(f"{next_index}: {current}")
                current += step


class RangeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Range")
        self.setup_ui(parent)

    def setup_ui(self, parent):
        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("Minimum:"))
        self.min_spinner = QDoubleSpinBox()
        self.min_spinner.setRange(parent.min_value, parent.max_value)
        self.min_spinner.setDecimals(3)
        self.min_spinner.setValue(parent.min_value)
        layout.addWidget(self.min_spinner)

        layout.addWidget(QLabel("Maximum:"))
        self.max_spinner = QDoubleSpinBox()
        self.max_spinner.setRange(parent.min_value, parent.max_value)
        self.max_spinner.setDecimals(3)
        self.max_spinner.setValue(parent.max_value)
        layout.addWidget(self.max_spinner)

        layout.addWidget(QLabel("Step:"))
        self.step_spinner = QDoubleSpinBox()
        self.step_spinner.setRange(parent.min_value, parent.max_value)
        self.step_spinner.setDecimals(3)
        self.step_spinner.setValue(1.0)
        layout.addWidget(self.step_spinner)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_values(self):
        return (
            self.min_spinner.value(),
            self.max_spinner.value(),
            self.step_spinner.value(),
        )
