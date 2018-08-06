'''
Created on Aug 3, 2018

@author: root
'''
from lib_vct import NVMECom






   
class IdCtrl_NN_():
    dev="null"
    def __init__(self, dev="/dev/nvme0n1"):
        IdCtrl_NN_.dev = dev
    def __get__(self):
        return NVMECom.get_reg(IdCtrl_NN_.dev,"id-ctrl", "nn")
 
# register class
class IdCtrl_():
    NN=IdCtrl_NN_()  
    def __init__(self, dev):
        IdCtrl_NN_(dev)  
    
    
    
    