'''
Created on Aug 10, 2018

@author: root
'''

from SanitizeStatus import SanitizeStatus_
from DeviceSelfTest import DeviceSelfTest_




   

 
# register class
class GetLog_():
    def __init__(self, obj):        
        self.SanitizeStatus=SanitizeStatus_()  
        self.DeviceSelfTest=DeviceSelfTest_(obj)
    
    