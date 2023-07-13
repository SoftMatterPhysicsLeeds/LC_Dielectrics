import dearpygui.dearpygui as dpg
from lcdielectrics.lcd_ui import lcd_ui
from lcdielectrics.instruments import LinkamHotstage, AgilentSpectrometer
from lcdielectrics.excel_writer import make_excel
import json
import pyvisa
import time
from dataclasses import dataclass, field
import threading

# TODO: find a way to handle exceptions in instrument threads?


@dataclass
class lcd_state:
    resultsDict: dict = field(default_factory=dict)
    measurement_status: str = "Idle"
    t_stable_count: float = 0
    voltage_list_mode: bool = False
    linkam_connection_status: str = "Disconnected"
    agilent_connection_status: str = "Disconnected"
    linkam_action: str = "Idle"
    T_list: list = field(default_factory=list)
    freq_list: list = field(default_factory=list)
    voltage_list: list = field(default_factory=list)
    xdata: list = field(default_factory=list)
    ydata: list = field(default_factory=list)
    T_step: int = 0
    freq_step: int = 0
    volt_step: int = 0
    T_log_time: list = field(default_factory=list)
    T_log_T: list = field(default_factory=list)


@dataclass
class lcd_instruments:
    linkam: LinkamHotstage | None = None
    agilent: AgilentSpectrometer | None = None


def find_instruments(frontend: lcd_ui):
    # com_selector = [x.__str__() for x  in list_ports.comports()]

    dpg.set_value(frontend.measurement_status, "Finding Instruments...")
    rm = pyvisa.ResourceManager()
    visa_resources = rm.list_resources()

    com_selector = [x for x in visa_resources if x.split("::")[0][0:4] == "ASRL"]
    usb_selector = [x for x in visa_resources if x.split("::")[0][0:3] == "USB"]

    dpg.configure_item(frontend.linkam_com_selector, items=com_selector)
    dpg.configure_item(frontend.agilent_com_selector, items=usb_selector)

    dpg.set_value(frontend.measurement_status, "Found instruments!")
    dpg.set_value(frontend.measurement_status, "Idle")


def connect_to_instrument_callback(sender, app_data, user_data):
    if user_data["instrument"] == "linkam":
        thread = threading.Thread(
            target=init_linkam,
            args=(user_data["frontend"], user_data["instruments"], user_data["state"]),
        )
    elif user_data["instrument"] == "agilent":
        thread = threading.Thread(
            target=init_agilent,
            args=(user_data["frontend"], user_data["instruments"], user_data["state"]),
        )

    thread.daemon = True
    thread.start()


def run_spectrometer(
    frontend: lcd_ui, instruments: lcd_instruments, state: lcd_state
) -> None:
    thread = threading.Thread(
        target=run_experiment, args=(frontend, instruments, state)
    )
    thread.daemon = True
    thread.start()


def run_experiment(frontend: lcd_ui, instruments: lcd_state, state: lcd_state):
    result = dict()
    time.sleep(dpg.get_value(frontend.delay_time))
    result["CPD"] = instruments.agilent.measure("CPD")
    time.sleep(0.5)
    result["GB"] = instruments.agilent.measure("GB")
    time.sleep(0.5)
    get_result(result, state, frontend, instruments)


def init_agilent(
    frontend: lcd_ui, instruments: lcd_instruments, state: lcd_state
) -> None:
    agilent = AgilentSpectrometer(dpg.get_value(frontend.agilent_com_selector))
    dpg.set_value(frontend.agilent_status, "Connected")
    dpg.hide_item(frontend.agilent_initialise)
    instruments.agilent = agilent
    state.agilent_connection_status = "Connected"


def init_linkam(
    frontend: lcd_ui, instruments: lcd_instruments, state: lcd_state
) -> None:
    linkam = LinkamHotstage(dpg.get_value(frontend.linkam_com_selector))
    try:
        linkam.current_temperature()
        dpg.set_value(frontend.linkam_status, "Connected")
        dpg.hide_item(frontend.linkam_initialise)
        instruments.linkam = linkam
        state.linkam_connection_status = "Connected"
        with open("address.dat", "w") as f:
            f.write(dpg.get_value(frontend.linkam_com_selector))

    except pyvisa.errors.VisaIOError:
        dpg.set_value(frontend.linkam_status, "Couldn't connect")


def read_temperature(frontend: lcd_ui, instruments: lcd_instruments, state: lcd_state):
    log_time = 0
    while True:
        temperature, status = instruments.linkam.current_temperature()
        if temperature == 0.0:
            continue
        dpg.set_value(
            frontend.linkam_status, f"T: {str(temperature)}, Status: {status}"
        )
        state.T_log_time.append(log_time)
        state.T_log_T.append(temperature)

        if len(state.T_log_T) == 1000:
            state.T_log_T = state.T_log_T[1:]
            state.T_log_time = state.T_log_time[1:]

        dpg.set_value(frontend.temperature_log, [state.T_log_time, state.T_log_T])

        dpg.set_axis_limits(
            frontend.temperature_log_time_axis,
            min(state.T_log_time) - 0.1 * min(state.T_log_time),
            max(state.T_log_time) + 0.1 * max(state.T_log_time),
        )
        dpg.set_axis_limits(
            frontend.temperature_log_T_axis,
            min(state.T_log_T) - 0.5,
            max(state.T_log_T) + 0.5,
        )
        # dpg.fit_axis_data(frontend.temperature_log_time_axis)
        # dpg.fit_axis_data(frontend.temperature_log_T_axis)

        state.linkam_action = status
        time.sleep(0.01)
        log_time += 0.1


def start_measurement(
    state: lcd_state, frontend: lcd_ui, instruments: lcd_instruments
) -> None:
    state.freq_list = [
        float(x.split("\t")[1])
        for x in dpg.get_item_configuration(frontend.freq_list.list_handle)["items"]
    ]
    state.voltage_list = [
        float(x.split("\t")[1])
        for x in dpg.get_item_configuration(frontend.volt_list.list_handle)["items"]
    ]
    state.T_list = [
        float(x.split("\t")[1])
        for x in dpg.get_item_configuration(frontend.temperature_list.list_handle)[
            "items"
        ]
    ]

    state.T_list = [round(x, 2) for x in state.T_list]

    instruments.agilent.set_aperture_mode(
        dpg.get_value(frontend.meas_time_mode_selector),
        dpg.get_value(frontend.averaging_factor),
    )

    bias = dpg.get_value(frontend.bias_level)
    if bias == 1.5 or 2:
        instruments.agilent.set_DC_bias(float(bias))

    state.T_step = 0
    state.freq_step = 0
    state.volt_step = 0

    T = state.T_list[state.T_step]
    freq = state.freq_list[state.freq_step]

    state.resultsDict[state.T_list[state.T_step]] = dict()
    state.resultsDict[T][freq] = dict()
    state.resultsDict[T][freq]["volt"] = []
    state.resultsDict[T][freq]["Cp"] = []
    state.resultsDict[T][freq]["D"] = []
    state.resultsDict[T][freq]["G"] = []
    state.resultsDict[T][freq]["B"] = []

    state.measurement_status = "Setting temperature"


def get_result(
    result: dict, state: lcd_state, frontend: lcd_ui, instruments: lcd_instruments
) -> None:
    parse_result(result, state, frontend)

    if state.measurement_status == "Idle":
        pass

    else:
        if len(state.voltage_list) == 1:
            make_excel(
                state.resultsDict,
                dpg.get_value(frontend.output_file_path),
                True,
            )
        else:
            make_excel(
                state.resultsDict,
                dpg.get_value(frontend.output_file_path),
                False,
            )

        with open(dpg.get_value(frontend.output_file_path), "w") as write_file:
            json.dump(state.resultsDict, write_file, indent=4)
        if (
            state.T_step == len(state.T_list) - 1
            and state.volt_step == len(state.voltage_list) - 1
            and state.freq_step == len(state.freq_list) - 1
        ):
            state.measurement_status = "Finished"

        else:
            if (
                state.volt_step == len(state.voltage_list) - 1
                and state.freq_step == len(state.freq_list) - 1
            ):
                state.T_step += 1
                state.freq_step = 0
                state.volt_step = 0

                T = state.T_list[state.T_step]
                freq = state.freq_list[state.freq_step]

                state.resultsDict[state.T_list[state.T_step]] = dict()
                state.resultsDict[T][freq] = dict()
                state.resultsDict[T][freq]["volt"] = []
                state.resultsDict[T][freq]["Cp"] = []
                state.resultsDict[T][freq]["D"] = []
                state.resultsDict[T][freq]["G"] = []
                state.resultsDict[T][freq]["B"] = []

                instruments.agilent.set_voltage(0)
                state.measurement_status = "Setting temperature"

            elif state.volt_step == len(state.voltage_list) - 1:
                state.freq_step += 1
                state.volt_step = 0

                T = state.T_list[state.T_step]
                freq = state.freq_list[state.freq_step]

                state.resultsDict[T][freq] = dict()
                state.resultsDict[T][freq]["volt"] = []
                state.resultsDict[T][freq]["Cp"] = []
                state.resultsDict[T][freq]["D"] = []
                state.resultsDict[T][freq]["G"] = []
                state.resultsDict[T][freq]["B"] = []

                state.measurement_status = "Temperature Stabilised"
            else:
                state.volt_step += 1
                state.measurement_status = "Temperature Stabilised"


def parse_result(result: dict, state: lcd_state, frontend: lcd_ui) -> None:
    T = state.T_list[state.T_step]
    freq = state.freq_list[state.freq_step]
    volt = state.voltage_list[state.volt_step]
    state.resultsDict[T][freq]["volt"].append(volt)
    state.resultsDict[T][freq]["Cp"].append(result["CPD"][0])
    state.resultsDict[T][freq]["D"].append(result["CPD"][1])
    state.resultsDict[T][freq]["G"].append(result["GB"][0])
    state.resultsDict[T][freq]["B"].append(result["GB"][1])
    state.xdata = state.resultsDict[T][freq]["volt"]
    state.ydata = state.resultsDict[T][freq]["Cp"]

    dpg.set_value(frontend.results_plot, [state.xdata, state.ydata])

    dpg.set_axis_limits(
        frontend.results_Cp_axis,
        min(state.ydata) - 0.1 * min(state.ydata),
        max(state.ydata) + 0.1 * max(state.ydata),
    )
    dpg.set_axis_limits(
        frontend.results_V_axis,
        min(state.xdata) - 0.1,
        max(state.xdata) + 0.1,
    )


    # self.update_plot()


def stop_measurement(instruments: lcd_instruments, state: lcd_state) -> None:
    instruments.linkam.stop()
    instruments.agilent.reset_and_clear()
    state.measurement_status = "Idle"


