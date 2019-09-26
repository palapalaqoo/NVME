'''
Created on Aug 3, 2018

@author: root
'''
from lib_vct.NVMECom import NVMECom
from lib_vct.RegDescriptor import RegDescriptor
from lib_vct.RegDescriptor import RegType
# register class
class IdCtrl_(object, NVMECom):
    def __init__(self, obj):        
        self.VID=RegDescriptor("id-ctrl", "vid", nsSpec=False, NVMEobj=obj)
        self.SSVID=RegDescriptor("id-ctrl", "ssvid", nsSpec=False, NVMEobj=obj)
        self.SN=RegDescriptor("id-ctrl", "sn", nsSpec=False, NVMEobj=obj)
        self.MN=RegDescriptor("id-ctrl", "mn", nsSpec=False, NVMEobj=obj)
        self.FR=RegDescriptor("id-ctrl", "fr", nsSpec=False, NVMEobj=obj)
        self.RAB=RegDescriptor("id-ctrl", "rab", nsSpec=False, NVMEobj=obj)
        self.IEEE=RegDescriptor("id-ctrl", "ieee", nsSpec=False, NVMEobj=obj)
        self.CMIC=RegDescriptor("id-ctrl", "cmic", nsSpec=False, NVMEobj=obj)
        self.MDTS=RegDescriptor("id-ctrl", "mdts", nsSpec=False, NVMEobj=obj)
        self.CNTLID=RegDescriptor("id-ctrl", "cntlid", nsSpec=True, NVMEobj=obj)
        self.VER=RegDescriptor("id-ctrl", "ver", nsSpec=False, NVMEobj=obj)
        self.RTD3R=RegDescriptor("id-ctrl", "rtd3r", nsSpec=False, NVMEobj=obj)
        self.RTD3E=RegDescriptor("id-ctrl", "rtd3e", nsSpec=False, NVMEobj=obj)
        self.OAES=RegDescriptor("id-ctrl", "oaes", nsSpec=False, NVMEobj=obj)
        self.CTRATT=RegDescriptor("id-ctrl", "ctratt", nsSpec=False, NVMEobj=obj)
        self.FGUID=RegDescriptor("id-ctrl", "fguid", nsSpec=False, NVMEobj=obj)
        self.OACS=RegDescriptor("id-ctrl", "oacs", nsSpec=False, NVMEobj=obj)
        self.ACL=RegDescriptor("id-ctrl", "acl", nsSpec=False, NVMEobj=obj)
        self.AERL=RegDescriptor("id-ctrl", "aerl", nsSpec=False, NVMEobj=obj)
        self.FRMW=RegDescriptor("id-ctrl", "frmw", nsSpec=False, NVMEobj=obj)
        self.LPA=RegDescriptor("id-ctrl", "lpa", nsSpec=False, NVMEobj=obj)
        self.ELPE=RegDescriptor("id-ctrl", "elpe", nsSpec=False, NVMEobj=obj)
        self.NPSS=RegDescriptor("id-ctrl", "npss", nsSpec=False, NVMEobj=obj)
        self.AVSCC=RegDescriptor("id-ctrl", "avscc", nsSpec=False, NVMEobj=obj)
        self.APSTA=RegDescriptor("id-ctrl", "apsta", nsSpec=False, NVMEobj=obj)
        self.WCTEMP=RegDescriptor("id-ctrl", "wctemp", nsSpec=False, regType=RegType.decimal, NVMEobj=obj)
        self.CCTEMP=RegDescriptor("id-ctrl", "cctemp", nsSpec=False, NVMEobj=obj)
        self.MTFA=RegDescriptor("id-ctrl", "mtfa", nsSpec=False, NVMEobj=obj)
        self.HMPRE=RegDescriptor("id-ctrl", "hmpre", nsSpec=False, NVMEobj=obj)
        self.HMMIN=RegDescriptor("id-ctrl", "hmmin", nsSpec=False, NVMEobj=obj)
        self.TNVMCAP=RegDescriptor("id-ctrl", "tnvmcap",0 , 65535, RegType.decimal, nsSpec=False, NVMEobj=obj)
        self.UNVMCAP=RegDescriptor("id-ctrl", "unvmcap",0 , 65535, RegType.decimal, nsSpec=False, NVMEobj=obj)
        self.RPMBS=RegDescriptor("id-ctrl", "rpmbs", nsSpec=False, NVMEobj=obj)
        self.EDSTT=RegDescriptor("id-ctrl", "edstt", nsSpec=False, NVMEobj=obj)
        self.DSTO=RegDescriptor("id-ctrl", "dsto", nsSpec=False, NVMEobj=obj)
        self.FWUG=RegDescriptor("id-ctrl", "fwug", nsSpec=False, NVMEobj=obj)
        self.KAS=RegDescriptor("id-ctrl", "kas", nsSpec=False, NVMEobj=obj)
        self.HCTMA=RegDescriptor("id-ctrl", "hctma", nsSpec=False, NVMEobj=obj)
        self.MNTMT=RegDescriptor("id-ctrl", "mntmt",0 , 65535, RegType.decimal, nsSpec=False, NVMEobj=obj)
        self.MXTMT=RegDescriptor("id-ctrl", "mxtmt",0 , 65535, RegType.decimal, nsSpec=False, NVMEobj=obj)
        self.SANICAP=RegDescriptor("id-ctrl", "sanicap", nsSpec=False, NVMEobj=obj)
        self.SQES=RegDescriptor("id-ctrl", "sqes", nsSpec=False, NVMEobj=obj)
        self.CQES=RegDescriptor("id-ctrl", "cqes", nsSpec=False, NVMEobj=obj)
        self.MAXCMD=RegDescriptor("id-ctrl", "maxcmd", nsSpec=False, NVMEobj=obj)
        self.NN=RegDescriptor("id-ctrl", "nn", nsSpec=False, NVMEobj=obj)
        self.ONCS=RegDescriptor("id-ctrl", "oncs", nsSpec=False, NVMEobj=obj)
        self.FUSES=RegDescriptor("id-ctrl", "fuses", nsSpec=False, NVMEobj=obj)
        self.FNA=RegDescriptor("id-ctrl", "fna", nsSpec=False, NVMEobj=obj)
        self.VWC=RegDescriptor("id-ctrl", "vwc", nsSpec=False, NVMEobj=obj)
        self.AWUN=RegDescriptor("id-ctrl", "awun", nsSpec=False, NVMEobj=obj)
        self.AWUPF=RegDescriptor("id-ctrl", "awupf", nsSpec=False, NVMEobj=obj)
        self.NVSCC=RegDescriptor("id-ctrl", "nvscc", nsSpec=False, NVMEobj=obj)
        self.ACWU=RegDescriptor("id-ctrl", "acwu", nsSpec=False, NVMEobj=obj)
        self.SGLS=RegDescriptor("id-ctrl", "sgls", nsSpec=False, NVMEobj=obj)
        self.SUBNQN=RegDescriptor("id-ctrl", "subnqn", nsSpec=False, NVMEobj=obj)
    
           

    
    
    