'''
Created on Aug 2, 2018

@author: sam
'''
from lib_vct import NVMECom




    
class CAP_MQES_(object):
    dev="null"
    def __init__(self, dev="/dev/nvme0n1"):
        CAP_MQES_.dev = dev
    def __get__(self, obj, objtype):
        return NVMECom.get_reg(CAP_MQES_.dev, "show-regs", "cap")[0:4]
        
class CAP_TO_(object):
    dev="null"
    def __init__(self, dev="/dev/nvme0n1"):
        CAP_TO_.dev = dev
    def __get__(self, obj, objtype):
        return NVMECom.get_reg(CAP_TO_.dev, "show-regs", "cap")[6:8]
    
    
# controller register class
class CR_():
    def __init__(self, dev):
        self.CAP=CAP_(dev)    
    
class CAP_(object):
    dev="null"
    MQES = CAP_MQES_()
    TO = CAP_TO_()
    def __init__(self, dev="/dev/nvme0n1"):
        CAP_.dev = dev        
        CAP_MQES_(dev)
        CAP_TO_(dev)    
  
    def __get__(self, obj, objtype):
        return NVMECom.get_reg(CAP_.dev,"show-regs", "cap")    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    