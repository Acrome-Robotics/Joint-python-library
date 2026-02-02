from acrome_joint.joint import*

keyword_for_usb = "USB-SERIAL"
port = SerialPort(USB_serial_port(keyword_for_usb), baudrate=921600, timeout=0.1, isTest=False)

joint_0 = Joint(0, port)
joint_1 = Joint(1, port)
joint_2 = Joint(2, port)

joint_0.enter_configuration()
joint_1.enter_configuration()
joint_2.enter_configuration()

joint_0.reset_absolute_encoder()
joint_1.reset_absolute_encoder()
joint_2.reset_absolute_encoder()

