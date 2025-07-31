@echo off
echo SysWatch Complete Cleanup Script
echo ================================
echo This will remove ALL versions of SysWatch from this computer.
echo.
pause

echo Stopping services and processes...
sc stop "SysWatch Agent" >nul 2>&1
timeout /t 3 /nobreak >nul

echo Killing any running processes...
taskkill /f /im syswatch-agent-windows.exe >nul 2>&1
taskkill /f /im syswatch-tray.exe >nul 2>&1
taskkill /f /im nssm.exe >nul 2>&1

echo Removing service...
sc delete "SysWatch Agent" >nul 2>&1

echo Removing installation directories...
if exist "C:\Program Files\SysWatch" (
    echo - Removing C:\Program Files\SysWatch
    rmdir /s /q "C:\Program Files\SysWatch"
)

if exist "C:\Program Files (x86)\SysWatch" (
    echo - Removing C:\Program Files (x86)\SysWatch
    rmdir /s /q "C:\Program Files (x86)\SysWatch"
)

if exist "%LOCALAPPDATA%\SysWatch" (
    echo - Removing %LOCALAPPDATA%\SysWatch
    rmdir /s /q "%LOCALAPPDATA%\SysWatch"
)

if exist "%PROGRAMDATA%\SysWatch" (
    echo - Removing %PROGRAMDATA%\SysWatch
    rmdir /s /q "%PROGRAMDATA%\SysWatch"
)

echo Removing registry entries...
reg delete "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\SysWatch SysWatch Agent" /f >nul 2>&1
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\SysWatch SysWatch Agent" /f >nul 2>&1
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "SysWatch Tray" /f >nul 2>&1

echo Removing shortcuts...
if exist "%DESKTOP%\SysWatch Tray.lnk" (
    echo - Removing desktop shortcut
    del "%DESKTOP%\SysWatch Tray.lnk"
)

echo Removing configuration files...
if exist "%APPDATA%\SysWatch" (
    echo - Removing %APPDATA%\SysWatch
    rmdir /s /q "%APPDATA%\SysWatch"
)

echo.
echo ================================
echo Cleanup completed successfully!
echo All SysWatch components have been removed.
echo You can now install the new MSI version.
echo ================================
pause