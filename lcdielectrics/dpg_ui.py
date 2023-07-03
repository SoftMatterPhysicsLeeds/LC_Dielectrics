import dearpygui.dearpygui as dpg

class lcd_ui():
    def __init__(self):
        self.status = "Idle"
        self.linkam_status = "Not Connected"
        self.agilent_status = "Not Connected"
        self._make_control_window()

    def _make_control_window(self):
        with dpg.window(label = "Status", pos = [0,0], width = 600) as self.control_window: 

            with dpg.group(tag = "status_window"):
                self.measurement_status = dpg.add_text(f"{self.status}", tag = "status_display")

                with dpg.group(horizontal=True):
                    self.linkam_status = dpg.add_text(f"Linkam: {self.linkam_status}", tag = "linkam_status_display")
                    self.linkam_com_selector = dpg.add_combo(items = ["COM1", "COM2", "COM3"], width = 200)
                    self.linkam_initialise = dpg.add_button(label = "Initialise")
                
                with dpg.group(horizontal=True):
                    self.agilent_status = dpg.add_text(f"Agilent: {self.agilent_status}", tag = "agilent_status_display")
                    self.agilent_com_selector = dpg.add_combo(items = ["USB1"], width = 200)
                    self.agilent_initialise = dpg.add_button(label = "Initialise")

            with dpg.window(label="Measurement Settings",pos= [0, 100]  ,width = 600):
                with dpg.group(horizontal=True):
                    dpg.add_text("Delay time (s): ")
                    self.delay_time = dpg.add_input_double(default_value=0.5, width = 100)
                    dpg.add_text("Meas. Time Mode: ")
                    self.meas_time_mode_selector = dpg.add_combo(["SHOR", "MED", "LONG"], width = 100)


                with dpg.group(horizontal=True):
                    dpg.add_text("Averaging Factor: ")
                    self.averaging_factor = dpg.add_input_int(default_value=1, width = 100)
                    dpg.add_text("Bias Level (V)")
                    self.bias_level = dpg.add_combo([0, 1.5, 2], width = 100)

            with dpg.window(label = "Frequency List", width = 300, pos = [0, 200]):
                self.freq_list, self.add_freq_text, self.freq_add, self.freq_add_range, self.freq_delete = make_variable_list_frame(20)
            
            with dpg.window(label = "Voltage List", width = 300, pos = [300, 200]):
                self.volt_list, self.add_volt_text, self.volt_add, self.volt_add_range, self.volt_delete = make_variable_list_frame(1)

            with dpg.window(label = "Temperature List", width = 600, pos = [0, 323]):
                with dpg.group(horizontal=True):
                    self.volt_list, self.add_volt_text, self.volt_add, self.volt_add_range, self.volt_delete = make_variable_list_frame(25)
                    with dpg.group():
                        with dpg.group(horizontal=True):
                            self.go_to_temp_button = dpg.add_button(label = "Go to:")
                            self.go_to_temp_input  = dpg.add_input_float(default_value=25)
                            dpg.add_text("°C")
                        with dpg.group(horizontal=True):
                            dpg.add_text("Rate (°C/min): ")
                            dpg.add_input_double(default_value=10)
                        with dpg.group(horizontal=True):
                            dpg.add_text("Stab. Time (s)")
                            dpg.add_input_double(default_value=1)


            with dpg.window(label = "Output Data Settings", pos = [0, 446], width = 600):
                with dpg.group(horizontal=True):
                    self.output_file_path  = dpg.add_input_text(default_value="results.json")
                    self.browse_button = dpg.add_button(label = "Browse", callback = lambda: dpg.show_item("file_dialog_id"))
            
            with dpg.file_dialog(directory_selector=False, show=False, callback=file_saveas_callback, user_data=self.output_file_path, id="file_dialog_id", width=700 ,height=400):
                dpg.add_file_extension(".json")
            

def file_saveas_callback(sender, app_data, output_file_path):
    # print("Sender: ", sender)
    # print("App Data: ", app_data)
    dpg.set_value(output_file_path, app_data["file_path_name"])


            
def make_variable_list_frame(default_val):
    with dpg.group(horizontal=True):
        listbox_handle = dpg.add_listbox([default_val], width = 200)
        with dpg.group():
            add_text = dpg.add_input_float(default_value = default_val, width = 100)
            add_button = dpg.add_button(label = "Add")
            add_range_button = dpg.add_button(label = "Add Range")
            delete_button = dpg.add_button(label = "Delete")
        

    return listbox_handle, add_text, add_button, add_range_button, delete_button


                

