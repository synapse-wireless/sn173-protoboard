"""sonic_ranger - Use HC-SR04 ultrasonic rangefinder to take distance measurements
Distance to target is measured as pulse width of echo return line: dist = pulse_sec * 340m/sec / 2
Range is 4m, meaning that roundtrip echo response could be up to 24ms in width. Allow 40ms for measurement cycle.
Developed with Synapse SN173 Protoboard.
"""

from SN173 import *
from atmega128rfa1_timers import *
from nv_settings import *

# HC-SR04 pin assignments. Note that two "Input Capture Pins" are connected to the single "ECHO" output
TRIG = 10   # Pad G4
ECHO_1 = 12 # Pad G3, ICP1
ECHO_2 = 23 # Pad C5, ICP3 

# Note: New versions of VM should be re-calibrated to confirm/adjust this offset.
#       This could be auto-cal'd, but left fixed for simplicity here.
ICP_COUNT_OFFSET = 76  # Determined using 'calibration_mode' as described below

# When multiple sonic-rangers are used in close proximity, they have to take turns to avoid 
# audio interference. Total number of sonic-rangers in network controls round robin cycle-rate.
# In this scenario, nodes are assigned node_index between 0 and NUM_SENSORS-1.
NUM_SENSORS = 4
NV_NODE_INDEX = NV_USER_MIN_ID + 0
node_index = None

reply_countdown = 0
trig_countdown = 0

@setHook(HOOK_STARTUP)
def init():
    global node_index
    
    init_nv_settings(1, 0, True, False, False)
    init_hcsr04()
    init_leds()
    init_input_capture()
    
    node_index = loadNvParam(NV_NODE_INDEX)
    if node_index is None:
        node_index = 0
        
    # If we're the "master" node, get the party started.
    if node_index == 0:
        start_trig_countdown()

def init_hcsr04():
    setPinDir(TRIG, True)
    writePin(TRIG, False)
    setPinDir(ECHO_1, False)
    setPinDir(ECHO_2, False)

def init_leds():
    i = 0
    while i < len(LED_TUPLE):
        led = LED_TUPLE[i]
        setPinDir(led, True)
        writePin(led, False)
        i += 1

def init_input_capture():
    # Setup timers as 250kHz free-running counter (assumes 16MHz system clock)
    # Full 16-bit range of count is 262ms, more than enough to cover full distance range of sensor.
    timer_init(TMR1, WGM_NORMAL, CLK_FOSC_DIV64, 0)
    timer_init(TMR3, WGM_NORMAL, CLK_FOSC_DIV64, 0)
    # Use ICP1 to detect leading edge, and ICP3 to detect trailing edge
    set_icp_mode(TMR1, True, True)
    set_icp_mode(TMR3, False, True)

def set_node_index(i):
    """Assign this node an integer index, controlling sequencing of ultrasonic pulses"""
    global node_index
    node_index = i
    saveNvParam(NV_NODE_INDEX, node_index)

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
    global reply_countdown, trig_countdown

    if trig_countdown:
        trig_countdown -= 1
        if trig_countdown == 0:
            start_ranging(True)
            
    if reply_countdown:
        reply_countdown -= 1
        if reply_countdown == 0:
            # Send ranging distance report
            mcastRpc(1, 2, 'dist', node_index, last_dist_meas())
            # If we're the master node, reschedule
            if node_index == 0:
                start_trig_countdown()
                
def dist(index, val):
    """Ranging distance report - use to reschedule trigger"""
    if index == 0:
        # Our countdown is calculated using node=0 as "master" report
        start_trig_countdown()

def start_trig_countdown():
    """Schedule based on node_index, about 50ms apart"""
    global trig_countdown
    i = NUM_SENSORS - 1 if node_index == 0 else node_index - 1
    trig_countdown = (i * 5) + 1

@setHook(HOOK_1S)
def tick1s():
    # Comforting LED blink - pulse LED indicating our node_index
    pulsePin(LED_TUPLE[node_index], 100, True)
