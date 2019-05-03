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


import sys
import os

'''
try:
    cwd = os.getcwd()
    import Tkinter as tk # this is for python2
except:
    self.Print("Try to  install %s/python27-tkinter-2.7.13-5.el7.x86_64.rpm"%cwd, "w")
    if sys.version_info[0] !=2.7 :
        raise Exception("Must be using Python 2.7")
        sys.exit(1)
    else:
        self.shell_cmd("yum localinstall python27-tkinter-2.7.13-5.el7.x86_64.rpm")
        try:
            import Tkinter as tk # this is for python3
        except:
            
            self.Print("Cant install %s/python27-tkinter-2.7.13-5.el7.x86_64.rpm, quit all"%cwd, "f")
            sys.exit(1)
'''


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
    def PreTest(self):    
        self.shell_cmd("rpm -qa |grep python27-tkinter-2.7.13-5.el7.x86_64.rpm")
             
        try:
            cwd = os.getcwd()
            import Tkinter as tk # this is for python2
        except:
            self.Print("Try to  install %s/python27-tkinter-2.7.13-5.el7.x86_64.rpm"%cwd, "w")
            if sys.version_info[0] !=2 :
                raise Exception("Must be using Python 2.x")
                return 1
            else:
                self.shell_cmd("yum localinstall python27-tkinter-2.7.13-5.el7.x86_64.rpm")
                try:
                    import Tkinter as tk # this is for python3
                except:
                    
                    self.Print("Cant install %s/python27-tkinter-2.7.13-5.el7.x86_64.rpm, quit all"%cwd, "f")
                    return 1
        return True            

    # <define sub item scripts>
    SubCase1TimeOut = 60
    SubCase1Desc = "Test Power State 0000"   
    SubCase1KeyWord = ""
    def SubCase1(self):
        ret_code=1
        
        root=tk.Tk()  
        root.mainloop()

                
        return ret_code
    
    def SubCase2(self):
        ret_code=1
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

    
    
    
    