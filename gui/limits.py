
# SPEED  = RPM, ACC= RPM/s
ENCODER_CPR = 16384

MOTOR_VEL_MAX = 3000.0 # in rpm
MOTOR_ACC_MAX = 3000.0

ENC_TO_RPM_CONSTANT = ENCODER_CPR / 60

MOTOR_VEL_MAX_IN_ENC_TYPE = MOTOR_VEL_MAX * ENC_TO_RPM_CONSTANT
MOTOR_ACC_MAX_IN_ENC_TYPE = MOTOR_ACC_MAX * ENC_TO_RPM_CONSTANT

def rpm_to_tick_per_second(rpm:float):
    return rpm*ENCODER_CPR/60

def tick_per_second_to_rpm(tick_per_second:float):
    return tick_per_second*60/ENCODER_CPR

