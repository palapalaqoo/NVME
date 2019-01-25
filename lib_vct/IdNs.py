'''
Created on Aug 3, 2018

@author: root
'''
from lib_vct.NVMECom import NVMECom
from lib_vct.RegDescriptor import RegDescriptor
import re



class IdNs_(object, NVMECom):
    NSZE=RegDescriptor("id-ns", "nsze")
    NCAP=RegDescriptor("id-ns", "ncap")
    NUSE=RegDescriptor("id-ns", "nuse")
    NSFEAT=RegDescriptor("id-ns", "nsfeat")
    NLBAF=RegDescriptor("id-ns", "nlbaf")
    FLBAS=RegDescriptor("id-ns", "flbas")
    MC=RegDescriptor("id-ns", "mc")
    DPC=RegDescriptor("id-ns", "dpc")
    DPS=RegDescriptor("id-ns", "dps")
    NMIC=RegDescriptor("id-ns", "nmic")
    RESCAP=RegDescriptor("id-ns", "rescap")
    FPI=RegDescriptor("id-ns", "fpi")
    #DLFEAT=RegDescriptor("id-ns", "dlfeat")    
    @property         
    def DLFEAT(self):
    # ret int
        IdnsStruct=self.shell_cmd("nvme admin-passthru %s --opcode=0x6 --data-len=48 -r -n 1 2>&1"%NVMECom.device)
        mStr="0020:\s\w{2}\s(\w{2})"
        if re.search(mStr, IdnsStruct):
            DLFEAT=int(re.search(mStr, IdnsStruct).group(1),16)
        else:
            DLFEAT=0   
        return DLFEAT
    
    NAWUN=RegDescriptor("id-ns", "nawun")
    NAWUPF=RegDescriptor("id-ns", "nawupf")
    NACWU=RegDescriptor("id-ns", "nacwu")
    NABSN=RegDescriptor("id-ns", "nabsn")
    NABO=RegDescriptor("id-ns", "nabo")
    NABSPF=RegDescriptor("id-ns", "nabspf")
    NOIOB=RegDescriptor("id-ns", "noiob")
    NVMCAP=RegDescriptor("id-ns", "nvmcap")
    NGUID=RegDescriptor("id-ns", "nguid")
    EUI64=RegDescriptor("id-ns", "eui64")


    
    
    