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

Inst = SATA_c(sys.argv)

print "Device: %s"%Inst.dev

print ""

print "Power test"

CMD = "sg_raw -v  %s  85 6 20 0 0 0 0 0 0 0 0 0 0 40 e5 0 -R"%Inst.dev
print "Issue cmd to check current power status"
print "cmd: %s"%CMD
rt = Inst.ata_cmd(CMD)

if rt.SecotrCount==255:
    print "active/standby"











