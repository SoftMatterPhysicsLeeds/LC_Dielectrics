from lcdielectrics.lcd_utils import (
    find_instruments,
    lcd_instruments,
    lcd_state,
    read_temperature,
    run_spectrometer,
)
from lcdielectrics.lcd_themes import generate_global_theme
import dearpygui.dearpygui as dpg
from lcdielectrics.lcd_ui import lcd_ui, VIEWPORT_WIDTH, DRAW_HEIGHT
from lcdielectrics.lcd_dataclasses import Status
import threading
import time


def main():
    dpg.create_context()

    dpg.create_viewport(
        title="LC Dielectrics", width=VIEWPORT_WIDTH, height=DRAW_HEIGHT
    )
    dpg.setup_dearpygui()
    dpg.show_viewport()

    state = lcd_state()
    frontend = lcd_ui()
    instruments = lcd_instruments()

    frontend.extra_config(instruments, state)

    dpg.bind_theme(generate_global_theme())

    # Search for instruments using a thread so GUI isn't blocked.
    thread = threading.Thread(target=find_instruments, args=(frontend,))
    thread.daemon = True
    thread.start()

    linkam_thread = threading.Thread(
        target=read_temperature, args=(frontend, instruments, state)
    )
    linkam_thread.daemon = True

    while dpg.is_dearpygui_running():
        # check if linkam is connected. If it is, start thread to poll temperature.
        current_wait = 0
        if state.linkam_connection_status == "Connected":
            linkam_thread.start()
            state.linkam_connection_status = "Reading"

        if state.measurement_status == Status.IDLE or Status.COLLECTING_DATA:
            pass
        elif state.measurement_status == Status.SET_TEMPERATURE and (
            state.linkam_action == "Stopped" or state.linkam_action == "Holding"
        ):
            instruments.linkam.set_temperature(
                state.T_list[state.T_step], dpg.get_value(frontend.T_rate)
            )
            state.measurement_status = Status.GOING_TO_TEMPERATURE
            state.measurement_status = f"Going to T: {state.T_list[state.T_step]}"

        elif (
            state.measurement_status == Status.GOING_TO_TEMPERATURE
            and state.linkam_action == "Holding"
        ):
            state.t_stable_start = time.time()
            state.measurement_status = Status.STABILISING_TEMPERATURE

        elif Status.STABILISING_TEMPERATURE:
            current_wait = time.time() - state.t_stable_start
            dpg.set_value(
                frontend.measurement_status,
                f"Waiting for {current_wait}/{dpg.get_value(frontend.stab_time)}s",
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


        dpg.render_dearpygui_frame()

    dpg.destroy_context()

    if instruments.linkam:
        instruments.linkam.stop()
        instruments.linkam.close()
    if instruments.agilent:
        instruments.agilent.reset_and_clear()
        instruments.agilent.close()


if __name__ == "__main__":
    main()
