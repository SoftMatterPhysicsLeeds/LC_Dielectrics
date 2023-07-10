from lcdielectrics.lcd_utils import find_instruments
import dearpygui.dearpygui as dpg
from lcdielectrics.lcd_ui import lcd_ui, VIEWPORT_HEIGHT, VIEWPORT_WIDTH, DRAW_HEIGHT
# from serial.tools import list_ports
import threading 
import ctypes
ctypes.windll.shcore.SetProcessDpiAwareness(2)

#TODO: hook up UI to functions that actually run the experiment. State class perhaps? 
FONT_SCALE = 1


def main():
    dpg.create_context()

    with dpg.font_registry():
        font_regular = dpg.add_font('consola.ttf', 14*FONT_SCALE)
    
    dpg.set_global_font_scale(1/FONT_SCALE)    
    dpg.bind_font(font_regular)



    dpg.create_viewport(
        title = "LC Dielectrics",
        width = VIEWPORT_WIDTH,
        height= DRAW_HEIGHT
    
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