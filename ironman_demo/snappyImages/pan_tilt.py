"""Pan-tilt control for IronMan head

Hardware is an SN173 driving two servos from PWM channels:
  Upper connector (antenna end) is "Tilt" = OC2A, pin E3, I/O 4
  Lower connector is "Pan" = OC0B, pin G5, I/O 37

Servo control:
  Standard servos respond to "pulse position modulation".
  Pulses are sent at 50Hz
  Pulse width controls servo position: 1.5ms is center, +-0.5ms swing either direction
"""

from SN173 import *
from atmega128rfa1_timers import *
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

# Pulse widths in microseconds
pan_pulse_width = 1500
tilt_pulse_width = 1500
servos_enabled = False
alt20ms = False  # Toggle to create 50Hz one-shot pulse rate

# Current "driving" state
drive_pan = None
drive_tilt = None
speed_pan = 0
speed_tilt = 0

# Trim values, thousandths of full-scale (+-)
trim_tilt = 0
trim_pan = 0

# Limits on movement (percent)
pan_ll = -100
pan_ul = 200
tilt_ll = -100
tilt_ul = 200

# Calculated Atmel timer count for one-shot
tmr0_oneshot_trig = 0

def pt_init():
    """Initialize pan_tilt controller"""
    setPinDir(TILT_IO, True)
    writePin(TILT_IO, False)
    setPinDir(PAN_IO, True)
    writePin(PAN_IO, False)
    init_timers()
    load_limits()
    load_trim()
    
def drive_to(pan, tilt, speed):
    """Drive servos to designated postions at given speed in deg/sec
    """
    global drive_pan, drive_tilt, speed_pan, speed_tilt
    ticks_per_degree = 33  # pulse_width delta per degree = 6000/180

    #print "drive_to(", pan, ",",tilt,")"

    pan = check_limits(pan, pan_ll, pan_ul)
    tilt = check_limits(tilt, tilt_ll, tilt_ul)

    # Scale speed (in pulse-width units) for 10ms timer
    speed_ticks = (speed * ticks_per_degree) / 100
    if speed_ticks == 0:
        # Ensure some motion
        speed_ticks = 1

    drive_pan = percent2pulse(pan)
    drive_tilt = percent2pulse(tilt)
    sign = -1 if drive_pan < pan_pulse_width else +1
    speed_pan = sign * speed_ticks
    sign = -1 if drive_tilt < tilt_pulse_width else +1
    speed_tilt = sign * speed_ticks

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
    
def set_position(pan, tilt):
    """Set immediate position of pan/tilt servos"""
    global pan_pulse_width, tilt_pulse_width
    
    pan = check_limits(pan, pan_ll, pan_ul)
    tilt = check_limits(tilt, tilt_ll, tilt_ul)
    
    pan_pulse_width = percent2pulse(pan)
    tilt_pulse_width = percent2pulse(tilt)
    set_pulsewidths()

def dump_state():
    print "pan_trim=", trim_pan
    print "tilt_trim=", trim_tilt
    print "cur_pan=", pan_pulse_width
    print "cur_tilt=", tilt_pulse_width
    
def init_timers():
    """Initialize Atmega timers used for precision servo pulse timing"""
    # Timer0 is only 8-bits, so we are going with "one-shot" mode rather than PWM in order to get better resolution
    # of pulse widths at <100Hz pulse rate.
    # Use CLK_FOSC_DIV256 for a clock freq of 16M/256, yeilding a 16us tick. With 8-bit counters that gives 4.096ms 
    # of pulse-width range.
    timer8_init(TMR0, WGM0_FASTPWM8_TOP_OCRA, CLK_FOSC_DIV256)  # 16us period
    set_tmr8_output(TMR0, OCR0B, TMR_OUTP_SET)   # Set on match
    set_tmr8_ocr(TMR0, OCR0A, 0)                 # Top=Bottom (one-shot mode)
    
    # Timer2 is also 8-bits, but it runs from the 32kHz crystal.  We can't use the one-shot technique, since our
    # output pin is driven by OC2A, meaning we lack independent control of TOP/MATCH values. Instead, we'll use a normal
    # PWM mode at the direct 32kHz rate, with 8-bit overflow yeilding a 125Hz pulse rate to the servos. Higher than
    # the target 50Hz, but with better pulse-resolution than if we went with DIV2 prescale for 62.5Hz rate.
    timer8_init(TMR2, WGM0_FASTPWM8, CLK2_FOSC)
    set_tmr8_output(TMR2, OCR0A, TMR_OUTP_SET)   # Set on match
    
def set_pulsewidths():
    """Calculate and set counter-match values based on desired pulsewidths"""
    global tmr0_oneshot_trig

    # Trigger value for oneshot timer, given 16us per tick.
    # This is one count below the counter 'match' setting which determines actual pulsewidth.
    tmr0_oneshot_trig = -1 - pan_pulse_width / 16
    set_tmr8_ocr(TMR0, OCR0B, tmr0_oneshot_trig + 1)

    # Timer2 is set to 31us per tick. Negative width yeilds counts high prior to 0xFFFF.
    tmr2_match = -tilt_pulse_width / 31
    set_tmr8_ocr(TMR2, OCR0A, tmr2_match)
    
def fire_oneshots():
    # Generate pulse, by setting count just below match (will end at overflow)
    set_tmr8_count(TMR0, tmr0_oneshot_trig)

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

def pt_tick10ms():
    """Call this from 10ms timer hook"""
    global alt20ms
    alt20ms = not alt20ms
    if servos_enabled:
        go_drive()
        
        # Fire one-shot servo controls at 50Hz rate
        if alt20ms:
            fire_oneshots()

def go_drive():
    global speed_pan, speed_tilt
    global pan_pulse_width, tilt_pulse_width
    pulse_changed = False
    
    # If we're driving, then drive
    if speed_pan:
        pulse_changed = True
        pan_pulse_width += speed_pan
        if abs(pan_pulse_width - drive_pan) <= abs(speed_pan):
            pan_pulse_width = drive_pan
            speed_pan = 0
    if speed_tilt:
        pulse_changed = True
        tilt_pulse_width += speed_tilt
        if abs(tilt_pulse_width - drive_tilt) <= abs(speed_tilt):
            tilt_pulse_width = drive_tilt
            speed_tilt = 0
    
    if pulse_changed:
        set_pulsewidths()
    
def abs(val):
    return -val if val < 0 else val

def percent2pulse(pct):
    """Convert 0-100% into 1000-2000us"""
    return 1000 + (pct * 10)

def is_driving():
    return speed_tilt or speed_pan

def drive_stop():
    """Abort in-progress driving"""
    global speed_pan, speed_tilt
    speed_pan = speed_tilt = 0

def enable_servos(do_enable):
    """Stop pulsing the servos, allowing them to relax"""
    global servos_enabled
    servos_enabled = do_enable
    
    if do_enable:
        set_tmr8_output(TMR2, OCR0A, TMR_OUTP_SET)
    else:
        set_tmr8_output(TMR2, OCR0A, TMR_OUTP_OFF)
    
def check_limits(val, ll, ul):
    """Constrain val within upper/lower limits"""
    return ul if val > ul else ll if val < ll else val

def set_direct(pan, tilt):
    """Diagnostic"""
    global pan_pulse_width, tilt_pulse_width
    pan_pulse_width = pan
    tilt_pulse_width = tilt
    set_pulsewidths()

