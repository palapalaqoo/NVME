import textwrap
import struct
import re

class OutputStr(str):
	def __new__(cls, str, type="line"):
		if type =="value": 
			return str
		else:
			obj = str.__new__(cls, str)
			obj.type = type
			return obj

	def __repr__(self):
		return self

	def get_bit(self, s_bit, e_bit):
		if self.type != "binary": return None
		return OutputStr(self[s_bit: (e_bit+1)], type="binary")
		# return self[s_bit: (e_bit+1)]

	def get_hex(self, s_byte, e_byte):
		if self.type != "hex": return None
		return OutputStr(self[2*s_byte: 2*(e_byte+1)], type="hex")
		# return self[2*s_byte: 2*(e_byte+1)]

class DataBuffer():
	def __init__(self, data=None):
		self.__dict__["_buffer"] = dict()
		self.__dict__["_data"] = None if (isinstance (data, dict)) else data
		if isinstance (data, dict): self.__dict__["_buffer"].update(data)				

	def __setattr__(self, name, value):
		if name == "returncode": self.__dict__["_returncode"] = value
		else: self._buffer[name] = value

	def __getattr__(self, name):
		if name == "returncode":
			return self._returncode if hasattr(self, '_returncode') else None
		elif name in self._buffer.keys():
			return self._buffer[name]
		else:
			return None

	def __setitem__(self,name):
		return self.__setattr__(name, value)

	def __getitem__(self,name):
		return self.__getattr__(name)

	def __repr__(self):
		if self._buffer: return repr(self._buffer)
		else : return repr(self._data)

	def __str__(self):
		if self._buffer: 
			return '{%s}'%(', '.join( map(lambda k: "'%s': %s"%(k, '{0:#x}'.format(self._buffer[k]) if isinstance(self._buffer[k], int) else str(self._buffer[k])),self._buffer.keys()) ))
			# return str(self._buffer)
		else : return str(self._data)

	def __int__(self):
		return int(self._data)

	def __coerce__(self, other):
		return (self.__int__(), other)

	def __eq__(self, other):
		if other == None: return False
		else:
			if isinstance(other, int):
				return int(self._data) == other
			elif isinstance(other, dict):
				return self._buffer == other
			else:
				return self.__dict__ == other.__dict__

	def __ne__(self, other):
		if other == None: return False
		return not self.__eq__(other)

	def setint(self, data):
		self.__dict__["_data"] = None if (isinstance (data, dict)) else data

	def keys(self):
		return self.__dict__["_buffer"].keys()

	def values(self):
		return self.__dict__["_buffer"].values()

	def items(self):
		return self.__dict__["_buffer"].items()

class StatusField(DataBuffer):
	def __eq__(self, other):
		if other == None: return False
		else:
			if isinstance(other, StatusField) or isinstance(other, DataBuffer):
				return ((self._buffer['SC'] == other._buffer['SC']) and 
						(self._buffer['SCT'] == other._buffer['SCT']))
			elif isinstance(other, int):
				return int(self._data) == other&0x7ff
			elif isinstance(other, dict):
				return ((self._buffer['SC'] == other._buffer['SC']) and 
						(self._buffer['SCT'] == other._buffer['SCT']))
			else:
				return False

	def __and__(self, other):
		return self.__int__() & other

def toSMI_DataBuffer(r):
	if isinstance(r, list):
		return map(lambda i: toSMI_DataBuffer(i), r)
	elif isinstance(r, dict):
		tmp = DataBuffer()
		map(lambda a: tmp.__setattr__(a[0], toSMI_DataBuffer(a[1])), r.items())
		return tmp
	else:
		return r

def hex_to_int(hex_val, little_endian=False):
	if little_endian:
		# struct.unpack('<Q',struct.pack('>Q',   int(DST_log.get_hex(i+4, i+11),16)    ))[0]
		tmp_hex_val = textwrap.wrap(hex_val, 2)
		hex_val = ""
		for byte in reversed(tmp_hex_val):
			hex_val += byte
	return int(hex_val, 16)

def bin_to_int(bin_val, little_endian=False):
	if little_endian == True: 
		tmp_bin_val = textwrap.wrap(bin_val, 8)
		bin_val = ""
		for byte in reversed(tmp_bin_val):
			bin_val += byte

	return int(bin_val, 2)
	