# Copyright (C) 2015 Synapse Wireless, Inc.
# Subject to your agreement of the disclaimer set forth below, permission is given by Synapse Wireless, Inc. ("Synapse") to you to freely modify, redistribute or include this SNAPpy code in any program. The purpose of this code is to help you understand and learn about SNAPpy by code examples.
# BY USING ALL OR ANY PORTION OF THIS SNAPPY CODE, YOU ACCEPT AND AGREE TO THE BELOW DISCLAIMER. If you do not accept or agree to the below disclaimer, then you may not use, modify, or distribute this SNAPpy code.
# THE CODE IS PROVIDED UNDER THIS LICENSE ON AN "AS IS" BASIS, WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING, WITHOUT LIMITATION, WARRANTIES THAT THE COVERED CODE IS FREE OF DEFECTS, MERCHANTABLE, FIT FOR A PARTICULAR PURPOSE OR NON-INFRINGING. THE ENTIRE RISK AS TO THE QUALITY AND PERFORMANCE OF THE COVERED CODE IS WITH YOU. SHOULD ANY COVERED CODE PROVE DEFECTIVE IN ANY RESPECT, YOU (NOT THE INITIAL DEVELOPER OR ANY OTHER CONTRIBUTOR) ASSUME THE COST OF ANY NECESSARY SERVICING, REPAIR OR CORRECTION. UNDER NO CIRCUMSTANCES WILL SYNAPSE BE LIABLE TO YOU, OR ANY OTHER PERSON OR ENTITY, FOR ANY LOSS OF USE, REVENUE OR PROFIT, LOST OR DAMAGED DATA, OR OTHER COMMERCIAL OR ECONOMIC LOSS OR FOR ANY DAMAGES WHATSOEVER RELATED TO YOUR USE OR RELIANCE UPON THE SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGES OR IF SUCH DAMAGES ARE FORESEEABLE. THIS DISCLAIMER OF WARRANTY AND LIABILITY CONSTITUTES AN ESSENTIAL PART OF THIS LICENSE. NO USE OF ANY COVERED CODE IS AUTHORIZED HEREUNDER EXCEPT UNDER THIS DISCLAIMER.

'''SNAPpy LED Pulse-width Modulation Demo
    Sample SNAPpy script to demonstrate one method of setting up and using the PWM capability.
    This script is intended to be used with the SN173 evaluation boards.
'''
from atmega128rfa1_timers import *
from SN173 import *

# Run start-up function
@setHook(HOOK_STARTUP)
def start_up():
    # Set pin direction as output
    setPinDir(LED1, True)
    
    # Set pin state
    writePin(LED1, False)

    # Initialize timer1 with TOP = ICR, frequency = 16Mhz/64 = 250kHz
    timer_init(TMR1, WGM_FASTPWM16_TOP_ICR, CLK2_FOSC_DIV64, 1000)
    
    # Initialize OC1A to toggle output
    set_tmr_output(TMR1, OCRxB, TMR_OUTP_CLR)
    setPinDir(LED1, True)
    
    
def led_duty_cycle(val):
    """ Control duty cycle by adjusting OCR1A from 0 - 1000 """
    set_tmr_ocr(TMR1, OCRxB, val)