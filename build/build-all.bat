@echo off
echo Building NxtClone Agent Executables...

REM Install build dependencies
pip install -r requirements-build.txt

REM Build Windows executable
echo Building Windows agent...
python build-windows.py

REM Build installer (requires NSIS)
if exist "C:\Program Files (x86)\NSIS\makensis.exe" (
    echo Creating Windows installer...
    "C:\Program Files (x86)\NSIS\makensis.exe" installer.nsi
) else (
    echo NSIS not found - skipping installer creation
    echo Download NSIS from https://nsis.sourceforge.io/
)

echo Build complete!
echo Windows executable: dist\nxtclone-agent.exe
echo Windows installer: nxtclone-agent-installer.exe