import pyvisa
import time

class LinkamHotstage(): 

    def __init__(self) -> None:
        
        self.initialise_linkam()

    def initialise_linkam(self) -> None:
        
        rm = pyvisa.ResourceManager()

        self.link = rm.open_resource('ASRL3::INSTR')

        self.link.baud_rate = 19200

        self.link.read_termination = '\r'
        self.link.write_termination = '\r'

        self.link.timeout = 3000
    

    def set_temperature(self, T: float, rate: float = 20.) -> None:

        #need to link.read after writing anything... there's probably a way to fix this.
    
        self.link.write(f"R1{int(rate*100)}")
        time.sleep(0.1)
        self.link.read()
        time.sleep(0.1)

        self.link.write(f"L1{int(T*10)}")
        time.sleep(0.1)
        self.link.read()
        time.sleep(0.1)

        self.link.write("S")
        time.sleep(0.1)
        self.link.read()
        time.sleep(0.1)


    def stop(self) -> None:
        self.link.write('E')
        self.link.read()

    def current_temperature(self) -> None:
        self.link.write('T')
        raw_string = self.link.read_raw()
        status_byte = int(raw_string[0])
        
        if status_byte == 1:
            status = "Stopped"
        elif status_byte == 16:
            status = "Heating"
        elif status_byte == 32:
            status = "Cooling"
        elif status_byte == 48:
            status = "Holding"
        else:
            status = "Holding"

        

        temperature = int(raw_string[6:10],16)/10.0
        #print(f"Temperature is {temperature}")
        return temperature, status
    


#link.read_bytes works for 'T'