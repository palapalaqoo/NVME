'''
Created on Jan 15, 2019

@author: root
'''

import shutil,os
import re
from shutil import copyfile

# copyType = 0, copy
# copyType = 1, simulate
copyType=1

copyFileName=[]
#copyFileName.append("lib_vct/NVMECom")
#copyFileName.append("Flow/Sanitize")
#copyFileName.append("SMI_Format.py")
copyFileName.append("SMI_SetGetFeatureCmd.py")
copyFileName.append("SMI_FeatureHCTM.py")









copyCnt=0
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
        
        # if define copyFileName, then copy copyFileName only
        # else copy all file
        if len(copyFileName)!=0:
            # ex, mfileName ="lib_vct.NVMECom"
            for mfileName in copyFileName:
                if re.search(mfileName, src_file):     
                    doCopy(src_file, dst_file)
        else:
            doCopy(src_file, dst_file)
               
            

        return 0

def doCopy(src_file, dst_file):
    # copy file
    global copyCnt
    copyCnt=copyCnt+1

    mStr = "{:<80} ->  {:<80}".format(src_file, dst_file)
    print mStr
    if copyType==0:
        shutil.copy2(src_file, dst_file)
    else:    
        pass    



def mCopy(name):
    srcDir="/root/sam/Eclipse/NVME/"

    #dstPath="/root/sam/share/Git/Linux/Linux_regress/Script/" 
    dstPath="/root/sam/Git/test/Linux/Linux_regress/Script/" 
    #dstPath="/root/sam/buf/"
       
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
Name="SMI_Compare"
mCopy(Name)
Name="SMI_CommandsSupportedAndEffectsLog"
mCopy(Name)

Name="SMI_Identify"
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

Name="SMI_StatusCode"
mCopy(Name)



print "copy counter : %s"%copyCnt
print "Done"





