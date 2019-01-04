'''
Created on Aug 10, 2018

@author: root
'''
from lib_vct.NVMECom import NVMECom
class SanitizeStatus_(object, NVMECom):
    
    @property
    def SPROG(self):
        # ret int form 0 - 25535           
        #return self.str2int(self.get_log(0x81, 20)[0:4])
        return self.str2int(self.get_log_passthru(LID=0x81, size=20, RAE=1,ReturnType=1 )[0:4])
    
    @property
    def SSTAT(self):
        # ret int        
        return self.str2int(self.get_log(0x81, 20)[4:8])
       
    @property
    def SCDW10(self):
        # ret str 4 byte
        return self.str2int(self.get_log(0x81, 20)[8:16])
    
    @property
    def ETFO(self):
        # Estimated Time For Overwrite:
        return self.get_log(0x81, 20)[16:24]
    
    @property
    def ETFBE(self):
        # Estimated Time For Block Erase:
        return self.get_log(0x81, 20)[24:32]
    
    @property
    def ETFCE(self):
        # Estimated Time For Crypto Erase:
        return self.get_log(0x81, 20)[32:40]
    
               





