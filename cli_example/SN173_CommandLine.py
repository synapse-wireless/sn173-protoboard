# Copyright (C) 2015 Synapse Wireless, Inc.
# Subject to your agreement of the disclaimer set forth below, permission is given by Synapse Wireless, Inc. ("Synapse") to you to freely modify, redistribute or include this SNAPpy code in any program. The purpose of this code is to help you understand and learn about SNAPpy by code examples.
# BY USING ALL OR ANY PORTION OF THIS SNAPPY CODE, YOU ACCEPT AND AGREE TO THE BELOW DISCLAIMER. If you do not accept or agree to the below disclaimer, then you may not use, modify, or distribute this SNAPpy code.
# THE CODE IS PROVIDED UNDER THIS LICENSE ON AN "AS IS" BASIS, WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING, WITHOUT LIMITATION, WARRANTIES THAT THE COVERED CODE IS FREE OF DEFECTS, MERCHANTABLE, FIT FOR A PARTICULAR PURPOSE OR NON-INFRINGING. THE ENTIRE RISK AS TO THE QUALITY AND PERFORMANCE OF THE COVERED CODE IS WITH YOU. SHOULD ANY COVERED CODE PROVE DEFECTIVE IN ANY RESPECT, YOU (NOT THE INITIAL DEVELOPER OR ANY OTHER CONTRIBUTOR) ASSUME THE COST OF ANY NECESSARY SERVICING, REPAIR OR CORRECTION. UNDER NO CIRCUMSTANCES WILL SYNAPSE BE LIABLE TO YOU, OR ANY OTHER PERSON OR ENTITY, FOR ANY LOSS OF USE, REVENUE OR PROFIT, LOST OR DAMAGED DATA, OR OTHER COMMERCIAL OR ECONOMIC LOSS OR FOR ANY DAMAGES WHATSOEVER RELATED TO YOUR USE OR RELIANCE UPON THE SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGES OR IF SUCH DAMAGES ARE FORESEEABLE. THIS DISCLAIMER OF WARRANTY AND LIABILITY CONSTITUTES AN ESSENTIAL PART OF THIS LICENSE. NO USE OF ANY COVERED CODE IS AUTHORIZED HEREUNDER EXCEPT UNDER THIS DISCLAIMER.

'''SNAPpy Command Line Demo
    Sample SNAPpy script to demonstrate one method of implementing a simple command line interface.
    This script is intended to be used with the SN173 evaluation boards.
    Connect a virtual com port and open a connection at 38,400 baud, N,8,1.
    
    NOTE:  This script captures UART0 for the CLI.
'''

from synapse.switchboard import *
from synapse.sysInfo import *
from SN173 import *
from AtmelTemperature import *

@setHook(HOOK_STARTUP)
def start_up():
    crossConnect(DS_STDIO, DS_UART0)
    initUart(0, 38400)
    stdinMode(0, True)      # Line Mode, Echo On
    flowControl(0, False)

    stdin_event('?')
 
@setHook(HOOK_STDIN)    
def stdin_event(data):
    ''' Process command line input '''
    global cmd, arg

    if data == '?':
        help()
    elif data[0:4] == 'echo':
        print
        echo(data[5:])
    elif len(data):
        ret = None
        print
        
        # Parse string for function and arguments
        ret = str_to_rpc(data)
        
        if ret != None:
            print " => ", ret
            
    print "\r\n>",

#----- The following are some simple functions for us to easily invoke from CLI -----

def help():
    print "\r\nThis sample CLI can call any SNAPpy function."
    print "Enter a function name [' ' + optional argument] [' ' + optional argument]"
    print
    print "Example: 'led 1 1' will turn on LED1"

def ver():
    print "SNAP v", getInfo(SI_TYPE_VERSION_MAJOR), '.', getInfo(SI_TYPE_VERSION_MINOR), '.', getInfo(SI_TYPE_VERSION_BUILD),
    if getInfo(8) == 1:
        print " with AES-128"
    #print "Device Type: ", deviceType
    
def led(led, pinState):
    # There is no LED0 so let's subtract 1 from led
    led = int(led) - 1
    setPinDir(LED_TUPLE[led], True)
    writePin(LED_TUPLE[led], int(pinState))

def echo(text):
    print text
    
def temperature():
    degC = read_internal_temp()/10
    tenthsC = read_internal_temp()%10
    print degC, '.',tenthsC, ' degrees C'

# String parser
def str_to_rpc(string):
    i = 0
    func = ''
    a1 = ''
    a2 = ''
    arg_status = 0
    while i < len(string):
        strEnd = 0
        if string[i] == ' ' or i == len(string)-1:
            if i == len(string)-1:
                strEnd = 1
            if func  == '':
                func = string[:i+strEnd]
                string = string[i+1:]
                i = 0
            elif a1  == '':
                a1 = string[:i+strEnd]
                string = string[i+1:]
                arg_status += 1
                i = 0
            elif a2  == '':
                a2 = string[:i+strEnd]
                string = string[i+1:]
                arg_status += 1
                i = 0
        else:
            i+=1
    if arg_status == 0:
        retval = func()
    elif arg_status == 1:
        retval = func(a1)
    elif arg_status == 2:
        retval = func(a1,a2)
    return retval