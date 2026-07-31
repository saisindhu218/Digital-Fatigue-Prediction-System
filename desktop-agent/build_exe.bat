@echo off
REM Builds CongiGuardAgent.exe using PyInstaller.
REM IMPORTANT: activate this folder's own venv FIRST, or pyinstaller
REM (and every other dependency) won't be found:
REM     .venv\Scripts\Activate.ps1     (PowerShell)
REM     .venv\Scripts\activate.bat     (cmd.exe)
REM then:  pip install -r requirements.txt
REM then:  build_exe.bat   (or .\build_exe.bat in PowerShell)

where pyinstaller >nul 2>nul
if errorlevel 1 (
    echo.
    echo ERROR: 'pyinstaller' was not found on PATH.
    echo This almost always means the venv isn't activated in THIS terminal.
    echo Run these first, in this exact folder:
    echo     .venv\Scripts\Activate.ps1
    echo     pip install -r requirements.txt
    echo then re-run build_exe.bat
    exit /b 1
)

REM NOTE: kept as a console app on purpose so "login"/"status" work
REM interactively. install_startup.bat launches "run" mode minimized so
REM you won't see a window during normal day-to-day use.
pyinstaller --onefile --name CongiGuardAgent main.py --hidden-import win32timezone

if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller failed - see the output above for the actual reason.
    echo Nothing was built. Do NOT trust a "Build finished" message unless
    echo you see it below this line.
    exit /b 1
)

if not exist "dist\CongiGuardAgent.exe" (
    echo.
    echo ERROR: PyInstaller reported success but dist\CongiGuardAgent.exe
    echo doesn't exist. Something is wrong - do not distribute this build.
    exit /b 1
)

echo.
echo Build finished. Real file at dist\CongiGuardAgent.exe
for %%A in ("dist\CongiGuardAgent.exe") do echo Size: %%~zA bytes (should be several MILLION bytes, not a few KB)
echo.
echo Next steps:
echo   1) dist\CongiGuardAgent.exe pair ^<CODE-from-website^>
echo   2) install_startup.bat   (registers it to run at Windows logon)
