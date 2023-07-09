import dearpygui.dearpygui as dpg
from dataclasses import dataclass

@dataclass
class variable_list:
    list_handle: str | int
    add_text_handle: str | int
    add_button_handle: str | int
    add_range_handle: str | int
    del_button_handle: str | int


class lcd_ui:
    def __init__(self):
        self.status = "Idle"
        self.linkam_status = "Not Connected"
        self.agilent_status = "Not Connected"
        self._make_control_window()

    def _make_control_window(self):
        with dpg.window(
            label="Status",
            pos=[0, 0],
            width=600,
            no_resize=True,
            no_collapse=True,
            no_close=True,
            no_move=True,
        ) as self.control_window:
            with dpg.group(tag="status_window"):
                self.measurement_status = dpg.add_text(
                    f"{self.status}", tag="status_display"
                )

                with dpg.group(horizontal=True):
                    self.linkam_status = dpg.add_text(
                        f"Linkam: {self.linkam_status}", tag="linkam_status_display"
                    )

                    
                
                    self.linkam_com_selector = dpg.add_combo(width=200
                    )
                    self.linkam_initialise = dpg.add_button(label="Initialise")

                with dpg.group(horizontal=True):

                    self.agilent_status = dpg.add_text(
                        f"Agilent: {self.agilent_status}", tag="agilent_status_display"
                    )
                
                    self.agilent_com_selector = dpg.add_combo(width=200)
                    self.agilent_initialise = dpg.add_button(label="Initialise")

                


            with dpg.window(
                label="Measurement Settings",
                pos=[0, 100],
                width=600,
                no_resize=True,
                no_collapse=True,
                no_close=True,
                no_move=True,
            ):
                with dpg.group(horizontal=True):
                    dpg.add_text("Delay time (s): ")
                    self.delay_time = dpg.add_input_double(default_value=0.5, width=100)
                    dpg.add_text("Meas. Time Mode: ")
                    self.meas_time_mode_selector = dpg.add_combo(
                        ["SHOR", "MED", "LONG"], width=100
                    )

                with dpg.group(horizontal=True):
                    dpg.add_text("Averaging Factor: ")
                    self.averaging_factor = dpg.add_input_int(
                        default_value=1, width=100
                    )
                    dpg.add_text("Bias Level (V)")
                    self.bias_level = dpg.add_combo([0, 1.5, 2], width=100)

            with dpg.window(
                label="Frequency List",
                width=300,
                pos=[0, 200],
                no_resize=True,
                no_collapse=True,
                no_close=True,
                no_move=True,
            ):
                self.freq_list = variable_list(*make_variable_list_frame(20.0))

            with dpg.window(
                label="Voltage List",
                width=300,
                pos=[300, 200],
                no_resize=True,
                no_collapse=True,
                no_close=True,
                no_move=True,
            ):
                self.volt_list = variable_list(*make_variable_list_frame(1.0))

            with dpg.window(
                label="Temperature List",
                width=600,
                pos=[0, 323],
                no_resize=True,
                no_collapse=True,
                no_close=True,
                no_move=True,
            ):
                with dpg.group(horizontal=True):
                    self.temperature_list = variable_list(
                        *make_variable_list_frame(25.0)
                    )
                    with dpg.group():
                        with dpg.group(horizontal=True):
                            self.go_to_temp_button = dpg.add_button(label="Go to:")
                            self.go_to_temp_input = dpg.add_input_float(
                                default_value=25
                            )
                            dpg.add_text("°C")
                        with dpg.group(horizontal=True):
                            dpg.add_text("Rate (°C/min): ")
                            dpg.add_input_double(default_value=10)
                        with dpg.group(horizontal=True):
                            dpg.add_text("Stab. Time (s)")
                            dpg.add_input_double(default_value=1)

            with dpg.window(
                label="Output Data Settings",
                pos=[0, 446],
                width=600,
                no_resize=True,
                no_collapse=True,
                no_close=True,
                no_move=True,
            ):
                with dpg.group(horizontal=True):
                    self.output_file_path = dpg.add_input_text(
                        default_value="results.json"
                    )
                    self.browse_button = dpg.add_button(
                        label="Browse", callback=lambda: dpg.show_item("file_dialog_id")
                    )

            with dpg.file_dialog(
                directory_selector=False,
                show=False,
                callback=file_saveas_callback,
                user_data=self.output_file_path,
                id="file_dialog_id",
                width=700,
                height=400,
            ):
                dpg.add_file_extension(".json")

            with dpg.window(pos = [0, 546], no_title_bar= True, width = 600):
                with dpg.group(horizontal=True):
                    self.start_button = dpg.add_button(label = "Start", pos = [10, 0],  width = 285, height = 50)
                    self.stop_button = dpg.add_button(label = "Stop", pos = [305, 0] , width = 285, height = 50 )


def file_saveas_callback(sender, app_data, output_file_path):
    dpg.set_value(output_file_path, app_data["file_path_name"])


def add_value_to_list_callback(sender, app_data, user_data):
    current_list = dpg.get_item_configuration(user_data["listbox_handle"])["items"]
    if len(current_list) == 0:
        new_item_number = 1
    else:
        new_item_number = int(current_list[-1].split(":")[0]) + 1
    current_list.append(
        f"{new_item_number}:\t" + str(dpg.get_value(user_data["add_text"]))
    )
    dpg.configure_item(user_data["listbox_handle"], items=current_list)


def del_value_from_list_callback(sender, app_data, user_data):
    current_list = dpg.get_item_configuration(user_data["listbox_handle"])["items"]
    if len(current_list) == 0:
        return
    selected_item = dpg.get_value(user_data["listbox_handle"])
    current_list.remove(selected_item)
    new_list = [f"{i+1}:{x.split(':')[1]}" for i, x in enumerate(current_list)]
    dpg.configure_item(user_data["listbox_handle"], items=new_list)


def make_variable_list_frame(default_val):
    with dpg.group(horizontal=True):
        listbox_handle = dpg.add_listbox(["1:\t" + str(default_val)], width=150)
        with dpg.group():
            add_text = dpg.add_input_float(default_value=default_val, width=100)
            add_button = dpg.add_button(
                label="Add",
                callback=add_value_to_list_callback,
                user_data={"listbox_handle": listbox_handle, "add_text": add_text},
            )
            add_range_button = dpg.add_button(label="Add Range")
            delete_button = dpg.add_button(
                label="Delete",
                callback=del_value_from_list_callback,
                user_data={"listbox_handle": listbox_handle, "add_text": add_text},
            )

    return listbox_handle, add_text, add_button, add_range_button, delete_button
