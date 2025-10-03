import struct
from crccheck.crc import Crc32Mpeg2 as CRC32
import serial
import time
from packaging.version import parse as parse_version
import requests
import hashlib
import tempfile
from stm32loader.main import main as stm32loader_main
import enum
from acrome_joint.Slave_Device import *


# enter here for extra commands: 
#class Device_ExtraCommands(enum.IntEnum):
	# .......... start with 11
	# .......... end of extra commmands max: 39


Index_Joint = enum.IntEnum('Index', [
	'Header',
	'DeviceID',
	'DeviceFamily',
	'PackageSize',
	'Command',
	'Status',
	'HardwareVersion',
	'SoftwareVersion',
	'Baudrate', #'WritableStart' = iBaudrate
	# user parameter start
	'OperationMode',
	'Enable',
	'Vbus_read',
	'Temprature_read',
	'currentId_loop_kp',
	'currentId_loop_ki',
	'currentId_loop_kd',
	'currentIq_loop_kp',
	'currentIq_loop_ki',
	'currentIq_loop_kd',
	'velocity_loop_kp',
	'velocity_loop_ki',
	'velocity_loop_kd',
	'position_loop_kp',
	'position_loop_ki',
	'position_loop_kd',
	'max_position',
	'min_position',
	'max_velocity',
	'max_current',
	'current_Va',
	'current_Vb',
	'current_Vc',
	'current_Ia',
	'current_Ib',
	'current_Ic',
	'current_Id',
	'current_Iq',
	'current_velocity',
	'current_position',
	'current_electrical_degree',
	'current_electrical_radian',
	'setpoint_current',
	'setpoint_velocity',
	'setpoint_position',
	'openloop_voltage_size',
	'openloop_angle_degree',
	'current_lock_angle_degree',
	# user parameter end
	'Config_TimeStamp',
	'Config_Description',
	'CRCValue',
], start=0)



def scan_joint_devices(port:SerialPort):
	device = Joint(0, port)
	available_devices = []

	for id in range(0,255):
		device._id = id
		if(device.ping()):
			available_devices.append(id)

	return available_devices


class Joint(Slave_Device):
	_PRODUCT_TYPE = 0xDA
	_PACKAGE_ESSENTIAL_SIZE = 6
	_STATUS_KEY_LIST = ['EEPROM', 'Software Version', 'Hardware Version']
	__RELEASE_URL = "https://api.github.com/repos/AAcrome-Smart-Motion-Devices/SMD-Blue-Firmware/releases/{version}"

	class Operation_Mode():
		OPERATION_OPENLOOP = 0
		OPERATION_CURRENT_LOCK = 1
		OPERATION_FOC_TORQUE = 2
		OPERATION_FOC_VELOCITY = 3
		OPERATION_FOC_POSITION = 4

	def __init__(self, ID, port:SerialPort) -> bool:
		self.__ack_size = 0
		if ID > 254 or ID < 0:
			raise ValueError("Device ID can not be higher than 254 or lower than 0!")
		device_special_data = [
            Data_(Index_Joint.Header, 'B', False, 0x55),
            Data_(Index_Joint.DeviceID, 'B'),
			Data_(Index_Joint.DeviceFamily, 'B'),
            Data_(Index_Joint.PackageSize, 'B'),
            Data_(Index_Joint.Command, 'B'),
			Data_(Index_Joint.Status, 'B'),
            Data_(Index_Joint.HardwareVersion, 'I'),
            Data_(Index_Joint.SoftwareVersion, 'I'),
            Data_(Index_Joint.Baudrate, 'I'),
			# user parameter starts
			Data_(Index_Joint.OperationMode, 'B'),
			Data_(Index_Joint.Enable, 'B'),
			Data_(Index_Joint.Vbus_read, 'f'),
			Data_(Index_Joint.Temprature_read, 'f'),
			Data_(Index_Joint.currentId_loop_kp, 'f'),
			Data_(Index_Joint.currentId_loop_ki, 'f'),
			Data_(Index_Joint.currentId_loop_kd, 'f'),
			Data_(Index_Joint.currentIq_loop_kp, 'f'),
			Data_(Index_Joint.currentIq_loop_ki, 'f'),
			Data_(Index_Joint.currentIq_loop_kd, 'f'),
			Data_(Index_Joint.velocity_loop_kp, 'f'),
			Data_(Index_Joint.velocity_loop_ki, 'f'),
			Data_(Index_Joint.velocity_loop_kd, 'f'),
			Data_(Index_Joint.position_loop_kp, 'f'),
			Data_(Index_Joint.position_loop_ki, 'f'),
			Data_(Index_Joint.position_loop_kd, 'f'),
			Data_(Index_Joint.max_position, 'i'),
			Data_(Index_Joint.min_position, 'i'),
			Data_(Index_Joint.max_velocity, 'f'),
			Data_(Index_Joint.max_current, 'f'),
			Data_(Index_Joint.current_Va, 'f'),
			Data_(Index_Joint.current_Vb, 'f'),
			Data_(Index_Joint.current_Vc, 'f'),
			Data_(Index_Joint.current_Ia, 'f'),
			Data_(Index_Joint.current_Ib, 'f'),
			Data_(Index_Joint.current_Ic, 'f'),
			Data_(Index_Joint.current_Id, 'f'),
			Data_(Index_Joint.current_Iq, 'f'),
			Data_(Index_Joint.current_velocity, 'f'),
			Data_(Index_Joint.current_position, 'i'),
			Data_(Index_Joint.current_electrical_degree, 'f'),
			Data_(Index_Joint.current_electrical_radian, 'f'),
			Data_(Index_Joint.setpoint_current, 'f'),
			Data_(Index_Joint.setpoint_velocity, 'f'),
			Data_(Index_Joint.setpoint_position, 'f'),
			Data_(Index_Joint.openloop_voltage_size, 'f'),
			Data_(Index_Joint.openloop_angle_degree, 'f'),
			Data_(Index_Joint.current_lock_angle_degree, 'f'),
			# user parameter end
			Data_(Index_Joint.Config_TimeStamp, 'Q'),
			Data_(Index_Joint.Config_Description, '100s'),
            Data_(Index_Joint.CRCValue, 'I'),
        ]
		super().__init__(ID, self._PRODUCT_TYPE, device_special_data, port)
		self._vars[Index_Joint.DeviceID].value(ID)

	# user start for extra commands.
	#def command(self): 

	def __del__(self):
		pass

	def get_latest_fw_version(self):
		""" Get the latest firmware version from the Github servers.

		Returns:
			String: Latest firmware version
		"""
		response = requests.get(url=self.__class__.__RELEASE_URL.format(version='latest'))
		if (response.status_code in [200, 302]):
			return (response.json()['tag_name'])

	def update_fw_version(self, version=''):
		""" Update firmware version with respect to given version string.

		Args:
			id (int): The device ID of the driver
			version (str, optional): Desired firmware version. Defaults to ''.

		Returns:
			Bool: True if the firmware is updated
		"""

		fw_file = tempfile.NamedTemporaryFile("wb+",delete=False)
		if version == '':
			version = 'latest'
		else:
			version = 'tags/' + version

		response = requests.get(url=self.__class__.__RELEASE_URL.format(version=version))
		if response.status_code in [200, 302]:
			assets = response.json()['assets']

			fw_dl_url = None
			md5_dl_url = None
			for asset in assets:
				if '.bin' in asset['name']:
					fw_dl_url = asset['browser_download_url']
				elif '.md5' in asset['name']:
					md5_dl_url = asset['browser_download_url']

			if None in [fw_dl_url, md5_dl_url]:
				raise Exception("Could not found requested firmware file! Check your connection to GitHub.")

			#  Get binary firmware file
			md5_fw = None
			response = requests.get(fw_dl_url, stream=True)
			if (response.status_code in [200, 302]):
				fw_file.write(response.content)
				md5_fw = hashlib.md5(response.content).hexdigest()
			else:
				raise Exception("Could not fetch requested binary file! Check your connection to GitHub.")

			#  Get MD5 file
			response = requests.get(md5_dl_url, stream=True)
			if (response.status_code in [200, 302]):
				md5_retreived = response.text.split(' ')[0]
				if (md5_fw == md5_retreived):

					# Put the driver in to bootloader mode
					self.enter_bootloader()
					time.sleep(0.1)

					# Close serial port
					serial_settings = self._port._ph.get_settings()
					self._port._ph.close()

					# Upload binary
					args = ['-p', self._port._ph.portstr, '-b', str(115200), '-e', '-w', '-v', fw_file.name]
					stm32loader_main(*args)

					# Delete uploaded binary
					if (not fw_file.closed):
						fw_file.close()

					# Re open port to the user with saved settings
					self._port._ph.apply_settings(serial_settings)
					self._port._ph.open()
					return True

				else:
					raise Exception("MD5 Mismatch!")
			else:
				raise Exception("Could not fetch requested MD5 file! Check your connection to GitHub.")
		else:
			raise Exception("Could not found requested firmware files list! Check your connection to GitHub.")
		
	def enable_torque(self, en: bool):
		""" Enable power to the motor of the driver.

    	Args:
    	    id (int): The device ID of the driver
    	    en (bool): Enable. True enables the torque.
    	"""

		self.set_variables([Index_Joint.Enable, en])
		self._post_sleep()

	def set_config_timeStamp(self):
		epoch_seconds = int(time.time())
		self.set_variables([Index_Joint.Config_TimeStamp, epoch_seconds])
		self._post_sleep()
		
	def set_config_description(self, description:str):
		if len(description) >= 100:
			text = description[:99] + '\0'
		else:
			text = description + '\0'
			text = text.ljust(100, ' ')
		text = text.encode('ascii')  # veya utf-8 eğer uyumluysa

		self.set_variables([Index_Joint.Config_Description, text])
		self._post_sleep()

	def set_variables_sync(self, *idx_val_pairs, ack=False):
		return super().set_variables(*idx_val_pairs, ack=ack)



	def get_FOC_parameters(self, package_number:int):
		if package_number >= 4:
			raise "invalid package number ex: 0, 1, 2"
		classic_package = [
			Index_Joint.Enable,
			Index_Joint.current_Id, Index_Joint.current_Iq,
			Index_Joint.current_velocity, Index_Joint.current_position,
			Index_Joint.Temprature_read,
			Index_Joint.setpoint_current, Index_Joint.setpoint_velocity, Index_Joint.setpoint_position
		]
		package_0 = [
			Index_Joint.currentId_loop_kp, 
			Index_Joint.currentId_loop_ki, 
			Index_Joint.currentId_loop_kd, 
			Index_Joint.currentIq_loop_kp, 
			Index_Joint.currentIq_loop_ki, 
			Index_Joint.currentIq_loop_kd, 
		]
		package_1 = [
			Index_Joint.velocity_loop_kp,
			Index_Joint.velocity_loop_ki,
			Index_Joint.velocity_loop_kd,
		]
		package_2 = [
			Index_Joint.position_loop_kp,
			Index_Joint.position_loop_ki,
			Index_Joint.position_loop_kd,
		]

		if package_number == 0:
			return self.get_variables(*classic_package , *package_0)
			
		elif package_number == 1:
			return self.get_variables(*classic_package , *package_1)
			
		elif package_number == 2:
			return self.get_variables(*classic_package , *package_2)
		
		elif package_number == 3:
			return self.get_variables(*classic_package)
		


def set_joint_variables_sync(port:SerialPort, parameter_idx, *idx_val_pairs):
    """
    Build & send a WRITE_SYNC packet:
      [HEADER, 0xFF, DEVICE_FAMILY, LENGTH, WRITE_SYNC, 0, PARAM_IDX, (ID, VALUE)*, CRC32]
    - parameter_idx: single parameter index to write on each target
    - idx_val_pairs: variadic list of 2-tuples/lists like (id, value) or [id, value]
    - port: SerialPort-like object that has write(bytes) method

    Returns: number of bytes written.
    Raises: ValueError on malformed inputs.
    """

    # --- Validate & fetch parameter meta
    if parameter_idx not in VARS:
        raise ValueError(f"Unknown parameter index: {parameter_idx}")

    var_desc = VARS[parameter_idx]
    val_fmt = var_desc.type()     # e.g., 'f', 'i', 'H', etc. (little-endian will be applied later)
    val_size = var_desc.size()    # size in bytes

    # --- Validate pairs; normalize to tuples
    pairs = []
    for p in idx_val_pairs:
        if not hasattr(p, '__len__') or len(p) != 2:
            raise ValueError(f"{p} must be a pair like [ID, value]")
        dev_id, value = p[0], p[1]

        # Device ID range (0..254), 255 is reserved for broadcast in header
        if not (0 <= int(dev_id) <= 254):
            raise ValueError(f"Device ID out of range (0..254): {dev_id}")

        pairs.append((int(dev_id), value))

    if not pairs:
        raise ValueError("At least one [ID, value] pair is required.")

    # --- Compute size field used by your protocol
    # Payload after the 6 fixed header bytes:
    #   PARAM_IDX (1 byte)
    # + for each pair: ID (1 byte) + VALUE (val_size bytes)
    payload_size = 1 + len(pairs) * (1 + val_size)

    # Protocol total-length field used in your other function:
    # size + PING_PACKAGE_SIZE (to mirror your existing framing)
    length_field = payload_size + PING_PACKAGE_SIZE

    # --- Build struct format string & flat args
    # Fixed header: '<BBBBBB'
    # Then: PARAM_IDX (B)
    # Then for each pair: ID (B) + VALUE (val_fmt)
    fmt = '<BBBBBB' + 'B' + ''.join(['B' + val_fmt for _ in pairs])

    flat = [
        dev.SERIAL_HEADER,			# header
        0xFF,                   # broadcast ID
        DEVICE_FAMILY,          # device family
        length_field,           # total length field
        Device_Commands.WRITE_SYNC,  # command
        0x00,                   # reserved
        int(parameter_idx),     # parameter index
    ]

    # Append all (ID, VALUE) flattened; VALUE goes in native python type, struct packs it
    for dev_id, value in pairs:
        flat.append(dev_id)
        flat.append(value)

    # --- Pack without CRC
    pkt_wo_crc = struct.pack(fmt, *flat)

    # --- Append CRC32 (little-endian uint32 of the bytes above)
    pkt = pkt_wo_crc + struct.pack('<I', CRC32.calc(pkt_wo_crc))

    # --- Send over the provided port (broadcast sync write typically has no ACK)
    written = port.write(pkt)
    return written


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