#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import python built-ins
import sys
import re
import threading
import time
from time import sleep
tkinter = None
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
        
        self.SlotItems=[]
        self.root=None
        
        
    def import_with_auto_install(self):
        package = "Tkinter"
        try:
            return __import__(package)
        except ImportError:
            self.Print("Linux has not install tkinter, Try to install tkinter (yum -y install tkinter)", "w")           
            InstallSuccess =  True if self.shell_cmd("yum -y install tkinter 2>&1 >/dev/null ; echo $?")=="0" else False
            
            if InstallSuccess:
                self.Print("Install Success!, restart script..", "p")                           
                os.execl(sys.executable, sys.executable, * sys.argv)
                return None
            else:
                self.Print("Install fail!, using console mode", "f")
                return None
        

    # define pretest  
    def PreTest(self):    
        #self.shell_cmd("rpm -qa |grep python27-tkinter-2.7.13-5.el7.x86_64.rpm")
        global  tkinter   
        cwd = os.getcwd()   

        tkinter = self.import_with_auto_install()
        if tkinter==None:
            return False
        return True
    
    def ThreadCreatUI(self):
        numOfDev = 4
        ListWidth = 20  # width in characters for current testing item
        ListHight = 20  # hight in characters for current testing item
        ListWidth_ava = 20  # width in characters for list available test item
        ListHight_ava = 10  # hight in characters for list available test item        

        InfoHight = 20 # hight in characters

        

        
        self.root=tkinter.Tk()  
        self.root.geometry('{}x{}'.format(1000, 800))
        import tkMessageBox

        
        F_slotView = tkinter.Frame(self.root)
        F_slotView.pack(side="top")
        
        
        for slot in range(numOfDev):
            # ---- per slot
            
            # create fram for put all slot elements there
            F_slotView_oneSlot = tkinter.Frame(F_slotView)
            F_slotView_oneSlot.pack(side="left")
            
            # add header
            slotHeader = tkinter.Label( F_slotView_oneSlot, text="nvme0n1" ,relief="solid", width= ListWidth)
            slotHeader.pack(side="top")      
                  
            # add listview for current testing item
            Lb = tkinter.Listbox(F_slotView_oneSlot, height = ListHight, width= ListWidth)
            Lb.pack(side="top")
            Lb.insert(1, "Python")
            Lb.insert(2, "Perl")
            # save to SlotItems for further processing
            self.SlotItems.append(Lb)
            
            # hight in characters for list available test item  
            Lb = tkinter.Listbox(F_slotView_oneSlot, height = ListHight_ava, width= ListWidth_ava)
            Lb.pack(side="top")
            Lb.insert(1, "ava")
            Lb.insert(2, "ava1")         
            
            # ---- end per slot
        
        
        F_Info = tkinter.Frame(self.root)
        F_Info.pack(side="bottom")        
        self.root.mainloop()
        return True
                            

    # <define sub item scripts>
    SubCase1TimeOut = 60
    SubCase1Desc = "Test Power State 0000"   
    SubCase1KeyWord = ""
    def SubCase1(self):
        ret_code=1
        
        startT = time.time()

        t = threading.Thread(target = self.ThreadCreatUI)
        t.start() 
        
        while True:
            if not t.is_alive():
                break
            else:
                if len(self.SlotItems)!=0:
                    sleep(1)
                    slot = self.SlotItems[1]
                    slot.insert("end", "Python")
                    
                    CurrentT = time.time()
                    timeUsed=int(CurrentT - startT)
                    
                    if timeUsed>=4:
                        sleep(1)                        
                        self.root.quit()
                        
                        
                        return 0
                
        
        

                
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

    
    
    
    