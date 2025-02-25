@echo off
echo Pushing HTC Vive Controller Tracker to GitHub...

REM Check if Git is installed
where git >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Git is not installed or not in your PATH.
    echo Please install Git from https://git-scm.com/downloads
    pause
    exit /b 1
)

REM Check if repository is already initialized
if not exist .git (
    echo Initializing Git repository...
    git init
    
    REM Configure Git if needed
    echo Please enter your Git username:
    set /p GIT_USERNAME=
    git config user.name "%GIT_USERNAME%"
    
    echo Please enter your Git email:
    set /p GIT_EMAIL=
    git config user.email "%GIT_EMAIL%"
)

REM Add all files
echo Adding files to repository...
git add .

REM Commit changes
echo Committing changes...
git commit -m "Initial commit: HTC Vive Controller Tracker"

REM Check if remote already exists
git remote -v | findstr "origin" >nul
if %ERRORLEVEL% NEQ 0 (
    echo Adding remote repository...
    git remote add origin git@github.com:TontonTremblay/controller_vive_communication.git
)

REM Determine default branch (main or master)
echo Checking default branch...
git branch | findstr "main" >nul
if %ERRORLEVEL% EQU 0 (
    set BRANCH=main
) else (
    set BRANCH=master
)

REM Push to GitHub
echo Pushing to GitHub (branch: %BRANCH%)...
git push -u origin %BRANCH%

echo.
if %ERRORLEVEL% EQU 0 (
    echo Successfully pushed to GitHub!
) else (
    echo Failed to push to GitHub.
    echo.
    echo Possible issues:
    echo 1. SSH key not set up for GitHub
    echo 2. Repository already exists and has different history
    echo 3. Network connectivity issues
    echo.
    echo For SSH key setup, visit: https://docs.github.com/en/authentication/connecting-to-github-with-ssh
)

echo.
pause 