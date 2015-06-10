"""Servo test using pan_tilt code"""

from pan_tilt import *


@setHook(HOOK_STARTUP)
def init():
    pt_init()
    set_position(50, 50)
    enable_servos(True)
    
@setHook(HOOK_10MS)
def tick10ms():
    pt_tick10ms()
    
    