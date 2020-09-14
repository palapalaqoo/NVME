from Data import *
import nvme_ioctl
import logging

import struct
import os
import re

class NVMe(object):

	##################################################################################

	import NVMeStatus as status
	from NVMeMacro import *

	##################################################################################

	__path = None

	def __init__(self, path=None):
		# super(NVMe, self).__init__(path)
		if path != None:
			self.set_device_path(path)

	def set_device_path(self, path):
		self.__path = path
		if self.check_device(path): return 1
		return 0

	def check_device(self, path):
		if not os.path.exists(path):
			logging.error("%s: no such device!"%(path)) 
			return 1
		return 0

	def path(self): return self.__path
 
 #################################################################################################################

	def get_log_page(self, log_page, ns=0xffffffff, opt_arg="", timeout=0):

		def parseStructure(structPattern, binary, parseAttr=None):

			if parseAttr == None: parseAttr = DataBuffer()

			for (attr, cont) in structPattern.items():
				try:
					# e.g. 'CAP_NAME': [u_byte,l_byte] --> proc.CAP_NAME = binary[l_byte:u_byte]
					(l_byte, u_byte) = (min(cont), max(cont))
					fmt = "<%s"%("B"*(u_byte-l_byte+1))
					mem_read = struct.unpack(fmt, binary[l_byte:u_byte+1])
					mem_read = sum( map(lambda x: mem_read[x]<<(8*x), range(len(mem_read)) ) )
				except:
					mem_read = 0
				parseAttr.__setattr__(attr, mem_read)
			
			return parseAttr

		if self.__path == None: return None
		
		(lid, rae, data_len) = (log_page, False, 0)
		proc = DataBuffer()

		fd = nvme_ioctl.open_path(self.__path)
		if fd < 0: 
			Status_Field = DataBuffer(fd)
			Status_Field.SC, Status_Field.SCT = fd, 0
			proc.returncode = Status_Field
			return proc

		data_len = opt_arg if isinstance(opt_arg, int) else data_len
		log_structure = {'DataStruct': [data_len-1,0]}

		ret = nvme_ioctl.nvme_get_log(fd, ns, lid, rae, data_len)
		os.close(fd)

		proc = parseStructure(log_structure, ret['data'])

		Status_Field = StatusField(ret['status_field'])
		(Status_Field.DNR, Status_Field.M, 
			Status_Field.SCT, Status_Field.SC) = ((ret['status_field']>>14)&0x1, (ret['status_field']>>13)&0x1, 
													(ret['status_field']>>8)&0x3, ret['status_field']&0xff)
		proc.returncode = Status_Field
		return proc
