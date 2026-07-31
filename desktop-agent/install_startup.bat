@echo off
REM Registers CongiGuardAgent to start automatically when you log in to
REM Windows, running in your interactive session.
REM
REM IMPORTANT: this deliberately uses a Scheduled Task set to "run at
REM logon", NOT a Windows Service. A real Windows Service runs in
REM Session 0, isolated from your desktop, and CANNOT see global
REM keyboard/mouse input or the foreground window - so the agent would
REM silently collect nothing. Run-at-logon keeps it in your session
REM where the hooks actually work, while still requiring no manual
REM double-click after each reboot.

set EXE_PATH=%~dp0dist\CongiGuardAgent.exe
set TASK_NAME=CongiGuardAgent

if not exist "%EXE_PATH%" (
    echo ERROR: %EXE_PATH% not found. Run build_exe.bat first.
    exit /b 1
)

schtasks /Create ^
    /TN "%TASK_NAME%" ^
    /TR "\"%EXE_PATH%\" run" ^
    /SC ONLOGON ^
    /RL LIMITED ^
    /F

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Installed. CongiGuardAgent will start automatically next time you log in.
    echo To start it right now without rebooting, run:
    echo     schtasks /Run /TN "%TASK_NAME%"
) else (
    echo Failed to create scheduled task. Try running this .bat as Administrator.
)
