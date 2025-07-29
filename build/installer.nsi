!define APPNAME "SysWatch Agent"
!define COMPANYNAME "SysWatch"
!define DESCRIPTION "Remote monitoring and management agent"
!define VERSIONMAJOR 1
!define VERSIONMINOR 1
!define VERSIONBUILD 37

!define HELPURL "https://github.com/your-username/syswatch"
!define UPDATEURL "https://github.com/your-username/syswatch/releases"
!define ABOUTURL "https://github.com/your-username/syswatch"

!define INSTALLSIZE 10000

RequestExecutionLevel admin
InstallDir "$PROGRAMFILES64\SysWatch"
Name "${APPNAME}"
Icon "icon.ico"
outFile "dist\syswatch-agent-installer.exe"

!include LogicLib.nsh
!include nsDialogs.nsh
!include WinMessages.nsh

Var Dialog
Var ServerUrlLabel
Var ServerUrlText
Var ServerUrl
Var TrayCheckbox
Var InstallTray

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
    
    ${NSD_CreateCheckbox} 0 60u 100% 12u "Install system tray control application (optional)"
    Pop $TrayCheckbox
    ${NSD_Check} $TrayCheckbox

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
    
    ${NSD_GetState} $TrayCheckbox $InstallTray
FunctionEnd

Section "install"
    SetOutPath $INSTDIR
    
    # Create temp directory for updates
    CreateDirectory "C:\temp"
    
    # Copy the agent executable
    File "dist\syswatch-agent-windows.exe"
    
    # Copy the tray application if user selected it
    ${If} $InstallTray == ${BST_CHECKED}
        File /nonfatal "dist\syswatch-tray.exe"
        # Create desktop shortcut for tray app
        CreateShortCut "$DESKTOP\SysWatch Tray.lnk" "$INSTDIR\syswatch-tray.exe"
        
        # Create tray config file with server URL
        FileOpen $4 "$INSTDIR\tray_config.json" w
        FileWrite $4 '{"server_url": "'
        FileWrite $4 $ServerUrl
        FileWrite $4 '"}'
        FileClose $4
        
        # Add to Windows startup (auto-start on boot)
        WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "SysWatch Tray" '"$INSTDIR\syswatch-tray.exe"'
        
        # Start tray app immediately after installation
        Exec '"$INSTDIR\syswatch-tray.exe"'
    ${EndIf}
    
    # Verify file was copied
    IfFileExists "$INSTDIR\syswatch-agent-windows.exe" +2 0
    MessageBox MB_OK "Error: Agent executable not found after copy!"
    
    # Check if service exists and stop it if running
    DetailPrint "Checking for existing service..."
    ExecWait 'sc query "${APPNAME}"' $8
    ${If} $8 == 0
        DetailPrint "Existing service found, stopping..."
        ExecWait 'sc stop "${APPNAME}"' $9
        Sleep 3000
        DetailPrint "Removing existing service..."
        ExecWait 'sc delete "${APPNAME}"' $9
        Sleep 2000
    ${Else}
        DetailPrint "No existing service found"
    ${EndIf}
    

    
    # Copy NSSM (include nssm.exe in build/dist/)
    File /nonfatal "dist\nssm.exe"
    
    # Install PSWindowsUpdate module for Windows Updates feature
    DetailPrint "Installing PSWindowsUpdate module..."
    ExecWait 'powershell -Command "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine -Force; Install-Module PSWindowsUpdate -Force -Scope AllUsers"' $3
    
    # Install service using NSSM
    ExecWait '"$INSTDIR\nssm.exe" install "${APPNAME}" "$INSTDIR\syswatch-agent-windows.exe" $ServerUrl' $0
    ExecWait '"$INSTDIR\nssm.exe" set "${APPNAME}" Start SERVICE_AUTO_START' $1
    ExecWait '"$INSTDIR\nssm.exe" start "${APPNAME}"' $2
    
    # Check if service creation failed
    ${If} $0 != 0
        MessageBox MB_OK "Warning: Service creation failed. You may need to start the service manually."
    ${EndIf}
    
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
    
    # Show final message
    ${If} $3 == 0
        StrCpy $4 "PSWindowsUpdate module installed successfully."
    ${Else}
        StrCpy $4 "PSWindowsUpdate module installation failed - Windows Updates feature may not work."
    ${EndIf}
    
    ${If} $0 == 0
        ${If} $2 == 0
            StrCpy $2 "Service installed and started successfully."
        ${Else}
            StrCpy $2 "Service installed but failed to start - check Event Viewer."
        ${EndIf}
    ${Else}
        StrCpy $2 "Service installation failed."
    ${EndIf}
    
    ${If} $InstallTray == ${BST_CHECKED}
        MessageBox MB_OK "Installation complete!$\n$\nSysWatch Agent: $2$\nPSWindowsUpdate: $4$\nTray app: Desktop shortcut created$\nServer: $ServerUrl"
    ${Else}
        MessageBox MB_OK "Installation complete!$\n$\nSysWatch Agent: $2$\nPSWindowsUpdate: $4$\nServer: $ServerUrl"
    ${EndIf}
SectionEnd

Section "uninstall"
    # Check if service exists before trying to stop/remove it
    ExecWait 'sc query "${APPNAME}"' $8
    ${If} $8 == 0
        DetailPrint "Service found, stopping and removing..."
        ExecWait '"$INSTDIR\nssm.exe" stop "${APPNAME}"'
        Sleep 3000
        ExecWait '"$INSTDIR\nssm.exe" remove "${APPNAME}" confirm'
    ${Else}
        DetailPrint "Service not found, skipping service removal"
    ${EndIf}
    
    # Remove files
    Delete "$INSTDIR\syswatch-agent-windows.exe"
    Delete "$INSTDIR\syswatch-tray.exe"
    Delete "$INSTDIR\tray_config.json"
    Delete "$INSTDIR\nssm.exe"
    Delete "$INSTDIR\uninstall.exe"
    Delete "$DESKTOP\SysWatch Tray.lnk"
    RMDir "$INSTDIR"
    
    # Remove registry entries
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}"
    DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "SysWatch Tray"
SectionEnd