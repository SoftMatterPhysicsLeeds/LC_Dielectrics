import pyvisa
import numpy as np

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
            
        except pyvisa.errors.VisaIOError:
            print("Could not connect to E4980A. Check address is correct.")

        self.reset_and_clear()
        
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

    def set_voltage(self,volt: float) -> None:
        self.spectrometer.write(f":VOLT {volt}")

    def set_func(self, func: str, auto: bool = True) -> None:
        self.spectrometer.write(f":FUNC:IMP {func}")
        if auto:
            self.spectrometer.write(":FUNC:IMP:RANG:AUTO ON")

    def set_aperture_mode(self, mode: str, av_factor: int) -> None:
        self.spectrometer.write(f":APER {mode},{av_factor}")

    def measure(self) -> None:
        # self.spectrometer.write(":INIT")
        self.spectrometer.write(":TRIG:IMM")
        self.spectrometer.write(":FETC?") # request data acquisition
        return self.spectrometer.read_ascii_values() # get data as [val1, val2, data_status]. For CP-D func, this is [Cp, D, data_status]

