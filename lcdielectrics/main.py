import dearpygui.dearpygui as dpg
from lcdielectrics.dpg_ui import lcd_ui
from serial.tools import list_ports

def main():
    dpg.create_context()
    dpg.create_viewport(
        title = "LC Dielectrics",
    
    )
    dpg.setup_dearpygui()
    dpg.show_viewport()

    frontend = lcd_ui()

    com_selector = [x.__str__() for x  in list_ports.comports()]


     # get all visa resources:
    # rm = pyvisa.ResourceManager()
    # resource_list = rm.list_resources()
    # com_selector = []
    # usb_selector = []

    # for resource in resource_list:
    #     if resource.split("::")[0][0:4] == "ASRL":
    #         com_selector.append(resource)
    #     elif resource.split("::")[0][0:3] == "USB":
    #         usb_selector.append(resource)
    #     else:
    #         print(f"Unknown resource: {resource} ")
    
    dpg.configure_item(frontend.linkam_com_selector, items = com_selector)
    # dpg.configure_item(frontend.agilent_com_selector, items = usb_selector)
    dpg.show_item_registry()


    while dpg.is_dearpygui_running():

        dpg.render_dearpygui_frame()

    dpg.destroy_context()

if __name__ == "__main__":
    main()