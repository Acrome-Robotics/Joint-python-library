from acrome_joint.joint import*

keyword_for_usb = "USB-SERIAL"
altarnate_keyword_for_usb = "USB-Enhanced-SERIAL"
if(not USB_serial_port(keyword_for_usb)):
    if(not USB_serial_port(altarnate_keyword_for_usb)):
        raise Exception("No USB serial port found. Please check your connections.")
    else:
        keyword_for_usb = altarnate_keyword_for_usb

port = SerialPort(USB_serial_port(keyword_for_usb), baudrate=921600, timeout=0.1)


Device = Joint(1, port)
