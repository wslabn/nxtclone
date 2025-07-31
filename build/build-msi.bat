@echo off
echo Building SysWatch MSI Installer...

REM Check if WiX is installed
where candle >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: WiX Toolset not found. Please install WiX Toolset v3.11+
    echo Download from: https://wixtoolset.org/releases/
    pause
    exit /b 1
)

REM Create dist directory if it doesn't exist
if not exist "dist" mkdir dist

REM Copy required files to dist
echo Copying files...
copy "..\agents\dist\syswatch-agent-windows.exe" "dist\" >nul 2>&1
copy "..\agents\dist\syswatch-tray.exe" "dist\" >nul 2>&1
copy "dist\nssm.exe" "dist\" >nul 2>&1

if not exist "dist\syswatch-agent-windows.exe" (
    echo Error: syswatch-agent-windows.exe not found in agents\dist\
    echo Please build the agent first using build-windows.py
    pause
    exit /b 1
)

REM Compile WiX source
echo Compiling WiX source...
candle SysWatch.wxs -out dist\SysWatch.wixobj
if %errorlevel% neq 0 (
    echo Error: WiX compilation failed
    pause
    exit /b 1
)

REM Link to create MSI
echo Creating MSI package...
light dist\SysWatch.wixobj -out dist\SysWatch-Agent-Installer.msi -ext WixUIExtension
if %errorlevel% neq 0 (
    echo Error: MSI creation failed
    pause
    exit /b 1
)

REM Cleanup
del dist\SysWatch.wixobj >nul 2>&1

echo.
echo MSI installer created successfully: dist\SysWatch-Agent-Installer.msi
echo.
echo To install silently: msiexec /i SysWatch-Agent-Installer.msi /quiet SERVER_URL="ws://your-server:3000" INSTALL_TRAY=1
echo.
pause