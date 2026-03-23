from acrome_joint.joint import*
from servo import ServoSurucu


keyword_for_usb = "USB-SERIAL"
port = SerialPort(USB_serial_port(keyword_for_usb), baudrate=921600, timeout=0.1, isTest=True)

joint_0 = Joint(0, port)
joint_1 = Joint(1, port)


set_joint_variables_sync(port, Index_Joint.Enable, [0, 1], [1, 1])



