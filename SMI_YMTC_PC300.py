#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import python built-ins
import sys
# Import VCT modules
from lib_vct.NVME import NVME

class SMI_YMTC_PC300(NVME):
    ScriptName = "SMI_YMTC_PC300.py"
    Author = "Sam"
    Version = "20210204"

    def getENDGID(self, ns):
        CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=0x0 --namespace-id=%s 2>&1"%(self.dev_port, ns)
        rTDS=self.shell_cmd(CMD)
        DS=self.AdminCMDDataStrucToListOrString(rTDS, 2)            
        if DS==None:
            return None
        else:
            return (DS[103]<<8) + DS[102]  
    
    def __init__(self, argv):
        # initial parent class
        super(SMI_YMTC_PC300, self).__init__(argv)

    # define pretest, if not return 0 , skip all subcases
    def PreTest(self):        
        return 0            

    # <define sub item scripts>
    SubCase1TimeOut = 600
    SubCase1Desc = "[VCTDEPT-718][CTA-211] Identify controller info FLUSH-NON-VOLATILE Supported value is 0b expect is 1b."   
    SubCase1KeyWord = ""
    def SubCase1(self):
        ret_code=0
        self.Print("Issue command to get 4096byte of identify data")
        CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=0x1 2>&1"%self.dev_port
        # returnd data structure
        rTDS=self.shell_cmd(CMD)
        # format data structure to list 
        DS=self.AdminCMDDataStrucToListOrString(strIn=rTDS, ReturnType=2)
        if DS==None:
            self.Print( "Fail to get data structure, quit !","f")
            return 0
        else:
            self.Print( "Success to get data structure")   
  
        self.Print("")
        byte3999 = DS[3999]
        self.Print ("Identify data structure, offset 3999, current value: 0x%X"%byte3999)
        self.Print ("check bit 0( FLUSH-NON-VOLATILE), expect is 1")        
        if byte3999&(1)==1:
            self.Print("PASS", "p")  
        else:
            self.Print("Fail", "f")
            ret_code=1 
                
        return ret_code
    
    
    SubCase2TimeOut = 600
    SubCase2Desc = "[VCTDEPT-719][CTA-212] PCIe Register L0s Exit Latency is not 111b."   
    SubCase2KeyWord = ""
    def SubCase2(self):
        ret_code = 0
        self.Print("PCI Express Capability offset(PXCAP): %s"%self.PXCAP)
        LCR_o = self.PXCAP + 0xC
        self.Print("Link Capabilities Register offset: %s(PXCAP + 0xC)"%LCR_o)
        
        self.Print("")
        LCR = (self.read_pcie(LCR_o, 0)<<0) + (self.read_pcie(LCR_o, 1)<<8) + (self.read_pcie(LCR_o, 1)<<16) + (self.read_pcie(LCR_o, 1)<<24)
        self.Print("Current Link Capabilities Register(LCR): 0x%X"%LCR)        
        ASPMS = (LCR>>10)&0x3
        self.Print("Current ASPM Support(LCR[11:10]): 0x%X"%ASPMS, "b")                
        L0sEL = (LCR>>12)&0x7
        self.Print("Current L0s Exit Latency(LCR[14:12]): 0x%X"%L0sEL, "b")        
        ASPMOC = 1 if LCR&(1<<22)>=1 else 0
        self.Print("Current ASPM Optionality Compliance(LCR[22]): 0x%X"%ASPMOC, "b")

        
                
        self.Print("")
        self.Print("Check if Current ASPM Optionality Compliance = 1")
        if ASPMOC==1:
            self.Print("PASS", "p")  
        else:
            self.Print("Fail", "f")
            ret_code=1
        self.Print("")     
               
        self.Print("When a component does not advertise that it supports L0s,")
        self.Print("as indicated by its ASPM Support field value being 00b or 10b,")
        self.Print("it is recommended that the component's L0s Exit Latency field return a value of 111b")
        if not (ASPMS==0x0 or ASPMS==0x2):
            self.Print("Current ASPM Support not 00b or 10b, skip", "b")
        else:
            self.Print("Chcek if L0s Exit Latency field return a value of 111b") 
            if L0sEL==0x7:
                self.Print("PASS", "p")  
            else:
                self.Print("Fail", "f")
                ret_code=1                  
                    
        return ret_code

    SubCase3TimeOut = 600
    SubCase3Desc = "[YMTC CTA-296] Endurance Group Identifier (ENDGID) should not be 0"   
    SubCase3KeyWord = ""
    def SubCase3(self):
        ret_code = 0
        self.Print("Expect:")
        self.SetPrintOffset(4, "add")
        self.Print("Endurance Group Identifier (ENDGID) value should be 1.")
        self.Print("Controller Attributes (CTRATT) Bit 4 is 1.")
        self.Print("Asynchronous Events Supported (OAES）bit14 is 1.")
        self.SetPrintOffset(-4, "add")
        self.Print("")
        
        self.Print("Actual:")
        self.SetPrintOffset(4, "add")        
        ENDGID = self.getENDGID(ns=1)
        self.Print("ENDGID: %s"%ENDGID)
        self.Print("Check if ENDGID = 1")
        if ENDGID==1:
            self.Print("Pass", "p")  
        else:
            self.Print("Fail", "f")         
            ret_code = 1
        
        self.Print("")
        CTRATT =  self.IdCtrl.CTRATT.int            
        self.Print("CTRATT: %s(%s)"%(CTRATT, self.intToBinaryStr(CTRATT)))
        self.Print("Check if CTRATT bit 4 = 1")
        if self.IdCtrl.CTRATT.bit(4)=="1":
            self.Print("Pass", "p")  
        else:
            self.Print("Fail", "f")         
            ret_code = 1        
        
        self.Print("")
        OAES =  self.IdCtrl.OAES.int
        self.Print("OAES: %s(%s)"%(OAES, self.intToBinaryStr(OAES)))
        self.Print("Check if OAES bit 14 = 1")
        if self.IdCtrl.OAES.bit(14)=="1":
            self.Print("Pass", "p")  
        else:
            self.Print("Fail", "f")         
            ret_code = 1        
                    
        self.Print("")
        self.SetPrintOffset(-4, "add")
        return ret_code
        
    SubCase4TimeOut = 600
    SubCase4Desc = "[YMTC CTA-296] Endurance Group Identifier (ENDGID) should not be 0"   
    SubCase4KeyWord = ""
    def SubCase4(self):
        ret_code = 0
        pass
        return ret_code        
        
    # </define sub item scripts>

    # define PostTest  
    def PostTest(self): 
        return True 


if __name__ == "__main__":
    DUT = SMI_YMTC_PC300(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    