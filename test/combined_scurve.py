from acrome_joint.joint import *
from gui.ramp_trajectory import *   # <-- S-Curve Ramp sınıfını kullanacağız

keyword_for_usb = "USB-SERIAL"
port = SerialPort(USB_serial_port(keyword_for_usb), baudrate=921600, timeout=0.1)

joint_0 = Joint(0, port)
joint_1 = Joint(1, port)

while True:
    print(joint_1.ping())
    print(joint_0.ping())

    
# S curve setpoint
joint_0.enable_torque(True)
joint_1.enable_torque(True)

while True:
    sp = input("enter position setpoint : ")
    joint_0.set_variables([Index_Joint.setpoint_position, float(sp)])
    joint_1.set_variables([Index_Joint.setpoint_position, float(sp)])




#blue.set_variables([Index_Blue.Config_TimeStamp, 123])
#blue.set_variables([Index_Blue.Config_Description, ''])

#blue.set_config_description()
#blue.set_config_timeStamp()




