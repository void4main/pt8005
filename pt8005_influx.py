import serial
from datetime import datetime
from influxdb import InfluxDBClient


class pt8005():
    ''' Serial communication '''
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

    def read(self, num=1):
        ''' Read data from serial port '''
        data = self.ser.read(num)
        return data

    def output(self, value):
        print(value, " ", end="")
        for i in range(1, int(value)):
            print("*", end="")
        print("")

    def stream(self):
        ''' Stream decoding of data sent by the device '''
        while 1:
            data = self.read(1)                       # read byte from serial
            if data == self.SYNC:                     # sync found?
                data = self.read(1)                   # read next
                if data == self.INDICATOR_DBA:
                    self.state_dba_dbc = self.INDICATOR_DBA
                if data == self.INDICATOR_DBC:
                    self.state_dba_dbc = self.INDICATOR_DBC
                if data == self.INDICATOR_DATA:
                    # Read two bytes from serial port
                    data1 = self.read(1)              # read next
                    data2 = self.read(1)              # read next
                    # Byte 1
                    part1 = data1[0]
                    # Byte 2 - extract Bit 5-8
                    part2 = bytes([data2[0] >> 4])
                    # Byte 2 - extract Bit 1-4
                    part3 = bytes([data2[0] & 15])
                    # Build float
                    value = (part1*10)+int(part2.hex())+(int(part3.hex())/10)
                    return value


class datadump():
    def __init__(self, host="localhost", dbname="pt8005_pa10", port="8086"):
        try:
            self.client = InfluxDBClient(host, port)
            self.client.switch_database(dbname)
        except:
            print("Some error occured.")
            exit(1)

    def _create_json(self, value, type):
        data = [{"measurement": "Construction Site ABC HH",
                "tags": {
                    "Device": "PT001",
                    "Room": "1.2.3",
                    "Floor": "3",
                    "Name": "Joe",
                    "Street": "Townhall 10",
                    "Postcode": "20000",
                    "City": "Hamburg"
                    },
                "time": str(datetime.now()),
                "fields": {
                    "Type": type,
                    "Value": value
                }
                }]
        return data

    def dump(self, value=0, type="dBA"):
        data = self._create_json(value, "dBA")
        result = self.client.write_points(data)
        return result


def main():
    print("Connecting to serial port ...")
    pt = pt8005()
    print("Connecting to InfluxDB ...")
    dd = datadump()
    print("Reading data from PeakTech 8005 ...")

    while 1:
        value = pt.stream()     # Read from serialport
        dd.dump(value, "dBA")   # Write values to InfluxDB


if __name__ == "__main__":
    main()
