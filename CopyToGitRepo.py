'''
Created on Jan 15, 2019

@author: root
'''

import shutil,os
import re
from shutil import copyfile


def copyDir(root_src_dir, root_dst_dir):
    for src_dir, dirs, files in os.walk(root_src_dir):
        dst_dir = src_dir.replace(root_src_dir, root_dst_dir, 1)
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        for file_ in files:
            src_file = os.path.join(src_dir, file_)
   
            dst_file = os.path.join(dst_dir, file_)
            copyDiffFile(src_file, dst_file)

def copyDiffFile(src_file, dst_file):
   
        # no need to copy the files with extension name as belowing
        RE=".pyc"
        if re.search(RE, src_file):                  
            return 0
        # in case of the src and dst are the same file
        if os.path.exists(dst_file):
            if os.path.samefile(src_file, dst_file):
                return 0
        # copy file
        shutil.copy2(src_file, dst_file)    
        return 0

def mCopy(name):
    srcDir="/root/sam/eclipse/pytest/"

    #dstPath="/root/sam/share/Git/Linux/Linux_regress/Script/" 
    #dstPath="/root/sam/git/Git/Linux/Linux_regress/Script/" 
    dstPath="/root/sam/buf/"
       
    # copy lib_vct
    dstDir=dstPath+name+"/"
    copyDir(srcDir+"lib_vct", dstDir+"lib_vct")
    # copy main py
    fileName=name+".py"
    copyDiffFile(srcDir+fileName, dstDir+fileName)
    
    if name=="SMI_TelemetryExample":
        # copy other py
        fileName="SMI_AsynchronousEventRequest"+".py"
        copyDiffFile(srcDir+fileName, dstDir+fileName)    
    

'''
Name="SMI_DSM"
mCopy(Name)
Name="SMI_FeatureHCTM"
mCopy(Name)
Name="SMI_FeatureNumberofQueues"
mCopy(Name)
Name="SMI_FeatureTimestamp"
mCopy(Name)
Name="SMI_Format"
mCopy(Name)
Name="SMI_NVMEReset"
mCopy(Name)
Name="SMI_Read"
mCopy(Name)
Name="SMI_Sanitize"
mCopy(Name)
Name="SMI_SetGetFeatureCmd"
mCopy(Name)
Name="SMI_SmartHealthLog"
mCopy(Name)
Name="SMI_Telemetry"
mCopy(Name)
Name="SMI_TelemetryExample"
mCopy(Name)
Name="SMI_Write"
mCopy(Name)
'''

Name="SMI_Identify"
mCopy(Name)


print "Done"






