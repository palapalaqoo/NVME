import logging

import random
import struct
import fcntl
import ctypes
import time
import os
# import ioctl_opt

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

# define NVME_IOCTL_ADMIN_CMD	_IOWR('N', 0x41, struct nvme_admin_cmd)
# _NVME_IOCTL_ADMIN_CMD = ioctl_opt.IOWR(ord('N'), 0x41, _nvme_passthru_cmd)
_NVME_IOCTL_ADMIN_CMD = 0xc0484e41

#-------------------------------------------------------------------------------------

def open_path(path):
	fd = -1
	max_retry = 10
	for retry_i in xrange(max_retry):
		try:
			fd = os.open(path, os.O_RDONLY)
		except OSError as e:
			fd = -(e.errno)

		if fd >= 0 : break
		time.sleep(random.randint(30, 150)/1000.0)

	return fd

def nvme_submit_admin_passthru(fd, cmd):
	try:
		return fcntl.ioctl(fd, _NVME_IOCTL_ADMIN_CMD, cmd)
	except (OSError, IOError) as e:
		logging.error(e)
		return -(e.errno)	

def nvme_get_log13(fd, nsid, log_id, lsp, lpo, lsi, rae, data_len):
	data = ctypes.create_string_buffer(data_len)

	numd = (data_len >> 2) - 1
	numdu = (numd >> 16) & 0xffff
	numdl = numd & 0xffff
	cdw10 = log_id | (numdl << 16) | ((1 << 15) if rae else 0)
	if lsp: cdw10 |= (lsp << 8)
	cdw11 = numdu | (lsi << 16)
	cdw12 = lpo
	cdw13 = (lpo >> 32)

	nvme_passthru_cmd = _nvme_passthru_cmd(	
			0x2, # opcode
			0, # flags
			0, # rsvd1
			nsid, # nsid
			0, # cdw2
			0, # cdw3
			0, # metadata
			ctypes.addressof(data) if len(data) else 0, # addr
			0, # metadata_len
			data_len, # data_len
			cdw10, # cdw10
			cdw11, # cdw11
			cdw12, # cdw12
			cdw13, # cdw13
			0, # cdw14
			0, # cdw15
			0, # timeout_ms
			0, # result
	)
	return {'status_field': nvme_submit_admin_passthru(fd, nvme_passthru_cmd), 
			'data': data.raw} 

def nvme_get_log(fd, nsid, log_id, rae, data_len):
	data = ''
	offset, xfer_len = 0, data_len
	while True: # See NVMe Cli
		xfer_len = data_len - offset
		if (xfer_len > 4096): xfer_len = 4096;
		ret = nvme_get_log13(fd, nsid, log_id, 0x0, offset, 0, rae, xfer_len)
		if ret['status_field']: break
		offset += xfer_len
		data = data + ret['data']

		if (offset >= data_len): break

	return {'status_field': ret['status_field'], 'data': data}
