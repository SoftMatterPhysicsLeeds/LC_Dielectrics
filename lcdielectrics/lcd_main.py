from lcdielectrics.lcd_utils import (
    find_instruments,
    lcd_instruments,
    lcd_state,
    read_temperature,
    handle_measurement_status,
    connect_to_instrument_callback, 
    start_measurement,
    stop_measurement
)
from lcdielectrics.lcd_themes import generate_global_theme
import dearpygui.dearpygui as dpg
from lcdielectrics.lcd_ui import lcd_ui, VIEWPORT_WIDTH, DRAW_HEIGHT
import threading
from pathlib import Path
import importlib
import ctypes


def find_instruments_thread(frontend: lcd_ui):
    thread = threading.Thread(target=find_instruments, args=(frontend,))
    thread.daemon = True
    thread.start()


def main():
    dpg.create_context()
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
    MODULE_PATH = importlib.resources.files(__package__)
    dpg.create_viewport(
        title="LC Dielectrics", width=VIEWPORT_WIDTH, height=DRAW_HEIGHT
    )
    
    dpg.set_viewport_large_icon(MODULE_PATH / "assets/LCD_icon.ico")
    dpg.set_viewport_small_icon(MODULE_PATH / "assets/LCD_icon.ico")
    dpg.setup_dearpygui()
    dpg.show_viewport()
    user32 = ctypes.windll.user32
    screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    
    font_path = Path(MODULE_PATH / "assets/OpenSans-Regular.ttf")
    with dpg.font_registry():
        default_font = dpg.add_font(font_path, 18 * screensize[1] / 1080)
        status_font = dpg.add_font(font_path, 36 * screensize[1] / 1080)
        

    dpg.bind_font(default_font)
    
    

    state = lcd_state()
    frontend = lcd_ui()
    instruments = lcd_instruments()

    dpg.bind_item_font(frontend.measurement_status, status_font)
    dpg.bind_item_font(frontend.status_label, status_font)
    dpg.bind_item_font(frontend.start_button, status_font)
    dpg.bind_item_font(frontend.stop_button, status_font)



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
        frontend.oscilloscope_initialise,
        callback=connect_to_instrument_callback,
        user_data={
            "instrument": "oscilloscope",
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
        frontend.stop_button,
        callback=lambda: stop_measurement(instruments, state, frontend),
    )

    dpg.configure_item(
        frontend.go_to_temp_button,
        callback=lambda: instruments.linkam.set_temperature(
            dpg.get_value(frontend.go_to_temp_input),
            dpg.get_value(frontend.T_rate),
        ),
    )

    dpg.bind_theme(generate_global_theme())

    # Search for instruments using a thread so GUI isn't blocked.
    thread = threading.Thread(target=find_instruments, args=(frontend,))
    thread.daemon = True
    thread.start()

    find_instruments_thread(frontend)

    linkam_thread = threading.Thread(
        target=read_temperature, args=(frontend, instruments, state)
    )
    linkam_thread.daemon = True
    viewport_width = dpg.get_viewport_client_width()
    viewport_height = dpg.get_viewport_client_height()
    
    while dpg.is_dearpygui_running():
        # check if linkam is connected. If it is, start thread to poll temperature.
        if (
            viewport_width != dpg.get_viewport_client_width()
            or viewport_height != dpg.get_viewport_client_height()
        ):
            # redraw_windows.
            viewport_width = dpg.get_viewport_client_width()
            viewport_height = dpg.get_viewport_client_height()
            frontend.draw_children(viewport_width, viewport_height)

        if state.linkam_connection_status == "Connected":
            linkam_thread.start()
            state.linkam_connection_status = "Reading"

        handle_measurement_status(state, frontend, instruments)

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
