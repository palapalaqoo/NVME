import subprocess
import time
import sys
import os

class CMD:
	executed = False
	FNULL = open(os.devnull, 'w')
	def __init__(self, cmd, BIN_PATH=None, bg=False, non_blocking_IO=False, timeout=60000):
		self.bg = bg
		self.timeout = timeout # in ms
		self.stdout = None
		self.returncode = None
		self.string = None
		self.non_blocking_IO = non_blocking_IO
		if BIN_PATH != None:
			self.cmd = cmd
			self.BIN_PATH = BIN_PATH
			self.CURR_PATH = os.getcwd()
		else: self.cmd = cmd

	def exe(self):
		try:
			cmdLog = open('./cmdLog/log.sh', 'a')
			cmdLog.write(self.cmd+'\n')
			cmdLog.close()
		except:
			pass
		if hasattr(self, 'BIN_PATH'): os.chdir(self.BIN_PATH)
		self.proc = subprocess.Popen(self.cmd, shell=True, universal_newlines=self.non_blocking_IO, stdout=subprocess.PIPE, stderr=self.FNULL)
		self.executed = True
		# MSG.print_msg("debug", self.cmd)
		self.start_ts = time.time()
		if self.non_blocking_IO: 
			self.returncode = self.proc.poll()
			return self
		return self.wait()

	def get_stdout(self, type, base=10, exp_returncode=0):
		# self.bg = True
		if not self.executed: self.exe()
		else: 
			try:
				self.stdout, proc_err = self.proc.communicate()
			except:
				pass
		# proc_out, proc_err = self.proc.communicate()
		proc_out = self.stdout
		if self.returncode == exp_returncode:
			if type == "multi_line":
				self.string = OutputStr(proc_out, type="multi_line")
			elif type == "binary":
				string = proc_out
				self.string = OutputStr(
					format(int(string.encode('hex'), 16), '0>%db'%(8*len(string)) ),
					type="binary")
			elif type == "hex":
				string = proc_out
				self.string = OutputStr(
					format(int(string.encode('hex'), 16), '0>%dx'%(2*len(string))),
					type="hex")
			elif type == "value":
				self.string = OutputStr(
					int(proc_out.strip().replace(",", ""), base),
					type="value")
			elif type == "line":
				self.string = OutputStr( proc_out.strip(), type="line")
			else:
				self.string = OutputStr( proc_out, type="line")
			return self.string
		else: 
			# MSG.print_msg("err", "Cmd (%s) get value fail!" %(self.cmd))
			return None

	def get_non_blocking_stdout(self, type, base=10):
		if not self.executed: self.exe()
		if not self.non_blocking_IO: return None

		if self.timeout != 0 and ((time.time()- self.start_ts)*1000) > self.timeout:
			self.proc.kill()
			time.sleep(1)
			self.returncode = self.proc.poll()
			return None

		data = self.proc.stdout.readline()
		if data == '': 
			self.returncode = self.proc.poll()
			return None
		else: 
			if self.stdout == None: self.stdout = ''
			self.stdout += data

		if type == "binary":
			string = data
			self.string = OutputStr(
				format(int(string.encode('hex'), 16), '0>%db'%(8*len(string)) ),
				type="binary")
		elif type == "hex":
			string = data
			self.string = OutputStr(
				format(int(string.encode('hex'), 16), '0>%dx'%(2*len(string))),
				type="hex")
		elif type == "value":
			self.string = OutputStr(
				int(data.strip().replace(",", ""), base),
				type="value")
		elif type == "line":
			self.string = OutputStr( data, type="line")
		else:
			self.string = OutputStr( data, type="line")

		return self.string

	def wait(self):
		if self.bg == False: # fg
			if self.timeout == 0: # no time limit and wait
				self.stdout, proc_err = self.proc.communicate()
				self.returncode = self.proc.returncode
			else: # self.timeout > 0
				while True: # Do while < self.timeout
					self.returncode = self.proc.poll()
					if self.returncode != None:
						self.stdout, proc_err = self.proc.communicate()
						break
					if ((time.time()- self.start_ts)*1000) > self.timeout: break

				if self.returncode == None:
					self.proc.kill()
					time.sleep(1)
					self.returncode = self.proc.poll()
		else:
			self.returncode = self.proc.poll()

		if hasattr(self, 'CURR_PATH'): os.chdir(self.CURR_PATH)
		return self

class OutputStr(str):
	def __new__(cls, string, type="line"):
		if type =="value": 
			return string
		else:
			obj = string.__new__(cls, string)
			obj.type = type
			return obj

	def __repr__(self):
		return self

	def get_bit(self, s_bit, e_bit):
		if self.type != "binary": return None
		return self[s_bit: (e_bit+1)]

	def get_hex(self, s_byte, e_byte):
		if self.type != "hex": return None
		return self[2*s_byte: 2*(e_byte+1)]