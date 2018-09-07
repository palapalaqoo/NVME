'''
Created on Aug 3, 2018

@author: root
'''
from lib_vct.NVMECom import NVMECom
from lib_vct.RegDescriptor import RegDescriptor
 
# register class
class IdCtrl_(object, NVMECom):
    
    VID=RegDescriptor("id-ctrl", "vid")
    SSVID=RegDescriptor("id-ctrl", "ssvid")
    SN=RegDescriptor("id-ctrl", "sn")
    MN=RegDescriptor("id-ctrl", "mn")
    FR=RegDescriptor("id-ctrl", "fr")
    RAB=RegDescriptor("id-ctrl", "rab")
    IEEE=RegDescriptor("id-ctrl", "ieee")
    CMIC=RegDescriptor("id-ctrl", "cmic")
    MDTS=RegDescriptor("id-ctrl", "mdts")
    CNTLID=RegDescriptor("id-ctrl", "cntlid")
    VER=RegDescriptor("id-ctrl", "ver")
    RTD3R=RegDescriptor("id-ctrl", "rtd3r")
    RTD3E=RegDescriptor("id-ctrl", "rtd3e")
    OAES=RegDescriptor("id-ctrl", "oaes")
    CTRATT=RegDescriptor("id-ctrl", "ctratt")
    FGUID=RegDescriptor("id-ctrl", "fguid")
    OACS=RegDescriptor("id-ctrl", "oacs")
    ACL=RegDescriptor("id-ctrl", "acl")
    AERL=RegDescriptor("id-ctrl", "aerl")
    FRMW=RegDescriptor("id-ctrl", "frmw")
    LPA=RegDescriptor("id-ctrl", "lpa")
    ELPE=RegDescriptor("id-ctrl", "elpe")
    NPSS=RegDescriptor("id-ctrl", "npss")
    AVSCC=RegDescriptor("id-ctrl", "avscc")
    APSTA=RegDescriptor("id-ctrl", "apsta")
    WCTEMP=RegDescriptor("id-ctrl", "wctemp")
    CCTEMP=RegDescriptor("id-ctrl", "cctemp")
    MTFA=RegDescriptor("id-ctrl", "mtfa")
    HMPRE=RegDescriptor("id-ctrl", "hmpre")
    HMMIN=RegDescriptor("id-ctrl", "hmmin")
    TNVMCAP=RegDescriptor("id-ctrl", "tnvmcap")
    UNVMCAP=RegDescriptor("id-ctrl", "unvmcap")
    RPMBS=RegDescriptor("id-ctrl", "rpmbs")
    EDSTT=RegDescriptor("id-ctrl", "edstt")
    DSTO=RegDescriptor("id-ctrl", "dsto")
    FWUG=RegDescriptor("id-ctrl", "fwug")
    KAS=RegDescriptor("id-ctrl", "kas")
    HCTMA=RegDescriptor("id-ctrl", "hctma")
    MNTMT=RegDescriptor("id-ctrl", "mntmt")
    MXTMT=RegDescriptor("id-ctrl", "mxtmt")
    SANICAP=RegDescriptor("id-ctrl", "sanicap")
    SQES=RegDescriptor("id-ctrl", "sqes")
    CQES=RegDescriptor("id-ctrl", "cqes")
    MAXCMD=RegDescriptor("id-ctrl", "maxcmd")
    NN=RegDescriptor("id-ctrl", "nn")
    ONCS=RegDescriptor("id-ctrl", "oncs")
    FUSES=RegDescriptor("id-ctrl", "fuses")
    FNA=RegDescriptor("id-ctrl", "fna")
    VWC=RegDescriptor("id-ctrl", "vwc")
    AWUN=RegDescriptor("id-ctrl", "awun")
    AWUPF=RegDescriptor("id-ctrl", "awupf")
    NVSCC=RegDescriptor("id-ctrl", "nvscc")
    ACWU=RegDescriptor("id-ctrl", "acwu")
    SGLS=RegDescriptor("id-ctrl", "sgls")
    SUBNQN=RegDescriptor("id-ctrl", "subnqn")

       

    
    
    