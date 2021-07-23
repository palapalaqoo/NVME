#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import python built-ins
import sys
import re
# Import VCT modules
from lib_vct.NVME import NVME

from ctypes import *

class HostMetadataDataStructure(Structure):
    def __init__(self, NVMEinst):
        # save to mNVME
        self.mNVME = NVMEinst        
        # set default value according to spec.
        self.ElementValue=" " *128 # all string to space(ASCII 20h).
        self.NumberofMetadataElementDescriptors = 1 # always is 1
        self.SetFeature_CDW11_ElementAction = 0 # for set cmd
        self.GetFeature_CDW11_ElementType = 0  # for get cmd
        self.CDW10_SV = 0
    _pack_=1
    _fields_=[('NumberofMetadataElementDescriptors',c_ubyte),
            ('Reserved',c_ubyte),
            ('ElementType',c_ubyte,6), # 6 bit
            ('Reserved_7_6',c_ubyte,2),
            ('ElementRevision',c_ubyte,4),
            ('Reserved_15_12',c_ubyte,4),
            ('ElementLength',c_ushort),
            ('ElementValue',c_char * 128)]  # 128 byte
    def hexdumpMetadataElementDescriptor(self):
        mStr = string_at(addressof(self),sizeof(self))
        mStr = self.mNVME.hexdump(src=mStr)
        return  mStr
    def getMetadataElementDescriptorInHexList(self):
        mStr = string_at(addressof(self),sizeof(self))
        hex_chars = map(ord,mStr)
        return  hex_chars        
    def IssueSetFeatureCMD(self):
    # return mStr, sc
        CDW11 = (self.SetFeature_CDW11_ElementAction&0b11)<<13 # 2 bit was used
        mStr = string_at(addressof(self),sizeof(self))
        hex_chars = map(ord,mStr)
        Data = ""
        for mByte in hex_chars:
            Data = Data+"\\x%X"%mByte
            
        mStr, sc = self.mNVME.set_feature_with_sc(fid=0xDA, value=CDW11, SV=self.CDW10_SV, Data=Data, nsid=0)
        return mStr, sc

    def IssueGetFeatureCMD(self):
    # return true/false       
        #TODO fid
        rawDataList, SC = self.mNVME.GetFeatureValueWithSC(fid=0xDA, cdw11=self.GetFeature_CDW11_ElementType, sel=0, nsid=0, nsSpec=False)
        if SC !=0:
            self.mNVME.Print("Get feature fail","f")
            return False
        # convert hex to string
        mStr = self.mNVME.HexListToStr(rawDataList)
        # ctypes.memmove(dst, src, count), copies count bytes from src to dst.
        if sizeof(self) != len(rawDataList):
            self.mNVME.Print("Error!, structure size: %s, getfeature rawData size: %s"%(sizeof(self), len(rawDataList)), "f")
            return False
        memmove(addressof(self),mStr,sizeof(self))        
        return True

    def PrintAlignString(self,S0, S1, S2, S3, S4, PO="d"):
        #PO: print option: p/f/b/d .. etc, i.e. p=pass, f=fail, b=bold, d=default
        mStr = "{:<12}\t{:<32}\t{:<16}\t{:<16}\t{:<30}".format(S0, S1, S2, S3, S4)
        self.mNVME.Print( mStr , PO)        

            
    def PrintMetadataElementDescriptorTitle(self, PO="d"):
        self.PrintAlignString(S0="ElementType", S1="Definition", S2="ElementRevision", S3="ElementLength", \
                              S4="Element Value", PO=PO)
                    
    def PrintMetadataElementDescriptor(self, PO="d"):
    # PF: default/pass/fail
        # find  Definition name i.e. self.ElementType was defined in MEDlist
        Definition = None
        for MED in self.mNVME.MEDlist:
            definedMED = MED[self.mNVME.MED_Value]
            if definedMED == self.ElementType:
                Definition = MED[self.mNVME.MED_Definition]
                break
        self.PrintAlignString(S0=self.ElementType, S1=Definition, S2=self.ElementRevision, S3=self.ElementLength, \
                              S4=self.ElementValue, PO=PO)

class SMI_Dell_HostMetadataDataStructure(NVME):
    ScriptName = "SMI_Dell_HostMetadataDataStructure.py"
    Author = ""
    Version = "20210707"
  
    def GetFeatureValueWithSC(self, fid, cdw11=0, sel=0, nsid=1, nsSpec=False, dataLen=134, data=None):
    # get feature with status code
        rawDataList=[] 
        SC=0     
        if True:
            buf, SC = self.get_feature_with_sc(fid = fid, cdw11=cdw11, sel = sel, nsid = nsid, nsSpec=nsSpec, dataLen=dataLen, data=data) 
            # if command success
            if SC==0:
                # find all byte data, start with : to last byte, 
                patten=re.findall(":\s.*\s\w{2}\s", buf) # e.x. 0000: bc 14 ed 3d 78 01 02 00 00 00 00 00 00 00 00 00 "...=x..........."
                patten1= ''.join(patten)
                #remove : and space
                patten1=patten1.replace(":", "")
                line=patten1.replace(" ", "")
                # return list
                # put patten in to list type
                n=2
                rawDataList = [line[i:i+n] for i in range(0, len(line), n)]
                if len(rawDataList)!=dataLen:
                        SC = 255   
        return rawDataList, SC  
    
    def WriteOrReplaceAllEntry(self, appendPattern):
        rtCode = True
        self.SetPrintOffset(4)
        mData_Set = HostMetadataDataStructure(self)# set feature structure
        mData_Set.SetFeature_CDW11_ElementAction = 0 # add Entry
        mData_Set.ElementLength = 128
        
        mData_Get = HostMetadataDataStructure(self)# get feature structure   
        for MED in self.MEDlist:
            mData_Set.ElementType = MED[self.MED_Value]
            mData_Set.ElementValue="ElementType %s with appendPattern=%s"%(MED[self.MED_Value], appendPattern) # message will be write
            self.Print("")
            self.Print("ElementType = %s"%MED[self.MED_Value], "b")
            self.SetPrintOffset(4, "add")
            self.Print("1. Set feature with Metadata Element Descriptor as below")
            self.SetPrintOffset(4, "add")
            # print title and data
            mData_Set.PrintMetadataElementDescriptorTitle("d")
            mData_Set.PrintMetadataElementDescriptor("d")
            mStr, sc = mData_Set.IssueSetFeatureCMD()
            if sc!=0:
                self.Print("Set feature CMD fail!","f")
                self.Print("Metadata Element Descriptor:")
                self.Print( mData_Set.hexdumpMetadataElementDescriptor("d"))
                return False
            self.SetPrintOffset(-4, "add")
            mData_Get.GetFeature_CDW11_ElementType = MED[self.MED_Value]
            if not mData_Get.IssueGetFeatureCMD():
                self.Print("Get feature CMD fail!","f")
                return False
            else:
                self.SetMEDtoMEDlist(mData_Get.GetFeature_CDW11_ElementType, mData_Get.getMetadataElementDescriptorInHexList()) # save                
                self.Print("2. Get feature returned Metadata Element Descriptor and print as below")
                self.SetPrintOffset(4, "add")
                # print title and data
                mData_Get.PrintMetadataElementDescriptorTitle("d")
                # if MetadataElementDescriptor from get feature is not equal to set feature command.
                if mData_Get.getMetadataElementDescriptorInHexList()!=mData_Set.getMetadataElementDescriptorInHexList():
                    mData_Get.PrintMetadataElementDescriptor("f") # fail
                    rtCode = False
                else:
                    mData_Get.PrintMetadataElementDescriptor("d") # bold
            if not rtCode:
                self.Print("Fail!, MetadataElementDescriptor from get feature is not equal to MetadataElementDescriptor of set feature command.","f")
                return  False
            
            self.SetPrintOffset(-4, "add")
            self.Print("3. Check if the other entrys remain unchanged.")
            self.SetPrintOffset(4, "add")
            if not self.CheckAllMEDwithMEDlist(MED):
                self.Print("Fail", "f")  
                return False  
            else:
                self.Print("Pass", "p") 
            self.SetPrintOffset(-8, "add")
        self.SetPrintOffset(0)               
        return rtCode

    def VerifySV(self, appendPattern):
        rtCode = True
        self.SetPrintOffset(4)
        mData_Set = HostMetadataDataStructure(self)# set feature structure
        mData_Set.SetFeature_CDW11_ElementAction = 0 # add Entry
        mData_Set.ElementLength = 128
        
        mData_Get = HostMetadataDataStructure(self)# get feature structure   
        for MED in self.MEDlist:
            mData_Set.ElementType = MED[self.MED_Value]
            mData_Set.ElementValue="ElementType %s with appendPattern=%s"%(MED[self.MED_Value], appendPattern) # message will be write
            self.Print("")
            self.Print("Verify ElementType = %s"%MED[self.MED_Value], "b")
            self.SetPrintOffset(4, "add")
            self.Print("1. Set feature with Metadata Element Descriptor as below with SV=1")
            mData_Set.CDW10_SV=1
            self.SetPrintOffset(4, "add")
            # print title and data
            mData_Set.PrintMetadataElementDescriptorTitle("d")
            mData_Set.PrintMetadataElementDescriptor("d")
            self.Print("")
            mStr, sc = mData_Set.IssueSetFeatureCMD()
            self.Print("Return status:%s "%mStr)
            self.Print("Check status, expected status code = 0xD(Feature Identifier Not Savable)'")
            if sc==0xD:
                self.Print("Pass", "p")
            else:
                self.Print("Fail", "f")
                self.Print("Set feature CMD: %s"%self.LastCmd,"f")
                return False
            
            mData_Get.GetFeature_CDW11_ElementType = MED[self.MED_Value]            
            self.SetPrintOffset(-4, "add")
            self.Print("2. Check if the other entrys remain unchanged.")
            self.SetPrintOffset(4, "add")
            if not self.CheckAllMEDwithMEDlist(MED):
                self.Print("Fail", "f")  
                return False  
            else:
                self.Print("Pass", "p")   
            self.SetPrintOffset(-8, "add")          
        self.SetPrintOffset(0)
        return rtCode
    
    def CheckAllMEDwithMEDlist(self, MEDskip=None):
    # compare all MED with MEDlist, expect data is the same
        skipEventType = MEDskip[self.MED_Value]
        mData_Get = HostMetadataDataStructure(self)# get feature structure  
        for MED in self.MEDlist:            
            if MED[self.MED_Value] == skipEventType: # skip
                continue
            # set ElementType and issue get feature
            mData_Get.GetFeature_CDW11_ElementType = MED[self.MED_Value]
            if not mData_Get.IssueGetFeatureCMD():
                self.Print("Get feature CMD fail at ElementType = %s"%mData_Get.GetFeature_CDW11_ElementType,"f")
                return False
            else:
                expectedData = mData_Get.getMetadataElementDescriptorInHexList()
                currData = self.GetMEDfromMEDlist(ID = mData_Get.GetFeature_CDW11_ElementType)
                if expectedData!=currData:
                    self.Print("Fail at ElementType=%s"%mData_Get.GetFeature_CDW11_ElementType, "f")
                    self.Print("Expected MetadataElementDescriptor")
                    src = self.HexListToStr(expectedData)
                    self.Print(self.hexdump(src))
                    self.Print("Current MetadataElementDescriptor")
                    src = self.HexListToStr(currData)
                    self.Print(self.hexdump(src))                
                    return False 
        return True       
    
    def GetMEDfromMEDlist(self, ID):
        for MED in self.MEDlist:
            if MED[self.MED_Value] == ID:
                return MED[self.MED_RawData]
        return None
    
    def SetMEDtoMEDlist(self, ID, rawData):
        for i, MED in enumerate(self.MEDlist):
            if MED[self.MED_Value] == ID:
                self.MEDlist[i][self.MED_RawData]=rawData
                return True
        return False    
    
    def CheckIfIsEmptyEntry(self, MED):
    # MED in self.MEDlist:
        mData = HostMetadataDataStructure(self)
        mData.PrintMetadataElementDescriptorTitle()
        mData.GetFeature_CDW11_ElementType = MED[self.MED_Value]
        if not mData.IssueGetFeatureCMD():
            self.Print("Get feature CMD fail!","f")
            return False
        else:
            self.SetMEDtoMEDlist(mData.GetFeature_CDW11_ElementType, mData.getMetadataElementDescriptorInHexList()) # save
            # Check if all Element Value is zero
            if mData.ElementValue=="":
                isPass = True
            else:
                isPass = False
            '''
            cnt = 0
            for value in mData.getMetadataElementDescriptorInHexList():
                cnt +=1
                if cnt <=6: # skip first 6 byte(byte 0 to byte 6), Element Value start at 6th byte(byte 7) of MetadataElementDescriptor
                    continue
                if value!=0x0:
                    isPass = False
            '''
            # print        
            if isPass:
                mData.PrintMetadataElementDescriptor(PO="p")
                '''        
                for MED in self.MEDlist: 
                    print MED[self.MED_RawData]
                '''                    
            else:
                mData.PrintMetadataElementDescriptor(PO="f")
                self.Print("Metadata Element Descriptor:")
                self.Print( mData.hexdumpMetadataElementDescriptor())
                return False
        return True     
    
    def DeleteAllEntrys(self):
        mData = HostMetadataDataStructure(self)
        mData.SetFeature_CDW11_ElementAction = 1 # Delete Entry
        mData.ElementLength = 0
        for MED in self.MEDlist:
            mData.ElementType = MED[self.MED_Value]
            self.Print("Delete ElementType %s .."%mData.ElementType, "b")
            self.SetPrintOffset(4, "add")
            self.Print("1. Issue set feature to delete ElementType %s"%mData.ElementType)
            mStr, sc = mData.IssueSetFeatureCMD()
            if sc!=0:
                self.Print("Set feature CMD fail!","f")
                self.Print("Metadata Element Descriptor:")
                self.Print( mData.hexdumpMetadataElementDescriptor())
                return False
            self.SetPrintOffset(4, "add")
            self.Print("Done")
            self.SetPrintOffset(-4, "add")
            self.Print("2. Issue get feature to check if ElementType %s was deleted(return zero (NULL character) as the Element Value)"%mData.ElementType)
            self.SetPrintOffset(4, "add")
            if not self.CheckIfIsEmptyEntry(MED):
                self.Print("Fail", "f")    
                return False  
            else:
                self.Print("Pass", "p")    
            self.SetPrintOffset(-4, "add") 

            self.Print("3. Issue get feature to check if all the other entrys remain unchanged.")
            self.SetPrintOffset(4, "add")
            if not self.CheckAllMEDwithMEDlist(MED):
                self.Print("Fail", "f")  
                return False  
            else:
                self.Print("Pass", "p")  
            self.SetPrintOffset(-4, "add")
            self.Print("")
            self.SetPrintOffset(-4, "add")                          
        return True    
    
    def __init__(self, argv):
        # initial parent class
        super(SMI_Dell_HostMetadataDataStructure, self).__init__(argv)
        
        # initial Element Types
        self.MED_Value = 0
        self.MED_Definition = 1
        self.MED_RawData = 2 # MetadataElementDescriptors raw data
        self.MEDlist = []   # Element Type, desc, raw data(MetadataElementDescriptorInHexList)
        self.MEDlist.append([0x1, "Operating System Host Name", None])
        self.MEDlist.append([0x2, "Operating System Driver Name", None])
        self.MEDlist.append([0x3, "Operating System Driver Version:", None])
        self.MEDlist.append([0x4, "Pre-boot Host Name", None])
        self.MEDlist.append([0x5, "Pre-boot Driver Name", None])
        self.MEDlist.append([0x6, "Pre-boot Driver Version", None])
        self.MEDlist.append([0x7, "System Processor Model", None])
        self.MEDlist.append([0x8, "Chipset Driver Name", None])
        self.MEDlist.append([0x9, "Chipset Driver Version", None])
        self.MEDlist.append([0xA, "Operating System Name and Build", None])
        self.MEDlist.append([0xB, "System Product Name", None])
        self.MEDlist.append([0xC, "Firmware Version", None])
        self.MEDlist.append([0xD, "Operating System Driver Filename", None])
        self.MEDlist.append([0xE, "Display Driver Name", None])
        self.MEDlist.append([0xF, "Display Driver Version", None])
        self.MEDlist.append([0x10, "Host-Determined Failure Record", None])

    # define pretest, if not return 0 , skip all subcases
    def PreTest(self):        
        return 0            

    # <define sub item scripts>
    SubCase1TimeOut = 6000
    SubCase1Desc = "[Hynix SRS][Dell] Host Metadata Log"
    SubCase1KeyWord = ""   
    def SubCase1(self):
        ret_code=0

        self.Print("Issue identify to get Dell Unique Features field at vendor specific area (offset 3,072 to 4095) of the Identify Controller Data Structure.")
        CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=0x1 2>&1"%self.dev_port
        # returnd data structure
        rTDS=self.shell_cmd(CMD)
        # format data structure to list 
        DS=self.AdminCMDDataStrucToListOrString(rTDS, ReturnType=2)      
        if len(DS)!=4096:
            self.Print("Identify command fail, CMD : %s"%CMD, "f")
        value = DS[3108] + (DS[3109]<<8)
        
        # TODO
        #value = 0x8003
        
        self.Print("")
        self.Print("Parser Dell Unique Features field")
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
        self.Print("1) Read all host meta data log")
        self.SetPrintOffset(4)
        mData = HostMetadataDataStructure(self)
        mData.PrintMetadataElementDescriptorTitle()
        for MED in self.MEDlist:
            mData.GetFeature_CDW11_ElementType = MED[self.MED_Value]
            if not mData.IssueGetFeatureCMD():
                self.Print("CMD fail!","f")
                return 1
            else:
                self.SetMEDtoMEDlist(mData.GetFeature_CDW11_ElementType, mData.getMetadataElementDescriptorInHexList()) # save                
                mData.PrintMetadataElementDescriptor()
        self.SetPrintOffset(0)
        
        self.Print("")
        self.Print("2) Delete the host meta data log one by one and and check if the other entrys remain unchanged.")
        self.SetPrintOffset(4)
        if not self.DeleteAllEntrys(): return 1
        self.SetPrintOffset(0)
        
        self.Print("")
        self.Print("3) Add the entrys one by one and check the MetadataElementDescriptor of get feature CMD, and check if the other entrys remain unchanged.")
        if not self.WriteOrReplaceAllEntry(appendPattern="Add in Step 3"): return 1
        self.Print("")
        self.Print("4) Replace the entrys one by one and check the MetadataElementDescriptor of get feature CMD, and check if the other entrys remain unchanged.")
        if not self.WriteOrReplaceAllEntry(appendPattern="Replace in Step 4"): return 1  

        self.Print("")
        self.Print("5) Delete the host meta data log one by one and and check if the other entrys remain unchanged.")
        self.SetPrintOffset(4)
        if not self.DeleteAllEntrys(): return 1
        self.SetPrintOffset(0)

        self.Print("")
        self.Print("6) Verify The Save (SV) Field in the Set Features command.")
        if not self.VerifySV(appendPattern="Step 6"): return 1                        
                
        return ret_code

    # </define sub item scripts>

    # define PostTest  
    def PostTest(self): 
        return True 


if __name__ == "__main__":
    DUT = SMI_Dell_HostMetadataDataStructure(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    