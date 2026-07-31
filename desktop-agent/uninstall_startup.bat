@echo off
schtasks /Delete /TN "CongiGuardAgent" /F
echo Removed CongiGuardAgent from Windows startup.
