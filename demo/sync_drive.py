from acrome_joint.joint import*

keyword_for_usb = "USB-SERIAL"
port = SerialPort(USB_serial_port(keyword_for_usb), baudrate=921600, timeout=0.1, isTest=True)

joint_0 = Joint(0, port)
joint_1 = Joint(1, port)
joint_2 = Joint(2, port)
joint_3 = Joint(3, port)

set_joint_variables_sync(port, Index_Joint.Enable, [0, True], [1, True], [2, True], [3, True])

set_joint_variables_sync(port, Index_Joint.setpoint_position, [0, setpoint_0], [1, setpoint_1], [2, setpoint_2], [3, setpoint_3])

joint_0.get_currentStatus_parameters()
joint_1.get_currentStatus_parameters()
joint_2.get_currentStatus_parameters()
joint_3.get_currentStatus_parameters()

