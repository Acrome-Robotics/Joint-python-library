from acrome_joint.joint import *
from gui.ramp_trajectory import *   # <-- S-Curve Ramp sınıfını kullanacağız

keyword_for_usb = "USB-SERIAL"
port = SerialPort(USB_serial_port(keyword_for_usb), baudrate=921600, timeout=0.01)


joint_0 = Joint(0, port)
joint_1 = Joint(1, port)


# S curve setpoint

while True:
    print(joint_0.ping())
    print(joint_1.ping())





#blue.set_variables([Index_Blue.Config_TimeStamp, 123])
#blue.set_variables([Index_Blue.Config_Description, ''])

#blue.set_config_description()
#blue.set_config_timeStamp()




