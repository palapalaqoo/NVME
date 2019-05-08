'''
Created on Aug 3, 2018

@author: root
'''
from lib_vct.NVMECom import NVMECom
from lib_vct.RegDescriptor import RegDescriptor
import re



class IdNs_(object, NVMECom):
    def __init__(self, obj):
        self._mNVME=obj
            
        self.NSZE=RegDescriptor("id-ns", "nsze", NVMEobj=obj)
        self.NCAP=RegDescriptor("id-ns", "ncap", NVMEobj=obj)
        self.NUSE=RegDescriptor("id-ns", "nuse", NVMEobj=obj)
        self.NSFEAT=RegDescriptor("id-ns", "nsfeat", NVMEobj=obj)
        self.NLBAF=RegDescriptor("id-ns", "nlbaf", NVMEobj=obj)
        self.FLBAS=RegDescriptor("id-ns", "flbas", NVMEobj=obj)
        self.MC=RegDescriptor("id-ns", "mc", NVMEobj=obj)
        self.DPC=RegDescriptor("id-ns", "dpc", NVMEobj=obj)
        self.DPS=RegDescriptor("id-ns", "dps", NVMEobj=obj)
        self.NMIC=RegDescriptor("id-ns", "nmic", NVMEobj=obj)
        self.RESCAP=RegDescriptor("id-ns", "rescap", NVMEobj=obj)
        self.FPI=RegDescriptor("id-ns", "fpi", NVMEobj=obj)
      
        self.NAWUN=RegDescriptor("id-ns", "nawun", NVMEobj=obj)
        self.NAWUPF=RegDescriptor("id-ns", "nawupf", NVMEobj=obj)
        self.NACWU=RegDescriptor("id-ns", "nacwu", NVMEobj=obj)
        self.NABSN=RegDescriptor("id-ns", "nabsn", NVMEobj=obj)
        self.NABO=RegDescriptor("id-ns", "nabo", NVMEobj=obj)
        self.NABSPF=RegDescriptor("id-ns", "nabspf", NVMEobj=obj)
        self.NOIOB=RegDescriptor("id-ns", "noiob", NVMEobj=obj)
        self.NVMCAP=RegDescriptor("id-ns", "nvmcap", NVMEobj=obj)
        self.NGUID=RegDescriptor("id-ns", "nguid", NVMEobj=obj)
        self.EUI64=RegDescriptor("id-ns", "eui64", NVMEobj=obj)
        
    #DLFEAT=RegDescriptor("id-ns", "dlfeat")    
    @property         
    def DLFEAT(self):
    # ret int
        IdnsStruct=self.shell_cmd("nvme admin-passthru %s --opcode=0x6 --data-len=48 -r -n 1 2>&1"%self._mNVME.dev)
        mStr="0020:\s\w{2}\s(\w{2})"
        if re.search(mStr, IdnsStruct):
            DLFEAT=int(re.search(mStr, IdnsStruct).group(1),16)
        else:
            DLFEAT=0   
        return DLFEAT
    @property         
    def LBAFinUse(self):
    # ret [lbafId, ms, lbads, rp] whick current format in use
        CmdRt=self.shell_cmd("nvme id-ns %s| grep 'in use' 2>&1"%self._mNVME.dev)
        mStr="^lbaf\s*(\d+)\D+(\d+)\D+(\d+)\D+(\d+)\D+"
        if re.search(mStr, CmdRt):
            lbaf=int(re.search(mStr, CmdRt).group(1))
            ms=int(re.search(mStr, CmdRt).group(2))
            lbads=int(re.search(mStr, CmdRt).group(3))
            rp=int(re.search(mStr, CmdRt).group(4),16)
            rtLBAFinUse=[lbaf, ms, lbads, rp] 
        else:
            rtLBAFinUse=None  
        return rtLBAFinUse


    
    
    