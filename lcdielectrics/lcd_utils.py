import dearpygui.dearpygui as dpg
from lcdielectrics.lcd_ui import lcd_ui
from lcdielectrics.instruments import LinkamHotstage, AgilentSpectrometer
import pyvisa
import time
from dataclasses import dataclass, field
import threading

# TODO: find a way to handle exceptions in instrument threads?


@dataclass
class lcd_state:
    results: dict = field(default_factory=dict)
    measurement_status: str = "Idle"
    t_stable_count: float = 0
    voltage_list_mode: bool = False
    linkam_connection_status: str = "Disconnected"
    agilent_connection_status: str = "Disconnected"


@dataclass
class lcd_instruments:
    linkam: LinkamHotstage | None = None
    agilent: AgilentSpectrometer | None = None


def find_instruments(frontend: lcd_ui):
    # com_selector = [x.__str__() for x  in list_ports.comports()]

    dpg.set_value(frontend.measurement_status, "Finding Instruments...")
    rm = pyvisa.ResourceManager()
    visa_resources = rm.list_resources()

    com_selector = [x for x in visa_resources if x.split("::")[0][0:4] == "ASRL"]
    usb_selector = [x for x in visa_resources if x.split("::")[0][0:3] == "USB"]

    dpg.configure_item(frontend.linkam_com_selector, items=com_selector)
    dpg.configure_item(frontend.agilent_com_selector, items=usb_selector)

    dpg.set_value(frontend.measurement_status, "Found instruments!")
    dpg.set_value(frontend.measurement_status, "Idle")


def connect_to_instrument_callback(sender, app_data, user_data):
    print(user_data["instrument"])
    if user_data["instrument"] == "linkam":
        thread = threading.Thread(
            target=init_linkam,
            args=(user_data["frontend"], user_data["instruments"], user_data["state"]),
        )
    elif user_data["instrument"] == "agilent":
        thread = threading.Thread(
            target=init_agilent,
            args=(user_data["frontend"], user_data["instruments"], user_data["state"]),
        )

    thread.daemon = True
    thread.start()


def run_experiment(frontend: lcd_ui):
    frontend.result = dict()
    frontend.result["CPD"] = frontend.agilent.measure("CPD")
    time.sleep(0.5)
    frontend.result["GB"] = frontend.agilent.measure("GB")
    time.sleep(0.5)


def init_agilent(
    frontend: lcd_ui, instruments: lcd_instruments, state: lcd_state
) -> None:
    agilent = AgilentSpectrometer(dpg.get_value(frontend.agilent_com_selector))
    dpg.set_value(frontend.agilent_status, "Connected")
    dpg.hide_item(frontend.agilent_initialise)
    instruments.agilent = agilent
    state.agilent_connection_status = "Connected"


def init_linkam(
    frontend: lcd_ui, instruments: lcd_instruments, state: lcd_state
) -> None:
    linkam = LinkamHotstage(dpg.get_value(frontend.linkam_com_selector))
    try:
        linkam.current_temperature()
        dpg.set_value(frontend.linkam_status, "Connected")
        dpg.hide_item(frontend.linkam_initialise)
        instruments.linkam = linkam
        state.linkam_connection_status = "Connected"
        with open("address.dat", "w") as f:
            f.write(dpg.get_value(frontend.linkam_com_selector))

    except pyvisa.errors.VisaIOError:
        dpg.set_value(frontend.linkam_status, "Couldn't connect")


def read_temperature(frontend: lcd_ui, instruments: lcd_instruments):
    dpg.set_value(
        frontend.linkam_status, str(instruments.linkam.current_temperature()[0])
    )
