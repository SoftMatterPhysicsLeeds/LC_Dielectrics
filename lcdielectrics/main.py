from lcdielectrics.lcd_utils import (
    find_instruments,
    lcd_instruments,
    connect_to_instrument_callback,
)
from lcdielectrics.lcd_themes import generate_global_theme
import dearpygui.dearpygui as dpg
from lcdielectrics.lcd_ui import lcd_ui, VIEWPORT_HEIGHT, VIEWPORT_WIDTH, DRAW_HEIGHT
from dataclasses import dataclass, field

# from serial.tools import list_ports
import threading
import ctypes

ctypes.windll.shcore.SetProcessDpiAwareness(1)

# TODO: hook up UI to functions that actually run the experiment. State class perhaps?
FONT_SCALE = 1


@dataclass
class lcd_state:
    results: dict = field(default_factory=dict)
    measurement_status: str = "Idle"
    t_stable_count: float = 0
    voltage_list_mode: bool = False
    linkam_connected: bool = False
    agilent_connected: bool = False


def main():
    dpg.create_context()

    with dpg.font_registry():
        font_regular = dpg.add_font("consola.ttf", 18 * FONT_SCALE)

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
        },
    )

    dpg.configure_item(
        frontend.linkam_initialise,
        callback=connect_to_instrument_callback,
        user_data={
            "instrument": "linkam",
            "frontend": frontend,
            "instruments": instruments,
        },
    )
    dpg.bind_theme(generate_global_theme())
    # dpg.show_item_registry()
    dpg.show_style_editor()
    
    # Search for instruments using a thread so GUI isn't blocked.
    thread = threading.Thread(target=find_instruments, args=(frontend,))
    thread.daemon = True
    thread.start()

    while dpg.is_dearpygui_running():
        # check if linkam is connected. If it is, start thread to poll temperature.

        dpg.render_dearpygui_frame()

    dpg.destroy_context()


if __name__ == "__main__":
    main()
