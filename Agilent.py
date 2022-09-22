import pyvisa

rm = pyvisa.ResourceManager()

address = rm.list_resouces()[0]

agi = rm.open_resource(address)

agi.read_termination = '\n'
agi.write_termination = '\n'

agi.timeout = 10000

#test if it's the right address: 

agi.write('*IDN')

agi_id = read()

if agi_id == "Agilent Technologies,E4980A,MY46309287,A.06.11":
    print("Correct address!")
    
else:
    print("something's wrong")
 
 
agi.write('*RST; *CLS') # reset and clear buffer


agi.write(':APER MED, 10') #set aperture (SHORT, MED, LONG) and averaging 

agi.write(':FREQ 5000') # set frequency (could also set this as a list potentially: LIST:FREQ?...).
agi.write(':VOLT 1.0') # set voltage

agi.write(':FUNC:IMP CPD') # set measurement function

agi.write(':FUNC:IMP:RANG:AUTO ON') # set auto-range for impedance

agi.write(':INIT')
agi.write(':FETC?') # fetch data
agi.read_ascii_values() # get data as [CP, D, data_status]
