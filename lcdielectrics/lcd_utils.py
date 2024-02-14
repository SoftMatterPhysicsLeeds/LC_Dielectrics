import dearpygui.dearpygui as dpg
from lcdielectrics.lcd_ui import lcd_ui
from lcdielectrics.lcd_excel_writer import make_excel
from lcdielectrics.lcd_dataclasses import lcd_instruments, lcd_state, Status, OutputType
from lcdielectrics.lcd_instruments import AgilentSpectrometer, LinkamHotstage
import json
import pyvisa
import time
import threading

# TODO: find a way to handle exceptions in instrument threads?


def start_measurement(
    state: lcd_state, frontend: lcd_ui, instruments: lcd_instruments
) -> None:

    dpg.configure_item(frontend.start_button, enabled=False)
    with dpg.theme() as DEACTIVATED_THEME:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(
                dpg.mvThemeCol_Button, (100, 100, 100), category=dpg.mvThemeCat_Core
            )
    dpg.bind_item_theme(frontend.start_button, DEACTIVATED_THEME)
    state.freq_list = [
        float(x.split("\t")[-1])
        for x in dpg.get_item_configuration(frontend.freq_list.list_handle)["items"]
    ]
    state.voltage_list = [
        float(x.split("\t")[-1])
        for x in dpg.get_item_configuration(frontend.volt_list.list_handle)["items"]
    ]
    state.T_list = [
        float(x.split("\t")[-1])
        for x in dpg.get_item_configuration(frontend.temperature_list.list_handle)[
            "items"
        ]
    ]

    state.T_list = [round(x, 0) for x in state.T_list]

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

    T_str =f"{state.T_step + 1}: {state.T_list[state.T_step]}"
    freq_str = f"{state.freq_step+1}: {freq}"

    state.resultsDict[T_str] = dict()
    state.resultsDict[T_str][freq_str] = dict()
    state.resultsDict[T_str][freq_str]["volt"] = []
    state.resultsDict[T_str][freq_str]["Cp"] = []
    state.resultsDict[T_str][freq_str]["D"] = []
    state.resultsDict[T_str][freq_str]["G"] = []
    state.resultsDict[T_str][freq_str]["B"] = []

    state.measurement_status = Status.SET_TEMPERATURE
    state.xdata = []
    state.ydata = []


def stop_measurement(instruments: lcd_instruments, state: lcd_state) -> None:
    instruments.linkam.stop()
    instruments.agilent.reset_and_clear()
    state.measurement_status = Status.IDLE


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


def handle_measurement_status(
    state: lcd_state, frontend: lcd_ui, instruments: lcd_instruments
):
    current_wait = 0
    if state.measurement_status == Status.IDLE:
        dpg.set_value(frontend.measurement_status, "Idle")
        dpg.configure_item(frontend.start_button, enabled=True)

        with dpg.theme() as START_THEME:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(
                    dpg.mvThemeCol_Button, (0, 100, 0), category=dpg.mvThemeCat_Core
                )
        dpg.bind_item_theme(frontend.start_button, START_THEME)
    elif state.measurement_status == Status.SET_TEMPERATURE and (
        state.linkam_action == "Stopped" or state.linkam_action == "Holding"
    ):
        instruments.linkam.set_temperature(
            state.T_list[state.T_step], dpg.get_value(frontend.T_rate)
        )
        state.measurement_status = Status.GOING_TO_TEMPERATURE
        dpg.set_value(
            frontend.measurement_status, f"Going to {state.T_list[state.T_step]} C"
        )
    elif state.measurement_status == Status.GOING_TO_TEMPERATURE and (
        state.linkam_temperature > state.T_list[state.T_step] - 0.1
        and state.linkam_temperature < state.T_list[state.T_step] + 0.1
    ):
        state.t_stable_start = time.time()
        state.measurement_status = Status.STABILISING_TEMPERATURE

    elif state.measurement_status == Status.STABILISING_TEMPERATURE:
        current_wait = time.time() - state.t_stable_start
        dpg.set_value(
            frontend.measurement_status,
            f"Stabilising temperature for {current_wait:.2f}/{dpg.get_value(frontend.stab_time)}s",
        )
        if current_wait >= dpg.get_value(frontend.stab_time):
            state.measurement_status = Status.TEMPERATURE_STABILISED

    elif state.measurement_status == Status.TEMPERATURE_STABILISED:
        state.measurement_status = Status.COLLECTING_DATA
        instruments.agilent.set_frequency(state.freq_list[state.freq_step])
        instruments.agilent.set_voltage(state.voltage_list[state.volt_step])

        run_spectrometer(frontend, instruments, state)

    elif state.measurement_status == Status.COLLECTING_DATA:
        dpg.set_value(
            frontend.measurement_status,
            f"Measuring f = {state.freq_list[state.freq_step]}, V = {state.voltage_list[state.volt_step]}",
        )

    elif state.measurement_status == Status.FINISHED:
        instruments.linkam.stop()
        instruments.agilent.reset_and_clear()
        state.measurement_status = Status.IDLE
        dpg.set_value(frontend.measurement_status, "Idle")


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


def read_temperature(frontend: lcd_ui, instruments: lcd_instruments, state: lcd_state):
    log_time = 0
    time_step = 0.05
    while True:
        temperature, status = instruments.linkam.current_temperature()
        if temperature == 0.0:
            continue
        state.linkam_temperature = temperature
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
            frontend.temperature_log_T_axis,
            min(state.T_log_T) - 0.2,
            max(state.T_log_T) + 0.2,
        )
        dpg.fit_axis_data(frontend.temperature_log_time_axis)

        state.linkam_action = status
        time.sleep(time_step)
        log_time += time_step


def get_result(
    result: dict, state: lcd_state, frontend: lcd_ui, instruments: lcd_instruments
) -> None:
    parse_result(result, state, frontend)

    if state.measurement_status == Status.IDLE:
        pass

    else:
        if len(state.voltage_list) == 1 and len(state.freq_list) == 1:
            make_excel(
                state.resultsDict,
                dpg.get_value(frontend.output_file_path),
                OutputType.SINGLE_VOLT_FREQ,
            )
        elif len(state.voltage_list) == 1:
            make_excel(
                state.resultsDict,
                dpg.get_value(frontend.output_file_path),
                OutputType.SINGLE_VOLT,
            )
        elif len(state.freq_list) == 1:
            make_excel(
                state.resultsDict,
                dpg.get_value(frontend.output_file_path),
                OutputType.SINGLE_FREQ,
            )
        else:
            make_excel(
                state.resultsDict,
                dpg.get_value(frontend.output_file_path),
                OutputType.MULTI_VOLT_FREQ
            )

        with open(dpg.get_value(frontend.output_file_path), "w") as write_file:
            json.dump(state.resultsDict, write_file, indent=4)
        if (
            state.T_step == len(state.T_list) - 1
            and state.volt_step == len(state.voltage_list) - 1
            and state.freq_step == len(state.freq_list) - 1
        ):
            state.measurement_status = Status.FINISHED

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
                T_str =f"{state.T_step + 1}: {state.T_list[state.T_step]}"
                state.resultsDict[
                    f"{state.T_step + 1}: {state.T_list[state.T_step]}"
                ] = dict()
                freq_str = f"{state.freq_step+1}: {freq}"
                state.resultsDict[T_str] = dict()
                state.resultsDict[T_str][freq_str] = dict()
                state.resultsDict[T_str][freq_str]["volt"] = []
                state.resultsDict[T_str][freq_str]["Cp"] = []
                state.resultsDict[T_str][freq_str]["D"] = []
                state.resultsDict[T_str][freq_str]["G"] = []
                state.resultsDict[T_str][freq_str]["B"] = []

                instruments.agilent.set_voltage(0)
                state.measurement_status = Status.SET_TEMPERATURE

            elif state.volt_step == len(state.voltage_list) - 1:
                state.freq_step += 1
                state.volt_step = 0

                T = state.T_list[state.T_step]
                freq = state.freq_list[state.freq_step]

                T_str =f"{state.T_step + 1}: {state.T_list[state.T_step]}"
                freq_str = f"{state.freq_step+1}: {freq}"

                state.resultsDict[T_str][freq_str] = dict()
                state.resultsDict[T_str][freq_str]["volt"] = []
                state.resultsDict[T_str][freq_str]["Cp"] = []
                state.resultsDict[T_str][freq_str]["D"] = []
                state.resultsDict[T_str][freq_str]["G"] = []
                state.resultsDict[T_str][freq_str]["B"] = []
                state.measurement_status = Status.TEMPERATURE_STABILISED
            else:
                state.volt_step += 1
                state.measurement_status = Status.TEMPERATURE_STABILISED


def parse_result(result: dict, state: lcd_state, frontend: lcd_ui) -> None:
    T = state.T_list[state.T_step]
    freq = state.freq_list[state.freq_step]

    T_str =f"{state.T_step + 1}: {state.T_list[state.T_step]}"
    freq_str = f"{state.freq_step+1}: {freq}"

    volt = state.voltage_list[state.volt_step]
    state.resultsDict[T_str][freq_str]["volt"].append(volt)
    state.resultsDict[T_str][freq_str]["Cp"].append(result["CPD"][0])
    state.resultsDict[T_str][freq_str]["D"].append(result["CPD"][1])
    state.resultsDict[T_str][freq_str]["G"].append(result["GB"][0])
    state.resultsDict[T_str][freq_str]["B"].append(result["GB"][1])

    if len(state.voltage_list) == 1 and len(state.freq_list) == 1:
        state.xdata.append(T)
        state.ydata.append(state.resultsDict[T_str][freq_str]["Cp"])
        dpg.configure_item(frontend.results_V_axis, label="T")
    elif len(state.voltage_list) == 1:
        state.xdata.append(freq)
        state.ydata.append(state.resultsDict[T_str][freq_str]["Cp"])
        dpg.configure_item(frontend.results_V_axis, label="freq (Hz)")
    elif len(state.freq_list) == 1:
        state.xdata = state.resultsDict[T_str][freq_str]["volt"]
        state.ydata = state.resultsDict[T_str][freq_str]["Cp"]
        dpg.configure_item(frontend.results_V_axis, label="voltage (V)")

    dpg.set_value(frontend.results_plot, [state.xdata, state.ydata])
    
    if len(state.ydata) > 1 and len(state.xdata) > 1:

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
