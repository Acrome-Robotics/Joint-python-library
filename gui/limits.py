
# SPEED  = RPM, ACC= RPM/s
ENCODER_CPR = 4096

MOTOR_VEL_MAX = 150.0 # in rpm
MOTOR_ACC_MAX = 500.0


MOTOR_VEL_MAX_IN_ENC_TYPE = MOTOR_VEL_MAX * 68.2666
MOTOR_ACC_MAX_IN_ENC_TYPE = MOTOR_ACC_MAX * 68.2666

def rpm_to_tick_per_second(rpm:float):
    return rpm*ENCODER_CPR/60

def tick_per_second_to_rpm(tick_per_second:float):
    return tick_per_second*60/ENCODER_CPR

