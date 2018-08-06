'''
Created on Aug 3, 2018

@author: root
'''
from lib_vct import NVMECom


# register class




   
class IdNs_NUSE_(object):
    dev="null"
    def __init__(self, dev="/dev/nvme0n1"):
        IdNs_NUSE_.dev = dev
    def __get__(self, obj, objtype):
        return NVMECom.get_reg(IdNs_NUSE_.dev,"id-ns", "nuse", 16)

        
 
class IdNs_NCAP_(object):
    dev="null"
    def __init__(self, dev="/dev/nvme0n1"):
        IdNs_NCAP_.dev = dev
    def __get__(self, obj, objtype):
        return NVMECom.get_reg(IdNs_NCAP_.dev,"id-ns", "ncap", 16)

class IdNs_(object):
    NUSE=IdNs_NUSE_()
    NCAP=IdNs_NCAP_()
    def __init__(self, dev):
        IdNs_NUSE_(dev)
        IdNs_NCAP_(dev)


    
    
    