from acrome_joint.joint import*

port = SerialPort("COM14", baudrate=921600, timeout=0.01)

Device = Joint(0, port)