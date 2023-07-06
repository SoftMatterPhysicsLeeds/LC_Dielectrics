import dearpygui.dearpygui as dpg
from lcdielectrics.lcd_ui import lcd_ui
import pyvisa
import time

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

def run_experiment(frontend: lcd_ui):
    frontend.result = dict()
    frontend.result["CPD"] = frontend.agilent.measure("CPD")
    time.sleep(0.5)
    frontend.result["GB"] = frontend.agilent.measure("GB")
    time.sleep(0.5)
