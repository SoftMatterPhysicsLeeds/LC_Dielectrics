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

        if state.linkam_connection_status == "Connected":
            linkam_thread.start()
            state.linkam_connection_status = "Reading"

        if state.measurement_status == "Idle":
            pass
        elif state.measurement_status == "Setting temperature" and (
            state.linkam_action == "Stopped" or state.linkam_action == "Holding"
        ):
            instruments.linkam.set_temperature(
                state.T_list[state.T_step], dpg.get_value(frontend.T_rate)
            )

            state.measurement_status = f"Going to T: {state.T_list[state.T_step]}"

        elif (
            state.measurement_status == f"Going to T: {state.T_list[state.T_step]}"
            and state.linkam_action == "Holding"
        ):

            state.t_stable_start = time.time()
            state.measurement_status = (
                f"Stabilising temperature for {dpg.get_value(frontend.stab_time)}s"
            )
        elif (
            state.measurement_status
            == f"Stabilising temperature for {dpg.get_value(frontend.stab_time)}s"
        ):
            current_wait = time.time() - state.t_stable_start
            if current_wait >= dpg.get_value(frontend.stab_time):
                state.measurement_status = "Temperature Stabilised"


        elif state.measurement_status == "Temperature Stabilised":
            state.measurement_status = "Collecting data"
            instruments.agilent.set_frequency(state.freq_list[state.freq_step])
            instruments.agilent.set_voltage(state.voltage_list[state.volt_step])

            run_spectrometer(frontend, instruments, state)

        elif state.measurement_status == "Finished":
            instruments.linkam.stop()
            instruments.agilent.reset_and_clear()
            state.measurement_status = "Idle"

        dpg.set_value(frontend.measurement_status, state.measurement_status)

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
