#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import python built-ins
import sys
# Import VCT modules
from lib_vct.NVME import NVME
from lib_vct import mStruct
from firewall.functions import getPortID

class SMI_SRIOV(NVME):
    ScriptName = "SMI_SRIOV.py"
    Author = "Sam"
    Version = "20190415"
    
    TypeInt=0x0
    TypeStr=0x1    
    
    # PrimaryControllerCapabilitiesStructure
    class PCCS(mStruct.Struct):
        _format = mStruct.Format.LittleEndian
        CNS=0x14
        CNTLID=mStruct.Type.Byte2   # 2byte
        PORTID=mStruct.Type.Byte2
        CRT=mStruct.Type.Byte1
        RESERVED0=mStruct.Type.Byte1[31-5+1]
        VQFRT=mStruct.Type.Byte4
        VQRFA=mStruct.Type.Byte4
        VQRFAP=mStruct.Type.Byte2
        VQPRT=mStruct.Type.Byte2
        VQFRSM=mStruct.Type.Byte2
        VQGRAN=mStruct.Type.Byte2
        RESERVED1=mStruct.Type.Byte1[63-48+1]
        VIFRT=mStruct.Type.Byte4
        FIRFA=mStruct.Type.Byte4
        VIRFAP=mStruct.Type.Byte2
        VIPRT=mStruct.Type.Byte2
        VIFRSM=mStruct.Type.Byte2
        VIGRAN=mStruct.Type.Byte2
                
                    
    def Get_PrimaryControllerCapabilitiesStructure(self, printInfo=False):
        # expected data length from shell command
        dataLen=self.PCCS.StructSize
        cns=self.PCCS.CNS
        CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=%s -r --cdw10=%s --namespace-id=%s 2>&1"%(self.dev_port, dataLen, cns, 1)
        # issue command to get binary data structure
        rTDS=self.shell_cmd(CMD)
        # format data structure to class
        if len(rTDS)!=dataLen:
            # if return size !=  dataLen            
            self.Print( "Fail to get data structure, quit !","f")  if printInfo else None
            return None
        else:            
            # format data structure to class PrimaryControllerCapabilitiesStructure 
            rtStruct = self.PCCS(rTDS)
            return rtStruct
        
    # Secondary Controller Entry
    class SCE(mStruct.Struct):
        _format = mStruct.Format.LittleEndian
        SCID=mStruct.Type.Byte2   # 2byte
        PCID=mStruct.Type.Byte2
        SCS=mStruct.Type.Byte1
        RESERVED0=mStruct.Type.Byte1[3]
        VFN=mStruct.Type.Byte2
        NVQ=mStruct.Type.Byte2
        NVI=mStruct.Type.Byte2
        RESERVED1=mStruct.Type.Byte1[31-14+1]
        
    def Get_SecondaryControllerList(self, printInfo=False):
        # 
        NumberofIdentifiers=0
        cns=0x15
        CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=%s -r --cdw10=%s --namespace-id=%s 2>&1"%(self.dev_port, 16, cns, 1)
        # issue command to get data structure(return string) for get NumberofIdentifiers
        rTDS=self.shell_cmd(CMD)     
        DS=self.AdminCMDDataStrucToListOrString(rTDS, 0)            
        if DS==None:
            self.Print( "Fail to get data structure, quit !","f") if printInfo else None
            return False
        else:
            NumberofIdentifiers=self.convert(lists=DS, stopByte=0, startByte=0, mtype=self.TypeInt)
            
            # issue command again to get binary data structure (return binary) for get all SCEntry  
            CMD = CMD +" -b"     
            rTDS=self.shell_cmd(CMD) 
            # expected size for all SCEntry which equal to 32
            SCEntrySize=self.SCE.StructSize
            for SCEntry in range(NumberofIdentifiers):
                offset = SCEntrySize*(SCEntry+1)
                data=rTDS[offset : offset+SCEntrySize]
                # get structure here
                rtStruct = self.SCE(data)
                # save to list , e.g., SecondaryControllerList = [SecondaryControllerList, class SCE]
                self.SecondaryControllerList.append([SCEntry, rtStruct])
        
            return True        
    
    def convert(self, lists, stopByte, startByte, mtype, endian="little-endian"):   
        # return is string , eg, '0x1A' or 'SMI2262'        
        # if error
        if startByte>stopByte and mtype==self.TypeInt:
            return "0"
        if startByte>stopByte and mtype==self.TypeStr:
            return ""                    
        # sub bytes
        subList=lists[startByte : stopByte+1]
        mStr=""
        if mtype==self.TypeInt:
            if endian=="little-endian":
                # reverse it and combine
                subList=subList[::-1]
            subList_Str="".join(subList)
            # Converting string to int
            # mStr = hex(int(subList_Str, 16))
            mStr = "0x"+subList_Str            
        elif mtype==self.TypeStr: 
            for byte in subList:
                mStr=mStr+chr(int(byte,16))    
        else:
            mStr =  "0"
        return mStr    
    
    def GetCurrentNumOfVF(self):
        path="/sys/class/block/%s/device/device/sriov_numvfs"%self.dev
        if self.isfileExist(path):
            return self.shell_cmd("cat %s"%path)
        else:
            return None
    
    def __init__(self, argv):
        # initial parent class
        super(SMI_SRIOV, self).__init__(argv)
        
        # get PrimaryControllerCapabilitiesStructure
        self.PCCStructure = self.Get_PrimaryControllerCapabilitiesStructure()
        
        # get SecondaryControllerList
        # [SecondaryControllerList, class SCE]
        self.SecondaryControllerList=[]
        self.Get_SecondaryControllerList()     
        
        # 
        self.VirtualizationManagementCommandSupported= True if self.IsOpcodeSupported(CMDType="admin", opcode=0x1C) else False
        self.Sysfs_SRIOV_Supported= True if self.GetCurrentNumOfVF()!=None else False
        

    # define pretest  
    def PreTest(self):        
        if self.VirtualizationManagementCommandSupported:
            self.Print("Virtualization Management Command Supported")
        else:
            self.Print("Virtualization Management Command is not Supported", "w")
            
        if self.PCCStructure != None:
            self.Print("Primary Controller Capabilities Structure is avaliable")
        else:
            self.Print("Primary Controller Capabilities Structure is not avaliable", "w")         

        if len(self.SecondaryControllerList) != 0:
            self.Print("Secondary Controller List is avaliable")
        else:
            self.Print("Secondary Controller List is not avaliable", "w")                    
        
        if self.Sysfs_SRIOV_Supported:
            self.Print("Linux sysfs support SRIOV")
        else:
            self.Print("Linux sysfs is not support SRIOV", "w")    
                    
        return True            

    # <define sub item scripts>
    SubCase1TimeOut = 60
    SubCase1Desc = ""   
    SubCase1KeyWord = ""
    def SubCase1(self):
        ret_code=0
        
        


        
        return ret_code

    # </define sub item scripts>

    # define PostTest  
    def PostTest(self): 
        return True 


if __name__ == "__main__":
    DUT = SMI_SRIOV(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    