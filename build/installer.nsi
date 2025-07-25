; NxtClone Agent Windows Installer
!define APPNAME "NxtClone Agent"
!define COMPANYNAME "NxtClone"
!define DESCRIPTION "Remote monitoring and management agent"
!define VERSIONMAJOR 1
!define VERSIONMINOR 0
!define VERSIONBUILD 0

RequestExecutionLevel admin
InstallDir "$PROGRAMFILES64\${COMPANYNAME}\${APPNAME}"
Name "${APPNAME}"
OutFile "nxtclone-agent-installer.exe"

!include "MUI2.nsh"
!include "nsDialogs.nsh"
!include "LogicLib.nsh"

Page directory
Page custom ServerURLPage
Page instfiles

Var ServerURL

Function ServerURLPage
    !insertmacro MUI_HEADER_TEXT "Server Configuration" "Enter the RMM server URL"
    
    nsDialogs::Create 1018
    Pop $0
    
    ${NSD_CreateLabel} 0 0 100% 12u "Enter the RMM server URL (e.g., ws://192.168.1.100:3000):"
    Pop $0
    
    ${NSD_CreateText} 0 20u 100% 12u "ws://localhost:3000"
    Pop $1
    
    nsDialogs::Show
    
    ${NSD_GetText} $1 $ServerURL
FunctionEnd

Section "install"
    SetOutPath $INSTDIR
    File "dist\nxtclone-agent.exe"
    
    ; Create version file
    FileOpen $0 "$INSTDIR\version.txt" w
    FileWrite $0 "1.0.0"
    FileClose $0
    
    ; Create service with server URL
    ExecWait 'sc create "NxtClone Agent" binPath= "$INSTDIR\nxtclone-agent.exe $ServerURL" start= auto'
    ExecWait 'sc start "NxtClone Agent"'
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"
    
    ; Registry entries
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "DisplayName" "${APPNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "UninstallString" "$INSTDIR\uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "Publisher" "${COMPANYNAME}"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "VersionMajor" ${VERSIONMAJOR}
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "VersionMinor" ${VERSIONMINOR}
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "NoRepair" 1
SectionEnd

Section "uninstall"
    ExecWait 'sc stop "NxtClone Agent"'
    ExecWait 'sc delete "NxtClone Agent"'
    Delete "$INSTDIR\nxtclone-agent.exe"
    Delete "$INSTDIR\version.txt"
    Delete "$INSTDIR\uninstall.exe"
    RMDir "$INSTDIR"
    
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}"
SectionEnd