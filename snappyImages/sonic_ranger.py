"""sonic_ranger - Use HC-SR04 ultrasonic rangefinder to take distance measurements
Distance to target is measured as pulse width of echo return line: dist = pulse_sec * 340m/sec / 2
Range is 4m, meaning that roundtrip echo response could be up to 24ms in width. Allow 40ms for measurement cycle.
Developed with SN173 Protoboard
"""

from SN173 import *
from atmega128rfa1_timers import *

# HC-SR04 pin assignments. Note that two "Input Capture Pins" are connected to the single "ECHO" output
TRIG = 10   # Pad G4
ECHO_1 = 12 # Pad G3, ICP1
ECHO_2 = 23 # Pad C5, ICP3 

# Note: New versions of VM should be re-calibrated to confirm/adjust this offset.
#       This could be auto-cal'd, but left fixed for simplicity here.
ICP_COUNT_OFFSET = 76  # Determined using 'calibration_mode' as described below

reply_countdown = 0

@setHook(HOOK_STARTUP)
def init():
    setPinDir(TRIG, True)
    writePin(TRIG, False)
    setPinDir(ECHO_1, False)
    setPinDir(ECHO_2, False)
    
    setPinDir(LED1, True)
    writePin(LED1, False)
    setPinDir(LED2, True)
    writePin(LED2, False)

    init_input_capture()

def init_input_capture():
    # Setup timers as 250kHz free-running counter (assumes 16MHz system clock)
    # Full 16-bit range of count is 262ms, more than enough to cover full distance range of sensor.
    timer_init(TMR1, WGM_NORMAL, CLK_FOSC_DIV64, 0)
    timer_init(TMR3, WGM_NORMAL, CLK_FOSC_DIV64, 0)
    # Use ICP1 to detect leading edge, and ICP3 to detect trailing edge
    set_icp_mode(TMR1, True, True)
    set_icp_mode(TMR3, False, True)

def trig():
    pulsePin(TRIG, -100, True)
    
def calibration_mode(do_enable):
    """Allows measuring offset count between clearing the two ICP counters.
       After entering this mode, ranging measurements reflect this fixed offset.
    """
    if do_enable:
        # Configure both capture inputs for rising edge
        set_icp_mode(TMR3, True, True)
    else:
        # Restore normal config
        init_input_capture()
    
def start_ranging(do_reply):
    """Begin ranging operation. Should complete within 20ms"""
    global reply_countdown
    
    # Clear both counters. The time delta between the next two lines of code determines the calibration offset needed.
    set_tmr_count(TMR1, 0)
    set_tmr_count(TMR3, 0)
    trig()
    
    if do_reply:
        # Wait until N ticks (x10ms) then send measurement reply
        reply_countdown = 4

def dump_icp_vals():
    """Show the raw input capture values from last ranging operation"""
    icp1 = get_icp_val(TMR1)
    icp3 = get_icp_val(TMR3)
    print "icp1=", icp1
    print "icp3=", icp3
    print "diff=", icp3 - icp1

def last_dist_meas():
    """Return distance measurement in inches"""
    counts_per_inch = 37  # 250000 * (0.0254/340) * 2 = 37.353
    icp1 = get_icp_val(TMR1) - ICP_COUNT_OFFSET
    icp3 = get_icp_val(TMR3)
    diff = icp3 - icp1
    return diff / 37
    

@setHook(HOOK_10MS)
def tick10ms():
    global reply_countdown

    if reply_countdown:
        reply_countdown -= 1
        if reply_countdown == 0:
            mcastRpc(1, 2, 'dist', last_dist_meas())


@setHook(HOOK_100MS)
def tick100ms():
    start_ranging(True)

@setHook(HOOK_1S)
def tick1s():
    # Comforting LED blink
    pulsePin(LED1, 100, True)
