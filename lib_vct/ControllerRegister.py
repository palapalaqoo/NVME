'''
Created on Aug 2, 2018

@author: sam
'''
from lib_vct.NVMECom import NVMECom
from lib_vct.RegDescriptor import RegDescriptor



    
        
# controller register class
class CR_(object,NVMECom):
     
    CAP=RegDescriptor("show-regs", "cap")
    CAP.MQES=RegDescriptor("show-regs", "cap", 0, 15)
    CAP.CQR=RegDescriptor("show-regs", "cap", 16, 16)
    CAP.AMS=RegDescriptor("show-regs", "cap", 17, 18)
    CAP.TO=RegDescriptor("show-regs", "cap", 24, 31)
    CAP.DSTRD=RegDescriptor("show-regs", "cap", 32, 35)
    CAP.NSSRS=RegDescriptor("show-regs", "cap", 36, 36)
    CAP.CSS=RegDescriptor("show-regs", "cap", 37, 44)
    CAP.BPS=RegDescriptor("show-regs", "cap", 45, 45)
    CAP.MPSMIN=RegDescriptor("show-regs", "cap", 48, 51)
    CAP.MPSMAX=RegDescriptor("show-regs", "cap", 52, 55)
    
    VS=RegDescriptor("show-regs", "version")
    VS.TER=RegDescriptor("show-regs", "version", 0, 7)
    VS.MNR=RegDescriptor("show-regs", "version", 8, 15)
    VS.MJR=RegDescriptor("show-regs", "version", 16, 31)
    
    INTMS=RegDescriptor("show-regs", "intms")
    INTMS.IVMS=RegDescriptor("show-regs", "intms", 0, 31)
    
    INTMC=RegDescriptor("show-regs", "intmc")
    INTMC.IVMS=RegDescriptor("show-regs", "intmc", 0, 31)    
    
    CC=RegDescriptor("show-regs", "cc")
    CC.EN=RegDescriptor("show-regs", "cc", 0, 0)
    CC.CSS=RegDescriptor("show-regs", "cc", 4, 6)
    CC.MPS=RegDescriptor("show-regs", "cc", 7, 10)
    CC.AMS=RegDescriptor("show-regs", "cc", 11, 13)
    CC.SHN=RegDescriptor("show-regs", "cc", 14, 15)
    CC.IOSQES=RegDescriptor("show-regs", "cc", 16, 19)
    CC.IOCQES=RegDescriptor("show-regs", "cc", 20, 23)
    CC.RO=RegDescriptor("show-regs", "cc", 24, 31)

    
    CSTS=RegDescriptor("show-regs", "csts")
    CSTS.bss=RegDescriptor("show-regs", "csts")
    AQA=RegDescriptor("show-regs", "aqa")  
    ASQ=RegDescriptor("show-regs", "asq")  
    AQA=RegDescriptor("show-regs", "aqa") 
    ACQ=RegDescriptor("show-regs", "acq") 

    
    
    
    
    
    
    
    
    