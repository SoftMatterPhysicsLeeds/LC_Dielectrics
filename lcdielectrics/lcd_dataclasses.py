from dataclasses import dataclass, field
from lcdielectrics.lcd_instruments import LinkamHotstage, AgilentSpectrometer
@dataclass
class range_selector_window:
    window_tag: str | int
    spacing_combo: str | int
    number_of_points_input: str | int
    spacing_input: str | int  # number of points or spacing depending on the spacing combo value
    spacing_label: str | int
    min_value_input: str | int
    max_value_input: str | int


@dataclass
class variable_list:
    list_handle: str | int
    add_text_handle: str | int
    add_button_handle: str | int
    add_range_handle: str | int
    del_button_handle: str | int
    range_selector: range_selector_window



@dataclass
class lcd_state:
    resultsDict: dict = field(default_factory=dict)
    measurement_status: str = "Idle"
    t_stable_count: float = 0
    voltage_list_mode: bool = False
    linkam_connection_status: str = "Disconnected"
    agilent_connection_status: str = "Disconnected"
    linkam_action: str = "Idle"
    T_list: list = field(default_factory=list)
    freq_list: list = field(default_factory=list)
    voltage_list: list = field(default_factory=list)
    xdata: list = field(default_factory=list)
    ydata: list = field(default_factory=list)
    T_step: int = 0
    freq_step: int = 0
    volt_step: int = 0
    T_log_time: list = field(default_factory=list)
    T_log_T: list = field(default_factory=list)


@dataclass
class lcd_instruments:
    linkam: LinkamHotstage | None = None
    agilent: AgilentSpectrometer | None = None