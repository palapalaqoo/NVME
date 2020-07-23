from Data import *
from CMD import CMD

import logging
import textwrap
import struct
import re

class PCI(object):

	##################################################################################

	PCI_HEADER = [0x0, 'PCI'] 		# PCI Header
	PMCAP = [0x1, 'PCI'] 			# PCI Power Management Capability
	MSICAP = [0x5, 'PCI'] 			# Message Signaled Interrupt Capability
	PXCAP = [0x10, 'PCI']			# PCI Express Capability
	MSIXCAP = [0x11, 'PCI'] 		# MSI-X Capability
	AERCAP = [0x1, 'PCIEext'] 		# Advanced Error Reporting Capability

	##################################################################################

	__System_Bus_Registers = {
		'PCI_HEADER': {'offset': [0x0,0x3f], 'regs': {
			'ID': 	{'offset': [0x0,0x3], 'regs': { 'DID': [31,16], 'VID': [15,00], }}, 
			'CMD': 	{'offset': [0x4,0x5], 'regs': { 'ID': [10], 'FBE': [9], 'SEE': [8], 'PEE': [6], 'VGA': [5], 
													'MWIE': [4], 'SCE': [3], 'BME': [2], 'MSE': [1], 'IOSE': [0], }}, 
			'STS': 	{'offset': [0x6,0x7], 'regs': { 'DPE': [15], 'SSE': [14], 'RMA': [13], 'RTA': [12], 'STA': [11], 
													'DEVT': [10,9], 'DPD': [8], 'FBC': [7], 'C66': [5], 'CL': [4], 
													'IS': [3], }}, 
			'RID': 	{'offset': [0x8,0x8], 'regs': { 'RID': [7,0], }}, 
			'CC': 	{'offset': [0x9,0x9], 'regs': { 'BCC': [23,16], 'SCC': [15,8], 'PI': [7,0], }}, 
			'CLS': 	{'offset': [0xc,0xc], 'regs': { 'CLS': [7,0], }}, 
			'MLT': 	{'offset': [0xd,0xd], 'regs': { 'MLT': [7,0], }}, 
			'HTYPE': {'offset': [0xe,0xe], 'regs': { 'MFD': [7], 'HL': [6,0], }}, 
			'BIST': {'offset': [0xf,0xf], 'regs': { 'BC': [7], 'SB': [6], 'CC': [3,0], }}, 
			'MLBAR': {'offset': [0x10,0x13], 'regs': { 'BA': [31,14], 'PF': [3], 'TP': [2,1], 'RTE': [0], }}, 
			'MUBAR': {'offset': [0x14,0x17], 'regs': { 'BA': [31,0], }}, 
			'BAR2': {'offset': [0x18,0x1b], 'regs': { 'BA': [31,3], 'RTE': [0], }}, 
			'CCPTR': {'offset': [0x28,0x2b], 'regs': [31,0]}, 
			'SS': 	{'offset': [0x2c,0x2f], 'regs': { 'SSID': [31,16], 'SSVID': [15,00], }}, 
			'EROM': {'offset': [0x30,0x33], 'regs': { 'RBA': [31,0], }}, 
			'CAP': 	{'offset': [0x34,0x34], 'regs': { 'CP': [7,0], }},
			'INTR': {'offset': [0x3c,0x3d], 'regs': { 'IPIN': [15,8], 'ILINE': [7,0], }},
			'MGNT': {'offset': [0x3e,0x3e], 'regs': { 'GNT': [7,0], }},
			'MLAT': {'offset': [0x3f,0x3f], 'regs': { 'LAT': [7,0], }},
		}}, 
		'CAP_PM': {'offset': ['CAP_PM','CAP_PM+0x7'], 'regs': {
			'PID': 	{'offset': [0x0,0x1], 'regs': { 'NEXT': [15,8], 'CID': [7,0], }}, 
			'PC': 	{'offset': [0x2,0x3], 'regs': { 'PSUP': [15,11], 'D2S': [10], 'D1S': [9], 'AUXC': [8,6], 
													'DSI': [5], 'PMEC': [3], 'VS': [2,0], }}, 
			'PMCS': {'offset': [0x4,0x5], 'regs': { 'PMES': [15], 'DSC': [14,13], 'DSE': [12,9], 'PMEE': [8], 
													'NSFRST': [3], 'PS': [1,0], }}, 
		}},
		'CAP_MSI': {'offset': ['CAP_MSI','CAP_MSI+0x9'], 'regs': {
			'MID': 	{'offset': [0x0,0x1], 'regs': { 'NEXT': [15,8], 'CID': [7,0], }}, 
			'MC': 	{'offset': [0x2,0x3], 'regs': { 'PVM': [8], 'C64': [7], 'MME': [6,4], 'MMC': [3,1], 
													'MSIE': [0], }}, 
			'MA': 	{'offset': [0x4,0x7], 'regs': { 'ADDR': [31,2], }}, 
			'MUA': 	{'offset': [0x8,0xb], 'regs': { 'UADDR': [31,0], }}, 
			'MD': 	{'offset': [0xc,0xd], 'regs': { 'MD': [15,0], }}, 
			'MMASK': {'offset': [0x10,0x13], 'regs': { 'MASK': [31,0], }}, 
			'MPEND': {'offset': [0x14,0x17], 'regs': { 'PEND': [31,0], }}, 
		}},
		'CAP_EXP': {'offset': ['CAP_EXP','CAP_PCIX+0x29'], 'regs': {
			'PXID': 	{'offset': [0x0,0x1], 'regs': { 'NEXT': [15,8], 'CID': [7,0], }}, 
			'PXCAP': 	{'offset': [0x2,0x3], 'regs': { 'IMN': [13,9], 'SI': [8], 'DPT': [7,4], 'VER': [3,0], }}, 
			'PXDCAP': 	{'offset': [0x4,0x7], 'regs': { 'FLRC': [28], 'CSPLS': [27,26], 'CSPLV': [25,18], 'RER': [15],
														'L1L': [11,9], 'L0SL': [8,6], 'ETFS': [5], 'PFS': [4,3],
														'MPS': [2,0], }}, 
			'PXDC': 	{'offset': [0x8,0x9], 'regs': { 'IFLR': [15], 'MRRS': [14,12], 'ENS': [11], 'APPME': [10],
														'PFE': [9], 'ETE': [8], 'MPS': [7,5], 'ERO': [4],
														'URRE': [3], 'FERE': [2], 'NFERE': [1], 'CERE': [0], }}, 
			'PXDS': 	{'offset': [0xa,0xb], 'regs': { 'TP': [5], 'APD': [4], 'URD': [3], 'FED': [2],
														'NFED': [1], 'CED': [0], }}, 
			'PXLCAP': 	{'offset': [0xc,0xf], 'regs': { 'PN': [31,24], 'AOC': [22], 'LBNC': [21], 'DLLLA': [20],
														'SDERC': [19], 'CPM': [18], 'L1EL': [17,15], 'L0SEL': [14,12],
														'ASPMS': [11,10], 'MLW': [9,4], 'SLS': [3,0], }}, 
			'PXLC': 	{'offset': [0x10,0x11], 'regs': { 'HAWD': [9], 'ECPM': [8], 'ES': [7], 'CCC': [6],
														'RCB': [3], 'ASPMC': [1,0], }}, 
			'PXLS': 	{'offset': [0x12,0x13], 'regs': { 'SCC': [12], 'NLW': [9,4], 'CLS': [3,0], }}, 
			'PXDCAP2': 	{'offset': [0x24,0x27], 'regs': { 'MEETP': [23,22], 'EETPS': [21], 'EFFS': [20], 'OBFFS': [19,18],
														'TPHCS': [13,12], 'LTRS': [11], 'NPRPR': [10], '128CCS': [9],
														'64AOCS': [8], '32AOCS': [7], 'AORS': [6], 'ARIFS': [5],
														'CTDS': [4], 'CTRS': [3,0], }}, 
			'PXDC2': 	{'offset': [0x28,0x29], 'regs': { 'OBFFE': [14,13], 'LTRME': [10], 'CTD': [4], 'CTV': [3,0], }}, 
		}},
		'CAP_MSIX': {'offset': ['CAP_MSIX','CAP_MSIX+0xb'], 'regs': {
			'MXID': 	{'offset': [0x0,0x1], 'regs': { 'NEXT': [15,8], 'CID': [7,0], }}, 
			'MXC': 		{'offset': [0x2,0x3], 'regs': { 'MXE': [15], 'FM': [14], 'TS': [10,0] }}, 
			'MTAB': 	{'offset': [0x4,0x7], 'regs': { 'TO': [31,3], 'TBIR': [2,0], }}, 
			'MPBA': 	{'offset': [0x8,0xb], 'regs': { 'PBAO': [31,3], 'CID': [2,0], }}, 
		}},
	}

	__path = None
	__slot = None

	def __init__(self, path=None):
		if path != None:
			self.set_device_path(path)

	def set_device_path(self, path):
		self.__path = None
		if self.check_device(path) != 0: return 1
		self.__path = path
		self.slot()
		return 0

	def check_device(self, path=None):
		path = path if path is not None else self.path()
		cmd = "find %s &> /dev/null" %(path)
		if CMD(cmd).exe().returncode !=0 :
			logging.error("%s: no such device!" %(path)) 
			return 1
		return 0

	def path(self): return self.__path
 
 	def slot(self):
 		if not self.__slot:
			self.__slot = CMD("udevadm info %s |grep P: |cut -d '/' -f 5" %(self.path())).get_stdout("line")

		return self.__slot

	def PCI_registers(self):
		if self.__slot == None: return None
		cmd = "timeout 2s lspci -xxxx -s %s" %(self.__slot)
		proc = CMD(cmd).exe()
		if proc.returncode !=0 :
			logging.error("Error!!! Get PCI Express Registers of %s fail!!!" %(self.__slot)) 
			return None
		PCI_REG = proc.get_stdout("multiline")
		parsed_PCI_REG = []
		for i in xrange(0, 4096, 16):
			if i < 256: re_str = "(?<=^%02x:)(?: [\da-fA-F]{2}){16}" %(i)
			else: re_str = "(?<=^%03x:)(?: [\da-fA-F]{2}){16}" %(i)
			item = re.findall(re_str, PCI_REG, flags=re.MULTILINE)[0]
			item = item.split(" ", 16)
			item.pop(0)
			# parsed_PCI_REG.extend(map(lambda x:int(x,16), item))
			parsed_PCI_REG.extend(item)
		
		if parsed_PCI_REG == []: parsed_PCI_REG = None
		return OutputStr(''.join(parsed_PCI_REG), type="hex")
		# return parsed_PCI_REG

 #################################################################################################################		

	def get_register(self, reg):
		if reg == self.PCI_HEADER: cid = "PCI_HEADER" 	# PCI Header
		elif reg == self.PMCAP: cid = "CAP_PM"			# PCI Power Management Capability
		elif reg == self.MSICAP: cid = "CAP_MSI"		# Message Signaled Interrupt Capability
		elif reg == self.PXCAP: cid = "CAP_EXP"		# PCI Express Capability
		elif reg == self.MSIXCAP: cid = "CAP_MSIX"		# MSI-X Capability
		# elif reg == self.AERCAP: cid = "AERCAP"			# Advanced Error Reporting Capability
		else: cid = None

		parsed_register = DataBuffer()
		parsed_register.returncode = 0
		System_Bus_Register = self.__System_Bus_Registers[cid]
		for symbol in System_Bus_Register['regs']:
			symbol_offset = System_Bus_Register['regs'][symbol]['offset']
			symbol_regs = System_Bus_Register['regs'][symbol]['regs']
			cmd = "setpci -s %s %s+%#x.%s" %(
				self.slot(), str(min(System_Bus_Register['offset'])), min(symbol_offset), 
				'b' if(max(symbol_offset)==min(symbol_offset)) else(
				'w' if(max(symbol_offset)-min(symbol_offset) <2) else 'l') )
			proc = CMD(cmd).exe()
			parsed_register.returncode |= proc.returncode
			if proc.returncode != 0: return parsed_register
			val = int(proc.get_stdout("line"), 16)
			tmp = DataBuffer(val)
			if isinstance(symbol_regs, dict):
				map(lambda r: tmp.__setattr__(r, (val>>min(symbol_regs[r]))&(2**(max(symbol_regs[r])-min(symbol_regs[r])+1)-1)), 
				symbol_regs.keys())

			parsed_register.__setattr__(symbol, tmp)

		return parsed_register

	def set_register(self, reg):
		if reg == self.PCI_HEADER: cid = "PCI_HEADER" 	# PCI Header
		elif reg == self.PMCAP: cid = "CAP_PM"			# PCI Power Management Capability
		elif reg == self.MSICAP: cid = "CAP_MSI"		# Message Signaled Interrupt Capability
		elif reg == self.PXCAP: cid = "CAP_EXP"			# PCI Express Capability
		elif reg == self.MSIXCAP: cid = "CAP_MSIX"		# MSI-X Capability
		# elif reg == self.AERCAP: cid = "AERCAP"			# Advanced Error Reporting Capability
		else: cid = None

		System_Bus_Register = self.__System_Bus_Registers[cid]
		slot = self.slot()
		class PCIregisrer(DataBuffer):
			returncode = 0
			prev_symbol = ""
			def __init__(self, symbol=None):
				self.__dict__['prev_symbol'] = symbol

			def __setattr__(self, symbol, value):
				target_symbol = symbol
				symbol = self.prev_symbol if self.prev_symbol else symbol
				# if (symbol in System_Bus_Register['regs']):
				try:
					symbol_offset = System_Bus_Register['regs'][symbol]['offset']
					symbol_regs = System_Bus_Register['regs'][symbol]['regs']
					cmd = "setpci -s %s %s+%#x.%s=%#x:%#x" %(
							slot, str(min(System_Bus_Register['offset'])), min(symbol_offset), 
							'b' if(max(symbol_offset)==min(symbol_offset)) else(
							'w' if(max(symbol_offset)-min(symbol_offset) <2) else 'l'),
							value if (not self.prev_symbol) else (value<<min(symbol_regs[target_symbol]) ),
							value if (not self.prev_symbol) else (2**(max(symbol_regs[target_symbol])+1)-2**min(symbol_regs[target_symbol]))
						)
				except:
					logging.error("Error!!! No such register (%s%s)!!!"%(
						"%s."%(self.prev_symbol) if self.prev_symbol else "", target_symbol))
					self.__dict__['returncode'] = 1
					return self

				if CMD(cmd).exe().returncode !=0 :
					self.__dict__['returncode'] = 1
					return self

			def __getattr__(self, symbol):
				register = PCIregisrer(symbol)
				return register

		return PCIregisrer()

	def remove(self):
		cmd = "timeout 2s echo 1 > /sys/bus/pci/devices/%s/remove" %(self.__slot)
		if CMD(cmd).exe().returncode !=0 :
			logging.error("Error!!! Remove %s fail!!!" %(self.__slot)) 
			return 1
		else:
			self.__slot = None
		return 0
