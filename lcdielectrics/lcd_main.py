from lcdielectrics.lcd_utils import (
    find_instruments,
    lcd_instruments,
    lcd_state,
    read_temperature,
    handle_measurement_status,
)
from lcdielectrics.lcd_themes import generate_global_theme
import dearpygui.dearpygui as dpg
from lcdielectrics.lcd_ui import lcd_ui, VIEWPORT_WIDTH, DRAW_HEIGHT
import threading
from pathlib import Path
import importlib
import ctypes


def main():
    dpg.create_context()
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
