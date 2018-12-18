'''
Created on Aug 3, 2018

@author: root
'''
from lib_vct.NVMECom import NVMECom
from lib_vct.RegDescriptor import RegDescriptor
from lib_vct.RegDescriptor import RegType
# register class
class IdCtrl_(object, NVMECom):
    VID=RegDescriptor("id-ctrl", "vid", nsSpec=False)
    SSVID=RegDescriptor("id-ctrl", "ssvid", nsSpec=False)
    SN=RegDescriptor("id-ctrl", "sn", nsSpec=False)
    MN=RegDescriptor("id-ctrl", "mn", nsSpec=False)
    FR=RegDescriptor("id-ctrl", "fr", nsSpec=False)
    RAB=RegDescriptor("id-ctrl", "rab", nsSpec=False)
    IEEE=RegDescriptor("id-ctrl", "ieee", nsSpec=False)
    CMIC=RegDescriptor("id-ctrl", "cmic", nsSpec=False)
    MDTS=RegDescriptor("id-ctrl", "mdts", nsSpec=False)
    CNTLID=RegDescriptor("id-ctrl", "cntlid", nsSpec=False)
    VER=RegDescriptor("id-ctrl", "ver", nsSpec=False)
    RTD3R=RegDescriptor("id-ctrl", "rtd3r", nsSpec=False)
    RTD3E=RegDescriptor("id-ctrl", "rtd3e", nsSpec=False)
    OAES=RegDescriptor("id-ctrl", "oaes", nsSpec=False)
    CTRATT=RegDescriptor("id-ctrl", "ctratt", nsSpec=False)
    FGUID=RegDescriptor("id-ctrl", "fguid", nsSpec=False)
    OACS=RegDescriptor("id-ctrl", "oacs", nsSpec=False)
    ACL=RegDescriptor("id-ctrl", "acl", nsSpec=False)
    AERL=RegDescriptor("id-ctrl", "aerl", nsSpec=False)
    FRMW=RegDescriptor("id-ctrl", "frmw", nsSpec=False)
    LPA=RegDescriptor("id-ctrl", "lpa", nsSpec=False)
    ELPE=RegDescriptor("id-ctrl", "elpe", nsSpec=False)
    NPSS=RegDescriptor("id-ctrl", "npss", nsSpec=False)
    AVSCC=RegDescriptor("id-ctrl", "avscc", nsSpec=False)
    APSTA=RegDescriptor("id-ctrl", "apsta", nsSpec=False)
    WCTEMP=RegDescriptor("id-ctrl", "wctemp", nsSpec=False)
    CCTEMP=RegDescriptor("id-ctrl", "cctemp", nsSpec=False)
    MTFA=RegDescriptor("id-ctrl", "mtfa", nsSpec=False)
    HMPRE=RegDescriptor("id-ctrl", "hmpre", nsSpec=False)
    HMMIN=RegDescriptor("id-ctrl", "hmmin", nsSpec=False)
    TNVMCAP=RegDescriptor("id-ctrl", "tnvmcap",0 , 65535, RegType.decimal, nsSpec=False)
    UNVMCAP=RegDescriptor("id-ctrl", "unvmcap",0 , 65535, RegType.decimal, nsSpec=False)
    RPMBS=RegDescriptor("id-ctrl", "rpmbs", nsSpec=False)
    EDSTT=RegDescriptor("id-ctrl", "edstt", nsSpec=False)
    DSTO=RegDescriptor("id-ctrl", "dsto", nsSpec=False)
    FWUG=RegDescriptor("id-ctrl", "fwug", nsSpec=False)
    KAS=RegDescriptor("id-ctrl", "kas", nsSpec=False)
    HCTMA=RegDescriptor("id-ctrl", "hctma", nsSpec=False)
    MNTMT=RegDescriptor("id-ctrl", "mntmt",0 , 65535, RegType.decimal, nsSpec=False)
    MXTMT=RegDescriptor("id-ctrl", "mxtmt",0 , 65535, RegType.decimal, nsSpec=False)
    SANICAP=RegDescriptor("id-ctrl", "sanicap", nsSpec=False)
    SQES=RegDescriptor("id-ctrl", "sqes", nsSpec=False)
    CQES=RegDescriptor("id-ctrl", "cqes", nsSpec=False)
    MAXCMD=RegDescriptor("id-ctrl", "maxcmd", nsSpec=False)
    NN=RegDescriptor("id-ctrl", "nn", nsSpec=False)
    ONCS=RegDescriptor("id-ctrl", "oncs", nsSpec=False)
    FUSES=RegDescriptor("id-ctrl", "fuses", nsSpec=False)
    FNA=RegDescriptor("id-ctrl", "fna", nsSpec=False)
    VWC=RegDescriptor("id-ctrl", "vwc", nsSpec=False)
    AWUN=RegDescriptor("id-ctrl", "awun", nsSpec=False)
    AWUPF=RegDescriptor("id-ctrl", "awupf", nsSpec=False)
    NVSCC=RegDescriptor("id-ctrl", "nvscc", nsSpec=False)
    ACWU=RegDescriptor("id-ctrl", "acwu", nsSpec=False)
    SGLS=RegDescriptor("id-ctrl", "sgls", nsSpec=False)
    SUBNQN=RegDescriptor("id-ctrl", "subnqn", nsSpec=False)

       

    
    
    