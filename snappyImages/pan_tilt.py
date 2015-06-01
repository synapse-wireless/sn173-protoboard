"""Pan-tilt control for IronMan head

Hardware is an SN173 driving two servos from PWM channels:
  Upper connector (antenna end) is "Tilt" = OC3A, pin E3, I/O 37
  Lower connector is "Pan" = OC0B, pin G5, I/O 4

Servo control:
  Standard servos respond to "pulse position modulation".
  Pulses are sent at 50Hz
  Pulse width controls servo position: 1.5ms is center, +-0.5ms swing either direction

Note:
  Although the pins driving servos are PWM capable, we are using basic I/O functions
  in the script below for simplicity.

"""

from SN173 import *
from synapse.nvparams import *

NV_PAN_LL = NV_USER_MIN_ID + 0
NV_PAN_UL = NV_USER_MIN_ID + 1
NV_PAN_TRIM = NV_USER_MIN_ID + 2
NV_TILT_LL = NV_USER_MIN_ID + 3
NV_TILT_UL = NV_USER_MIN_ID + 4
NV_TILT_TRIM = NV_USER_MIN_ID + 5

# I/O pin definitions
TILT_IO = 4
PAN_IO = 37

servos_enabled = False
boot_countdown = 20  # 100ms tick counts before servos enabled

# TODO: Check why pulsePin(-num) seems to be much less than 1us... New compiler optimization perhaps?
#       Appears that 5000 is about center, corresponding to 1500us
pan_pulse_width = 5000
tilt_pulse_width = 5000
alt20ms = False

drive_pan = None
drive_tilt = None
speed_pan = 0
speed_tilt = 0


# Trim values, thousandths of full-scale (+-)
trim_tilt = 0
trim_pan = 0

# Limits on movement (percent)
pan_ll = 0
pan_ul = 100
tilt_ll = 0
tilt_ul = 100

@setHook(HOOK_STARTUP)
def init():
    setPinDir(LED1, True)
    writePin(LED1, False)
    setPinDir(LED2, True)
    writePin(LED2, False)
    setPinDir(TILT_IO, True)
    writePin(TILT_IO, False)
    setPinDir(PAN_IO, True)
    writePin(PAN_IO, False)
    
    load_limits()
    load_trim()
    
def load_limits():
    global pan_ll, pan_ul, tilt_ll, tilt_ul
    
    lim = loadNvParam(NV_PAN_LL)
    if lim is not None:
        pan_ll = lim
    lim = loadNvParam(NV_PAN_UL)
    if lim is not None:
        pan_ul = lim
    lim = loadNvParam(NV_TILT_LL)
    if lim is not None:
        tilt_ll = lim
    lim = loadNvParam(NV_TILT_UL)
    if lim is not None:
        tilt_ul = lim
        
def load_trim():
    global trim_pan, trim_tilt
        
    trim = loadNvParam(NV_TILT_TRIM)
    if trim is not None:
        trim_tilt = trim
    trim = loadNvParam(NV_PAN_TRIM)
    if trim is not None:
        trim_pan = trim

def set_pan_limits(ll, ul):
    global pan_ll, pan_ul
    pan_ll = ll
    pan_ul = ul
    saveNvParam(NV_PAN_LL, pan_ll)
    saveNvParam(NV_PAN_UL, pan_ul)
    
def set_tilt_limits(ll, ul):
    global tilt_ll, tilt_ul
    tilt_ll = ll
    tilt_ul = ul
    saveNvParam(NV_TILT_LL, tilt_ll)
    saveNvParam(NV_TILT_UL, tilt_ul)
    
def set_pan_trim(val):
    global trim_pan
    trim_pan = val
    saveNvParam(NV_PAN_TRIM, trim_pan)
    
def set_tilt_trim(val):
    global trim_tilt
    trim_tilt = val
    saveNvParam(NV_TILT_TRIM, trim_tilt)
    
    
@setHook(HOOK_1S)
def tick1s():
    pulsePin(LED1, 100, True)
    
@setHook(HOOK_10MS)
def tick10ms():
    global alt20ms
    alt20ms = not alt20ms
    if servos_enabled:
        if alt20ms:
            pulsePin(PAN_IO, -(pan_pulse_width + trim_pan), True)
        else:
            pulsePin(TILT_IO, -(tilt_pulse_width + trim_tilt), True)

@setHook(HOOK_100MS)
def tick100ms():
    global speed_pan, speed_tilt
    global pan_pulse_width, tilt_pulse_width
    global boot_countdown
    
    if boot_countdown:
        boot_countdown -= 1
        pulsePin(LED2, 50, True)
        if boot_countdown == 0:
            enable_servos(True)
    
    # If we're driving, then drive
    if speed_pan:
        pan_pulse_width += speed_pan
        if abs(pan_pulse_width - drive_pan) <= abs(speed_pan):
            pan_pulse_width = drive_pan
            speed_pan = 0
    if speed_tilt:
        tilt_pulse_width += speed_tilt
        if abs(tilt_pulse_width - drive_tilt) <= abs(speed_tilt):
            tilt_pulse_width = drive_tilt
            speed_tilt = 0
    
def abs(val):
    return -val if val < 0 else val

def percent2pulse(pct):
    return 2000 + (pct * 60)

def drive_to(pan, tilt, speed):
    """Drive servos to designated postions at given speed in deg/sec
    """
    global drive_pan, drive_tilt, speed_pan, speed_tilt
    ticks_per_degree = 33

    pan = check_limits(pan, pan_ll, pan_ul)
    tilt = check_limits(tilt, tilt_ll, tilt_ul)

    drive_pan = percent2pulse(pan)
    drive_tilt = percent2pulse(tilt)
    sign = -1 if drive_pan < pan_pulse_width else +1
    speed_pan = sign * (speed * ticks_per_degree) / 10
    sign = -1 if drive_tilt < tilt_pulse_width else +1
    speed_tilt = sign * (speed * ticks_per_degree) / 10
    

def drive_stop():
    """Abort in-progress driving"""
    global speed_pan, speed_tilt
    speed_pan = speed_tilt = 0

def enable_servos(do_enable):
    global servos_enabled
    servos_enabled = do_enable
    
def check_limits(val, ll, ul):
    """Constrain val within upper/lower limits"""
    return ul if val > ul else ll if val < ll else val

def set_pan_direct(val):
    """Diagnostic"""
    global pan_pulse_width
    pan_pulse_width = val

def set_position(pan, tilt):
    """Set immediate position of pan/tilt servos"""
    global pan_pulse_width, tilt_pulse_width
    
    pan = check_limits(pan, pan_ll, pan_ul)
    tilt = check_limits(tilt, tilt_ll, tilt_ul)
    
    # Note: 1.5ms calculations replaced with center=5000 +- 3000
    pan_pulse_width = 2000 + (pan * 60)
    tilt_pulse_width = 2000 + (tilt * 60)
    #pan_pulse_width = 1000 + (pan * 10)
    #tilt_pulse_width = 1000 + (tilt * 10)

    # Blink LED to show activity
    pulsePin(LED2, 50, True)
    
def dump_state():
    print "pan_trim=", trim_pan
    print "tilt_trim=", trim_tilt
    print "cur_pan=", pan_pulse_width
    print "cur_tilt=", tilt_pulse_width
    
    