'''
Created on Aug 2, 2018

@author: sam
'''
from lib_vct.NVMECom import NVMECom
from lib_vct.RegDescriptor import RegDescriptor



    
        
# controller register class
class CR_(object,NVMECom):
    def __init__(self, obj):
                 
        self.CAP=RegDescriptor("show-regs", "cap", NVMEobj=obj)
        self.CAP.MQES=RegDescriptor("show-regs", "cap", 0, 15, NVMEobj=obj)
        self.CAP.CQR=RegDescriptor("show-regs", "cap", 16, 16, NVMEobj=obj)
        self.CAP.AMS=RegDescriptor("show-regs", "cap", 17, 18, NVMEobj=obj)
        self.CAP.TO=RegDescriptor("show-regs", "cap", 24, 31, NVMEobj=obj)
        self.CAP.DSTRD=RegDescriptor("show-regs", "cap", 32, 35, NVMEobj=obj)
        self.CAP.NSSRS=RegDescriptor("show-regs", "cap", 36, 36, NVMEobj=obj)
        self.CAP.CSS=RegDescriptor("show-regs", "cap", 37, 44, NVMEobj=obj)
        self.CAP.BPS=RegDescriptor("show-regs", "cap", 45, 45, NVMEobj=obj)
        self.CAP.MPSMIN=RegDescriptor("show-regs", "cap", 48, 51, NVMEobj=obj)
        self.CAP.MPSMAX=RegDescriptor("show-regs", "cap", 52, 55, NVMEobj=obj)
        
        self.VS=RegDescriptor("show-regs", "version", NVMEobj=obj)
        self.VS.TER=RegDescriptor("show-regs", "version", 0, 7, NVMEobj=obj)
        self.VS.MNR=RegDescriptor("show-regs", "version", 8, 15, NVMEobj=obj)
        self.VS.MJR=RegDescriptor("show-regs", "version", 16, 31, NVMEobj=obj)
        
        self.INTMS=RegDescriptor("show-regs", "intms", NVMEobj=obj)
        self.INTMS.IVMS=RegDescriptor("show-regs", "intms", 0, 31, NVMEobj=obj)
        
        self.INTMC=RegDescriptor("show-regs", "intmc", NVMEobj=obj)
        self.INTMC.IVMS=RegDescriptor("show-regs", "intmc", 0, 31, NVMEobj=obj)    
        
        self.CC=RegDescriptor("show-regs", "cc", NVMEobj=obj)
        self.CC.EN=RegDescriptor("show-regs", "cc", 0, 0, NVMEobj=obj)
        self.CC.CSS=RegDescriptor("show-regs", "cc", 4, 6, NVMEobj=obj)
        self.CC.MPS=RegDescriptor("show-regs", "cc", 7, 10, NVMEobj=obj)
        self.CC.AMS=RegDescriptor("show-regs", "cc", 11, 13, NVMEobj=obj)
        self.CC.SHN=RegDescriptor("show-regs", "cc", 14, 15, NVMEobj=obj)
        self.CC.IOSQES=RegDescriptor("show-regs", "cc", 16, 19, NVMEobj=obj)
        self.CC.IOCQES=RegDescriptor("show-regs", "cc", 20, 23, NVMEobj=obj)
        self.CC.RO=RegDescriptor("show-regs", "cc", 24, 31, NVMEobj=obj)
    
        
        self.CSTS=RegDescriptor("show-regs", "csts", NVMEobj=obj)
        self.CSTS.bss=RegDescriptor("show-regs", "csts", NVMEobj=obj)
        self.CSTS.SHST=RegDescriptor("show-regs", "csts", 2, 3, NVMEobj=obj)
        
        self.AQA=RegDescriptor("show-regs", "aqa", NVMEobj=obj)  
        self.ASQ=RegDescriptor("show-regs", "asq", NVMEobj=obj)  
        self.AQA=RegDescriptor("show-regs", "aqa", NVMEobj=obj) 
        self.ACQ=RegDescriptor("show-regs", "acq", NVMEobj=obj) 

    
    
    
    
    
    
    
    
    