# ChangeLog
This is a change log for SMI_SmartCheck.
All changes to this project will be documented in this file.

## [Unreleased]

## [20200731A]
### Added
- The first release (Using the SMI_TestTools_Lite 20200731A).
    - ##### Feature:
        Monitoring customization SMART periodically, and checks if SMART attributes are incompatible with limit. Also parsed SMART log will output as '.json' and '.txt' file.
    - ##### Usage 1 (as Python library):
            The `SMI_SmartCheck` class
                - SMI_SmartCheck(disk_id, smart_config_file, total_cycle, smart_monitor_period, log_file)  [constructor]
                    - disk_id:              Device's path / SN.
                    - smart_config_file:    (Ref. [jira 228])
                    - total_cycle:          Test cycle, 0 means infinite.
                    - smart_monitor_period: Period of monitoring SMART data (in seconds).
                    - log_file:             Location of SMART log file to save.
                - SMI_SmartCheck.loadFromConfig():      Checks and parses parameters from constructor (checks .ini file etc.).
                - SMI_SmartCheck.startMonitoring():     Starts monitoring SMART periodically.
                - SMI_SmartCheck.stopMonitoring():      Stops monitoring SMART.
                - SMI_SmartCheck.isMonitoring():        Checks if still monitoring SMART periodically.
                - SMI_SmartCheck.getSmart():            Gets and checks SMART once.
                
            - Usage Examples:
                from SMI_SmartCheck.SMI_SmartCheck import SMI_SmartCheck
                smart = SMI_SmartCheck("SMART.ini", "/dev/nvme0", total_cycle=0, smart_monitor_period=2, log_file='./SmartLog/exampleLog')
	            if smart.loadFromConfig(): exit(1)
	            smart.startMonitoring()

            	while smart.isMonitoring(): pass # Do something...
            	
    - ##### Usage 2 (as individual script):
            command device [args=<flag>]
                device:     /dev/nvmex
                
            - Args:
                -h | --help:                    Showing the help file.
                -c | --total_cycle:         	Set test cycle, 0 means infinite. Default is 0.
                -l | --log_file: 	        	SMART log filename. Keep empty if you do not want to keep SMART data log.
                -p | --smart_monitor_period: 	Set period of monitoring SMART data (in seconds). Default is 5.
                -s | --smart_config_file:   	Assign SMART configuration filename. Keep empty if you do not want to monitor SMART data.
                
            - Usage Examples:
                SMI_SmartCheck.py /dev/nvme0 --smart_config_file SMART.ini --total_cycle 0 --smart_monitor_period 1 --log_file ./SmartLog/exampleLog
                SMI_SmartCheck.py /dev/nvme0 -s SMART.ini -c 0 -p 1 -l ./SmartLog/exampleLog
                
    - ##### SMART Limit Examples (smart_config_file)
            * Format: [value_type[bitend:bitstart]][comparator][value] && [][][] && ...
            *   [value_type]: diff -> The dfference between the previous one and the current one
            *                 val  -> The current value
            *   [comparator]: ==, !=, >=, >, <=, <
            * Examples:
            *   1. Current value minus previous value should be lesser or equal to 1
            *      diff<=1
            *   2. Current value should equal to 0xC0
            *      val==0xC0
            *   3. Current value minus previous value should be in range 10~100
            *      diff>=10 && diff<=100
            *   4. Bits examination. For example, NVMe SMART byte 0 logs "Critical Warning" data, if you expect all flags keep non-raised except bit 1 temperature, you could simply assign limit as below:
            *      val[0]==0 && val[7:2]==0




[Jira 228]: <https://jira.siliconmotion.com.tw:8443/browse/VCTDEPT-228>
