'''
Created on Aug 2, 2018

@author: sam
'''
from lib_vct.NVMECom import NVMECom




    
class CAP_MQES_(object, NVMECom):
    def __get__(self, obj, objtype):
        return self.get_reg( "show-regs", "cap")[0:4]
        
class CAP_TO_(object,NVMECom):
    def __get__(self, obj, objtype):
        return self.get_reg( "show-regs", "cap")[6:8]
    
    

  
    
class CAP_(object,NVMECom):
    MQES = CAP_MQES_()
    TO = CAP_TO_()
  
    def __get__(self, obj, objtype):
        return self.get_reg("show-regs", "cap")    
    
    
# controller register class
class CR_(object,NVMECom):
    CAP=CAP_()    
    
    
    
    
    
    
    
    
    
    
    
    
    