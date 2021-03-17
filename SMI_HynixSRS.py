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
        self.CDW11_ElementAction = 0 # for set cmd
        self.CDW11_ElementType = 0  # for get cmd
        self.CDW10_SV = 0
    _pack_=1
    _fields_=[('NumberofMetadataElementDescriptors',c_ubyte),
            ('Reserved',c_ubyte),
            ('ElementType',c_ubyte,6),
            ('Reserved_7_6',c_ubyte,2),
            ('ElementRevision',c_ubyte,4),
            ('Reserved_15_12',c_ubyte,4),
            ('ElementLength',c_ushort),
            ('ElementValue',c_char * 128)]  
    def hexdumpMetadataElementDescriptor(self):
        mStr = string_at(addressof(self),sizeof(self))
        mStr = self.mNVME.hexdump(src=mStr)
        return  mStr
    def getMetadataElementDescriptorInHexList(self):
        mStr = string_at(addressof(self),sizeof(self))
        hex_chars = map(ord,mStr)
        return  hex_chars        
    def IssueSetFeatureCMD(self):
        CDW11 = (self.CDW11_ElementAction&0b11)<<13 # 2 bit was used
        mStr = string_at(addressof(self),sizeof(self))
        hex_chars = map(ord,mStr)
        Data = ""
        for mByte in hex_chars:
            Data = Data+"\\x%X"%mByte
        #TODO 
        #print Data
        return True            
            
        mStr, sc = self.mNVME.set_feature_with_sc(fid=0xDA, value=CDW11, SV=self.CDW10_SV, Data=Data, nsid=0)
        if sc==0:
            return True
        else:
            return False

    def IssueGetFeatureCMD(self):
        mStr = string_at(addressof(self),sizeof(self))
        hex_chars = map(ord,mStr)
        Data = ""
        for mByte in hex_chars:
            Data = Data+"\\x%X"%mByte        
        #TODO fid
        rawDataList, SC = self.mNVME.GetFeatureValueWithSC(fid=0xE, cdw11=self.CDW11_ElementType, sel=0, nsid=0, nsSpec=False, dataLen=134, data=Data)
        if SC !=0:
            self.mNVME.Print("Get feature with dataLen=134 fail","f")
            return False
        # convert hex to string
        mStr = ''.join([chr(int(x, 16)) for x in rawDataList])
        # ctypes.memmove(dst, src, count), copies count bytes from src to dst.
        if sizeof(self) != len(rawDataList):
            self.mNVME.Print("Error!, structure size: %s, getfeature rawData size: %s"%(sizeof(self), len(rawDataList)), "f")
            return False
        memmove(addressof(self),mStr,sizeof(self))        
        return True



class SMI_HynixSRS(NVME):
    ScriptName = "SMI_HynixSRS.py"
    Author = ""
    Version = "20210316"
  
    def GetFeatureValueWithSC(self, fid, cdw11=0, sel=0, nsid=1, nsSpec=False, dataLen=134, data=None):
    # get feature with status code
        rawDataList=[] 
        SC=0     
        if True:
            buf, SC = self.get_feature_with_sc(fid = fid, cdw11=cdw11, sel = sel, nsid = nsid, nsSpec=nsSpec, dataLen=dataLen, data=data) 
            # if command success
            if SC==0:
                # find all byte data, start with : to last byte, 
                patten=re.findall(":\s.*\w{2}", buf) # e.x. 0000: bc 14 ed 3d 78 01 02 00 00 00 00 00 00 00 00 00 "...=x..........."
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
    
    def __init__(self, argv):
        # initial parent class
        super(SMI_HynixSRS, self).__init__(argv)
        self.ETlist = range(1, 18)
        self.ETlist.append(object)

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
        self.Print("1) Read all host meta data log")
        self.SetPrintOffset(4)
        mData = HostMetadataDataStructure(self)
        for ET in self.ETlist:
            mData.CDW11_ElementType = ET
            if not mData.IssueGetFeatureCMD():
                self.Print("CMD fail!","f")
                return 1
            else:
                self.Print("ElementType %s, EVAL: %s"%(ET, mData.ElementValue))
        
        
        self.Print("")
        self.SetPrintOffset(0)
        self.Print("2) Delete all host meta data log")
        self.SetPrintOffset(4)
        mData = HostMetadataDataStructure(self)
        mData.CDW11_ElementAction = 1 # Delete Entry
        mData.ElementLength = 0
        for ET in self.ETlist:
            mData.ElementType = ET
            if not mData.IssueSetFeatureCMD():
                self.Print("CMD fail!","f")
                self.Print("Metadata Element Descriptor:")
                self.Print( mData.hexdumpMetadataElementDescriptor())
                return 1
        self.Print("Done", "p")   

        self.Print("")
        self.SetPrintOffset(0)
        self.Print("3) Read all host meta data log and check if all data log was deleted(return zero (NULL character) as the Element Value)")
        self.SetPrintOffset(4)
        mData = HostMetadataDataStructure(self)
        for ET in self.ETlist:
            mData.CDW11_ElementType = ET
            if not mData.IssueGetFeatureCMD():
                self.Print("CMD fail!","f")
                return 1
            else:
                self.Print("ElementType %s, EVAL: %s"%(ET, mData.ElementValue))
                cnt = 0
                for value in mData.getMetadataElementDescriptorInHexList():
                    cnt +=1
                    # TODO
                    if cnt <=7: #if cnt <=6: # skip first 6 byte, Element Value start at 6th byte of MetadataElementDescriptor
                        continue
                    if value!=0x0:
                        self.Print("Check if all Element Value is zero: Fail!","f")
                        self.Print("Metadata Element Descriptor:")
                        self.Print( mData.hexdumpMetadataElementDescriptor())
                        return 1
                self.Print("Check if all Element Value is zero: Pass!","p")

        
        
        


        

        
        return ret_code

    # </define sub item scripts>

    # define PostTest  
    def PostTest(self): 
        return True 


if __name__ == "__main__":
    DUT = SMI_HynixSRS(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    