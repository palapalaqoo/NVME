'''
Created on Aug 2, 2018

@author: sam
'''
from lib_vct.NVMECom import NVMECom
from __builtin__ import str




class CAP_(object,NVMECom):    
    @property
    def MQES(self):
        return self.get_reg( "show-regs", "cap")[0:4]
    @property
    def TO(self):
        return self.get_reg( "show-regs", "cap")[6:8]     
    def __get__(self, obj, objtype):
        return self.get_reg("show-regs", "cap")    
    
       
class mDescriptor(object,NVMECom):  
    def __init__(self, mcmd=None, mreg='var'):
        self.cmd = mcmd
        self.reg = mreg     
    
    @property
    def ToStr(self):
        return self.get_reg(self.cmd, self.reg)    
    
    @property
    def ToInt(self):
        return int(self.ToStr,16)  
    

    def Bit(self, *args):
    #-- return string
    #-- ex. Bit(7,0), return bit[7:0]
    #-- return string "00100011"  if self.ToStr = "0123" where byte[0] = 0x23, byte[1] = 0x01 (value = 0x0123), last_bit=7, first_bit=0
    #-- ex. Bit(7), return bit 7
        Len = len(args)
        if Len ==1:
            last_bit=args[0]
            first_bit=args[0]
        elif Len ==2:
            last_bit=args[0]
            first_bit=args[1]     
        else:
            return "0"      

        binstr = self.str_reverse(bin(self.ToInt).zfill(16))        
        return self.str_reverse(binstr[first_bit:last_bit+1])
    
    def __str__(self, *args, **kwargs):      
        return self.ToStr
    
class CSTS_(object,NVMECom):    
    RDY=mDescriptor("show-regs", "cap")  
    
    def __get__(self, obj, objtype):
        return self.get_reg("show-regs", "cap")  
    
        
# controller register class
class CR_(object,NVMECom):
    CAP=CAP_()        

    CSTS=mDescriptor("show-regs", "csts")
    AQA=mDescriptor("show-regs", "aqa")  
    ASQ=mDescriptor("show-regs", "asq")  
    AQA=mDescriptor("show-regs", "aqa") 
    ACQ=mDescriptor("show-regs", "acq") 

    
    
    
    
    
    
    
    
    