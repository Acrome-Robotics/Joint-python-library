## this is master for connected devices.
import struct
from crccheck.crc import Crc32Mpeg2 as CRC32
import time
import enum
from acrome_joint.serial_port import *
'''
COMMUNICATION PACKAGE => 
HEADER, ID, DEVICE_FAMILY, PACKAGE_SIZE, COMMAND, STATUS, .............. DATA ................. , CRC
'''

PING_PACKAGE_SIZE = 10

#Classical Device Indexes
Index_Device_Classical = enum.IntEnum('Index', [
	'Header',
	'DeviceID',
    'DeviceFamily',
	'PackageSize',
	'Command',
    'Status',
	'HardwareVersion',
	'SoftwareVersion',
    'Baudrate',
], start=0)

#Classical_Commands
class Device_Commands(enum.IntEnum):
    ACK = 0x80
    SYNC = 0x40

    PING = 0x00
    WRITE = 0x01
    READ = 0x02
    EEPROM_SAVE = 0x03
    ERROR_CLEAR = 0x04
    REBOOT = 0x05
    EEPROM_RESET = 0x06
    BL_JUMP = 0x07
    ENTER_CONFIGURATION = 0x08
    ENTER_OPERATION = 0x09
    ERROR = 0x10

    ENTER_CONFIGURATION_ACK = 0x80 | 0x08       # ACK | ENTER_CONFIGURATION
    ENTER_OPERATION_ACK = 0x80 | 0x09           # ACK | ENTER_OPERATION
    WRITE_ACK = 0x80 | 0x01                     # ACK | WRITE
    WRITE_SYNC = 0x40 | 0x01                    # SYNC | WRITE
    EEPROM_SAVE_ACK = 0x80 | 0x03               # ACK | EEPROM_WRITE
    EEPROM_SAVE_SYNC = 0x40 | 0x03              # SYNC | EEPROM_WRITE

def set_variables_directly(header:int, device_family:int, id:int, status:int=0, *idx_val_pairs, ack = False, port:SerialPort):
        # returns : did ACK come?
        port._ph.flushInput()

        fmt_str = '<BBBBBB'
        var_count = 0
        size = 0
        for one_pair in idx_val_pairs:
            try:
                if len(one_pair) != 2:
                    raise ValueError(f"{one_pair} more than a pair! It is not a pair")
                else:
                    fmt_str += ('B' + self._vars[one_pair[0]].type())
                    var_count+=1
                    size += (1 + self._vars[one_pair[0]].size())
            except:
                raise ValueError(f"{one_pair} is not proper pair")
        
        flattened_list = [item for sublist in idx_val_pairs for item in sublist]

        struct_out = list(struct.pack(fmt_str, *[header, id, device_family, size + PING_PACKAGE_SIZE, Device_Commands.WRITE, status, *flattened_list]))
        struct_out = bytes(struct_out) + struct.pack('<' + 'I', CRC32.calc(struct_out))
        ack_size = PING_PACKAGE_SIZE


        port._ph.write(struct_out)
        raise NotImplementedError()

        if _read_ack():
            return True
        else:
            return False


class Slave_Device():
    SERIAL_HEADER = 0x55
    _BROADCAST_ID = 0xFF

    _BATCH_ID = 254
    def __init__(self, id, device_family, variables, port:SerialPort):
        self._port = port
        self._header = self.SERIAL_HEADER
        self._id = id
        self._device_family = device_family
        self._vars = variables
        self._ack_size = 0
        self.__post_sleep = 0.01
        self.__device_init_sleep = 3
        self.write_ack_enable = False

    def enable_get_ack(self):
        self.write_ack_enable = True

    def _init_sleep(self):
        time.sleep(self.__device_init_sleep)

    def _post_sleep(self):
        time.sleep(self.__post_sleep)
    
    def _write_port(self, data):
        self._port._write_bus(data)

    def _read_port(self, size) -> bytes:
        return self._port._read_bus(size=size)
    
    def _parse_received(self, data):
        id = data[Index_Device_Classical.DeviceID]
        data = data[4:-4]
        fmt_str = '<'

        i = 0
        while i < len(data):
            fmt_str += 'B' + self._vars[data[i]].type()
            i += self._vars[data[i]].size() + 1

        unpacked = list(struct.unpack(fmt_str, data))
        grouped = zip(*(iter(unpacked),) * 2)
        for group in grouped:
            self._vars[group[0]].value(group[1])
    
    def _read_ack(self) -> bool:
        ret = self._read_port(self._ack_size)
        if (ret == "True for test"):
            return True
        if(ret==None):
            return False
        if len(ret) == self._ack_size:
            if (CRC32.calc(ret[:-4]) == struct.unpack('<I', ret[-4:])[0]):
                if ret[Index_Device_Classical.PackageSize] > PING_PACKAGE_SIZE:
                    self._parse_received(ret)
                    return True
                else:
                    return True # ping islemi ve WRITE_ACK icin.
            else:
                return False
        else:
            return False
        
    def _read_var_no_timeout(self):
        self._port._no_timeout()
        ack_flag = self._read_ack()
        self._port.set_timeout(0.01)
        if ack_flag:
            return True
        else:
            return False 
        
    def _pure_command_send(self, command:int):
        fmt_str = '<BBBBBB'
        struct_out = list(struct.pack(fmt_str, *[self._header, self._id, self._device_family, PING_PACKAGE_SIZE, command, 0]))
        struct_out = bytes(struct_out) + struct.pack('<I', CRC32.calc(struct_out))
        self._write_port(struct_out)
        return struct_out

    def ping(self):
        self._pure_command_send(Device_Commands.PING)
        self._ack_size = PING_PACKAGE_SIZE
        if self._read_ack():
            return True
        else:
            return False
    
    def get_variables(self, *indexes):
        self._ack_size = 0
        fmt_str = '<BBBBBB'+'B'*len(indexes)

        struct_out = list(struct.pack(fmt_str, *[self._header, self._id, self._device_family ,len(indexes) + PING_PACKAGE_SIZE, Device_Commands.READ, 0, *indexes]))
        struct_out = bytes(struct_out) + struct.pack('<' + 'I', CRC32.calc(struct_out))
        for i in indexes:
            self._ack_size += (self._vars[int(i)].size() + 1)
        self._ack_size += PING_PACKAGE_SIZE

        self._write_port(struct_out)

        if self._read_ack():
            return [self._vars[index].value() for index in indexes]
        else:
            return [None]

    def set_variables(self, *idx_val_pairs, ack = False):
        # returns : did ACK come?
        fmt_str = '<BBBBBB'
        var_count = 0
        size = 0
        for one_pair in idx_val_pairs:
            try:
                if len(one_pair) != 2:
                    raise ValueError(f"{one_pair} more than a pair! It is not a pair")
                else:
                    fmt_str += ('B' + self._vars[one_pair[0]].type())
                    var_count+=1
                    size += (1 + self._vars[one_pair[0]].size())
            except:
                raise ValueError(f"{one_pair} is not proper pair")
        
        flattened_list = [item for sublist in idx_val_pairs for item in sublist]

        struct_out = list(struct.pack(fmt_str, *[self._header, self._id, self._device_family, size + PING_PACKAGE_SIZE, Device_Commands.WRITE, 0, *flattened_list]))
        struct_out = bytes(struct_out) + struct.pack('<' + 'I', CRC32.calc(struct_out))
        self._ack_size = PING_PACKAGE_SIZE

        self._write_port(struct_out)
        if(self.write_ack_enable):
            if self._read_ack():
                return True
            else:
                return False
        return False
        
    def reboot(self):
        self._pure_command_send(Device_Commands.REBOOT)
	
    def eeprom_save(self):
        self._pure_command_send(Device_Commands.EEPROM_SAVE)
        
    def factory_reset(self, ack=False):
        self._pure_command_send(Device_Commands.EEPROM_RESET)

    def enter_bootloader(self):
        self._pure_command_send(Device_Commands.BL_JUMP)

    def enter_operation(self):
        self._pure_command_send(Device_Commands.ENTER_OPERATION)

    def enter_configuration(self):
        self._pure_command_send(Device_Commands.ENTER_CONFIGURATION)

    def get_driver_info(self):
        """ Get hardware and software versions from the driver

        Args:
            id (int): The device ID of the driver.

        Returns:
            dict | None: Dictionary containing versions or None.
        """
        st = dict()
        data = self.get_variables([Index_Device_Classical.HardwareVersion, Index_Device_Classical.SoftwareVersion])
        if data is not None:
            ver = list(struct.pack('<I', data[0]))
            st['HardwareVersion'] = "v{1}.{2}.{3}".format(*ver[::-1])
            ver = list(struct.pack('<I', data[1]))
            st['SoftwareVersion'] = "v{1}.{2}.{3}".format(*ver[::-1])

            self.__driver_list[id]._config = st
            return st
        else:
            return None
        
    def update_driver_id(self, id: int, id_new: int):
        """ Update the device ID of the driver

        Args:
            id (int): The device ID of the driver
            id_new (int): New device ID

        Raises:
            ValueError: Current or updating device IDs are not valid
        """
        if (id < 0) or (id > 254):
            raise ValueError("{} is not a valid ID!".format(id))

        if (id_new < 0) or (id_new > 254):
            raise ValueError("{} is not a valid ID argument!".format(id_new))
        
        self.set_variables([Index_Device_Classical.DeviceID, id_new])
        self._post_sleep()
        
        self.eeprom_save(id_new)
        self._post_sleep()
        self.reboot(id)
        
    def get_all_variable(self):
        for i in range(0, len(self._vars), 10):
            j = i
            k = min(i + 9, len(self._vars) - 1)  # Son grupta sınırlamayı sağlar
            index_list = list(range(j, k + 1))
            self.read_var(*index_list) # her birisi maksimum data sayisiymis gibi dusunerek yazarsak 4 byte olur. her bir pakette 10 adet alsin. maksimuma vurmak istemedigimizden dolayi.

class Data_():
    def __init__(self, index, var_type, rw=True, value = 0):
        self.__index = index
        self.__type = var_type
        self.__size  = struct.calcsize(self.__type)
        self.__value = value
        self.__rw = rw

    def value(self, value=None):
        if value is None:
            return self.__value
        elif self.__rw:
            self.__value = struct.unpack('<' + self.__type, struct.pack('<' + self.__type, value))[0]

    def index(self) ->enum.IntEnum:
        return self.__index
    
    def writeable(self) -> bool:
        return self.__rw

    def size(self) -> int:
        return self.__size
	
    def type(self) -> str:
        return self.__type
