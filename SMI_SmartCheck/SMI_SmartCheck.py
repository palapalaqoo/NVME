#!/usr/bin/env python
from Data import *
from NVMe import NVMe

import sys
import os

import argparse
import ctypes
import struct
import fcntl
import random
import time
import logging
import ConfigParser
import signal
import subprocess
import re
import threading 
		
class SMI_SmartCheck(object):
	version = '20200722A'



	attrDescriptors = {} 								# Saves log pages' attr. descriptors. format: {lid: {dict of a page's attr. descriptors}, ...}
	logPgDescriptors = {} 								# Saves log pages' descriptors, format: {lid: {dict of a page's descriptors}, ...}
	attrValues = {'init':{}, 'prev':{}, 'curr':{}} 		# Saves init, prev, curr values of log pages' attributes.
	attrIncompatibleLimit = {}							# Saves attrID that is incompatible with limit, format: {lid: [attrID, ...], ...}

	_monitoringTimer = None								# Threading timer uses for auto monitoring during a specific period.
	_startMonitoringTS = 0								# Saves timestamp that starts monitoring SMART.

	totalExecutedCycle = 0

	NVMe = None

	def __init__(self, config, outdir=''):
		super(SMI_SmartCheck, self).__init__()

		self.config = config
		self.outdir = outdir

	@staticmethod
	def loadConfig(defaultVarName, varType, defaultValue, sectionName, configFile):
		config = ConfigParser.SafeConfigParser(dict(zip(defaultVarName, map(str, defaultValue))))
		getConfigVal = lambda sName,opt,t: config.getfloat(sName, opt) if (t is float) else (config.getint(sName, opt) if (t is int) else (config.getboolean(sName, opt) if (t is bool) else config.get(sName, opt)))
		try:
			config.read(configFile)
			return map(lambda (N,t): (N,getConfigVal(sectionName, N, t)), zip(defaultVarName, varType))
		except:
			if defaultValue:
				logging.warning("Warning!!! Load / parse '%s' failed!!!"%(configFile))
				return map(lambda (N,dV): (N,dV), zip(defaultVarName, defaultValue))
			else: 
				logging.error("Error!!! Load / parse '%s' failed!!!"%(configFile))
				return []

	def loadFromConfig(self):
		# Load the config file setting from 'self.config'.
		## Arguments Supported in config, which they will be save as the class' attribute.
		# * total_cycle           -> Test cycle, 0 means infinite
		# * exec_cmd              -> If assigned, call it as program starts. Give string 'fio' will run default heavy loading process.
		# * smart_monitor_period  -> Period of monitoring SMART data (in seconds).
		# * smart_config_file     -> Assign SMART configuration filename. Keep empty if you do not want to monitor SMART data.
		# * disk_id               -> Disk ID which is going to be tested

		# If load data fail, uses default setting.
		sectionName = "global"
		configFile = self.config

		# Arguments and default values, and also their data types.
		defaultVarName = ['total_cycle','exec_cmd','smart_config_file','smart_monitor_period','disk_id']
		varType = [int, str, str, int, str]
		defaultValue = [0,'fio','SMART.ini',5,'/dev/nvme0']

		map(lambda (N,V): self.__setattr__(N,V), 
			self.loadConfig(defaultVarName, varType, defaultValue, sectionName, configFile))

		# Load SMART config file setting from 'self.smart_config_file'.
		if self.loadSmartConfigFile(): return 1

		self.attrValues = {'init':{}, 'prev':{}, 'curr':{}}
		self.totalExecutedCycle = 0

		if (self.protocol).lower() == 'nvme': self.NVMe = NVMe(self.disk_id)
		else: pass

		return 0

	def loadSmartConfigFile(self):
		## .ini Format: 
		# [global]											->	In the "global" section
		# test_sections=nvme_log_page_2,nvme_log_page_7		->	log page sections
		# protocol=nvme										->	set device protocol
		# In each log page section: 
		# [nvme_log_page_2]									->	Section name
		# attr_amount=30									->	Amount of attribute
		# log_page=2										->	log page id (NVMe)
		# log_page_size=512									->	Log page size in byte

		# attr_id_2=2:1										->	attribute ID's offset and len
		# attr_desc_1=Composite Temperature					->	Description (It's Name)
		# attr_limit_1=	"SMART Limit"						->	SMART Limit

		## SMART Limit Examples
		# * Format: [value_type[bitend:bitstart]][comparator][value] && [][][] && ...
		# *   [value_type]: diff -> The dfference between the previous one and the current one
		# *                 val  -> The current value
		# *   [comparator]: ==, !=, >=, >, <=, <
		# * Examples:
		# *   1. Current value minus previous value should be lesser or equal to 1
		# *      diff<=1
		# *   2. Current value should equal to 0xC0
		# *      val==0xC0
		# *   3. Current value minus previous value should be in range 10~100
		# *      diff>=10 && diff<=100
		# *   4. Bits examination. For example, NVMe SMART byte 0 logs "Critical Warning" data, if you expect all flags keep non-raised except bit 1 temperature, you could simply assign limit as below:
		# *      val[0]==0 && val[7:2]==0

		sectionName = "global"
		configFile = self.smart_config_file

		# Parse how may log section, and testing which protocol.
		# Arguments and default values, and also their data types.
		defaultVarName = ['test_sections','protocol']
		varType = [str, str]
		defaultValue = [] # ['nvme_log_page_2,ferri_telemetry','nvme']

		parsedConfig = self.loadConfig(defaultVarName, varType, defaultValue, sectionName, configFile)
		if parsedConfig: map(lambda (N,V): self.__setattr__(N,V), parsedConfig)
		else: return 1

		# Now knows testing which log section --> prepare to parse their (log page's) attribute.
		# logging.info( map(lambda N: getattr(self, N), defaultVarName) )
		self.test_sections = self.test_sections.split(',')

		def loadSmartSection(sectionName): # Uses to get attribute from a log page section 'sectionName'.
			# This function will get and return log page section 'sectionName' 's:
			# 'attr, 'attr_amount','log_page','log_page_size','log_page_offset'
			# Where:
			#	- 'attr' is log page's descriptor, e.g.: {1: {'attr_id': [2,3], 'attr_desc': "Descript", 'attr_limit': "diff<3", 'attr_type': "string"}, ...}; 
			#	- 'attr_amount' is amount of attr. in this log page; 
			#	- 'log_page' is log page ID (NVMe); 
			#	- 'log_page_size' is log page's size in bytes (NVMe); 
			#	- 'log_page_offset' is log page's offset (NVMe).

			cvrtBytes2ListFmt = lambda s: map(lambda i: int(i,0) if (i != '') else None, s.split(':')) # in .ini file: "3:2" --> [3,2];"3" --> [3] ; "" --> [None]
			cvrtStrType2Type = lambda t: str if (t == 'string' or t == 'str') else int # Convert .ini file's attr_type_X (in string) to python recognizable data type.

			defaultVarName = ['attr_amount','log_page','log_page_size','log_page_offset']
			varType = [int, str, int, int]
			defaultValue =  [0, '0x0', 512, 0]

			(attr_amount, log_page, log_page_size, log_page_offset) = zip(*self.loadConfig(defaultVarName, varType, defaultValue, sectionName, self.smart_config_file))[1]
			
			# To get log page's attr. descriptor.
			attrDescriptors = {}
			for attrID in xrange(1, attr_amount+1):
				a = zip(*self.loadConfig(	['attr_id_%d'%(attrID),'attr_desc_%d'%(attrID),'attr_limit_%d'%(attrID),'attr_type_%d'%(attrID)], 
										[str, str, str, str], ['','','',''], sectionName, self.smart_config_file ) )[1]

				if a[0] != "": # To prevent non-exists attr_id.
					attrDescriptors.update( {attrID: {'attr_id': cvrtBytes2ListFmt(a[0]), 'attr_desc': a[1], 'attr_limit': a[2], 'attr_type': cvrtStrType2Type(a[3]) }} )

			return (attrDescriptors, attr_amount, int(log_page,0), log_page_size, log_page_offset)

		self.attrDescriptors = {}
		self.logPgDescriptors = {}
		for sectionName in self.test_sections:
			(attrDescriptors, attr_amount, log_page, log_page_size, log_page_offset) = loadSmartSection(sectionName)
			if attrDescriptors == {}: return 1

			log_page = log_page if (self.protocol == 'nvme') else 0
			self.attrIncompatibleLimit.update({log_page: []})
			self.attrDescriptors.update({log_page: attrDescriptors})
			self.logPgDescriptors.update({log_page: {'attr_amount': attr_amount, 'log_page_size': log_page_size, 'log_page_offset': log_page_offset}})

		return 0

	def checkSMARTLimit(self):
		# Checks if SMART attributes are incompatible with limit.
		# Return 1 if exists any attribute is incompatible with limit, otherwise 0.

		limitExpressionRE = re.compile('(?P<value_type>val|diff)(\[(?P<bits>\d+(\:\d+)?)\])? *(?P<comparator>==|!=|>=|>|<=|<) *(?P<limit_value>\d+)')
		Mask = lambda l_byte,u_byte,Bin: Bin>>(l_byte)&(2**(u_byte-l_byte+1)-1)
		CutOffBits = lambda v,e: v if ((limitExpressionRE.search(e).group('bits') is None) or (v is None)) else Mask(int(min(limitExpressionRE.search(e).group('bits').split(':'))),int(max(limitExpressionRE.search(e).group('bits').split(':'))),v)		
		def cmpLimitExpression(prevVal, currVal, limitExpressions):
			# Checks if a attribute's value is incompatible with limit 'limitExpressions'.
			# Return 1 if incompatible with limit, otherwise 0.

			if limitExpressions == '': return 0 # No limit for this attribute --> No needs to check

			for limitExpression in map(lambda l: l.strip(), limitExpressions.split('&&')): # Checks each expression

				isBitwiseExpression = '[' in limitExpression # Defines if need bitwise examination

				# If no needs bitwise examination:
				#	'currVal' is then move to 'val';
				#	Diff. of 'currVal' and 'prevVal' is saved to 'diff'
				#	eval is used for the examination.
				# Else if needs bitwise examination:
				# 	Both 'val', 'prevVal' and 'limitExpression' must do some pre-work,
				#	'val', 'prevVal' must cut the bits from related values.
				#	'[bitend:bitstart]' must be removes from 'limitExpression'.
				val = CutOffBits(currVal,limitExpression) if isBitwiseExpression else currVal
				prevVal = CutOffBits(prevVal,limitExpression) if isBitwiseExpression else prevVal
				diff = None if (prevVal is None) else (val-prevVal)
				limitExpression = (limitExpressionRE.search(limitExpression).group('value_type')+limitExpressionRE.search(limitExpression).group('comparator')+limitExpressionRE.search(limitExpression).group('limit_value')) if isBitwiseExpression else limitExpression
				if (limitExpression[0] == 'd') and (diff is None): continue # First time running and try to checks its diff. -> skip
				if not eval(limitExpression): return 1 # Recaches the limitation --> fail

			return 0

		isFail=0
		for lid in sorted(self.attrDescriptors.keys()):
			self.attrIncompatibleLimit[lid] = []
			# try:
			# 	if any( map(lambda attrID: cmpLimitExpression(self.attrValues['prev'][lid][attrID], self.attrValues['curr'][lid][attrID], self.attrDescriptors[lid][attrID]['attr_limit']), self.attrValues['curr'][lid].keys()) ): exit(1)
			# except KeyError:
			# 	if any( map(lambda attrID: cmpLimitExpression(None, self.attrValues['curr'][lid][attrID], self.attrDescriptors[lid][attrID]['attr_limit']), self.attrValues['curr'][lid].keys()) ): exit(1)
			for attrID in self.attrValues['curr'][lid].keys():
				prevVal = self.attrValues['prev'][lid][attrID] if (lid in self.attrValues['prev']) else None
				currVal = self.attrValues['curr'][lid][attrID]
				limitExpression = self.attrDescriptors[lid][attrID]['attr_limit']
				if cmpLimitExpression(prevVal, currVal, limitExpression):
					# logging.error("%s: [prev: %s], [curr: %s], [limit exp.: %s]"%(self.attrDescriptors[lid][attrID]['attr_desc'], prevVal, currVal, limitExpression))
					self.attrIncompatibleLimit[lid].append(attrID)
					isFail=1
					# return 1
		return isFail
		return 0

	def getSmart(self):
		# FNULL = open(os.devnull, 'w')
		# cmd = 'nvme get-log /dev/nvme0 -i 2 -l 512'
		# timeout = 1000
		# returncode = None
		# start_ts = time.time()
		# proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=FNULL)
		# while True: # Do while < self.timeout
		# 	returncode = proc.poll()
		# 	if returncode != None:
		# 		stdout, proc_err = proc.communicate()
		# 		break
		# 	if ((time.time()- start_ts)*1000) > timeout: break

		# if returncode == None:
		# 	proc.kill()
		# 	time.sleep(1)
		# 	returncode = proc.poll()


		# if returncode: 
		# 	logging.error( returncode )
		# 	return 1

		# -------------------------------------------SATA-------------------------------------------
		#	unset arg;for((i=1;i<=255;i++));do arg[i]="-v$i,raw48";done;smartctl -A /dev/sda ${arg[@]}| grep '^[[:space:][:digit:]]' | awk '{printf "{%d: %d},",$1,$10}'
		#	{1: 211641346},{3: 0},{4: 1466},{5: 0},{7: 53754585},{9: 9333},{10: 0},{12: 1458},{183: 0},{184: 0},{187: 0},{188: 8},{189: 0},{190: 706215975},{193: 1707},{194: 68719476775},{195: 211641346},{197: 0},{198: 0},{199: 0},{240: 205591494534207},{241: 4073426008},{242: 8271790727},
		# ---------------------------------------End of SATA----------------------------------------

		# -------------------------------------------NVMe-------------------------------------------
		def parseStructure(structPattern, binary, parseAttr=None):
			if parseAttr == None: parseAttr = DataBuffer()

			Mask = lambda l_byte,u_byte,Bin: Bin>>(l_byte<<3)&(2**((u_byte-l_byte+1)<<3)-1)
			# {{1: {'attr_id': [0], 'attr_desc': 'Critical Warning', 'attr_limit': ''}, .....}
			map(lambda (attrID,attr): parseAttr.__setattr__(attrID, 0 if (attr['attr_id']==[None]) else Mask(min(attr['attr_id']),max(attr['attr_id']),binary) ), structPattern.items())
			return parseAttr

		tmpCurrAttrValue = {}
		for lid in sorted(self.attrDescriptors.keys()):
			proc = self.NVMe.get_log_page(lid, opt_arg=self.logPgDescriptors[lid]['log_page_size'])
			if proc.returncode != self.NVMe.status.successfulCompletion: return 1

			tmpCurrAttrValue.update( {lid: parseStructure(self.attrDescriptors[lid], int(proc.DataStruct) )} )
		# ---------------------------------------End of NVMe----------------------------------------

		if self.attrValues['init'] == {}: self.attrValues['init'] = tmpCurrAttrValue
		self.attrValues['prev'] = self.attrValues['curr']
		self.attrValues['curr'] = tmpCurrAttrValue

		if self.checkSMARTLimit():
			logging.error('\n'+self.logPagesTable())
			return 1
		else: logging.info('\n'+self.logPagesTable())
		return 0

	def logPagesTable(self):
		ceil = lambda dividend,divisor: -(dividend/-divisor)
		valFmt= lambda v,t: reversed(''.join(chr((v>>8*(ceil(len(bin(stringInt))-2,8)-byte-1))&0xff) for byte in xrange(ceil(len(bin(stringInt))-2,8)))) if (t is str) else v

		logPagesTable = ""
		for lid in sorted(self.attrDescriptors.keys()):
			logPagesTable += '{:=^104}\n'.format(" LOG PAGE %02X DATA "%(lid))
			logPagesTable += "  Offset   Value (curr/prev/init)                                            Description\n"
			logPagesTable += "-"*104 + "\n"
			try:
				logPagesTable += '\n'.join(filter(None, map(lambda attrID: "{MARK} {EB}:{SB}  {VAL}{DSEC}".format(
					MARK='*' if (attrID in self.attrIncompatibleLimit[lid]) else ('-' if (self.attrValues['curr'][lid][attrID]!=self.attrValues['init'][lid][attrID]) else ' '), 
					EB='{:>3}'.format("%X"%(max(self.attrDescriptors[lid][attrID]['attr_id']))),
					SB='{:<3}'.format("%X"%(min(self.attrDescriptors[lid][attrID]['attr_id']))),
					VAL='{:<66}'.format("%s/%s/%s"%(valFmt(self.attrValues['curr'][lid][attrID],self.attrDescriptors[lid][attrID]['attr_type']),
													valFmt(self.attrValues['prev'][lid][attrID],self.attrDescriptors[lid][attrID]['attr_type']) if (lid in self.attrValues['prev']) else '', 
													valFmt(self.attrValues['init'][lid][attrID],self.attrDescriptors[lid][attrID]['attr_type']) if (lid in self.attrValues['init']) else '')),
					DSEC=self.attrDescriptors[lid][attrID]['attr_desc']+("\n%sIncompatible with limit: %s"%(" "*77, self.attrDescriptors[lid][attrID]['attr_limit']) if (attrID in self.attrIncompatibleLimit[lid]) else ""), 
					) if (self.attrDescriptors[lid][attrID]['attr_id'] != [None]) else "",
				self.attrValues['curr'][lid].keys() ) ))
			except: pass
			logPagesTable += "\n"

		return logPagesTable

	def startMonitoring(self):

		def monitoring(self):
			ticksBeforeRecord = time.time()
			logging.info('{:=^104}'.format(self.totalExecutedCycle+1))
			if self.getSmart(): return 1
			logging.info('{:=^104}\n'.format(self.totalExecutedCycle+1))

			self.totalExecutedCycle += 1

			if self.total_cycle and (self.totalExecutedCycle > self.total_cycle): return 0

			self._monitoringTimer = threading.Timer(self.smart_monitor_period - (time.time() - ticksBeforeRecord), monitoring, (self,)) 
			self._monitoringTimer.start()
			return 0

		self._startMonitoringTS = time.time()
		monitoring(self)
		return 0

	def stopMonitoring(self):
		try: self._monitoringTimer.cancel()
		except: pass

	def isMonitoring(self):
		try: return self._monitoringTimer.is_alive()
		except: return False

if __name__ == "__main__":
	logging.getLogger().setLevel(logging.INFO)

	smart = SMI_SmartCheck('SmiSmartCheck.ini')
	if smart.loadFromConfig(): 
		print "Hi"
		exit(1)
	smart.startMonitoring()
	# smart.stopMonitoring()

	while smart.isMonitoring():
		# Do something...
		time.sleep(3)
	exit(0)
