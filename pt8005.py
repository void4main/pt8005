import serial
from datetime import datetime

class pt8005():

    SYNC = b'\xa5'
    INDICATOR_DBA = b'\x1B'
    INDICATOR_DBC = b'\x1C'
    INDICATOR_DATA = b'\x0D'
    POWER_OFF = b'\x33'
    TRANSMIT = b'\x5A\xAC'
    TOGGLE_RECORD = b'\x55'
    TOGGLE_DISPLAY_MAX = b'\x11'
    TOGGLE_DISPLAY_FAST = b'\x77'
    TOGGLE_RANGE = b'\x88'
    TOGGLE_DBA_DBC = b'\x99'

    def __init__(self, port="/dev/ttyUSB0", baudrate=9600):
        state_dba_dbc = "unkown"
        serialport = port
        try:
            self.ser = serial.Serial(serialport, baudrate)
            self.ser.isOpen()
            self.ser.write(self.TRANSMIT)
        except IOError:
            print("IO Error: Can not connect to", port)
            exit(1)

    def _send_cmd(self, cmd):
        self.ser.write(cmd)

    def off(self):
        ''' Turn off device '''
        self._send_cmd(self.POWER_OFF)

    def rec(self):
        ''' Starts/stops recording in PT8005
            Not needed to read data via serial port.
        '''
        self._send_cmd(self.TOGGLE_RECORD)

    def display(self):
        ''' Switch display mode fast/slow '''
        self.ser.write(self.TOGGLE_DISPLAY_FAST)

    def range(self):
        ''' Switch range '''
        self.ser.write(self.TOGGLE_RANGE)

    def type(self):
        ''' Switch dBA/dBC '''
        self.ser.write(self.TOGGLE_DBA_DBC)

    def read(self,num=1):
        ''' Read data from serial port '''
        data = self.ser.read(num)
        return data

    def output(self,value):
        print(value, " ", end="")
        for i in range(1,int(value)):
            print("*", end="")
        print("")

    def stream(self):
        while 1:
            data = self.read(1)                       # read byte from serial
            if data == self.SYNC:                     # sync found?
                data = self.read(1)                   # read next
                if data == self.INDICATOR_DBA:
                    self.state_dba_dbc = self.INDICATOR_DBA
                if data == self.INDICATOR_DBC:
                    self.state_dba_dbc = self.INDICATOR_DBC
                if data == self.INDICATOR_DATA:
                    data1 = self.read(1)              # read next
                    data2 = self.read(1)              # read next
                    part1 = data1[0]                  # byte 1
                    part2 = bytes([data2[0] >> 4])    # byte 2 - extract bit 5-8
                    part3 = bytes([data2[0] & 15])    # byte 2 - extract bit 1-4
                    value = (part1*10)+int(part2.hex())+(int(part3.hex())/10)
                    return value

def main():
    pt = pt8005()
    print("Go ...")
    while 1:
        value = pt.stream()
        now = datetime.now().time()     # why read the time from pt8005?! :)
        print(now, value, " ", end="")
        for i in range(1,int(value)):
            print("*", end="")
        print("")


if __name__ == "__main__":
    main()
