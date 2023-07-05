import dearpygui.dearpygui as dpg
from lcdielectrics.dpg_ui import lcd_ui
from serial.tools import list_ports
import pyvisa

def main():
    dpg.create_context()
    dpg.create_viewport(
        title = "LC Dielectrics",
    
    )
    dpg.setup_dearpygui()
    dpg.show_viewport()

    frontend = lcd_ui()

    com_selector = [x.__str__() for x  in list_ports.comports()]
    rm = pyvisa.ResourceManager()
    visa_resources = rm.list_resources()

    usb_selector = [x for x in visa_resources if x.split("::")[0][0:3] == "USB"]

    dpg.configure_item(frontend.linkam_com_selector, items = com_selector)
    dpg.configure_item(frontend.agilent_com_selector, items = usb_selector)
    dpg.show_item_registry()


    while dpg.is_dearpygui_running():

        dpg.render_dearpygui_frame()

    dpg.destroy_context()

if __name__ == "__main__":
    main()