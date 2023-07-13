from lcdielectrics.lcd_utils import (
    find_instruments,
    lcd_instruments,
    lcd_state,
    connect_to_instrument_callback,
    read_temperature,
    run_spectrometer,
    start_measurement,
    stop_measurement,
)
from lcdielectrics.lcd_themes import generate_global_theme
import dearpygui.dearpygui as dpg
from lcdielectrics.lcd_ui import lcd_ui, VIEWPORT_WIDTH, DRAW_HEIGHT


# from serial.tools import list_ports
import threading
import ctypes

#ctypes.windll.shcore.SetProcessDpiAwareness(1)

# TODO: hook up UI to functions that actually run the experiment. State class perhaps?
FONT_SCALE = 1


def main():
    dpg.create_context()

    # with dpg.font_registry():
    #     font_regular = dpg.add_font(r"lcdielectrics\font\consola.ttf", 14 * FONT_SCALE)

    # dpg.set_global_font_scale(1 / FONT_SCALE)
    # dpg.bind_font(font_regular)

    dpg.create_viewport(
        title="LC Dielectrics", width=VIEWPORT_WIDTH, height=DRAW_HEIGHT
    )
    dpg.setup_dearpygui()
    dpg.show_viewport()

    state = lcd_state()
    frontend = lcd_ui()
    instruments = lcd_instruments()

    dpg.configure_item(
        frontend.agilent_initialise,
        callback=connect_to_instrument_callback,
        user_data={
            "instrument": "agilent",
            "frontend": frontend,
            "instruments": instruments,
            "state": state,
        },
    )

    dpg.configure_item(
        frontend.linkam_initialise,
        callback=connect_to_instrument_callback,
        user_data={
            "instrument": "linkam",
            "frontend": frontend,
            "instruments": instruments,
            "state": state,
        },
    )

    dpg.configure_item(
        frontend.start_button,
        callback=lambda: start_measurement(state, frontend, instruments),
    )

    dpg.configure_item(
        frontend.stop_button, callback=lambda: stop_measurement(instruments, state)
    )

    dpg.configure_item(
        frontend.go_to_temp_button,
        callback=lambda: instruments.linkam.set_temperature(
            dpg.get_value(frontend.go_to_temp_input), dpg.get_value(frontend.T_rate)
        ),
    )

    dpg.bind_theme(generate_global_theme())
    # dpg.show_item_registry()
    # dpg.show_style_editor()

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
            state.measurement_status = (
                f"Stabilising temperature for {dpg.get_value(frontend.stab_time)}s"
            )
        elif (
            state.measurement_status
            == f"Stabilising temperature for {dpg.get_value(frontend.stab_time)}s"
        ):
            state.t_stable_count += 1

            if state.t_stable_count * 0.15 >= dpg.get_value(frontend.stab_time):
                state.measurement_status = "Temperature Stabilised"
                state.t_stable_count = 0

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
