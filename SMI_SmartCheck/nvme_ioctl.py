import logging

import array
import random
import struct
import fcntl
import ctypes
import time
import os
# import ioctl_opt

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


# define NVME_IOCTL_ID		_IO('N', 0x40)
# _NVME_IOCTL_ID = ioctl_opt.IO(ord('N'), 0x40)
_NVME_IOCTL_ID = 0x4e40

# define NVME_IOCTL_ADMIN_CMD	_IOWR('N', 0x41, struct nvme_admin_cmd)
# _NVME_IOCTL_ADMIN_CMD = ioctl_opt.IOWR(ord('N'), 0x41, _nvme_passthru_cmd)
_NVME_IOCTL_ADMIN_CMD = 0xc0484e41

# define NVME_IOCTL_SUBMIT_IO	_IOW('N', 0x42, struct nvme_user_io)
# _NVME_IOCTL_SUBMIT_IO = ioctl_opt.IOW(ord('N'), 0x42, _nvme_user_io)
_NVME_IOCTL_SUBMIT_IO = 0x40304E42

# define NVME_IOCTL_IO_CMD	_IOWR('N', 0x43, struct nvme_passthru_cmd)
# _NVME_IOCTL_IO_CMD = ioctl_opt.IOWR(ord('N'), 0x43, _nvme_passthru_cmd)
_NVME_IOCTL_IO_CMD = 0xC0484E43

# define NVME_IOCTL_RESET	_IO('N', 0x44)
# _NVME_IOCTL_RESET = ioctl_opt.IO(ord('N'), 0x44)
_NVME_IOCTL_RESET = 0x4E44

# define NVME_IOCTL_SUBSYS_RESET	_IO('N', 0x45)
# _NVME_IOCTL_SUBSYS_RESET = ioctl_opt.IO(ord('N'), 0x45)
_NVME_IOCTL_SUBSYS_RESET = 0x4e45

# define NVME_IOCTL_RESCAN	_IO('N', 0x46)
# _NVME_IOCTL_RESCAN = ioctl_opt.IO(ord('N'), 0x46)
_NVME_IOCTL_RESCAN = 0x4e46

# define BLKGETSIZE _IO(0x12,96)                 /* return device size */
# _BLKGETSIZE = ioctl_opt.IO(0x12, 96)
_BLKGETSIZE = 0x1260

# definde BLKSSZGET  _IO(0x12,104) 				/* get block device sector size
# _BLKSSZGET = ioctl_opt.IO(0x12, 104)
_BLKSSZGET = 0x1268

# define BLKPBSZGET _IO(0x12,123) 				/* get device physical sector size */
# _BLKPBSZGET = ioctl_opt.IO(0x12, 123)
_BLKPBSZGET=0x127b

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

def ioctl_read_uint32(fd, req):
	# https://gist.github.com/shimarin/34f05caaf75d02966a30
	buf = array.array('c', [chr(0)] * 4)
	fcntl.ioctl(fd, req, buf)
	return struct.unpack('I',buf)[0]

def ioctl_read_uint64(fd, req):
	buf = array.array('c', [chr(0)] * 8)
	fcntl.ioctl(fd, req, buf)
	return struct.unpack('L',buf)[0]

def getBlockDeviceSectorSize(fd):
	try:
		return ioctl_read_uint32(fd, _BLKPBSZGET)
	except (OSError, IOError) as e:
		return -(e.errno)

def nvme_reset_controller(fd):
	try:
		return fcntl.ioctl(fd, _NVME_IOCTL_RESET, 0x2000) # 0x2000 = NVME_IOCTL_RESET
	except (OSError, IOError) as e:
		logging.error(e)
		return -(e.errno)

def nvme_submit_admin_passthru(fd, cmd):
	try:
		return fcntl.ioctl(fd, _NVME_IOCTL_ADMIN_CMD, cmd)
	except (OSError, IOError) as e:
		logging.error(e)
		return -(e.errno)	

def nvme_submit_io_passthru(fd, cmd):
	try:
		return fcntl.ioctl(fd, _NVME_IOCTL_IO_CMD, cmd)
	except (OSError, IOError) as e:
		logging.error(e)
		return -(e.errno)

def nvme_device_self_test (fd, action, ns):
	nvme_passthru_cmd = _nvme_passthru_cmd(	
			0x14, # opcode
			0, # flags
			0, # rsvd1
			ns, # nsid
			0, # cdw2
			0, # cdw3
			0, # metadata
			0, # addr
			0, # metadata_len
			0, # data_len
			action, # cdw10
			0, # cdw11 = ovrpat
			0, # cdw12
			0, # cdw13
			0, # cdw14
			0, # cdw15
			0, # timeout_ms
			0, # result
	)
	return {'status_field': nvme_submit_admin_passthru(fd, nvme_passthru_cmd)}

def nvme_feature(fd, opcode, nsid, cdw10, cdw11, cdw12, cdw13, cdw14, cdw15, data_len, data):
	if opcode == 0xa: data = ctypes.create_string_buffer(data_len)
	nvme_passthru_cmd = _nvme_passthru_cmd(	
			opcode, # opcode
			0, # flags
			0, # rsvd1
			nsid, # nsid
			0, # cdw2
			0, # cdw3
			0, # metadata
			0 if (data_len==0) else ((id(data)+36) if (opcode==0x9) else ctypes.addressof(data)), # addr
			0, # metadata_len
			data_len, # data_len
			cdw10, # cdw10
			cdw11, # cdw11
			cdw12, # cdw12
			cdw13, # cdw13
			cdw14, # cdw14
			cdw15, # cdw15
			0, # timeout_ms
			0, # result
	)
	err = nvme_submit_admin_passthru(fd, nvme_passthru_cmd)
	result = int(nvme_passthru_cmd.result) if ((not err) and (nvme_passthru_cmd.result)) else 0
	ret_val = {'status_field': err, 'result': result}
	if (opcode == 0xa) and (data_len): ret_val.update( {'data': data.raw} )
	return ret_val

def nvme_set_feature(fd, nsid, fid, value, cdw12, cdw13, cdw14, cdw15, save, data_len, data):
	cdw10 = fid | ((1<<31) if save else 0)
	data_len = min(data_len, (len(data) if (data) else 0 ))
	return nvme_feature(fd, 0x9, nsid, cdw10, value, cdw12, cdw13, cdw14, cdw15, data_len, data)

def nvme_get_feature(fd, nsid, fid, sel, cdw11, data_len):
	cdw10 = fid | sel << 8
	return nvme_feature(fd, 0xa, nsid, cdw10, cdw11, 0, 0, 0, 0, data_len, 0)

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

def nvme_identify13(fd, nsid, cdw10, cdw11):
	NVME_IDENTIFY_DATA_SIZE = 4096
	data = ctypes.create_string_buffer(NVME_IDENTIFY_DATA_SIZE)

	nvme_passthru_cmd = _nvme_passthru_cmd(	
			0x6, # opcode
			0, # flags
			0, # rsvd1
			nsid, # nsid
			0, # cdw2
			0, # cdw3
			0, # metadata
			ctypes.addressof(data) if len(data) else 0, # addr
			0, # metadata_len
			NVME_IDENTIFY_DATA_SIZE if len(data) else 0, # data_len
			cdw10, # cdw10
			cdw11, # cdw11
			0, # cdw12
			0, # cdw13
			0, # cdw14
			0, # cdw15
			0, # timeout_ms
			0, # result
	)
	return {'status_field': nvme_submit_admin_passthru(fd, nvme_passthru_cmd), 
			'data': data.raw}

def nvme_identify(fd, nsid, cdw10):

	return nvme_identify13(fd, nsid, cdw10, 0)

def nvme_ns_attachment(fd, nsid, num_ctrls, ctrlist, sel):

	class nvme_controller_list(ctypes.Structure):
		_fields_ = [
			('num', ctypes.c_uint16),				# 2 bytes
			('identifier', (ctypes.c_uint16*2047)), # 4094 bytes
		]
	cntlist = nvme_controller_list()

	nvme_passthru_cmd = _nvme_passthru_cmd(	
			0x15, # opcode
			0, # flags
			0, # rsvd1
			nsid, # nsid
			0, # cdw2
			0, # cdw3
			0, # metadata
			ctypes.addressof(cntlist), # addr
			0, # metadata_len
			0x1000, # data_len = 0x1000
			sel&0x1, # cdw10 = sel's bit 1 (0=attach)
			0, # cdw11
			0, # cdw12
			0, # cdw13
			0, # cdw14
			0, # cdw15
			0, # timeout_ms
			0, # result
	)
	cntlist.num = num_ctrls;
	for i in xrange(num_ctrls):
		cntlist.identifier[i] = ctrlist[i];

	return {'status_field': nvme_submit_admin_passthru(fd, nvme_passthru_cmd)} 

def nvme_ns_create(fd, nsze, ncap, flbas, dps, nmic, timeout=120000):
	# NVME_IOCTL_TIMEOUT = 120000 
	class nvme_lbaf(ctypes.Structure):
		_fields_ = [
			('ms', ctypes.c_uint16), 
			('ds', ctypes.c_uint8), 
			('rp', ctypes.c_uint8),
		]

	class nvme_id_ns(ctypes.Structure):
		_fields_ = [
			('nsze', ctypes.c_uint64), 
			('ncap', ctypes.c_uint64), 
			('nuse', ctypes.c_uint64), 
			('nsfeat', ctypes.c_uint8), 
			('nlbaf', ctypes.c_uint8), 
			('flbas', ctypes.c_uint8), 
			('mc', ctypes.c_uint8), 
			('dpc', ctypes.c_uint8), 
			('dps', ctypes.c_uint8), 
			('nmic', ctypes.c_uint8), 
			('rescap', ctypes.c_uint8), 
			('fpi', ctypes.c_uint8), 
			('dlfeat', ctypes.c_uint8), 
			('nawun', ctypes.c_uint16), 
			('nawupf', ctypes.c_uint16), 
			('nacwu', ctypes.c_uint16), 
			('nabsn', ctypes.c_uint16), 
			('nabo', ctypes.c_uint16), 
			('nabspf', ctypes.c_uint16), 
			('noiob', ctypes.c_uint16), 
			('nvmcap', ctypes.c_uint8*16), 
			('npwg', ctypes.c_uint16), 
			('npwa', ctypes.c_uint16), 
			('npdg', ctypes.c_uint16), 
			('npda', ctypes.c_uint16), 
			('nows', ctypes.c_uint16), 
			('rsvd74', ctypes.c_uint8*18), 
			('anagrpid', ctypes.c_uint32), 
			('rsvd96', ctypes.c_uint8*3), 
			('nsattr', ctypes.c_uint8), 
			('nvmsetid', ctypes.c_uint16), 
			('endgid', ctypes.c_uint16), 
			('nguid', ctypes.c_uint8*16), 
			('eui64', ctypes.c_uint8*8), 
			('lbaf', nvme_lbaf*16), 
			('rsvd192', ctypes.c_uint8*192), 
			('vs', ctypes.c_uint8*3712), 
		]
	ns = nvme_id_ns()
	(ns.nsze, ns.ncap, ns.flbas, ns.dps, ns.nmic) = (nsze, ncap, flbas, dps, nmic)

	nvme_passthru_cmd = _nvme_passthru_cmd(	
			0x0d, # opcode
			0, # flags
			0, # rsvd1
			0, # nsid
			0, # cdw2
			0, # cdw3
			0, # metadata
			ctypes.addressof(ns), # addr
			0, # metadata_len
			0x1000, # data_len
			0, # cdw10
			0, # cdw11
			0, # cdw12
			0, # cdw13
			0, # cdw14
			0, # cdw15
			timeout, # timeout_ms = timeout
			0, # result
	)

	err = nvme_submit_admin_passthru(fd, nvme_passthru_cmd)
	result = int(nvme_passthru_cmd.result) if ((not err) and (nvme_passthru_cmd.result)) else 0
	return {'status_field': err, 'result': result}

def nvme_ns_delete(fd, nsid, timeout=120000):
	# NVME_IOCTL_TIMEOUT = 120000 
	nvme_passthru_cmd = _nvme_passthru_cmd(	
			0x0d, # opcode
			0, # flags
			0, # rsvd1
			nsid, # nsid
			0, # cdw2
			0, # cdw3
			0, # metadata
			0, # addr
			0, # metadata_len
			0, # data_len
			1, # cdw10 = 1
			0, # cdw11
			0, # cdw12
			0, # cdw13
			0, # cdw14
			0, # cdw15
			timeout, # timeout_ms = timeout
			0, # result
	)

	return {'status_field': nvme_submit_admin_passthru(fd, nvme_passthru_cmd)} 

def nvme_sanitize(fd, sanact, ause, owpass, oipbp, no_dealloc, ovrpat):
	NVME_SANITIZE_OWPASS_SHIFT = 0x00000004
	cdw10 = (no_dealloc << 9 | oipbp << 8 | 
			owpass << NVME_SANITIZE_OWPASS_SHIFT | 
			ause << 3 | sanact)
	nvme_passthru_cmd = _nvme_passthru_cmd(	
			0x84, # opcode
			0, # flags
			0, # rsvd1
			0, # nsid
			0, # cdw2
			0, # cdw3
			0, # metadata
			0, # addr
			0, # metadata_len
			0, # data_len
			cdw10, # cdw10
			ovrpat, # cdw11 = ovrpat
			0, # cdw12
			0, # cdw13
			0, # cdw14
			0, # cdw15
			0, # timeout_ms
			0, # result
	)
	return {'status_field': nvme_submit_admin_passthru(fd, nvme_passthru_cmd)}

def nvme_compare(fd, ns, slba, nblocks, reftag, apptag, appmask, data, metadata):
	nvme_passthru_cmd = _nvme_passthru_cmd(	
			0x05, # opcode
			0, # flags
			0, # rsvd1
			ns, # nsid
			0, # cdw2
			0, # cdw3
			(id(metadata)+36) if len(metadata) else 0, # metadata *MUST be +36*
			(id(data)+36) if len(data) else 0, # addr *MUST be +36*
			len(metadata), # metadata_len
			len(data), # data_len
			slba&0xffffffff, # cdw10= slba&0xffffffff
			(slba&0xffffffff00000000)>>32, # cdw11= slba>>32
			nblocks, # cdw12= (LR<<31)|(FUA<<30)|((PRINFO&0xf)<<26)|NLB
			0, # cdw13
			reftag, # cdw14= EILBRT
			apptag | (appmask << 16), # cdw15= ((ELBATM&0xffff)<<16)|(ELBAT&0xffff)
			0, # timeout_ms
			0, # result
	)

	return {'status_field': nvme_submit_io_passthru(fd, nvme_passthru_cmd)}

def nvme_dsm(fd, ns, cdw11, dsm, nr_ranges):
	nvme_passthru_cmd = _nvme_passthru_cmd(	
			0x9, # opcode
			0, # flags
			0, # rsvd1
			ns, # nsid
			0, # cdw2
			0, # cdw3
			0, # metadata
			(id(dsm)+36) if len(dsm) else 0, # addr *MUST be +36*
			0, # metadata_len
			nr_ranges * 16, # data_len = nr_ranges*(8bytes @each entry)
			nr_ranges-1, # cdw10 = nr_ranges - 1
			cdw11, # cdw11
			0, # cdw12
			0, # cdw13
			0, # cdw14
			0, # cdw15
			0, # timeout_ms
			0, # result
	)

	return {'status_field': nvme_submit_io_passthru(fd, nvme_passthru_cmd)}

def nvme_flush(fd, ns):
	nvme_passthru_cmd = _nvme_passthru_cmd(	
			0x0, # opcode
			0, # flags
			0, # rsvd1
			ns, # nsid
			0, # cdw2
			0, # cdw3
			0, # metadata
			0, # addr
			0, # metadata_len
			0, # data_len
			0, # cdw10
			0, # cdw11
			0, # cdw12
			0, # cdw13
			0, # cdw14
			0, # cdw15
			0, # timeout_ms
			0, # result
	)
	
	return {'status_field': nvme_submit_io_passthru(fd, nvme_passthru_cmd)}

def nvme_read(fd, ns, slba, nblocks, dsmgmt, reftag, apptag, appmask, data_len, metadata_len):
	data = ctypes.create_string_buffer(data_len)
	metadata = ctypes.create_string_buffer(metadata_len)
	nvme_passthru_cmd = _nvme_passthru_cmd(	
			0x02, # opcode
			0, # flags
			0, # rsvd1
			ns, # nsid
			0, # cdw2
			0, # cdw3
			ctypes.addressof(metadata) if len(metadata) else 0, # metadata
			ctypes.addressof(data) if len(data) else 0, # addr
			metadata_len, # metadata_len
			data_len, # data_len
			slba&0xffffffff, # cdw10= slba&0xffffffff
			(slba&0xffffffff00000000)>>32, # cdw11= slba>>32
			nblocks, # cdw12= (LR<<31)|(FUA<<30)|((PRINFO&0xf)<<26)|NLB
			dsmgmt, # cdw13= DSM
			reftag, # cdw14= EILBRT
			apptag | (appmask << 16), # cdw15= ((ELBATM&0xffff)<<16)|(ELBAT&0xffff)
			0, # timeout_ms
			0, # result
	)

	return {'status_field': nvme_submit_io_passthru(fd, nvme_passthru_cmd), 
			'data': data.raw, 'metadata': metadata.raw}

def nvme_write(fd, ns, slba, nblocks, dsmgmt, reftag, apptag, appmask, data, metadata):
	nvme_passthru_cmd = _nvme_passthru_cmd(	
			0x01, # opcode
			0, # flags
			0, # rsvd1
			ns, # nsid
			0, # cdw2
			0, # cdw3
			(id(metadata)+36) if len(metadata) else 0, # metadata *MUST be +36*
			(id(data)+36) if len(data) else 0, # addr *MUST be +36*
			len(metadata), # metadata_len
			len(data), # data_len
			slba&0xffffffff, # cdw10= slba&0xffffffff
			(slba&0xffffffff00000000)>>32, # cdw11= slba>>32
			nblocks, # cdw12= (LR<<31)|(FUA<<30)|((PRINFO&0xf)<<26)|((DTYPE&0xf)<<20)|NLB
			dsmgmt, # cdw13= DSM | (DSPEC<<16)
			reftag, # cdw14= ILBRT
			apptag | (appmask << 16), # cdw15= ((LBATM&0xffff)<<16)|(LBAT&0xffff)
			0, # timeout_ms
			0, # result
	)

	return {'status_field': nvme_submit_io_passthru(fd, nvme_passthru_cmd)}

def nvme_write_uncor(fd, ns, slba, nlb):
	nvme_passthru_cmd = _nvme_passthru_cmd(	
			0x04, # opcode
			0, # flags
			0, # rsvd1
			ns, # nsid
			0, # cdw2
			0, # cdw3
			0, # metadata
			0, # addr
			0, # metadata_len
			0, # data_len
			slba & 0xffffffff, # cdw10= slba&0xffffffff
			(slba&0xffffffff00000000)>>32, # cdw11= slba>>32
			nlb & 0xffff, # cdw12=nlb
			0, # cdw13
			0, # cdw14
			0, # cdw15
			0, # timeout_ms
			0, # result
	)
	
	return {'status_field': nvme_submit_io_passthru(fd, nvme_passthru_cmd)}

def nvme_write_zeroes(fd, ns, slba, nlb, control, reftag, apptag, appmask):
	nvme_passthru_cmd = _nvme_passthru_cmd(	
			0x08, # opcode
			0, # flags
			0, # rsvd1
			ns, # nsid
			0, # cdw2
			0, # cdw3
			0, # metadata
			0, # addr
			0, # metadata_len
			0, # data_len
			slba & 0xffffffff, # cdw10= slba&0xffffffff
			(slba&0xffffffff00000000)>>32, # cdw11= slba>>32
			nlb | (control << 16), # cdw12= nlb | (control << 16)
			0, # cdw13
			reftag, # cdw14= reftag
			apptag | (appmask << 16), # cdw15= apptag | (appmask << 16)
			0, # timeout_ms
			0, # result
	)
	
	return {'status_field': nvme_submit_io_passthru(fd, nvme_passthru_cmd)}

def nvme_passthru(fd, ioctl_cmd, opcode, flags, rsvd, nsid, cdw2, cdw3, 
					cdw10, cdw11, cdw12, cdw13, cdw14, cdw15, data_len, 
					data, metadata_len, metadata, timeout_ms=0):

	# Means thats this operation is used to get data -> creates buffer.
	read_data = True if ((not data) and data_len) else False
	read_metadata = True if ((not metadata) and metadata_len) else False

	if read_data: data = ctypes.create_string_buffer(data_len)
	if read_metadata: metadata = ctypes.create_string_buffer(metadata_len)

	nvme_passthru_cmd = _nvme_passthru_cmd(	
		opcode,
		flags,
		rsvd,
		nsid,
		cdw2,
		cdw3,
		0 if (metadata_len==0) else (ctypes.addressof(metadata) if read_metadata else (id(metadata)+36)),
		0 if (data_len==0) else (ctypes.addressof(data) if read_data else (id(data)+36)),
		metadata_len,
		data_len,
		cdw10,
		cdw11,
		cdw12,
		cdw13,
		cdw14,
		cdw15,
		timeout_ms,
		0,
	)

	if ioctl_cmd: err = nvme_submit_io_passthru(fd, nvme_passthru_cmd) # I/O passthru
	else: err = nvme_submit_admin_passthru(fd, nvme_passthru_cmd) # Admin passthru

	result = int(nvme_passthru_cmd.result) if ((not err) and (nvme_passthru_cmd.result)) else None
	ret_val = {'status_field': err, 'result': result}
	if read_data: ret_val.update( {'data': data.raw} )
	if read_metadata: ret_val.update( {'metadata': metadata.raw} )
	return ret_val
