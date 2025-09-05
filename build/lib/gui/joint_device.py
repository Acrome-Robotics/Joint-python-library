from acrome_joint.joint import*

keyword_for_usb = "STMicroelectronics"
port = SerialPort(USB_serial_port(keyword_for_usb), baudrate=921600, timeout=0.01)

Device = Joint(0, port)