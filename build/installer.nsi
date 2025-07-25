!define APPNAME "SysWatch Agent"
!define COMPANYNAME "SysWatch"
!define DESCRIPTION "Remote monitoring and management agent"
!define VERSIONMAJOR 1
!define VERSIONMINOR 1
!define VERSIONBUILD 8

!define HELPURL "https://github.com/your-username/syswatch"
!define UPDATEURL "https://github.com/your-username/syswatch/releases"
!define ABOUTURL "https://github.com/your-username/syswatch"

!define INSTALLSIZE 10000

RequestExecutionLevel admin
InstallDir "$PROGRAMFILES\${COMPANYNAME}\${APPNAME}"
Name "${APPNAME}"
Icon "icon.ico"
outFile "syswatch-agent-installer.exe"

!include LogicLib.nsh
!include nsDialogs.nsh
!include WinMessages.nsh

Var Dialog
Var ServerUrlLabel
Var ServerUrlText
Var ServerUrl

Page custom ServerUrlPage ServerUrlPageLeave
Page instfiles

Function ServerUrlPage
    nsDialogs::Create 1018
    Pop $Dialog

    ${If} $Dialog == error
        Abort
    ${EndIf}

    ${NSD_CreateLabel} 0 0 100% 12u "Enter the server URL to connect to:"
    Pop $ServerUrlLabel

    ${NSD_CreateLabel} 0 20u 100% 12u "Examples: ws://192.168.1.100:3000 or ws://server.domain.com:3000"
    Pop $0

    ${NSD_CreateText} 0 40u 100% 12u "ws://localhost:3000"
    Pop $ServerUrlText

    nsDialogs::Show
FunctionEnd

Function ServerUrlPageLeave
    ${NSD_GetText} $ServerUrlText $ServerUrl
    
    ${If} $ServerUrl == ""
        MessageBox MB_OK "Please enter a server URL"
        Abort
    ${EndIf}
    
    StrCpy $0 $ServerUrl 5
    ${If} $0 != "ws://"
        MessageBox MB_OK "Server URL must start with 'ws://'"
        Abort
    ${EndIf}
FunctionEnd

Section "install"
    SetOutPath $INSTDIR
    
    # Copy the agent executable
    File "dist\syswatch-agent.exe"
    
    # Verify file was copied
    IfFileExists "$INSTDIR\syswatch-agent.exe" +2 0
    MessageBox MB_OK "Error: Agent executable not found after copy!"
    
    # Stop existing service if running
    ExecWait 'sc stop "${APPNAME}"'
    ExecWait 'sc delete "${APPNAME}"'
    
    # Create the service with the provided server URL
    ExecWait 'sc create "${APPNAME}" binPath= "\"$INSTDIR\syswatch-agent.exe\" $ServerUrl" start= auto'
    
    # Don't start service automatically - let user start it manually
    # ExecWait 'sc start "${APPNAME}"'
    
    # Create uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"
    
    # Registry entries for Add/Remove Programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "DisplayName" "${APPNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "QuietUninstallString" "$\"$INSTDIR\uninstall.exe$\" /S"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "InstallLocation" "$\"$INSTDIR$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "DisplayIcon" "$\"$INSTDIR\nxtclone-agent.exe$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "Publisher" "${COMPANYNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "HelpLink" "${HELPURL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "URLUpdateInfo" "${UPDATEURL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "URLInfoAbout" "${ABOUTURL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "DisplayVersion" "${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "VersionMajor" ${VERSIONMAJOR}
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "VersionMinor" ${VERSIONMINOR}
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "NoRepair" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "EstimatedSize" ${INSTALLSIZE}
    
    MessageBox MB_OK "Installation complete! The SysWatch Agent service has been installed."
SectionEnd

Section "uninstall"
    # Stop and remove service
    ExecWait 'sc stop "${APPNAME}"'
    ExecWait 'sc delete "${APPNAME}"'
    
    # Remove files
    Delete "$INSTDIR\syswatch-agent.exe"
    Delete "$INSTDIR\uninstall.exe"
    RMDir "$INSTDIR"
    
    # Remove registry entries
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}"
SectionEnd