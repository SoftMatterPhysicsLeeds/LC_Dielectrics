import dearpygui.dearpygui as dpg
from lcdielectrics.dpg_ui import lcd_ui
# from serial.tools import list_ports
import pyvisa
import threading 

def find_instruments(frontend: lcd_ui):
    # com_selector = [x.__str__() for x  in list_ports.comports()]
    
    dpg.set_value(frontend.measurement_status, "Finding Instruments...")
    rm = pyvisa.ResourceManager()
    visa_resources = rm.list_resources()

    com_selector = [x for x in visa_resources if x.split("::")[0][0:4] == "ASRL"]
    usb_selector = [x for x in visa_resources if x.split("::")[0][0:3] == "USB"]

    dpg.configure_item(frontend.linkam_com_selector, items = com_selector)
    dpg.configure_item(frontend.agilent_com_selector, items = usb_selector)

    dpg.set_value(frontend.measurement_status, "Found instruments!")
    dpg.set_value(frontend.measurement_status, "Idle")


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