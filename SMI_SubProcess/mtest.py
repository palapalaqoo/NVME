#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import python built-ins
import sys
import re
import threading
import time
from time import sleep
# Import VCT modules
from lib_vct.NVME import NVME
from lib_vct import mStruct
import struct
class SMI_PCIPowerStatus(NVME):

    class Point(mStruct.Struct):
        _format = mStruct.Format.LittleEndian
        CNS=0x2
        CNSs=0x2
        x = mStruct.Type.Byte1
        y = mStruct.Type.Byte2
        #z = mStruct.Type.Byte4

    def __init__(self, argv):
        # initial parent class
        super(SMI_PCIPowerStatus, self).__init__(argv)
        

        
        print self.Point.StructSize
        
        #aa=self.shell_cmd("nvme admin-passthru /dev/nvme0n1 --opcode=0x6 --data-len=16 -r --cdw10=0 --namespace-id=1 -b")
        bb='\x01\x04\x02'
        #bb=aa[0:3]
        
        p = self.Point(bb)
        
        cc=p.x
        dd=p.y

        print p.x, p.y   # Prints 1,2
      
        
        
        

    # define pretest  
    def PreTeset(self):                
        return True            

    # <define sub item scripts>
    SubCase1TimeOut = 60
    SubCase1Desc = "1111111111111111111111111111"   
    SubCase1KeyWord = ""
    def SubCase1(self):
        ret_code=0
        self.Print("dev=%s"%self.dev)
        self.Print("dev=%s"%self.dev)
        self.Print("dev=%s"%self.dev)
        self.Print("dev=%s"%self.dev)
        self.Print("dev=%s"%self.dev)
        self.Print("dev=%s"%self.dev)
        self.Print(self.shell_cmd("pwd"))
                
        return ret_code

    SubCase2TimeOut = 60
    SubCase2Desc = "222222222222222222"  
    def SubCase2(self):
        ret_code=1
        self.Print("sleep 1s")
        #sleep(1)
        self.Print("sleep 1s done")

                
        return ret_code

    SubCase3TimeOut = 60
    SubCase3Desc = "333333333333333333"  
    def SubCase3(self):
        ret_code=0
        self.Print("sleep 1s")
        sleep(1)
        self.Print("sleep 1s done")

                
        return ret_code
    # </define sub item scripts>

    # define PostTest  
    def PostTest(self): 
        return True 


if __name__ == "__main__":
    DUT = SMI_PCIPowerStatus(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    
