'''
Created on Aug 3, 2018

@author: root
'''
from lib_vct.NVMECom import NVMECom






   
class IdCtrl_NN_(object, NVMECom):
    def __get__(self, obj, objtype):
        return self.get_reg("id-ctrl", "nn")
 
# register class
class IdCtrl_(object, NVMECom):
    NN=IdCtrl_NN_()  

    
    
    
    