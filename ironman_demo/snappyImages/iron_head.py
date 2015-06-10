"""iron_head - Animatronic Iron Man head, controlled by Synapse SN173 protoboard"""

from pan_tilt import *

# 100ms tick count intervals
boot_countdown = 20   # before servos enabled
SENSOR_CHECK_INTERVAL = 2
sensor_check_cnt = SENSOR_CHECK_INTERVAL
AVG_RESET_INTERVAL = 10
avg_reset_cnt = AVG_RESET_INTERVAL

idle_count = 0  # Number of SENSOR_CHECK_INTERVALs with no activity
sleep_requested = False

# Pan/Tilt positions (percent, where 50% is theoretical center)
TILT_LEVEL = 70   # Note: servo assy 2 has level=15
TILT_DOWN = 140
TILT_UP = 40
PAN_CENTER = 40
PAN_RIGHT = -25
PAN_LEFT = 125

# Max distance (inches) to attract iron_head
SENSE_DISTANCE = 36
SENSOR_LOCS = ((-20, 70),  # Sensor 0 pan,tilt
               (20, 70),  # Sensor 1 pan,tilt  
               (60, 70),  # Sensor 2 pan,tilt
               (110, 70))  # Sensor 3 pan,tilt

sensor_drive_speed = 40

@setHook(HOOK_STARTUP)
def init():
    # Initialize pan/tilt assy, and LEDs
    pt_init()
    init_leds()
    
    # Reset distance accumulator
    accum_dist(0, 0, True)
    
def sleep_head(do_sleep):
    """Move to resting position, and relax servos"""
    global sleep_requested
    # Defer disabling servos till finished driving
    sleep_requested = do_sleep
    
    if do_sleep:
        drive_to(PAN_CENTER, TILT_DOWN, 10)
    else:
        enable_servos(True)

@setHook(HOOK_10MS)
def tick10ms():
    pt_tick10ms()
    
def init_leds():
    i = 0
    while i < len(LED_TUPLE):
        led = LED_TUPLE[i]
        setPinDir(led, True)
        writePin(led, False)
        i += 1

@setHook(HOOK_1S)
def tick1s():
    # Comforting LED blink
    pulsePin(LED1, 100, True)

@setHook(HOOK_100MS)
def tick100ms():    
    global boot_countdown, sleep_requested, sensor_check_cnt, avg_reset_cnt

    if sensor_check_cnt:
        sensor_check_cnt -= 1
        if not sensor_check_cnt:
            sensor_check_cnt = SENSOR_CHECK_INTERVAL
            check_sensors()

    if avg_reset_cnt:
        avg_reset_cnt -= 1
        if not avg_reset_cnt:
            avg_reset_cnt = AVG_RESET_INTERVAL
            accum_dist(0, 0, True)

    if sleep_requested and not is_driving():
        enable_servos(False)
        sleep_requested = False
    
    if boot_countdown:
        boot_countdown -= 1
        pulsePin(LED2, 50, True)
        if boot_countdown == 0:
            enable_servos(True)

def dist(index, val):
    """RPC call-in from distance sensors"""
    if val < SENSE_DISTANCE:
        accum_dist(index, val, False)

def min_avg(index, sum, num):
    """Adjust current sensor minimum-distance avg/index"""
    global min_val, min_index
    if num > 0:
        avg = sum / num
        if avg < min_val:
            min_val = avg
            min_index = index

def check_sensors():
    """Check sensor readings, and react accordingly"""
    global min_val, min_index, idle_count
    min_val = 30000
    min_index = None
    min_avg(0, sum0, num0)
    min_avg(1, sum1, num1)
    min_avg(2, sum2, num2)
    min_avg(3, sum3, num3)
    
    if min_index is not None:
        idle_count = 0
        sleep_head(False)
        print "Min index=", min_index, " avg=", min_val
        sensor = SENSOR_LOCS[min_index]
        drive_to(sensor[0], sensor[1], sensor_drive_speed)
    else:
        if is_driving():
            return
        
        # While idle, execute "seek" sequence, then sleep
        idle_count += 1
        if idle_count == 8:
            print "idle: center1"
            drive_to(PAN_CENTER, TILT_LEVEL, 20)
        elif idle_count == 30:
            print "idle: left-up"
            drive_to(PAN_LEFT, TILT_UP, 20)
        elif idle_count == 40:
            print "idle: right-up"
            drive_to(PAN_RIGHT, TILT_UP, 20)
        elif idle_count == 60:
            print "idle: center2"
            drive_to(PAN_CENTER, TILT_LEVEL, 20)
        elif idle_count == 80:
            print "idle: sleep"
            sleep_head(True)
        
def accum_dist(index, val, reset):
    global sum0, sum1, sum2, sum3
    global num0, num1, num2, num3
    
    if reset:
        sum0 = sum1 = sum2 = sum3 = 0
        num0 = num1 = num2 = num3 = 0
        return

    if index == 0:
        sum0 += val
        num0 += 1
    elif index == 1:
        sum1 += val
        num1 += 1
    elif index == 2:
        sum2 += val
        num2 += 1
    elif index == 3:
        sum3 += val
        num3 += 1

