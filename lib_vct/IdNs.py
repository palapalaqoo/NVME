'''
Created on Aug 3, 2018

@author: root
'''
from lib_vct.NVMECom import NVMECom


# register class




   
class IdNs_NUSE_(object, NVMECom):
    def __get__(self, obj, objtype):
        return self.get_reg("id-ns", "nuse", 16)

        
 
class IdNs_NCAP_(object, NVMECom):
    def __get__(self, obj, objtype):
        return self.get_reg("id-ns", "ncap", 16)

class IdNs_(object, NVMECom):
    NUSE=IdNs_NUSE_()
    NCAP=IdNs_NCAP_()



    
    
    