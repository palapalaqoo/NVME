from Data import *
from PCI import PCI
from CMD import CMD
import nvme_ioctl
import logging

import textwrap
import struct
import os, mmap
import re
import random
import ctypes
from time import sleep


BIN__path = os.path.dirname(os.path.abspath(__file__)) + "/bin"

class NVMe(PCI):

	##################################################################################

	import NVMeStatus as status
	from NVMeMacro import *

	##################################################################################

	__Controller_Registers = {
		'CTRL_REGS': {'offset': ['addr','addr+0x1030'], 'regs': {
			'CAP': 	{'offset': [0x0,0x7], 'regs': { 'MPSMAX': [55,52], 'MPSMIN': [51,48], 'BPS': [45], 'CSS': [44,37], 
													'NSSRS': [36], 'DSTRD': [35,32], 'TO': [31,24], 'AMS': [18,17], 
													'CQR': [16], 'MQES': [15,00], }}, 
			'VS': 	{'offset': [0x8,0xb], 'regs': { 'MJR': [31,16], 'MNR': [15,8], 'TER': [7,0], }}, 
			'INTMS': {'offset': [0xc,0xf], 'regs': { 'IVMS': [31,0], }}, 
			'INTMC': {'offset': [0x10,0x13], 'regs': { 'IVMC': [31,0], }}, 
			'CC': 	{'offset': [0x14,0x17], 'regs': { 'IOCQES': [23,20], 'IOSQES': [19,16], 'SHN': [15,14], 'AMS': [13,11], 
														'MPS': [10,7], 'CSS': [6,4], 'EN': [0], }}, 
			'CSTS': {'offset': [0x1c,0x1f], 'regs': { 'PP': [5], 'NSSRO': [4], 'SHST': [3,2], 
														'CFS': [1], 'RDY': [0], }}, 
			'NSSR': {'offset': [0x20,0x23], 'regs': { 'NSSRC': [31,0], }}, 
			'AQA': {'offset': [0x24,0x27], 'regs': { 'ACQS': [27,16], 'ASQS': [11,0], }}, 
			'ASQ': {'offset': [0x28,0x2f], 'regs': { 'ASQB': [63,12], }}, 
			'ACQ': {'offset': [0x30,0x37], 'regs': { 'ACQB': [63,12], }}, 
			'CMBLOC': {'offset': [0x38,0x3b], 'regs': { 'OFST': [31,12], 'BIR': [2,0], }}, 
			'CMBSZ': {'offset': [0x3c,0x3f], 'regs': { 'SZ': [31,12], 'SZU': [11,8], 'WDS': [4], 'RDS': [3], 
														'LISTS': [2], 'CQS': [1], 'SQS': [0], }}, 
			'BPINFO': {'offset': [0x40,0x43], 'regs': {'ABPID': [31], 'BRS': [25,24], 'BPSZ': [14,0], }}, 
			'BPRSEL': 	{'offset': [0x44,0x47], 'regs': { 'BPID': [31], 'BPROF': [29,10], 'BPRSZ': [9,0], }}, 
			'BPMBL': {'offset': [0x48,0x4f], 'regs': { 'BMBBA': [63,12], }}, 
			# 'SQHDBL': 	{'offset': [0x1000,0x1003], 'regs': { 'CP': [7,0], }},
			# 'CQHDBL': {'offset': [0x1004,0x1007], 'regs': { 'IPIN': [15,8], 'ILINE': [7,0], }},
			# 'SQHDBL': 	{'offset': {'pos': [0x1000,0x1003], 'num': 1}, 'regs': { 'CP': [7,0], }},							
		}}, 
	}

	identify_NS = {}

	__path = None
	__ori_log = False # Deafult not return the empty part of the log page (e.g. DST log's 0xf record).

	def __init__(self, path=None):
		super(NVMe, self).__init__(path)
		if path != None:
			self.set_device_path(path)
			self.update_info()

	def _parseStructure(self, structPattern, binary, parseAttr=None):

		if parseAttr == None: parseAttr = DataBuffer()

		for (attr, cont) in structPattern.items():
			try:
				if isinstance(cont, list): # e.g. 'CAP_NAME': [u_byte,l_byte] --> proc.CAP_NAME = binary[l_byte:u_byte]
					(l_byte, u_byte) = (min(cont), max(cont))
					fmt = "<%s"%("B"*(u_byte-l_byte+1))
					mem_read = struct.unpack(fmt, binary[l_byte:u_byte+1])
					mem_read = sum( map(lambda x: mem_read[x]<<(8*x), range(len(mem_read)) ) )
				else: # e.g. 'CAP_NAME': {'pos': [u_byte,l_byte], 'num': NUM_OF_ENTRY, 'byteorder': 'big', 'struct': {'SUB_CAP_NAME': [u_bit,l_bit]}}
					is_utf8 = True if (('datatype' in cont) and (cont['datatype'] == 'utf8')) else False
					is_ascii = True if (('datatype' in cont) and (cont['datatype'] == 'ascii')) else False
					big_endian = True if ( is_utf8 or is_ascii or (('byteorder' in cont) and (cont['byteorder'] == 'big')) ) else False

					if cont['num'] == 0: cont['num'] = 1
					else:
						start_idx = cont['start_idx'] if ('start_idx' in cont.keys()) else 0 
						mem_read = {} if start_idx else []

					(l_byte, u_byte) = (min(cont['pos']), max(cont['pos']))
					entry_size = (u_byte-l_byte+1) // cont['num']
					for i in xrange(cont['num']):
						fmt = "<%s"%("B"*(entry_size))
						data = struct.unpack(fmt, binary[l_byte+i*entry_size:l_byte+(i+1)*entry_size])
						if big_endian: data = data[::-1]
						data = int(sum( map(lambda x: data[x]<<(8*x), range(len(data)) ) ))
						if (is_utf8 or is_ascii): entry = ("%x"%(data)).decode('hex').rstrip('\x00')
						else:
							entry = DataBuffer(data)
							map(lambda a: entry.__setattr__(a, int((data>>min(cont['struct'][a]))&(2**(max(cont['struct'][a])-min(cont['struct'][a])+1)-1)) ), 
								cont['struct'].keys())
						try:
							if isinstance(mem_read, dict): mem_read.update({i+start_idx: entry})
							else: mem_read.append(entry)
						except:
							mem_read = entry
			except:
				mem_read = 0
			parseAttr.__setattr__(attr, mem_read)
		
		return parseAttr

	def set_ori_log(self): self.__ori_log = True

	def set_device_path(self, path):
		self.__path = None
		if self.check_device(path) != 0: return 1
		path = re.search("(?:/\w+)+/nvme\d+", path).group(0)
		self.__path = path
		return 0

	def check_device(self, path=None):
		path = path if path is not None else self.__path
		cmd = "find %s &> /dev/null" %(path)
		if CMD(cmd).exe().returncode !=0 :
			logging.error("%s: no such device!" %(path)) 
			return 1
		return 0

	def update_info(self):
		if self.check_device() != 0: return 1
		return 0

	def on_off(self, on_off, por_opt="spor"):
		cmd = "lsblk"
		lsblk = CMD(cmd).get_stdout("multi_line")
		try:
			PSH__path = "/dev/" + re.findall("[a-z,0-9]+ +8:16 +1 +1.4M +0 +disk", lsblk)[0].split(" ")[0]
		except:
			logging.error("Get \"power switch handle\" port error!!!") 
			return 1		

		logging.info("Switching %s the device." %(on_off)) 
		cmd = "./PWOnOff %s %s %s %s" %(PSH__path, self.__path, por_opt, on_off)
		proc = CMD(cmd, BIN__path).exe()
		if proc.returncode != 0:
			logging.error("Error while switching %s the device!!!" %(on_off)) 
			return proc.returncode
		else: # On / Off success
			if on_off == "on": 
				sleep(2)
				cmd = "lspci -n"
				proc = CMD(cmd)
				lspci = proc.get_stdout("multi_line")
				if lspci == None: return 1
				else: # lspci success
					re_str = "^((?:0[xX])?[\da-fA-F]+:(?:0[xX])?[\da-fA-F]+\.(?:0[xX])?[\da-fA-F]+)[\t ]+0108:.+$"
					addr_list = re.findall(re_str, lspci, flags=re.MULTILINE)

					for addr in addr_list:
						cmd = "echo 1 > /sys/bus/pci/devices/0000:%s/remove" %(addr)
						proc = CMD(cmd).exe()
						if proc.returncode != 0 : return 1

					cmd = "echo 1 > /sys/bus/pci/rescan"
					proc = CMD(cmd).exe()
					if proc.returncode != 0 : return 1

				sleep(2)
		return 0

	def path(self): return self.__path
 
 #################################################################################################################

 	def get_block_path(self, ns, timeout=0):
 		# Retrieves the block path for the device's ns
 		if self.__path == None: return None

 		cmd = "ls %sn*" %(self.__path)
 		proc = CMD(cmd, timeout=timeout)
 		LS = proc.get_stdout("multiline")
		if LS == None : return proc

		try:
			LS = map(int, re.findall('%sn(\d+)\s+'%(self.__path), LS, flags=re.MULTILINE))
		except:
			LS = []

		parsed_block_path = DataBuffer()
		for block in LS:
			get_ns_id = self.get_ns_id(block=block, timeout=timeout)
			if get_ns_id.returncode == 0:
				if get_ns_id.ns == ns:
					parsed_block_path.block = block
					parsed_block_path.path = "%sn%d"%(self.__path, block)
					parsed_block_path.returncode = 0
					return parsed_block_path

		parsed_block_path.returncode = 0xff
		return parsed_block_path

 	def get_ns_id(self, block, timeout=0):
 		# Retrieves the NS for the block device ("%sn%d"%(self.device, block)).
 		if self.__path == None: return None

 		cmd = "nvme get-ns-id %sn%d" %(self.__path, block)
 		proc = CMD(cmd, timeout=timeout)
 		NS = proc.get_stdout("line")
		if NS == None : return proc

		parsed_NS = DataBuffer()
		try:
			parsed_NS.ns = int(re.findall('namespace-id\s*:\s*(\d+)', NS)[0])
			parsed_NS.returncode = proc.returncode
		except:
			parsed_NS.ns = None
			parsed_NS.returncode = 0xf
			
 		return parsed_NS

 	def get_register(self, timeout=0):
 		
		parsed_register = DataBuffer()
		parsed_register.returncode = 0
 		PCI_HEADER = super(NVMe, self).get_register(self.PCI_HEADER)
 		parsed_register.returncode = PCI_HEADER.returncode
 		if parsed_register.returncode != 0: return parsed_register

 		addr = (PCI_HEADER.MUBAR.BA << 32) + (PCI_HEADER.MLBAR.BA << 14)

 		#-----------------------Open /dev/mem---------------------
 		fd, max_retry= -1, 10
		for retry_i in xrange(max_retry):
			try:
				fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
			except OSError as e:
				fd = -(e.errno)

			if fd >= 0 : break
			sleep(random.randint(30, 150)/1000.0)

		parsed_register.returncode = fd if fd < 0 else 0
		try:
			mem = mmap.mmap(fd, 0x1030, offset=addr)
			os.close(fd)
		except:
			return parsed_register

		#-----------Parse the register's content from /dev/mem-------- 
		Controller_Register = self.__Controller_Registers['CTRL_REGS']
		for symbol in Controller_Register['regs']:
			symbol_offset = Controller_Register['regs'][symbol]['offset']
			symbol_regs = Controller_Register['regs'][symbol]['regs']
			reg_size = max(symbol_offset)-min(symbol_offset)+1

			mem.seek(min(symbol_offset))
			fmt = "<%s"%("B"*(reg_size))
			mem_read = struct.unpack(fmt, mem.read(reg_size))
			mem_read = sum( map(lambda x: mem_read[x]<<(8*x), range(len(mem_read)) ) )
			tmp = DataBuffer(mem_read)
			if isinstance(symbol_regs, dict):
				map(lambda r: tmp.__setattr__(r, (mem_read>>min(symbol_regs[r]))&(2**(max(symbol_regs[r])-min(symbol_regs[r])+1)-1)), 
				symbol_regs.keys())

			parsed_register.__setattr__(symbol, tmp)

		return parsed_register

	def set_register(self, timeout=0):
		parsed_register = DataBuffer()
		parsed_register.returncode = 0
 		PCI_HEADER = super(NVMe, self).get_register(self.PCI_HEADER)

 		parsed_register.returncode = PCI_HEADER.returncode
 		if parsed_register.returncode != 0: return parsed_register
 		Controller_Register = self.__Controller_Registers['CTRL_REGS']

 		addr = (PCI_HEADER.MUBAR.BA << 32) + (PCI_HEADER.MLBAR.BA << 14)
	
 		class ControllerRegisrer(DataBuffer):
 			returncode = 0
			prev_symbol = ""
			def __init__(self, symbol=None):
				self.__dict__['prev_symbol'] = symbol

			def __setattr__(self, symbol, value):

				#-----------Parse the register's content from /dev/mem--------
				target_symbol = symbol
				symbol = self.prev_symbol if self.prev_symbol else symbol
				try: # if Register exists:
					symbol_offset = Controller_Register['regs'][symbol]['offset']
					symbol_regs = Controller_Register['regs'][symbol]['regs']

					reg_size_bit = (max(symbol_regs[target_symbol])-min(symbol_regs[target_symbol])+1) if self.prev_symbol else 0
					reg_size = (reg_size_bit//8) if self.prev_symbol else (max(symbol_offset)-min(symbol_offset)+1)
					offset = min(symbol_offset) + ((min(symbol_regs[target_symbol])//8) 
													if self.prev_symbol else 0)
				except:
					logging.error("Error!!! No such register (%s%s)!!!"%(
						"%s."%(self.prev_symbol) if self.prev_symbol else "", target_symbol))
					self.__dict__['returncode'] = 1
					return self

				#-----------------------Open /dev/mem---------------------
		 		fd, max_retry= -1, 10
				for retry_i in xrange(max_retry):
					try:
						fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
					except OSError as e:
						fd = -(e.errno)

					if fd >= 0 : break
					sleep(random.randint(30, 150)/1000.0)

				parsed_register.returncode = fd if fd < 0 else 0
				try:
					mem = mmap.mmap(fd, 0x1030, offset=addr)
				except:
					os.close(fd)
					return parsed_register

				#-----------------------Read then Write reg---------------------
				try:
					mem.seek(offset)
					fmt = "<%s"%("B"*reg_size)
					mem_read = struct.unpack(fmt, mem.read(reg_size))
					mem_read = sum( map(lambda x: mem_read[x]<<(8*x), range(len(mem_read)) ) )

					value = (value&2**(reg_size*8)-1)<<((min(symbol_regs[target_symbol])//8) 
													if self.prev_symbol else 0)

					mask = ~(((2**(reg_size*8)-1)<<(min(symbol_regs[target_symbol])//8)) 
													if self.prev_symbol else 0)

					value = ((mem_read&mask)|value)

					mem.seek(offset)
					bytes = [ (value>>(8*i))&0xff for i in xrange(reg_size) ]
					mem.write(struct.pack(fmt, *bytes))

					os.close(fd)
				except:
					logging.error("Error!!! Write register (%s%s) failed!!!"%(
						"%s."%(self.prev_symbol) if self.prev_symbol else "", target_symbol))
					self.__dict__['returncode'] = 1
					os.close(fd)
					return self

			def __getattr__(self, symbol):
				register = ControllerRegisrer(symbol)
				return register

		return ControllerRegisrer()

	def device_self_test(self, action, ns):
		if isinstance(action, int):
			stc = action & 0xf
		else:
			stc = {
				"short": 0x1,
				"extended": 0x2,
				"vendor": 0xe,
				"abort": 0xf
			}
			stc = stc.get(action, 0)
			if stc == 0: return None 

		proc = DataBuffer()
		fd = nvme_ioctl.open_path(self.__path)
		if fd < 0: 
			Status_Field = DataBuffer(fd)
			Status_Field.SC, Status_Field.SCT = fd, 0
			proc.returncode = Status_Field
			return proc

		ret = nvme_ioctl.nvme_device_self_test(fd, action, ns)

		os.close(fd)

		Status_Field = StatusField(ret['status_field'])
		(Status_Field.DNR, Status_Field.M, 
			Status_Field.SCT, Status_Field.SC) = ((ret['status_field']>>14)&0x1, (ret['status_field']>>13)&0x1, 
													(ret['status_field']>>8)&0x3, ret['status_field']&0xff)
		proc.returncode = Status_Field
		return proc

	def get_feature(self, feature, select, ns=1, value={}, opt_arg="", raw=False):
		if self.__path == None: return None
		if isinstance(feature, int): fid = feature & 0xff
		else:
			fid = {
				"arbitration": 0x1,
				"power_management": 0x2, 
				"LBA_range_type": 0x3, "LBA": 0x3, 
				"temperature_threshold": 0x4, "temperature": 0x4, "TMPTH": 0x4,
				"error_recovery": 0x5,
				"volatile_write_cache": 0x6, "VWC": 0x6,
				"num_of_queues": 0x7,
				"interrupt_coalescing": 0x8, "int_coalesce": 0x8,
				"interrupt_vector_configuration": 0x9, "int_vect": 0x9,
				"autonomous_power_state_transition": 0xc, "APST": 0xc,
				"host_memory_buffer": 0xd, "HMB": 0xd, 
				"non_operational_power_state_config": 0x11, "NOPSC": 0x11,
				"software_progress_marker": 0x80, "SWPM": 0x80
			}.get(feature, 0)

		if isinstance(select, int): SEL = select & 0x7
		else:
			SEL = {
				"current": 0x0,
				"default": 0x1,
				"saved": 0x2,
				"supported_capabilities": 0x3
			}.get(select, 7) # 7 is a reserved value for the SEL field

		cdw11_val, data_len = 0, 0
		parsed_attribute = DataBuffer()

		proc = DataBuffer()
		fd = nvme_ioctl.open_path(self.__path)
		if fd < 0: 
			Status_Field = DataBuffer(fd)
			Status_Field.SC, Status_Field.SCT = fd, 0
			proc.returncode = Status_Field
			return proc

		if fid == 0x1: # arbitration
			attributes = {'HPW': [31,24], 'MPW': [23,16], 'LPW': [15,8], 'AB': [2,0]}
		elif fid == 0x2: # power_management
			attributes = {'WH': [7,5], 'PS': [4,0]}
		elif fid == 0x3: # LBA_range_type
			data_len = 64*64
			attributes = {'NUM': [5,0]}
			attributes_DataStruct = {'LBA_range': {'pos': [data_len-1,0], 'num': 64, 
													'struct': {'TYPE': [0,7], 'ATTR':[8,15], 'SLBA':[128,191], 'NLB':[192,255], 'GUID':[256,383]}
													}
									}
		elif fid == 0x4: # temperature_threshold
			# value = {"THSEL": x, "TMPSEL": xx}
			cdw11_attr ={'THSEL': [21,20], 'TMPSEL': [19,16]}
			cdw11_val = sum( map(lambda a: ((value[a]&(2**(max(cdw11_attr[a])-min(cdw11_attr[a])+1)-1))<<min(cdw11_attr[a])) 
											if (a in cdw11_attr.keys()) else 0, 
								value.keys() ) )
			attributes = {'THSEL': [21,20], 'TMPSEL': [19,16], 'TMPTH': [15,00]}
		elif fid == 0x5: # error_recovery
			attributes = {'DULBE': [16], 'TLER': [15,00]}
		elif fid == 0x6: # volatile_write_cache
			attributes = {'WCE': [0]}
		elif fid == 0x7: # num_of_queues
			attributes = {'NCQA': [31,16], 'NSQA': [15,00]}
		elif fid == 0x8: # interrupt_coalescing
			attributes = {'TIME': [15,8], 'THR': [7,0]}
		elif fid == 0x9: # interrupt_vector_configuration
			# value = {"IV": xx}
			cdw11_attr ={'IV': [15,00]}
			cdw11_val = sum( map(lambda a: ((value[a]&(2**(max(cdw11_attr[a])-min(cdw11_attr[a])+1)-1))<<min(cdw11_attr[a])) 
											if (a in cdw11_attr.keys()) else 0, 
								value.keys() ) )
			attributes = {'CD': [16], 'IV': [15,00]}
		elif fid == 0xc: # autonomous_power_state_transition
			attributes = {'APSTE': [0]}
			data_len = 8*32
			attributes_DataStruct = {'entry': {'pos': [data_len-1,0],'num': 32, 'struct': {'ITPT': [31,8], 'ITPS':[7,3]}}}
		elif fid == 0xd: # host_memory_buffer
			attributes = {'EHM': [0]}
			attributes_DataStruct = {'HSIZE': [3,0], 'HMDLAL': [7,4], 'HMDLAU': [11,8], 'HMDLEC': [15,12]}
			data_len = 4096
		elif fid == 0x11: # non_operational_power_state_config
			attributes = {'NOPPME': [0]}
		elif fid == 0x80: # software_progress_marker
			attributes = {'PBSLC': [7,0]}
		else:
			data_len = opt_arg if isinstance(opt_arg, int) else data_len
			attributes = {'Attr': [31,0]}
			attributes_DataStruct = {'DataStruct': [data_len-1,0]}
			cdw11_val = value if isinstance(value, int) else 0

		if SEL == 3:
			attributes = {'changeable': [2], 'ns_specific': [1], 'saveable': [0]}
			data_len = 0
					
		ret = nvme_ioctl.nvme_get_feature(fd, ns, fid, SEL, cdw11_val, data_len)

		os.close(fd)
		proc = DataBuffer(ret['result'])
		try:
			map(lambda a: proc.__setattr__(a, (ret['result']>>min(attributes[a]))&(2**(max(attributes[a])-min(attributes[a])+1)-1)), 
			attributes.keys())
		except:
			map(lambda a: proc.__setattr__(a, 0), attributes.keys())

		if data_len: 
			proc = self._parseStructure(attributes_DataStruct, ret['data'], proc)
			if not raw:
				if fid == 0x3: proc.LBA_range = proc.LBA_range[:proc.NUM+ 1]				# LBA_range_type
				# elif fid == 0xc: proc.entry = map(lambda e: proc.entry[e], xrange(1+max([-1]+[e for e in range(32) if proc.entry[e]!={'ITPS': 0, 'ITPT': 0}]))) # autonomous_power_state_transition
				elif fid == 0xc: proc.entry = dict([(e,proc.entry[e]) for e in range(32) if proc.entry[e]!={'ITPS': 0, 'ITPT': 0}])

		Status_Field = StatusField(ret['status_field'])
		(Status_Field.DNR, Status_Field.M, 
			Status_Field.SCT, Status_Field.SC) = ((ret['status_field']>>14)&0x1, (ret['status_field']>>13)&0x1, 
													(ret['status_field']>>8)&0x3, ret['status_field']&0xff)
		proc.returncode = Status_Field
		return proc

	def get_log_page(self, log_page, ns=0xffffffff, opt_arg="", timeout=0):
		if self.__path == None: return None
		if isinstance(log_page, int): lid = log_page & 0xff
		else:
			lid = {
				"ErrorInfo": 0x1, 
				"SMART": 0x2, "smart": 0x2,
				"FWSlotInfo": 0x3,
				"CommandEffects": 0x5, 
				"Device_Self_test": 0x6, "DST": 0x6,
				"sanitize": 0x81
			}.get(log_page, 0x0) # 0x0 is a reserved value for the Log Identifier

		rae, data_len = False, 0
		proc = DataBuffer()

		fd = nvme_ioctl.open_path(self.__path)
		if fd < 0: 
			Status_Field = DataBuffer(fd)
			Status_Field.SC, Status_Field.SCT = fd, 0
			proc.returncode = Status_Field
			return proc

		if lid == 0x1: # ErrorInfo
			entries = int(opt_arg) if opt_arg else 64
			data_len = entries*64
			log_structure = {'LogEntry': {'pos': [data_len-1,0], 'num': entries, 'struct': {'ERROR_COUNT': [63,0], 'SQID': [79,64], 'CMDID': [95,80], 
																					'STATUS_FIELD': [111,96], 'PARM_ERROR_LOCATION': [127,112], 
																					'LBA': [191,128], 'NSID': [223,192], 'VS': [231,224], 'CS': [319,256]}}, 
							}
		# elif lid == 0x2: # SMART
		# 	data_len = 512
		# 	log_structure = {'critical_warning': {'pos': [0], 'num': 0,'struct': {'available_spare': [0], 'temperature':[1], 
		# 																		'subsystem_reliability':[2], 'media_read_only':[3], 
		# 																		'volatile_backup_fail':[4]}}, 
		# 					'composite_temperature': [2,1], 'available_spare': [3], 'available_spare_threshold': [4], 
		# 					'percentage_used': [5], 'data_units_read': [32,47], 'data_units_written': [48,63], 
		# 					'host_read_commands': [64,79], 'host_write_commands': [80,95], 'controller_busy_time': [96,111], 
		# 					'power_cycles': [112,127], 'power_on_hours': [128,143], 'unsafe_shutdowns': [144,159], 
		# 					'media_errors': [160,175], 'num_err_log_entries': [176,191], 'warning_temperature_time': [192,195], 
		# 					'critical_temperature_time': [196,199], 
		# 					'temperature_sensor': {'pos': [215,200], 'num': 8, 'start_idx': 1, 'struct': {'TST': [15,0]}}
		# 					}
		elif lid == 0x3: # FWSlotInfo (Firmware Slot Information)
			data_len = 512
			log_structure = {'AFI': [0], 'FRS1': [15,8], 'FRS2': [23,16], 'FRS3': [31,24], 
							'FRS4': [39,32], 'FRS5': [47,40], 'FRS6': [55,48], 'FRS7': [63,56]}
		elif lid == 0x5: # CommandEffects(Commands Supported and Effects)
			data_len = 2048
			log_structure = {'ACS': {'pos': [1023,0], 'num': 256, 'struct': {'CSE': [18,16], 'CCC': [4], 'NIC': [3], 
																		'NCC': [2], 'LBCC': [1], 'CSUPP': [0]}}, 
							'IOCS': {'pos': [2047,1024], 'num': 256, 'struct': {'CSE': [18,16], 'CCC': [4], 'NIC': [3], 
																		'NCC': [2], 'LBCC': [1], 'CSUPP': [0]}}
							}
		elif lid == 0x6: # DST
			data_len = 564
			log_structure = {'current_DST': {'pos': [1,0], 'num': 0, 'struct': {'operation': [3,0], 'completion': [14,8]}}, 
							'self_test_result': {'pos': [data_len-1,4], 'num': 20, 'struct': {'STC': [7,4], 'ST_result': [3,0], 'seg_num': [8,15], 
																					'SC_valid': [19], 'SCT_valid': [18], 'FLBA_valid': [17], 'NSID_valid': [16], 
																					'POH': [95,32], 
																					'NSID': [127,96], 'FLBA': [191,128], 'SCT': [194,192], 'SC': [207,200]}}, 
							}
		elif lid == 0x81: # Sanitize
			data_len = 512
			log_structure = {'SPROG': [1,0], 'ETOW': [11,8], 'ETBE': [15,12], 'ETCE': [19,16],  
							'SSTAT': {'pos': [3,2], 'num': 0,'struct': {'STATUS': [2,0], 'NCP':[7,3], 'GDE':[8]}}, 
							'SCDW10': {'pos': [3,2], 'num': 0,'struct': {'SANACT': [2,0], 'AUSE':[3], 'OWPASS':[7,4], 
																		'OIPBP':[8], 'NDEAC':[9]}}
							}
		else:
			data_len = opt_arg if isinstance(opt_arg, int) else data_len
			log_structure = {'DataStruct': [data_len-1,0]}

		ret = nvme_ioctl.nvme_get_log(fd, ns, lid, rae, data_len)
		os.close(fd)

		proc = self._parseStructure(log_structure, ret['data'])

		Status_Field = StatusField(ret['status_field'])
		(Status_Field.DNR, Status_Field.M, 
			Status_Field.SCT, Status_Field.SC) = ((ret['status_field']>>14)&0x1, (ret['status_field']>>13)&0x1, 
													(ret['status_field']>>8)&0x3, ret['status_field']&0xff)
		proc.returncode = Status_Field
		return proc

	def identify(self, identify, ns=0, timeout=0):
		if isinstance(identify, int): cns = identify & 0xff
		else:
			cns = {
				"id_ns": 0x0,
				"id_ctrl": 0x1,
				"list_ns": 0x2
			}.get(identify, 0xff) # 0xff is a reserved value for the CNS value

		parsed_identify = DataBuffer()
		
		proc = DataBuffer()
		fd = nvme_ioctl.open_path(self.__path)
		if fd < 0: 
			Status_Field = DataBuffer(fd)
			Status_Field.SC, Status_Field.SCT = fd, 0
			proc.returncode = Status_Field
			return proc

		if cns == 0x0: # id_ns
			idfy_structure = {	'NSZE': [7,0], 'NCAP': [15,8], 'NUSE': [23,16], 'NSFEAT': [24], 'NLBAF': [25], 'FLBAS': [26], 
								'MC': [27], 'DPC': [28], 'DPS': [29], 'NMIC': [30], 'RESCAP': [31], 'FPI': [32], 'DLFEAT': [33], 
								'NAWUN': [35,34], 'NAWUPF': [37,36], 'NACWU': [39,38], 'NABSN': [41,40], 'NABO': [43,42], 
								'NABSPF': [45,44], 'NOIOB': [47,46], 'NVMCAP': [63,48], 
								'NGUID': {'pos': [119,104], 'num': 0, 'byteorder': 'big', 'struct': {}},
								'EUI64': {'pos': [127,120], 'num': 0, 'byteorder': 'big', 'struct': {}},
								'LBAF': {'pos': [191,128], 'num': 16, 'struct': {'RP': [25,24], 'LBADS': [23,16], 'MS': [15,0], }},
							}
		elif cns == 0x1: # id_ctrl
			idfy_structure = {	'VID': [1,0], 'SSVID': [3,2], 
								'SN': {'pos': [23,4], 'num': 0, 'byteorder': 'big', 'datatype': 'ascii', 'struct': {}},
								'MN': {'pos': [63,24], 'num': 0, 'byteorder': 'big', 'datatype': 'ascii', 'struct': {}},
								'FR': {'pos': [71,64], 'num': 0, 'byteorder': 'big', 'datatype': 'ascii', 'struct': {}},
								'RAB': [72], 'IEEE': [75,73], 'CMIC': [76], 'MDTS': [77], 'CNTLID': [79,78], 'VER': [83,80], 
								'RTD3R': [87,84], 'RTD3E': [91,88], 'OAES': [95,92], 'CTRATT': [99,96], 'FGUID': [127,112], 
								'OACS': [257,256], 	'ACL': [258], 'AERL': [259], 	'FRMW': [260], 'LPA': [261], 
								'ELPE': [262], 'NPSS': [263], 'AVSCC': [264], 'APSTA': [265], 'WCTEMP': [267,266], 
								'CCTEMP': [269,268], 'MTFA': [271,270], 'HMPRE': [275,272], 'HMMIN': [279,276], 
								'TNVMCAP': [295,280], 'UNVMCAP': [311,296], 'RPMBS': [315,312], 'EDSTT': [317,316], 
								'DSTO': [318], 'FWUG': [319], 'KAS': [321,320], 'HCTMA': [323,322], 'MNTMT': [325,324], 
								'MXTMT': [327,326], 'SANICAP': [331,328], 'SQES': [512], 'CQES': [513], 'MAXCMD': [515,514], 
								'NN': [519,516], 'ONCS': [521,520], 'FUSES': [523,522], 'FNA': [524], 'VWC': [525], 
								'AWUN': [527,526], 'AWUPF': [529,528], 'NVSCC': [530], 'ACWU': [533,532], 'SGLS': [539,536], 
								'SUBNQN': {'pos': [1023,768], 'num': 0, 'byteorder': 'big', 'datatype': 'utf8', 'struct': {}},
								'PSD': {'pos': [3071,2048], 'num': 32, 'struct': {'APS': [183,182], 'APW': [178,176], 'ACTP': [175,760], 
																				'IPS': [151,150], 'IDLP': [143,128], 'RWL': [124,120], 
																				'RWT': [116,112], 'RRL': [108,104], 'RRT': [100,96], 
																				'EXLAT': [95,64], 'ENLAT': [63,32], 'NOPS': [25], 
																				'MXPS': [24], 'MP': [15,0], }},
							}
		elif cns == 0x2: # list_ns
			idfy_structure = {	'ns': {'pos': [4095,0], 'num': 1024, 'struct': {}} }
			
		else: # Others identify
			idfy_structure = {'DataStruct': [4095,0]}

		ret = nvme_ioctl.nvme_identify(fd, ns, cns)
		os.close(fd)

		# Uses ioctl method
		proc = self._parseStructure(idfy_structure, ret['data'])

		Status_Field = StatusField(ret['status_field'])
		(Status_Field.DNR, Status_Field.M, 
			Status_Field.SCT, Status_Field.SC) = ((ret['status_field']>>14)&0x1, (ret['status_field']>>13)&0x1, 
													(ret['status_field']>>8)&0x3, ret['status_field']&0xff)

		if (cns == self.ID_NS) and (Status_Field == 0x0): self.identify_NS[ns] = proc
		if (cns == self.LIST_NS) and (Status_Field == 0x0): proc.ns = list(set(map(int, proc.ns)) - set([0]))
		proc.returncode = Status_Field
		return proc

	def ns_attachment(self, sel, ns, cntlist=[]):
		proc = DataBuffer()
		fd = nvme_ioctl.open_path(self.__path)
		if fd < 0: 
			Status_Field = DataBuffer(fd)
			Status_Field.SC, Status_Field.SCT = fd, 0
			proc.returncode = Status_Field
			return proc

		if isinstance(cntlist, int): cntlist = [cntlist]
		elif not cntlist: cntlist = []

		ret = nvme_ioctl.nvme_ns_attachment(fd, ns, len(cntlist), cntlist, sel)
		
		os.close(fd)

		Status_Field = StatusField(ret['status_field'])
		(Status_Field.DNR, Status_Field.M, 
			Status_Field.SCT, Status_Field.SC) = ((ret['status_field']>>14)&0x1, (ret['status_field']>>13)&0x1, 
													(ret['status_field']>>8)&0x3, ret['status_field']&0xff)
		proc.returncode = Status_Field
		if proc.returncode == 0x0: self.identify_NS.pop(ns, None)
		return proc

	def ns_management(self, sel, data_struct):
		# data_struct = {'NSZE': xx, 'NCAP': xxx, 'FLBAS': x, 'DPS': x, 'NMIC': x} if self.NS_CREATE
		# data_struct = {'NS': ns} if self.NS_DELETE
		proc = DataBuffer()
		fd = nvme_ioctl.open_path(self.__path)
		if fd < 0: 
			Status_Field = DataBuffer(fd)
			Status_Field.SC, Status_Field.SCT = fd, 0
			proc.returncode = Status_Field
			return proc

		if not isinstance(data_struct, DataBuffer): data_struct = DataBuffer(data_struct)

		if sel == self.NS_CREATE: 
			[flbas, dps, nmic] = map(lambda x: data_struct[x] if (x in data_struct.keys()) else 0,
									['FLBAS', 'DPS', 'NMIC'])
			ret = nvme_ioctl.nvme_ns_create(fd, data_struct.NSZE, data_struct.NCAP, flbas, dps, nmic)
		else: # sel == self.NS_DELETE
			ret = nvme_ioctl.nvme_ns_delete(fd, data_struct.NS) 
		
		os.close(fd)

		Status_Field = StatusField(ret['status_field'])
		(Status_Field.DNR, Status_Field.M, 
			Status_Field.SCT, Status_Field.SC) = ((ret['status_field']>>14)&0x1, (ret['status_field']>>13)&0x1, 
													(ret['status_field']>>8)&0x3, ret['status_field']&0xff)
		proc.returncode = Status_Field
		if sel == self.NS_CREATE: proc.NS = ret['result']
		if proc.returncode == 0x0: self.identify_NS.pop(data_struct.NS if (sel == self.NS_DELETE) else ret['result'], None)
		return proc

	def set_feature(self, feature, value, save=False, ns=0xffffffff, opt_arg=""):
		if self.__path == None: return None
		if isinstance(feature, int): fid = feature & 0xff
		else:
			fid = {
				"arbitration": 0x1,
				"power_management": 0x2, 
				"LBA_range_type": 0x3, "LBA": 0x3, 
				"temperature_threshold": 0x4, "temperature": 0x4, "TMPTH": 0x4,
				"error_recovery": 0x5,
				"volatile_write_cache": 0x6, "VWC": 0x6,
				"num_of_queues": 0x7,
				"interrupt_coalescing": 0x8, "int_coalesce": 0x8,
				"interrupt_vector_configuration": 0x9, "int_vect": 0x9,
				"autonomous_power_state_transition": 0xc, "APST": 0xc,
				"host_memory_buffer": 0xd, "HMB": 0xd, 
				"non_operational_power_state_config": 0x11, "NOPSC": 0x11,
				"software_progress_marker": 0x80, "SWPM": 0x80
			}.get(feature, 0)
		
		(cdw12, cdw13, cdw14, cdw15, pattern) = (0, 0, 0, 0, 0)

		proc = DataBuffer()
		fd = nvme_ioctl.open_path(self.__path)
		if fd < 0: 
			Status_Field = DataBuffer(fd)
			Status_Field.SC, Status_Field.SCT = fd, 0
			proc.returncode = Status_Field
			return proc

		if not isinstance(value, DataBuffer): value = DataBuffer(value)

		if fid == 0x1: # arbitration
			# value = {"HPW": x, "MPW": xx, "LPW": xxx, "AB": xxxx}
			attributes = {'HPW': [31,24], 'MPW': [23,16], 'LPW': [15,8], 'AB': [2,0]}
		elif fid == 0x2: # power_management
			# value = {"WH": x, "PS": xx}
			attributes = {'WH': [7,5], 'PS': [4,0]}
		elif fid == 0x3: # LBA_range_type
			attributes = {'NUM': [5,0]}
			try:
				pattern = ""
				for entry_i in value['LBA_range']:
					pattern += "%02x%02x%028x" %(entry_i['TYPE'], entry_i['ATTR'], 0)
					pattern += struct.pack('<Q', entry_i['SLBA']).encode('hex') # little endian
					pattern += struct.pack('<Q', entry_i['NLB']).encode('hex') # little endian
					pattern += struct.pack('<QQ', entry_i['GUID']&0xffffffffffffffff, (entry_i['GUID']>>64)&0xffffffffffffffff).encode('hex') # little endian
					pattern += "%032x" %(0)
			except AttributeError as e:
				pattern = "00"*(64*64)
				logging.warning("Warning!!! (%s), set pattern to (%s)."%(e, pattern))
			pattern = pattern.decode("hex")
		elif fid == 0x4: # temperature_threshold
			# value = {'THSEL': x, 'TMPSEL': xx, 'TMPTH': xx}
			attributes = {'THSEL': [21,20], 'TMPSEL': [19,16], 'TMPTH': [15,00]}
		elif fid == 0x5: # error_recovery
			# value = {'DULBE': x, 'TLER':xx}
			attributes = {'DULBE': [16], 'TLER': [15,00]}
		elif fid == 0x6: # volatile_write_cache
			# value = {"WCE": x}
			attributes = {'WCE': [0]}
		elif fid == 0x7: # num_of_queues
			# value = {"NCQR": x, "NSQR": xx}
			attributes = {'NCQR': [31,16], 'NSQR': [15,00]}
		elif fid == 0x8: # interrupt_coalescing
			# value = {"TIME": x, "THR": xx}
			attributes = {'TIME': [15,8], 'THR': [7,00]}
		elif fid == 0x9: # interrupt_vector_configuration
			# value = {"CD": x, "IV": xx}
			attributes = {'CD': [16], 'IV': [15,00]}
		elif fid == 0xc: # autonomous_power_state_transition
			# value = {'APSTE': x, 'entry': {0:{'ITPS': 3, 'ITPT': 200}, 1:{...}, ...}}
			attributes = {'APSTE': [0]}
			data_len = 8*32
			try:
				pattern = ''.join(map(lambda entryVal: struct.pack('<Q', entryVal).encode('hex'), 
							map(lambda ps:((0xffffff & value['entry'][ps]['ITPT']) << 8) | ((0x1f & value['entry'][ps]['ITPS']) << 3) if (ps in value['entry'].keys()) else 0, 
																																								xrange(31+1))) )
															# ITPT: Bit 31:8							ITPS: Bit 7:3	
			except AttributeError as e:
				pattern = "0"*data_len
				logging.warning("Warning!!! (%s), set pattern to (%s)."%(e, pattern))
			pattern = pattern.decode("hex")
		elif fid == 0xd: # host_memory_buffer
			# value = {"EHM": x, "MR": x, "HSIZE": x, "HMDLLA": x, "HMDLUA": x, "HMDLEC": x}
			attributes = {'MR': [1], 'EHM': [0]}
			cdw12 = (value.HSIZE&0xffffffff) if ('HSIZE' in value.keys()) else cdw12
			cdw13 = (value.HMDLLA&0xffffffff) if ('HMDLLA' in value.keys()) else cdw13
			cdw14 = (value.HMDLUA&0xffffffff) if ('HMDLUA' in value.keys()) else cdw14
			cdw15 = (value.HMDLEC&0xffffffff) if ('HMDLEC' in value.keys()) else cdw15
		elif fid == 0x11: # non_operational_power_state_config
			# value = {"NOPPME": x}
			attributes = {'NOPPME': [0]}
		elif fid == 0x80: # software_progress_marker
			# value = {"PBSLC": x}
			attributes = {'PBSLC': [7,0]}
		else:
			# value = {'Attr': xxx, 'DataStruct': xxxxxxxxx(hex decoded), 'cdw12': xx, ..., 'cdw15': xx }
			attributes = {'Attr': [31,0]}
			pattern = value.DataStruct if ('DataStruct' in value.keys()) else 0 
			cdw12 = (value.cdw12&0xffffffff) if ('cdw12' in value.keys()) else cdw12
			cdw13 = (value.cdw13&0xffffffff) if ('cdw13' in value.keys()) else cdw13
			cdw14 = (value.cdw14&0xffffffff) if ('cdw14' in value.keys()) else cdw14
			cdw15 = (value.cdw15&0xffffffff) if ('cdw15' in value.keys()) else cdw15

		value_i = sum( map(lambda a: ((value[a]&(2**(max(attributes[a])-min(attributes[a])+1)-1))<<min(attributes[a])) 
											if (a in attributes.keys()) else 0, 
								value.keys() ) )
		ret = nvme_ioctl.nvme_set_feature(fd, ns, fid, value_i, cdw12, cdw13, cdw14, cdw15, save, len(pattern) if pattern else 0, pattern)

		os.close(fd)

		# Uses ioctl method
		Status_Field = StatusField(ret['status_field'])
		(Status_Field.DNR, Status_Field.M, 
			Status_Field.SCT, Status_Field.SC) = ((ret['status_field']>>14)&0x1, (ret['status_field']>>13)&0x1, 
													(ret['status_field']>>8)&0x3, ret['status_field']&0xff)
		proc.returncode = Status_Field
		return proc

	def sanitize(self, sanact, no_deac=False, ause=False, ow_arg={}, timeout=0):
		# Sanitize command: nvme sanitize ${device} -a ${action}
		# Ref. NVMe Revision 1.3b spec. PDF p.174
		proc = DataBuffer()
		fd = nvme_ioctl.open_path(self.__path)
		if fd < 0: 
			Status_Field = DataBuffer(fd)
			Status_Field.SC, Status_Field.SCT = fd, 0
			proc.returncode = Status_Field
			return proc

		owpass = ow_arg['OWPASS'] if ('OWPASS' in ow_arg.keys()) else 0x00000000
		if isinstance(owpass, str): owpass = int(owpass, 16)
		oipbp = ow_arg['OIPBP'] if ('OIPBP' in ow_arg.keys()) else 0
		ovrpat = ow_arg['OVRPAT'] if ('OVRPAT' in ow_arg.keys()) else 2
		ret = nvme_ioctl.nvme_sanitize(fd, sanact&0b111, ause, owpass, oipbp, no_deac, ovrpat)

		os.close(fd)

		Status_Field = StatusField(ret['status_field'])
		(Status_Field.DNR, Status_Field.M, 
			Status_Field.SCT, Status_Field.SC) = ((ret['status_field']>>14)&0x1, (ret['status_field']>>13)&0x1, 
													(ret['status_field']>>8)&0x3, ret['status_field']&0xff)
		proc.returncode = Status_Field
		return proc

	def compare(self, ns, SLBA, NLB, content, PRINFO=0, EILBRT=0, ELBATM=0, ELBAT=0, FUA=False, LR=False, timeout=0):
		proc = DataBuffer()
		fd = nvme_ioctl.open_path(self.__path)
		if fd < 0: 
			Status_Field = DataBuffer(fd)
			Status_Field.SC, Status_Field.SCT = fd, 0
			proc.returncode = Status_Field
			return proc

		nblocks = (LR<<31)|(FUA<<30)|((PRINFO&0xf)<<26)|NLB
		ret = nvme_ioctl.nvme_compare(fd, ns, SLBA, nblocks, EILBRT, ELBAT, ELBATM, content['data'], content['metadata'])

		os.close(fd)

		Status_Field = StatusField(ret['status_field'])
		(Status_Field.DNR, Status_Field.M, 
			Status_Field.SCT, Status_Field.SC) = ((ret['status_field']>>14)&0x1, (ret['status_field']>>13)&0x1, 
													(ret['status_field']>>8)&0x3, ret['status_field']&0xff)
		proc.returncode = Status_Field
		return proc

	def dataset_management(self, ns, range_list, AD=False, IDW=False, IDR=False, timeout=0):
		proc = DataBuffer()
		fd = nvme_ioctl.open_path(self.__path)
		if fd < 0: 
			Status_Field = DataBuffer(fd)
			Status_Field.SC, Status_Field.SCT = fd, 0
			proc.returncode = Status_Field
			return proc

		cdw11 = (AD << 2) | (IDW << 1) | (IDR << 0)
		nr_ranges = len(range_list)

		ctxAttrs = {'CAS': [31,24], 'WP': [10], 'SW': [9], 'SR': [8], 'AL': [5,4], 'AF': [3,0]}
		structToVal = lambda dataStructVal, dataStruct: sum( map(lambda a: ((dataStructVal&(2**(max(dataStruct[a])-min(dataStruct[a])+1)-1))<<min(dataStruct[a])) 
															if (a in dataStruct.keys()) else 0, dataStructVal.keys() ) )

		dsm = ''.join(map(lambda entry: ''.join(map(lambda (t,a,mask): struct.pack(t, 0 if (a not in entry) else (structToVal(entry[a],ctxAttrs) if isinstance(entry[a], dict) else (entry[a]&mask) )  ), 
				zip(['<L','<L','<Q'],['ctxAttr','NLB','SLBA'],[0xffffffff,0xffffffff,0xffffffffffffffff])) ), 
		range_list) )

		ret = nvme_ioctl.nvme_dsm(fd, ns, cdw11, dsm, nr_ranges)

		os.close(fd)

		Status_Field = StatusField(ret['status_field'])
		(Status_Field.DNR, Status_Field.M, 
			Status_Field.SCT, Status_Field.SC) = ((ret['status_field']>>14)&0x1, (ret['status_field']>>13)&0x1, 
													(ret['status_field']>>8)&0x3, ret['status_field']&0xff)
		proc.returncode = Status_Field
		return proc

	def flush(self, ns, timeout=0):
		proc = DataBuffer()
		fd = nvme_ioctl.open_path(self.__path)
		if fd < 0: 
			Status_Field = DataBuffer(fd)
			Status_Field.SC, Status_Field.SCT = fd, 0
			proc.returncode = Status_Field
			return proc

		ret = nvme_ioctl.nvme_flush(fd, ns)
		
		os.close(fd)

		Status_Field = StatusField(ret['status_field'])
		(Status_Field.DNR, Status_Field.M, 
			Status_Field.SCT, Status_Field.SC) = ((ret['status_field']>>14)&0x1, (ret['status_field']>>13)&0x1, 
													(ret['status_field']>>8)&0x3, ret['status_field']&0xff)
		proc.returncode = Status_Field
		return proc

	def read(self, ns, SLBA, NLB, PRINFO=0, DSM=0, EILBRT=0, ELBATM=0, ELBAT=0, FUA=False, LR=False, timeout=0):
		proc = DataBuffer()
		fd = nvme_ioctl.open_path(self.__path)
		if fd < 0: 
			Status_Field = DataBuffer(fd)
			Status_Field.SC, Status_Field.SCT = fd, 0
			proc.returncode = Status_Field
			return proc

		try: self.identify_NS[ns]
		except:
			identify_NS = 0x0
			self.identify(identify_NS, ns=ns)

		curr_LBAF = self.identify_NS[ns].FLBAS & 0xf # flbas[3:0]
		ms = self.identify_NS[ns].LBAF[curr_LBAF].MS # metadatasize
		lbads = pow(2, self.identify_NS[ns].LBAF[curr_LBAF].LBADS) # LBA datasize

		data_len, metadata_len = (NLB+1)*lbads, (NLB+1)*ms
		nblocks = (LR<<31)|(FUA<<30)|((PRINFO&0xf)<<26)|NLB
		dsmgmt = DSM
		
		ret = nvme_ioctl.nvme_read(fd, ns, SLBA, nblocks, dsmgmt, EILBRT, ELBAT, ELBATM, data_len, metadata_len)

		os.close(fd)

		Status_Field = StatusField(ret['status_field'])
		(Status_Field.DNR, Status_Field.M, 
			Status_Field.SCT, Status_Field.SC) = ((ret['status_field']>>14)&0x1, (ret['status_field']>>13)&0x1, 
													(ret['status_field']>>8)&0x3, ret['status_field']&0xff)
		proc.returncode = Status_Field
		proc.data = ret['data']
		proc.metadata = ret['metadata']
		proc.protect_info = ret['metadata']

		return proc

	def write(self, ns, SLBA, NLB, content, DTYPE=0, DSPEC=0, PRINFO=0, DSM=0, ILBRT=0, LBATM=0, LBAT=0, FUA=False, LR=False, timeout=0):
		proc = DataBuffer()
		fd = nvme_ioctl.open_path(self.__path)
		if fd < 0: 
			Status_Field = DataBuffer(fd)
			Status_Field.SC, Status_Field.SCT = fd, 0
			proc.returncode = Status_Field
			return proc

		nblocks = (LR<<31)|(FUA<<30)|((PRINFO&0xf)<<26)|((DTYPE&0xf)<<20)|NLB
		dsmgmt = DSM | (DSPEC<<16)
		ret = nvme_ioctl.nvme_write(fd, ns, SLBA, nblocks, dsmgmt, ILBRT, LBAT, LBATM, content['data'], content['metadata'])
		
		os.close(fd)

		Status_Field = StatusField(ret['status_field'])
		(Status_Field.DNR, Status_Field.M, 
			Status_Field.SCT, Status_Field.SC) = ((ret['status_field']>>14)&0x1, (ret['status_field']>>13)&0x1, 
													(ret['status_field']>>8)&0x3, ret['status_field']&0xff)
		proc.returncode = Status_Field
		return proc

	def write_uncor(self, ns, SLBA, NLB, timeout=0):
		proc = DataBuffer()
		fd = nvme_ioctl.open_path(self.__path)
		if fd < 0: 
			Status_Field = DataBuffer(fd)
			Status_Field.SC, Status_Field.SCT = fd, 0
			proc.returncode = Status_Field
			return proc

		ret = nvme_ioctl.nvme_write_uncor(fd, ns, SLBA, NLB)
		
		os.close(fd)

		Status_Field = StatusField(ret['status_field'])
		(Status_Field.DNR, Status_Field.M, 
			Status_Field.SCT, Status_Field.SC) = ((ret['status_field']>>14)&0x1, (ret['status_field']>>13)&0x1, 
													(ret['status_field']>>8)&0x3, ret['status_field']&0xff)
		proc.returncode = Status_Field
		return proc

	def write_zeroes(self, ns, SLBA, NLB, PRINFO=0, ILBRT=0, LBATM=0, LBAT=0, FUA=False, LR=False, DEAC=False, timeout=0):
		proc = DataBuffer()
		fd = nvme_ioctl.open_path(self.__path)
		if fd < 0: 
			Status_Field = DataBuffer(fd)
			Status_Field.SC, Status_Field.SCT = fd, 0
			proc.returncode = Status_Field
			return proc

		control = 0
		control |= (PRINFO << 10)
		if LR: control |= (1 << 15)# NVME_RW_LR;
		if FUA: control |= (1 << 14)# NVME_RW_FUA;
		if DEAC: control |= (1 << 9)# NVME_RW_DEAC;
		ret = nvme_ioctl.nvme_write_zeroes(fd, ns, SLBA, NLB, control, ILBRT, LBAT, LBATM)
		
		os.close(fd)

		Status_Field = StatusField(ret['status_field'])
		(Status_Field.DNR, Status_Field.M, 
			Status_Field.SCT, Status_Field.SC) = ((ret['status_field']>>14)&0x1, (ret['status_field']>>13)&0x1, 
													(ret['status_field']>>8)&0x3, ret['status_field']&0xff)
		proc.returncode = Status_Field
		return proc

	def reset(self, timeout=0):
		proc = DataBuffer()
		fd = nvme_ioctl.open_path(self.__path)
		if fd < 0: 
			Status_Field = DataBuffer(fd)
			Status_Field.SC, Status_Field.SCT = fd, 0
			proc.returncode = Status_Field
			return proc

		ret = nvme_ioctl.nvme_reset_controller(fd)

		os.close(fd)

		Status_Field = StatusField(ret)
		(Status_Field.DNR, Status_Field.M, 
			Status_Field.SCT, Status_Field.SC) = ((ret>>14)&0x1, (ret>>13)&0x1, 
													(ret>>8)&0x3, ret&0xff)
		proc.returncode = Status_Field
		return proc

	def passthru(self, opcode, cmdSet, data_struct={}): # cmdSet: 0 = Admin Command; 1 = I/O Command
		proc = DataBuffer()
		fd = nvme_ioctl.open_path(self.__path)
		if fd < 0: 
			Status_Field = DataBuffer(fd)
			Status_Field.SC, Status_Field.SCT = fd, 0
			proc.returncode = Status_Field
			return proc

		[flags, rsvd, nsid, cdw2, cdw3, cdw10, 
		cdw11, cdw12, cdw13, cdw14, cdw15, data_len, 
		data, metadata_len, metadata, timeout_ms] = map(lambda x: data_struct[x] if (x in data_struct.keys()) else 0,
															['FLAGS', 'RSVD', 'NS', 'CDW2', 'CDW3', 'CDW10', 
															'CDW11', 'CDW12', 'CDW13', 'CDW14', 'CDW15', 'DATA_LEN', 
															'DATA', 'METADATA_LEN', 'METADATA', 'TIMEOUT_MS'])

		ret = nvme_ioctl.nvme_passthru(fd, cmdSet, opcode, flags, rsvd, nsid, cdw2, cdw3, cdw10, cdw11, cdw12, cdw13, 
										cdw14, cdw15, data_len, data, metadata_len, metadata, timeout_ms)

		os.close(fd)

		Status_Field = StatusField(ret['status_field'])
		(Status_Field.DNR, Status_Field.M, 
			Status_Field.SCT, Status_Field.SC) = ((ret['status_field']>>14)&0x1, (ret['status_field']>>13)&0x1, 
													(ret['status_field']>>8)&0x3, ret['status_field']&0xff)
		proc.returncode = Status_Field
		proc.result = ret['status_field']
		proc.data = ret['data'] if ('data' in ret) else None
		proc.metadata = ret['metadata'] if ('metadata' in ret) else None
		return proc

	def admin_passthru(self, opcode, data_struct={}): return self.passthru(opcode, 0, data_struct)

	def io_passthru(self, opcode, data_struct={}): return self.passthru(opcode, 1, data_struct)
	