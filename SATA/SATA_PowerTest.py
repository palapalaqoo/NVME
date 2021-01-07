'''
Created on Dec 18, 2020

@author: root
'''

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Import python built-ins
import sys
import re
from time import sleep
from random import randint
import threading


# Import VCT modules
from lib_sata.SATA import SATA_c


def ParserPS(PS):
    if PS == 0x0:
        mStr = "00h Device is in the PM2:Standby state or Device is in the PM2:Standby state and the"\
        "Extended Power Conditions feature set is supported and enabled, and the device is"\
        "in the Standby_z power condition."
    elif PS == 0x1:
        mStr = "01h Device is in the PM2:Standby state and the Extended Power Conditions feature set is"\
        "supported and enabled, and the device is in the Standby_y power condition."
    elif PS == 0x40: 
        mStr = "40h Device is in the PM0:Active state, and the NV Cache power mode is enabled and the"\
        "spindle is spun down or spinning down."
    elif PS == 0x41:
        mStr = "41h Device is in the PM0:Active state and the NV Cache power mode is enabled and the"\
        "spindle is spun up or spinning up."
    elif PS == 0x80:
        mStr = "80h Device is in the PM1:Idle state and Extended Power Conditions feature set is not"\
        "supported or not enabled."
    elif PS == 0x81:
        mStr = "81h Device is in the PM1:Idle State, and Extended Power Conditions feature set is"\
        "supported and enabled, and the device is in the Idle_a power condition."
    elif PS == 0x82:
        mStr = "82h Device is in the PM1:Idle State, and Extended Power Conditions feature set is"\
        "supported and enabled, and the device is in the Idle_b power condition."
    elif PS == 0x83:
        mStr = "83h Device is in the PM1:Idle State, and Extended Power Conditions feature set is"\
        "supported and enabled, and the device is in the Idle_c power condition."
    elif PS == 0xFF:        
        mStr = "FFh Device is in the PM0:Active state or PM1:Idle State."
    else:
        mStr = "undefined(%s)"%PS
    return mStr

def VerifyPS(msg, cmd, expectMsg=None, expectList=None):
    sleep(0.1)    
    print ""
    CMD = cmd
    print msg
    print "cmd: %s"%CMD
    rt = Inst.ata_cmd(CMD)
    if rt.Error!=0:
        print "Error in ATA Descriptor Return is not 0x0"
        print rt.CmdRtStr
        rtCode = 1
        sys.exit(rtCode)     
    
    if expectMsg!=None and expectList!=None:
        print "Check Power Mode Normal Output"    
        print ParserPS(rt.SecotrCount)                
        print expectMsg
        if rt.SecotrCount in expectList:
            print "pass"
        else:
            print "fail"
            rtCode = 1
            sys.exit(rtCode) 
            
    return rt



# start ---------------------------------------------------------------------
rtCode = 0
Inst = SATA_c(sys.argv)

print "Device: %s"%Inst.dev

print ""

print "Power test"

print "== prcondition ====================================="
msg = "Issue cmd to make current power status to active state"
cmd = "sg_raw -v  %s  85 6 20 0 0 0 0 0 0 0 0 0 0 40 e5 0"%Inst.dev
expectMsg=None
expectList=None
VerifyPS(msg, cmd, expectMsg, expectList)

msg = "Issue cmd to check current power status"
cmd = "sg_raw -v  %s  85 6 20 0 0 0 0 0 0 0 0 0 0 40 e5 0 -R"%Inst.dev
expectMsg="expect current is active mode(0xFF)"
expectList=[0xFF]
VerifyPS(msg, cmd, expectMsg, expectList)

print "== STANDBY IMMEDIATE - E0h, Non-Data ====================================="
print "This command causes the device to immediately enter the Standby mode."

msg = "Issue cmd 'standby immediate'"
cmd = "sg_raw -v  %s  85 6 20 0 0 0 0 0 0 0 0 0 0 40 e0 0 -R"%Inst.dev
expectMsg=None
expectList=None
VerifyPS(msg, cmd, expectMsg, expectList)

msg = "Issue cmd to check current power status"
cmd = "sg_raw -v  %s  85 6 20 0 0 0 0 0 0 0 0 0 0 40 e5 0 -R"%Inst.dev
expectMsg="Check if Power Mode = standby or not, i.e. 00h/01h"
expectList=[0x0, 0x1]
VerifyPS(msg, cmd, expectMsg, expectList)

print "== STANDBY - E2h, Non-Data ====================================="
print "This command causes the device to enter the Standby mode."
msg = "Issue cmd to set standby timer after 5s "
cmd = "sg_raw -v  %s  85 6 20 0 0 0 1 0 0 0 0 0 0 40 e2 0"%Inst.dev
expectMsg=None
expectList=None
VerifyPS(msg, cmd, expectMsg, expectList)

msg = "Issue cmd to make current power status to active state"
cmd = "sg_raw -v  %s  85 6 20 0 0 0 0 0 0 0 0 0 0 40 e5 0"%Inst.dev
expectMsg=None
expectList=None
VerifyPS(msg, cmd, expectMsg, expectList)

msg = "Issue cmd to check current power status"
cmd = "sg_raw -v  %s  85 6 20 0 0 0 0 0 0 0 0 0 0 40 e5 0 -R"%Inst.dev
expectMsg="expect current is active mode(0xFF)"
expectList=[0xFF]
VerifyPS(msg, cmd, expectMsg, expectList)


print ""
print "sleep 7s"
sleep(7)

print ""
print "check if device enter the Standby mode after 7 second"
msg = "Issue cmd to check current power status"
cmd = "sg_raw -v  %s  85 6 20 0 0 0 0 0 0 0 0 0 0 40 e5 0 -R"%Inst.dev
expectMsg="Check if Power Mode = standby or not, i.e. 00h/01h"
expectList=[0x0, 0x1]
VerifyPS(msg, cmd, expectMsg, expectList)

msg = "Issue cmd to disable standby timer"
cmd = "sg_raw -v  %s  85 6 20 0 0 0 0 0 0 0 0 0 0 40 e2 0"%Inst.dev
expectMsg=None
expectList=None
VerifyPS(msg, cmd, expectMsg, expectList)


print ""
print "sleep 7s"
sleep(7)

print ""
print "check if device is active after 7 second"
msg = "Issue cmd to check current power status"
cmd = "sg_raw -v  %s  85 6 20 0 0 0 0 0 0 0 0 0 0 40 e5 0 -R"%Inst.dev
expectMsg="expect current is active mode(0xFF)"
expectList=[0xFF]
VerifyPS(msg, cmd, expectMsg, expectList)


# // idle immediate
print "== IDLE IMMEDIATE - E1h, Non-Data ====================================="
print "The IDLE IMMEDIATE command allows the host to immediately place the device in the Idle mode."
msg = "Issue idle immediate cmd"
cmd = "sg_raw -v  %s  85 6 20 0 0 0 0 0 0 0 0 0 0 40 e1 0 -R"%Inst.dev
expectMsg=None
expectList=None
VerifyPS(msg, cmd, expectMsg, expectList)

print ""
print "check if device is in idle mode"
msg = "Issue cmd to check current power status"
cmd = "sg_raw -v  %s  85 6 20 0 0 0 0 0 0 0 0 0 0 40 e5 0 -R"%Inst.dev
expectMsg="expect current is idle mode([0x80, 0x81, 0x82, 0x83])"
expectList=[0x80, 0x81, 0x82, 0x83]
VerifyPS(msg, cmd, expectMsg, expectList)

msg = "Issue cmd to make current power status to active state"
cmd = "sg_raw -v  %s  85 6 20 0 0 0 0 0 0 0 0 0 0 40 e5 0"%Inst.dev
expectMsg=None
expectList=None
VerifyPS(msg, cmd, expectMsg, expectList)

msg = "Issue cmd to check current power status"
cmd = "sg_raw -v  %s  85 6 20 0 0 0 0 0 0 0 0 0 0 40 e5 0 -R"%Inst.dev
expectMsg="expect current is active mode(0xFF)"
expectList=[0xFF]
VerifyPS(msg, cmd, expectMsg, expectList)

print "== IDLE - E3h, Non-Data ====================================="
print "The IDLE command allows the host to place the device in the Idle mode and also set the Standby timer."
msg = "Issue idle cmd and set Standby timer = 5s"
cmd = "sg_raw -v  %s  85 6 20 0 0 0 1 0 0 0 0 0 0 40 e3 0 -R"%Inst.dev
expectMsg=None
expectList=None
VerifyPS(msg, cmd, expectMsg, expectList)

print ""
print "check if device is in idle mode"
msg = "Issue cmd to check current power status"
cmd = "sg_raw -v  %s  85 6 20 0 0 0 0 0 0 0 0 0 0 40 e5 0 -R"%Inst.dev
expectMsg="expect current is idle mode([0x80, 0x81, 0x82, 0x83])"
expectList=[0x80, 0x81, 0x82, 0x83]
VerifyPS(msg, cmd, expectMsg, expectList)


print ""
print "sleep 7s"
sleep(7)

print ""
print "check if device enter the Standby mode after 7 second"
msg = "Issue cmd to check current power status"
cmd = "sg_raw -v  %s  85 6 20 0 0 0 0 0 0 0 0 0 0 40 e5 0 -R"%Inst.dev
expectMsg="Check if Power Mode = standby or not, i.e. 00h/01h"
expectList=[0x0, 0x1]
VerifyPS(msg, cmd, expectMsg, expectList)

msg = "Issue cmd to disable standby timer"
cmd = "sg_raw -v  %s  85 6 20 0 0 0 0 0 0 0 0 0 0 40 e2 0"%Inst.dev
expectMsg=None
expectList=None
VerifyPS(msg, cmd, expectMsg, expectList)

print ""
print "sleep 7s"
sleep(7)

print ""
print "check if device is active after 7 second"
msg = "Issue cmd to check current power status"
cmd = "sg_raw -v  %s  85 6 20 0 0 0 0 0 0 0 0 0 0 40 e5 0 -R"%Inst.dev
expectMsg="expect current is active mode(0xFF)"
expectList=[0xFF]
VerifyPS(msg, cmd, expectMsg, expectList)

