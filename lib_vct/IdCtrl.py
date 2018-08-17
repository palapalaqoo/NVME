'''
Created on Aug 3, 2018

@author: root
'''
from lib_vct.NVMECom import NVMECom

 
# register class
class IdCtrl_(object, NVMECom):
    
    @property
    def NN(self):
        return self.get_reg("id-ctrl", "nn")  
    
    @property
    def SANICAP(self):
        return self.get_reg("id-ctrl", "sanicap",16)  

    @property
    def LPA(self):
        return self.get_reg("id-ctrl", "lpa",16)      
    
    @property
    def NPSS(self):
        return self.get_reg("id-ctrl", "npss",16)      
    
       
    
    
    