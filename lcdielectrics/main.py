import dearpygui.dearpygui as dpg
from lcdielectrics.lcd_ui import lcd_ui
# from serial.tools import list_ports
import threading 

from lcdielectrics.lcd_utils import find_instruments


def main():
    dpg.create_context()
    dpg.create_viewport(
        title = "LC Dielectrics",
    
    )
    dpg.setup_dearpygui()
    dpg.show_viewport()

    frontend = lcd_ui()


    #dpg.show_item_registry()

    # Search for instruments using a thread so GUI isn't blocked.
    thread = threading.Thread(target=find_instruments, args = (frontend,))
    thread.daemon = True
    thread.start()


    while dpg.is_dearpygui_running():

        dpg.render_dearpygui_frame()

    dpg.destroy_context()

if __name__ == "__main__":
    main()