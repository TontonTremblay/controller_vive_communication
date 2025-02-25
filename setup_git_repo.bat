@echo off
echo Setting up Git repository for HTC Vive Controller Tracker...

REM Initialize Git repository
git init

REM Add all files
git add .

REM Make initial commit
git commit -m "Initial commit: HTC Vive Controller Tracker"

REM Add the remote repository
git remote add origin git@github.com:TontonTremblay/controller_vive_communication.git

echo.
echo Repository initialized successfully!
echo.
echo To push to GitHub, run:
echo git push -u origin main
echo.
echo Note: If your default branch is 'master' instead of 'main', use:
echo git push -u origin master
echo.
pause 