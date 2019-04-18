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
        path="/sys/class/block/%s/device/device/sriov_numvfs"%self.dev[5:]
        if self.isfileExist(path):
            return self.shell_cmd("cat %s"%path)
        else:
            return None

    def SetCurrentNumOfVF(self, value):
        path="/sys/class/block/%s/device/device/sriov_numvfs"%self.dev[5:]
        if self.isfileExist(path):
            return True if self.shell_cmd("echo %s > %s 2>&1 >/dev/null ; echo $?"%(value, path))==0 else False
        else:
            return False
        
    def VMC(self, CNTLID, RT, ACT, NR):
        CDW10=(CNTLID<<16) + (RT<<8) + ACT
        CDW11= NR
        CMD = "nvme admin-passthru %s --opcode=0x1C -w --cdw10=%s  --cdw11=%s 2>&1"%(self.dev, CDW10, CDW11, 1)
        rTDS=self.shell_cmd(CMD)
        return rTDS
        
    def Set_PF_ResourceMinimum(self, printInfo=False):        
        if self.VI_ResourceSupported:
            self.Print("Set Primary Controller Resource VI=1 (minimum)") if printInfo else None
            if self.VMC(CNTLID = self.PF_CNTLID, RT = 1, ACT = 1, NR= 1).find("success"):
                return True
            else:
                return False
            
        if self.VQ_ResourceSupported:
            self.Print("Set Primary Controller Resource VQ=2 (minimum)") if printInfo else None
            if self.VMC(CNTLID = self.PF_CNTLID, RT = 0, ACT = 1, NR= 2).find("success"):
                return True
            else:
                return False            

    def Set_VF_ResourceMinimum(self, printInfo=False):  
        for SCEntry in self.SecondaryControllerList:
            SCID= SCEntry.SCID
                
            if self.VI_ResourceSupported:
                self.Print("Set Secondary Controller Resource VI=0 (minimum)") if printInfo else None
                if not self.VMC(CNTLID = SCID, RT = 1, ACT = 1, NR= 0).find("success"):
                    return False
                
            if self.VQ_ResourceSupported:
                self.Print("Set Secondary Controller Resource VQ=0 (minimum)") if printInfo else None
                if not self.VMC(CNTLID = SCID, RT = 0, ACT = 1, NR= 0).find("success"):
                    return False
        return True   

    def Set_VF_ResourceMaxmum(self, printInfo=False):  
        # arrange VQ VI list for all VF
        VF_VQ_List=[]
        VF_VI_List=[]        
        VQResourcesFlexibleTotal  = self.PCCStructure.VQFRT        
        VIResourcesFlexibleTotal  = self.PCCStructure.VIFRT
        totalNumOfVF = len(self.SecondaryControllerList)
        NVQ=int(VQResourcesFlexibleTotal/totalNumOfVF)
        NVQ_mod = VQResourcesFlexibleTotal % totalNumOfVF
        NVI=int(VIResourcesFlexibleTotal/totalNumOfVF)
        NVI_mod = VIResourcesFlexibleTotal % totalNumOfVF        
        for i in range(totalNumOfVF):
            if i<NVQ_mod:
                VF_VQ_List.append(NVQ + 1)
            else:
                VF_VQ_List.append(NVQ)
            if i<NVI_mod:
                VF_VI_List.append(NVI + 1)
            else:
                VF_VI_List.append(NVI)                
        # end
        
        self.Print("Try to set all VF's VQ : %s"%VF_VQ_List) if printInfo else None
        i=0
        for SCEntry in self.SecondaryControllerList:
            SCID= SCEntry.SCID
            NVQ= VF_VQ_List[i]         
            if self.VQ_ResourceSupported:
                self.Print("Set Secondary Controller Resource VQ=%s"%NVQ) if printInfo else None
                if not self.VMC(CNTLID = SCID, RT = 0, ACT = 1, NR= 2).find("success"):
                    return False
            i=i+1   
        
        self.Print("Try to set all VF's VI : %s"%VF_VI_List) if printInfo else None
        i=0
        for SCEntry in self.SecondaryControllerList:
            SCID= SCEntry.SCID
            NVI= VF_VI_List[i]         
            if self.VI_ResourceSupported:
                self.Print("Set Secondary Controller Resource VI=%s "%NVI) if printInfo else None
                if not self.VMC(CNTLID = SCID, RT = 0, ACT = 1, NR= 2).find("success"):
                    return False
            i=i+1         
        return True
        
    def AttachNs(self, nsid, CNTLID):
        return self.shell_cmd("nvme attach-ns %s -n %s -c %s 2>&1 >/dev/null ; echo $?" %(self.dev_port,nsid, CNTLID))
                       
    def CreateMultiNs(self, NumOfNS=8, SizeInBlock=2097152):        
        # Create namespcaes form nsid 1 to nsid 8(default), size 1G(default), and attach to the controller
        # return MaxNs, ex, MaxNs=8, indicate the NS from 1 to 8
        # check if controller supports the Namespace Management and Namespace Attachment commands or not
        NsSupported=True if self.IdCtrl.OACS.bit(3)=="1" else False
        NN=self.IdCtrl.NN.int
        if NsSupported:
            #self.Print ("controller supports the Namespace Management and Namespace Attachment commands"            )
            # set max test namespace <=8(default)
            MaxNs=NumOfNS if NN>NumOfNS else NN
            self.Print(  "create namespcaes form nsid 1 to nsid %s, size 1G, and attach to the controller"%MaxNs )
            error=0            
            for i in range(1, NN+1):        
                # delete NS
                self.DeleteNs(i)    
            self.shell_cmd("nvme reset %s"%self.dev_port)           
            # Create namespaces, and attach it
            for i in range(1, MaxNs+1):

                CreatedNSID=self.CreateNs(SizeInBlock)        
                if CreatedNSID != i:
                    self.Print ("create namespace error!"    )
                    error=1
                    break  
                    
            # if creat ns error          
            if error==1:
                self.Print(  "create namespcaes Fail, reset to namespaces 1" ,"w")
                self.ResetNS()
                MaxNs=1
 
            return MaxNs
        
    def GetControllerList_ThatAreAttachedToTheNamespace(self, nsid):
        rtList=[]
        CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=%s --namespace-id=%s 2>&1"%(self.dev_port, 0x12, nsid)
        rTDS=self.shell_cmd(CMD)
        # format data structure to list 
        DS=self.AdminCMDDataStrucToListOrString(rTDS, 0)            
        if DS==None:
            self.Print( "Fail to get data structure, quit !","f")
            return None
        else:
            # self.Print( "Success to get data structure")            
            #self.Print( "According to Figure 38: Controller List Format")
            NumOfId=self.convert(lists=DS, stopByte=1, startByte=0, mtype=self.TypeInt)
            NumOfId=int(NumOfId, 16)
            #self.Print("    Number of Identifiers: %s"%hex(NumOfId))
            
            for i in range(NumOfId):
                Identifier=self.convert(lists=DS, stopByte=3+(2*i), startByte=2+(2*i), mtype=self.TypeInt)
                Identifier=int(Identifier, 16)            
                rtList.append(Identifier)
            return rtList
        
    def InitFormatTestItems(self):
        # self.TestItems=[[LBAF_number, RP, LBADS, MS],[LBAF_number, RP, LBADS, MS],..]   

        for x in range(15):
            RP = self.LBAF[x][self.lbafds.RP]
            LBADS = self.LBAF[x][self.lbafds.LBADS] 
            MS = self.LBAF[x][self.lbafds.MS] 
            #if MS!=0 and LBADS>=9:                           
            self.FormatTestItems.append([x, RP, LBADS, MS])        
    
    def __init__(self, argv):
        # initial parent class
        super(SMI_SRIOV, self).__init__(argv)
        
        # get PrimaryControllerCapabilitiesStructure
        self.PCCStructure = self.Get_PrimaryControllerCapabilitiesStructure()
        
        # get SecondaryControllerList
        # [SCEntry, class SCE] where SCEntry from 0
        self.SecondaryControllerList=[]
        self.Get_SecondaryControllerList()     
        
        self.PF_CNTLID = self.CNTLID
        
        # 
        self.VirtualizationManagementCommandSupported= True if self.IsOpcodeSupported(CMDType="admin", opcode=0x1C) else False
        self.NsManagementCommandSupported= True if self.IsOpcodeSupported(CMDType="admin", opcode=0x0D) else False
        self.Sysfs_SRIOV_Supported= True if self.GetCurrentNumOfVF()!=None else False
        
        self.VI_ResourceSupported=False
        if self.PCCStructure != None:
            self.VI_ResourceSupported = True if self.PCCStructure.CRT&0b0010 > 0 else False
            
        self.VQ_ResourceSupported=False
        if self.PCCStructure != None:
            self.VQ_ResourceSupported = True if self.PCCStructure.CRT&0b0001 > 0 else False        
        
        # format test    
        self.LBAF=self.GetAllLbaf()
        # [[LBAF_number, RP, LBADS, MS],[LBAF_number, RP, LBADS, MS],..]   
        self.FormatTestItems=[]
        self.InitFormatTestItems()

    # define pretest  
    def PreTest(self):        
        if self.VirtualizationManagementCommandSupported:
            self.Print("Virtualization Management Command Supported: Yes")
        else:
            self.Print("Virtualization Management Command Supported: No", "w")
            
        if self.NsManagementCommandSupported:
            self.Print("Namespace Management Command Supported: Yes")
        else:
            self.Print("Namespace Management Command Supported: No", "w")             
            
        if self.PCCStructure != None:
            self.Print("Primary Controller Capabilities Structure is avaliable: Yes")
        else:
            self.Print("Primary Controller Capabilities Structure is avaliable: No", "w")         

        if len(self.SecondaryControllerList) != 0:
            self.Print("Secondary Controller List is avaliable: Yes")
        else:
            self.Print("Secondary Controller List is avaliable: No", "w")                   
                    
        if self.Sysfs_SRIOV_Supported:
            self.Print("Linux's sysfs support SRIOV: Yes")
        else:
            self.Print("Linux's sysfs support SRIOV: No", "w")    
                    
        return True            

    # <define sub item scripts>
    SubCase1TimeOut = 60
    SubCase1Desc = "Enable all VF with all Flexible Resources"   
    SubCase1KeyWord = ""
    def SubCase1(self):
        ret_code=0
        
        self.Print("Try to set Primary Controller Resources to Minimum")
        self.Set_PF_ResourceMinimum(printInfo=True)
        self.Print("Done")
        
        self.Print("") 
        self.Print("Set all VF offline")
        if not self.SetCurrentNumOfVF(0):
            self.Print("Fail, quit all", "f"); return 1      
        
        self.Print("")     
        self.Print("Try to set Secondary Controller Resources to Minimum")
        self.Set_PF_ResourceMinimum(printInfo=True)
        self.Print("Done")  
        
        self.Print("") 
        self.Print("Set all VF online")
        if not self.SetCurrentNumOfVF(len(self.SecondaryControllerList)):
            self.Print("Fail, quit all", "f"); return 1               
        
        self.Print("")     
        NumOfNS=len(self.SecondaryControllerList)+1
        self.Print("Try to create %s namespaces"%NumOfNS)  
        if not self.CreateMultiNs(NumOfNS, 10000)!=   NumOfNS:
            self.Print("Fail, quit all", "f"); return 1    
            
        self.Print("")             
        self.Print("Try to attach namespaces to make each controller having a private namespace and access to a namespace shared by all controllers")  
        self.Print("    Try to attach namespaces 1 - %s to VF 1 - %s"%(NumOfNS-1, NumOfNS-1))
        nsid=1
        for SCEntry in self.SecondaryControllerList:
            SCID= SCEntry.SCID
            if not self.AttachNs(nsid, SCID) ==0:
                self.Print("    Fail at nsid=%s, quit all"%nsid, "f"); return 1    
            nsid=nsid+1      
        self.Print("Done")
        self.Print("    Try to attach namespaces %s to all VF"%(NumOfNS)) 
        nsid=NumOfNS
        for SCEntry in self.SecondaryControllerList:
            SCID= SCEntry.SCID
            if not self.AttachNs(nsid, SCID) ==0:
                self.Print("    Fail at SCID=%s, quit all"%SCID, "f"); return 1            
        self.nvme_reset()                
        self.Print("Done")
                
        self.Print("")     
        self.Print("Check if the Controller List of Identify command with CNS=0x12 indicates that namespaces 1 - %s was attached to VF 1 - %s"%(NumOfNS-1, NumOfNS-1))   
        self.Print("And namespaces %s was attached to all VF  "%(NumOfNS))
        self.Print("------------------------------------------------------")   
        for nsid in range(1 , NumOfNS+1):
            isPass = True
            # if not last one, namespaces attach to 1 SCID only
            if nsid!=NumOfNS:
                CL = self.GetControllerList_ThatAreAttachedToTheNamespace(nsid)
                SCID = self.SecondaryControllerList[nsid-1].SCID
                if CL[0]!=SCID: isPass = False
            else:
            # namespaces was attached to all VF 
                CL = self.GetControllerList_ThatAreAttachedToTheNamespace(nsid)
                CL.sort()                
                SCID = [SCEntry.SCID for SCEntry in self.SecondaryControllerList]
                SCID.sort()
                if CL[0]!=SCID: isPass = False

            if isPass:
                self.Print("namespaces %s : ControllerList: %s : Pass"%(nsid, CL), "p")
            else:
                self.Print("namespaces %s : ControllerList: %s : Fail"%(nsid, CL), "f")
                ret_code = 1
            
        self.Print("------------------------------------------------------")   
        if ret_code!=0: return 1
        
                
        self.Print("")     
        self.Print("Try to format all namespaces")   
        self.write
        
        
        
        
        
        self.Print("")    
        if self.VI_ResourceSupported:
            VIResourcesFlexibleTotal=self.PCCStructure.VIFRT
            
            
            
            
        # minimum number of VQ Resources that may be assigned is two    
            
            
        
        fdsafa


        
        return ret_code

    # </define sub item scripts>

    # define PostTest  
    def PostTest(self): 
        return True 


if __name__ == "__main__":
    DUT = SMI_SRIOV(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    