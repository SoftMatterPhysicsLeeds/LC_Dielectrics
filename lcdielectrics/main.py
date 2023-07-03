import dearpygui.dearpygui as dpg
from lcdielectrics.dpg_ui import lcd_ui

def main():
    dpg.create_context()
    dpg.create_viewport(
        title = "LC Dielectrics",
    
    )
    dpg.setup_dearpygui()
    dpg.show_viewport()

    lcdui = lcd_ui()

    dpg.show_item_registry()


    while dpg.is_dearpygui_running():

        dpg.render_dearpygui_frame()

    dpg.destroy_context()

if __name__ == "__main__":
    main()