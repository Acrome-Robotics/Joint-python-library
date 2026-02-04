from acrome_joint.joint import*
from servo import ServoSurucu

motor = ServoSurucu(port='COM9')

keyword_for_usb = "USB-SERIAL"
port = SerialPort(USB_serial_port(keyword_for_usb), baudrate=921600, timeout=0.1, isTest=False)

joint_0 = Joint(0, port)
joint_1 = Joint(1, port)
joint_2 = Joint(2, port)

joint_0.enter_operation()
joint_1.enter_operation()
joint_2.enter_operation()


#joint_0.set_variables([Index_Joint.setpoint_position, 180.0])
#joint_1.set_variables([Index_Joint.setpoint_position, 180.0])
#joint_2.set_variables([Index_Joint.setpoint_position, 180.0])
#joint_0.set_variables([Index_Joint.setpoint_position, 180.0])
#joint_1.set_variables([Index_Joint.setpoint_position, 180.0])
#joint_2.set_variables([Index_Joint.setpoint_position, 180.0])

input("Press Enter to continue...")

joint_0.enable_torque(True)
joint_1.enable_torque(True)
joint_2.enable_torque(True)

location_0 = [180.0, 180.0, 180.0]
location_1 = [180.0, 260.0, 140]
location_2 = [45.0, 180.0, 180.0] #
location_3 = [45.0, 260.0, 135.0] # 
location_4 = [220.0, 270.0, 180.0]
location_5 = [160.0, 110.0, 180.0]

locations = [location_0, location_1, location_2, location_3, location_4, location_5]

while True:
    location_type = int(input("enter the location: "))
    if(location_type == 9):
        motor.aci_gonder(120)
        continue
    if(location_type == 8):
        motor.aci_gonder(20)
        continue
    if (location_type != 0) and (location_type != 1) and (location_type != 2) and (location_type != 3) and (location_type != 4) and (location_type != 5):
        print("invalid location type")
        continue

    
    joint_0.set_variables([Index_Joint.setpoint_position, locations[location_type][0]])
    joint_1.set_variables([Index_Joint.setpoint_position, locations[location_type][1]])
    joint_2.set_variables([Index_Joint.setpoint_position, locations[location_type][2]])
    joint_0.set_variables([Index_Joint.setpoint_position, locations[location_type][0]])
    joint_1.set_variables([Index_Joint.setpoint_position, locations[location_type][1]])
    joint_2.set_variables([Index_Joint.setpoint_position, locations[location_type][2]])

    

motor.kapat()

    #set_joint_variables_sync(port, Index_Joint.setpoint_position, [0, locations[location_type][0]], [1, locations[location_type][1]], [2, locations[location_type][2]])


