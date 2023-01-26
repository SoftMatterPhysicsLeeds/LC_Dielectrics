import pyvisa
import numpy as np

class LinkamHotstage(): 

    def __init__(self, address: str) -> None:
        
        self.address = address
        self.initialise_linkam()

    def initialise_linkam(self) -> None:
        
        rm = pyvisa.ResourceManager()

        self.link = rm.open_resource(self.address)

        self.link.baud_rate = 19200

        self.link.read_termination = '\r'
        self.link.write_termination = '\r'

        self.link.timeout = 3000

        try: 
            self.current_temperature()
            print("Linkam Connected!")

        except pyvisa.errors.VisaIOError:
            print("Could not connect to Linkam Hotstage. Try different address (make sure it is switched on)")

    

    def set_temperature(self, T: float, rate: float = 20.) -> None:

        if self.init:
            self.link.write(f"R1{int(rate*100)}")
            self.link.read()
            self.link.write(f"L1{int(T*10)}")
            self.link.read()
        else:
            self.link.write(f"R1{int(rate*100)}")
            self.link.read()
            self.link.write(f"L1{int(T*10)}")
            self.link.read()
            self.link.write("S")
            self.link.read()

            self.init = True
    
    def stop(self) -> None:
        self.link.write('E')
        self.link.read()
        self.init = False

    def current_temperature(self) -> None:
        self.link.write('T')
        raw_string = self.link.read_raw()
        status_byte = int(raw_string[0])
        
        if status_byte == 1:
            status = "Stopped"
        elif status_byte == 16 or status_byte== 17:
            status = "Heating"
        elif status_byte == 32 or status_byte ==33:
            status = "Cooling"
        elif status_byte == 48 or status_byte == 49:
            status = "Holding"
        else:
            status = "Dunno"

        temperature = int(raw_string[6:10],16)/10.0
        return temperature, status
    

class AgilentSpectrometer():

    def __init__(self,address: str) -> None:

        self.address = address
        self.initialise(self.address)


    def initialise(self,address: str) -> None:

        rm = pyvisa.ResourceManager() 
        self.spectrometer = rm.open_resource(address) # if no USB attached, this just connects to whatever first instrument is... 
        #self.spectrometer = rm.open_resource(rm.list_resources()[0])
        self.spectrometer.read_termination = '\n'
        self.spectrometer.write_termination = '\n'
        self.spectrometer.timeout = 100000 # set timeout to long enough that the machine doesn't loose connection during measurement.
        #self.spectrometer.query("*IDN?")
        try: 
            self.spectrometer.write("*IDN?")
            self.spectrometer_id = self.spectrometer.read()
            print(self.spectrometer_id)
            self.reset_and_clear()
            
        except pyvisa.errors.VisaIOError:
            print("Could not connect to E4980A. Check address is correct.")

        
        
    def reset_and_clear(self) -> None:
        self.spectrometer.write("*RST; *CLS") # reset and clear buffer
        self.spectrometer.write(":DISP:ENAB") # enable display and update
        self.spectrometer.write(":INIT:CONT") # automatically perform continuous measurements
        self.spectrometer.write(":TRIG:SOUR EXT") # set trigger source to 'external'


    def set_frequency(self,freq: list) -> None:
        self.spectrometer.write(f":FREQ {freq}")

    def set_freq_list(self, freq_list: np.array)-> None:
        self.spectrometer.write(":DISP:PAGE LIST")
        self.spectrometer.write(":LIST:MODE SEQ")

        freq_str= str(freq_list)
        freq_str= freq_str.split('[')[1].split(']')[0]

        self.spectrometer.write(":LIST:FREQ ", freq_str)

    def set_volt_list(self, volt_list: np.array)-> None:
        self.spectrometer.write(":DISP:PAGE LIST")
        self.spectrometer.write(":LIST:MODE SEQ")

        volt_str= str(volt_list)
        volt_str= volt_str.split('[')[1].split(']')[0]

        self.spectrometer.write(":LIST:VOLT ", volt_str)

    def set_voltage(self,volt: float) -> None:
        self.spectrometer.write(f":VOLT {volt}")

    def set_func(self, func: str, auto: bool = True) -> None:
        self.spectrometer.write(f":FUNC:IMP {func}")
        if auto:
            self.spectrometer.write(":FUNC:IMP:RANG:AUTO ON")

    def set_aperture_mode(self, mode: str, av_factor: int) -> None:
        self.spectrometer.write(f":APER {mode},{av_factor}")

    def measure(self, func: str) -> list[float]:
        # self.spectrometer.write(":INIT")
        self.spectrometer.write(f":FUNC:IMP {func}")
        self.spectrometer.write(":TRIG:IMM")
        self.spectrometer.write(":FETC?") # request data acquisition
        return self.spectrometer.read_ascii_values() # get data as [val1, val2, data_status]. For CP-D func, this is [Cp, D, data_status]

    def set_DC_bias(self,voltage: float) -> None:
        self.spectrometer.write(f":BIAS:VOLT {voltage}")
        self.spectrometer.write(f":BIAS:STATE ON")

    def turn_off_DC_bias(self) -> None:
        self.spectrometer.write(f":BIAS:STATE OFF")