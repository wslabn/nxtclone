import win32serviceutil
import win32service
import win32event
import servicemanager
import sys
import os
import subprocess
import time

class SysWatchService(win32serviceutil.ServiceFramework):
    _svc_name_ = "SysWatch Agent"
    _svc_display_name_ = "SysWatch Agent"
    _svc_description_ = "Remote monitoring and management agent"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.process = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        if self.process:
            self.process.terminate()
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                            servicemanager.PYS_SERVICE_STARTED,
                            (self._svc_name_, ''))
        
        # Get server URL from command line args
        server_url = "ws://localhost:3000"
        if len(sys.argv) > 1:
            server_url = sys.argv[1]
        
        # Get the directory where this service is running
        service_dir = os.path.dirname(os.path.abspath(__file__))
        agent_path = os.path.join(service_dir, "syswatch-agent-windows.exe")
        
        # Start the agent process
        try:
            self.process = subprocess.Popen([
                agent_path, server_url
            ], cwd=service_dir)
            
            # Wait for stop signal or process to end
            while True:
                if win32event.WaitForSingleObject(self.hWaitStop, 1000) == win32event.WAIT_OBJECT_0:
                    break
                if self.process.poll() is not None:
                    # Process ended, restart it
                    time.sleep(5)
                    self.process = subprocess.Popen([
                        agent_path, server_url
                    ], cwd=service_dir)
                    
        except Exception as e:
            servicemanager.LogErrorMsg(f"Service error: {str(e)}")

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(SysWatchService)