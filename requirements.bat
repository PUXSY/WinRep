@echo off
echo Checking if Python is installed...

where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH.
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python is installed. Checking version:
python --version

echo Checking if pip is installed and working...
python -m pip --version >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Pip is not working properly.
    echo Attempting to install/repair pip...
    python -m ensurepip --upgrade
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to install pip. Please install pip manually.
        pause
        exit /b 1
    )
    echo Pip has been installed/repaired.
)

echo Pip is working properly. Checking version:
python -m pip --version

echo Running requirements installation script...
python "%~dp0\requirements.py"
if %ERRORLEVEL% EQU 0 (
    echo Installation completed successfully.
) else (
    echo Installation failed with error code %ERRORLEVEL%.
)
pause