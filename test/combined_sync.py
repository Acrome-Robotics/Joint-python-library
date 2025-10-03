from acrome_joint.joint import *
from gui.ramp_trajectory import *   # <-- S-Curve Ramp sınıfını kullanacağız

keyword_for_usb = "USB-SERIAL"
port = SerialPort(USB_serial_port(keyword_for_usb), baudrate=921600, timeout=0.01, isTest=False)

joint_0 = Joint(0, port)
joint_1 = Joint(1, port)

joint_0.enable_torque(True)
joint_1.enable_torque(True)


while True:
    sp = float(input("enter the setpoint: "))
    write_sync_to_many(port, Joint._PRODUCT_TYPE, Index_Joint.setpoint_position, [0, sp], [1, sp])