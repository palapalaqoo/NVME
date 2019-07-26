#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import python built-ins
import sys
import re
import threading
import time
from time import sleep
tkinter = None
# Import VCT modules
from lib_vct.NVME import NVME
from lib_vct import mStruct
import struct


import sys
import os



import fcntl
import ctypes
class _nvme_user_io(ctypes.Structure):
    _fields_ = [
        ('opcode', ctypes.c_byte),
        ('flags', ctypes.c_byte),
        ('control', ctypes.c_ushort),
        ('nblocks', ctypes.c_ushort),
        ('rsvd', ctypes.c_ushort),
        ('metadata', ctypes.c_ulonglong),
        ('addr', ctypes.c_ulonglong),
        ('slba', ctypes.c_ulonglong),
        ('dsmgmt', ctypes.c_uint),
        ('reftag', ctypes.c_uint),
        ('apptag', ctypes.c_ushort),
        ('appmask', ctypes.c_ushort),
    ]


class _nvme_passthru_cmd(ctypes.Structure):
    _fields_ = [
        ('opcode', ctypes.c_byte),
        ('flags', ctypes.c_byte),
        ('rsvd1', ctypes.c_ushort),
        ('nsid', ctypes.c_uint),
        ('cdw2', ctypes.c_uint),
        ('cdw3', ctypes.c_uint),
        ('metadata', ctypes.c_ulonglong),
        ('addr', ctypes.c_ulonglong),
        ('metadata_len', ctypes.c_uint),
        ('data_len', ctypes.c_uint),
        ('cdw10', ctypes.c_uint),
        ('cdw11', ctypes.c_uint),
        ('cdw12', ctypes.c_uint),
        ('cdw13', ctypes.c_uint),
        ('cdw14', ctypes.c_uint),
        ('cdw15', ctypes.c_uint),
        ('timeout_ms', ctypes.c_uint),
        ('result', ctypes.c_uint),
    ]


def nvme_write(ns, slba, nlb, data):
    #define NVME_IOCTL_IO_CMD    _IOWR('N', 0x43, struct nvme_passthru_cmd)
    # NVME_IOCTL_IO_CMD = ioctl_opt.IOWR(ord('N'), 0x43, _nvme_passthru_cmd)
    NVME_IOCTL_IO_CMD = 0xC0484E43

    fd = os.open("/dev/nvme0", os.O_RDONLY)
    nvme_passthru_cmd = _nvme_passthru_cmd(    0x01, # opcode
                                0, # flags = os.O_RDONLY if (0x01 & 1) else os.O_WRONLY | os.O_CREAT, # opcode & 1 ? O_RDONLY : O_WRONLY | O_CREAT
                                0, # rsvd1
                                ns, # nsid
                                0, # cdw2
                                0, # cdw3
                                0, # metadata
                                id(data)+36, # addr
                                0, # metadata_len
                                len(data), # data_len
                                slba&0xffffffff, # cdw10= SLBA&0xffffffff
                                (slba&0xffffffff00000000)>>32, # cdw11= (SLBA&0xffffffff00000000)>>32
                                nlb, # cdw12= (LR<<31)|(FUA<<30)|((PRINFO&0xf)<<26)|((DTYPE&0xf)<<20)|NLB
                                0, # cdw13= DSM
                                0, # cdw14= ILBRT
                                0, # cdw15= ((LBATM&0xffff)<<16)|(LBAT&0xffff)
                                0, # timeout_ms
                                0, # result
    )
    
    ret = fcntl.ioctl(fd, NVME_IOCTL_IO_CMD, nvme_passthru_cmd)
    os.close(fd)
    return ret

def nvme_write_t():
    while True:
        if nvme_write(1, 0, 511, data):
            print "Error"


data = (((''.join(["%02x"%x for x in xrange(0x0, 0xff +1)]))*2)*511).decode("hex")

for i in range(8):  
    t = threading.Thread(target = nvme_write_t)
    t.start() 


    
    