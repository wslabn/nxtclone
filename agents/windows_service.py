import win32serviceutil
import win32service
import win32event
import servicemanager
import sys
import os
import asyncio
from windows_agent import WindowsAgent

class NxtCloneService(win32serviceutil.ServiceFramework):
    _svc_name_ = "NxtClone Agent"
    _svc_display_name_ = "NxtClone Agent"
    _svc_description_ = "Remote monitoring and management agent"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.agent = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                            servicemanager.PYS_SERVICE_STARTED,
                            (self._svc_name_, ''))
        
        # Get server URL from command line args
        server_url = "ws://localhost:3000"
        if len(sys.argv) > 1:
            server_url = sys.argv[1]
        
        try:
            self.agent = WindowsAgent(server_url)
            asyncio.run(self.agent.connect())
        except Exception as e:
            servicemanager.LogErrorMsg(f"Service error: {e}")

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(NxtCloneService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(NxtCloneService)