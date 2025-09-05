import serial

class SerialPort:
    def __init__(self, port_name, baudrate=921600, timeout=0.1, isTest:bool=False):
        self.port_name = port_name
        self.baudrate = baudrate
        self.timeout = timeout
        self.isTest = isTest
        if(self.isTest != True):
            self._ph = serial.Serial(port=self.port_name, baudrate=self.baudrate, timeout=self.timeout)

    def close_port(self):
        if self.isTest:
            print(f"virtual port destroyed.")
        else:
            if self._ph and self._ph.is_open:
                self._ph.reset_input_buffer()
                self._ph.reset_output_buffer()
                self._ph.close()
                print(f"Port '{self.port_name}' shut down.")
            else:
                print(f"Port '{self.port_name}' already closed.")

    def __del__(self):
        try:
            self.close_port()
        except Exception as e:
            print(f"Port yok edilirken bir hata oluştu: {e}")
        
    def _write_bus(self,data):
        if(self.isTest == True):
            print(list(data))
        else:
            self._ph.flushInput()
            self._ph.write(data)
        pass

    def _read_bus(self, size):
        if(self.isTest == False):
            return self._ph.read(size=size)
        else:
            print("Read Bus(TEST!)")
            return "True for test"

    def _no_timeout(self):
        notimeout = 50 #in seconds
        if(self.isTest):
            print(f"port timeout update is setted to {notimeout} (TEST!)")
        else:
            self._ph.timeout = notimeout

    def set_timeout(self, timeout):
        if(self.isTest):
            print(f"port timeout update to {timeout} (TEST!)")
        else:
            self._ph.timeout = timeout



