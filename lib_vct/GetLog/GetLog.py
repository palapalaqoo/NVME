'''
Created on Aug 10, 2018

@author: root
'''

from SanitizeStatus import SanitizeStatus_
from DeviceSelfTest import DeviceSelfTest_
from SMART import SMART_



   

 
# register class
class GetLog_():
    def __init__(self, obj):        
        self.SanitizeStatus=SanitizeStatus_(obj)  
        self.DeviceSelfTest=DeviceSelfTest_(obj)
        self.SMART=SMART_(obj)
    