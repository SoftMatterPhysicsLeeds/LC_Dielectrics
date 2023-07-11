from lcdielectrics.lcd_utils import (
    find_instruments,
    lcd_instruments,
    lcd_state,
    connect_to_instrument_callback,
    read_temperature,
)
from lcdielectrics.lcd_themes import generate_global_theme
import dearpygui.dearpygui as dpg
from lcdielectrics.lcd_ui import lcd_ui, VIEWPORT_HEIGHT, VIEWPORT_WIDTH, DRAW_HEIGHT


# from serial.tools import list_ports
import threading
import ctypes

ctypes.windll.shcore.SetProcessDpiAwareness(1)

# TODO: hook up UI to functions that actually run the experiment. State class perhaps?
FONT_SCALE = 1


def main():
    dpg.create_context()

    with dpg.font_registry():
        font_regular = dpg.add_font("consola.ttf", 16 * FONT_SCALE)

    dpg.set_global_font_scale(1 / FONT_SCALE)
    dpg.bind_font(font_regular)

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
    dpg.bind_theme(generate_global_theme())
    # dpg.show_item_registry()
    # dpg.show_style_editor()

    # Search for instruments using a thread so GUI isn't blocked.
    thread = threading.Thread(target=find_instruments, args=(frontend,))
    thread.daemon = True
    thread.start()

    linkam_thread = threading.Thread(target=read_temperature, args=(frontend, instruments))
    linkam_thread.daemon = True

    while dpg.is_dearpygui_running():
        # check if linkam is connected. If it is, start thread to poll temperature.
        if state.linkam_connection_status == "Connected":
            linkam_thread.start()
            state.linkam_connection_status = "Reading"
        dpg.render_dearpygui_frame()

    dpg.destroy_context()


if __name__ == "__main__":
    main()
