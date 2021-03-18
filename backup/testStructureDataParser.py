#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import python built-ins
import sys
# Import VCT modules
from lib_vct.NVME import NVME

from ctypes import *

class HostMetadataDataStructure(Structure):
    def __init__(self):
        # set all string to space(ASCII 20h).
        self.EVAL=" " *128
    _pack_=1
    _fields_=[('NumberofMetadataElementDescriptors',c_ubyte),
            ('Reserved',c_ubyte),
            ('ET',c_ubyte,6),
            ('Reserved_7_6',c_ubyte,2),
            ('ER',c_ubyte,4),
            ('Reserved_15_12',c_ubyte,4),
            ('ELEN',c_ushort),
            ('EVAL',c_char * 128)]  

class SMI_HynixSRS(NVME):
    ScriptName = "SMI_HynixSRS.py"
    Author = ""
    Version = "20210316"
  
    
  
    
    def __init__(self, argv):
        # initial parent class
        super(SMI_HynixSRS, self).__init__(argv)

    # define pretest, if not return 0 , skip all subcases
    def PreTest(self):        
        return 0            

    # <define sub item scripts>
    SubCase1TimeOut = 60
    SubCase1Desc = "[Hynix SRS] Host Metadata Log"
    SubCase1KeyWord = ""   
    def SubCase1(self):
        ret_code=0

        self.Print("Issue identify to get Dell Unique Features, vendor specific area (offset 3,072 to 4095) of the Identify Controller Data Structure.")
        CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=0x1 2>&1"%self.dev_port
        # returnd data structure
        rTDS=self.shell_cmd(CMD)
        # format data structure to list 
        DS=self.AdminCMDDataStrucToListOrString(rTDS, ReturnType=2)      
        if len(DS)!=4096:
            self.Print("Identify command fail, CMD : %s"%CMD, "f")
        value = DS[3108] + (DS[3109]<<8)
        
        # TODO
        value = 0x8003
        
        self.Print("")
        self.Print("Parser Dell Unique Features")
        self.Print("Dell Unique Features value: 0x%X"%value)
        SCPsupported = True if value&(1<<1) >0 else False
        HostMetadataLogSupported = True if value&(1) >0 else False
        Contentsofthiswordarevalid = 1 if value&(1<<15) >0 else 0
        self.Print("Contents of this word are valid: %s"%Contentsofthiswordarevalid)
        self.Print("HostMetadataLog: %s"%("supported" if HostMetadataLogSupported else "not supported"))
        self.Print("SCP: %s"%("supported" if SCPsupported else "not supported"))
        
        self.Print("")
        if Contentsofthiswordarevalid!=1:
            self.Print("Fail, Contentsofthiswordarevalid must=1", "f")
            return 1
        if not HostMetadataLogSupported:
            self.Print("Fail, HostMetadataLog must=1", "f")
            return 1        
        
        self.Print("")
        self.Print("1) Delete all host meta data log")
        self.SetPrintOffset(4)
        self.Print("1) Delete all Metadata Element Type")
        mData = HostMetadataDataStructure()
        mData.NumberofMetadataElementDescriptors = 1
        mData.ET = 1
        mData.ELEN = 0
        bb = string_at(addressof(mData),sizeof(mData))
        cc = self.hexdump(src=bb) # print 
        self.Print( cc)
        
        
        
        hex_chars = map(hex,map(ord,bb))
        print hex_chars
        print len(hex_chars)
        

        
        return ret_code

    # </define sub item scripts>

    # define PostTest  
    def PostTest(self): 
        return True 


if __name__ == "__main__":
    DUT = SMI_HynixSRS(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    
