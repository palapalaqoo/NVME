#!/usr/bin/env python
import struct
import fcntl
# import ioctl_opt
import ctypes
import os
import time
import datetime

import subprocess

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


#-------------------------Reset-------------------------------


# fd = os.open("/dev/nvme0", os.O_RDONLY)
# # #define NVME_IOCTL_RESET	_IO('N', 0x44)
# # _NVME_IOCTL_RESET = ioctl_opt.IO(ord('N'), 0x44)
# _NVME_IOCTL_RESET = 0x4E44
# print "NVMe reset"
# fcntl.ioctl(fd, _NVME_IOCTL_RESET, 0x2000)
# os.close(fd)

#-------------------------------------------------------------


#-------------------------Write-------------------------------

# fd = os.open("/dev/nvme0n1", os.O_RDONLY)

# # #define NVME_IOCTL_SUBMIT_IO	_IOW('N', 0x42, struct nvme_user_io)
# # _NVME_IOCTL_SUBMIT_IO = ioctl_opt.IOW(ord('N'), 0x42, _nvme_user_io)
# _NVME_IOCTL_SUBMIT_IO = 0x40304E42

# # data = ("55" * 1024).decode("hex")
# data = (((''.join(["%02x"%x for x in xrange(0x0, 0xff +1)]))*2)*512).decode("hex")

# nvme_user_io = _nvme_user_io(	
# 					0x01, # opcode
# 					0, #os.O_RDONLY if (0x01 & 1) else os.O_WRONLY | os.O_CREAT, # opcode & 1 ? O_RDONLY : O_WRONLY | O_CREAT
# 					0, # control |= (cfg.prinfo << 10);
# 					511, # nblocks
# 					0, # rsvd
# 					0, # metadata
# 					id(data)+36, # addr
# 					0, # slba
# 					0, # dsmgmt
# 					0, # reftag
# 					0, # apptag
# 					0, # appmask
# )

# fcntl.ioctl(fd, _NVME_IOCTL_SUBMIT_IO, nvme_user_io)
# os.close(fd)

#-------------------------------------------------------------


#-------------------------Write2------------------------------

# fd = os.open("/dev/nvme0", os.O_RDONLY)

# #define NVME_IOCTL_IO_CMD	_IOWR('N', 0x43, struct nvme_passthru_cmd)
# # NVME_IOCTL_IO_CMD = ioctl_opt.IOWR(ord('N'), 0x43, _nvme_passthru_cmd)
# NVME_IOCTL_IO_CMD = 0xC0484E43

# # data = ("55" * 1024).decode("hex")
# data = (((''.join(["%02x"%x for x in xrange(0x0, 0xff +1)]))*2)*512).decode("hex")

# nvme_passthru_cmd = _nvme_passthru_cmd(	0x01, # opcode
# 							0, # flags = os.O_RDONLY if (0x01 & 1) else os.O_WRONLY | os.O_CREAT, # opcode & 1 ? O_RDONLY : O_WRONLY | O_CREAT
# 							0, # rsvd1
# 							1, # nsid
# 							0, # cdw2
# 							0, # cdw3
# 							0, # metadata
# 							id(data)+36, # addr
# 							0, # metadata_len
# 							len(data), # data_len
# 							0, # cdw10= SLBA&0xffffffff
# 							0, # cdw11= (SLBA&0xffffffff00000000)>>32
# 							511, # cdw12= (LR<<31)|(FUA<<30)|((PRINFO&0xf)<<26)|((DTYPE&0xf)<<20)|NLB
# 							0, # cdw13= DSM
# 							0, # cdw14= ILBRT
# 							0, # cdw15= ((LBATM&0xffff)<<16)|(LBAT&0xffff)
# 							0, # timeout_ms
# 							0, # result
# )

# # print ctypes.sizeof(_nvme_passthru_cmd)

# fcntl.ioctl(fd, NVME_IOCTL_IO_CMD, nvme_passthru_cmd)
# os.close(fd)

#-------------------------------------------------------------

#-------------------------Write Zeroes------------------------------

# fd = os.open("/dev/nvme0", os.O_RDONLY)

# # #define NVME_IOCTL_IO_CMD	_IOWR('N', 0x43, struct nvme_passthru_cmd)
# # NVME_IOCTL_IO_CMD = ioctl_opt.IOWR(ord('N'), 0x43, _nvme_passthru_cmd)
# NVME_IOCTL_IO_CMD = 0xC0484E43

# nvme_passthru_cmd = _nvme_passthru_cmd(	
# 							0x08, # opcode
# 							0, #os.O_RDONLY if (0x08 & 1) else os.O_WRONLY, # flags = os.O_CREAT, # opcode & 1 ? O_RDONLY : O_WRONLY | O_CREAT
# 							0, # rsvd1
# 							1, # nsid
# 							0, # cdw2
# 							0, # cdw3
# 							0, # metadata
# 							0, # addr
# 							0, # metadata_len
# 							0, # data_len
# 							0, # cdw10= SLBA&0xffffffff
# 							0, # cdw11= (SLBA&0xffffffff00000000)>>32
# 							511, # cdw12= nlb | (control << 16)
# 							0, # cdw13
# 							0, # cdw14= reftag
# 							0, # cdw15= apptag | (appmask << 16)
# 							0, # timeout_ms
# 							0, # result
# )

# # print ctypes.sizeof(_nvme_passthru_cmd)

# fcntl.ioctl(fd, NVME_IOCTL_IO_CMD, nvme_passthru_cmd)
# os.close(fd)

#-------------------------------------------------------------


#-------------------------Tseting------------------------------



def nvme_write(ns, slba, nlb, data):
	#define NVME_IOCTL_IO_CMD	_IOWR('N', 0x43, struct nvme_passthru_cmd)
	# NVME_IOCTL_IO_CMD = ioctl_opt.IOWR(ord('N'), 0x43, _nvme_passthru_cmd)
	NVME_IOCTL_IO_CMD = 0xC0484E43

	fd = os.open("/dev/nvme0", os.O_RDONLY)
	nvme_passthru_cmd = _nvme_passthru_cmd(	0x01, # opcode
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

	
data = (((''.join(["%02x"%x for x in xrange(0x0, 0xff +1)]))*2)*512).decode("hex")
loops = 81920 # 1GB=4096 loops for@ each loop 512blk

print "Compare writing %.2f GB data (BS: %d bytes) between using IOCTL and NVMe cli:"%(
	(loops*len(data))/1073741824.0, len(data))

start_time=time.localtime()
for x in xrange(0,loops): # 1GB=4096 loops for@ each loop 512blk
	SLBA = 512*x
	if nvme_write(1, SLBA, 511, data) != 0:
		print "Error: SLBA: %#xh"%(SLBA) 

print "Using IOCTL:"
print "{:0>8}".format(str(datetime.timedelta(seconds=int(time.mktime(time.localtime())-time.mktime(start_time)))))


print "\n"

start_time=time.localtime()

proc = []
for x in xrange(0,loops): # 1GB=4096 loops for@ each loop 512blk
	slba = 512*x
	cmd = "nvme io-passthru -o 0x1 /dev/nvme0 -n 1 -b -w --cdw10=%d --cdw11=%d --cdw12=511 -l 262144 -m 0 --cdw13=0x0 --cdw14=0x0 --cdw15=0x0 -i write_data_file"%(
		slba&0xffffffff, (slba&0xffffffff00000000)>>32)
	proc.append(subprocess.Popen(cmd, shell=True))

	if (x%4096 == 0) or (x == loops-1):
		ret = map(lambda x: x.wait(), proc)
		if any(ret): print "Error"
		proc = []

print "Using NVMe cli:"
print "{:0>8}".format(str(datetime.timedelta(seconds=int(time.mktime(time.localtime())-time.mktime(start_time)))))



#-------------------------------------------------------------
