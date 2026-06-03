@echo off
:: SWORDPHISH - Windows Installation Script:: Run as Administrator

setlocal enabledelayedexpansion

set SWORDPHISH_DIR=%USERPROFILE%\swordphish
set PYTHON_VERSION=3.11

echo ================================================
echo    SWORDPHISH - Windows Installation Script
echo ================================================
echo.

:: Check for Administrator privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Please run as Administrator!
    pause
    exit /b 1
)

:: Check Python installation
echo [INFO] Checking Python...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [WARN] Python not found. Installing Python %PYTHON_VERSION%...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe' -OutFile '%TEMP%\python-installer.exe'"
    start /wait %TEMP%\python-installer.exe /quiet InstallAllUsers=1 PrependPath=1
    del %TEMP%\python-installer.exe
)

:: Check pip
echo [INFO] Checking pip...
python -m pip --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [INFO] Installing pip...
    python -m ensurepip --upgrade
)

:: Create directory
echo [INFO] Creating installation directory...
mkdir "%SWORDPHISH_DIR%" 2>nul
mkdir "%SWORDPHISH_DIR%\.swordphish" 2>nul
mkdir "%SWORDPHISH_DIR%\reports" 2>nul
mkdir "%SWORDPHISH_DIR%\logs" 2>nul

:: Copy files
echo [INFO] Copying files...
copy "%~dp0swordphish.py" "%SWORDPHISH_DIR%\" 2>nul
copy "%~dp0requirements.txt" "%SWORDPHISH_DIR%\" 2>nul
copy "%~dp0requirements_minimal.txt" "%SWORDPHISH_DIR%\" 2>nul
copy "%~dp0requirements_check.py" "%SWORDPHISH_DIR%\" 2>nul

:: Install Python packages
echo [INFO] Installing Python packages...
python -m pip install --upgrade pip
python -m pip install -r "%SWORDPHISH_DIR%\requirements.txt"

:: Create virtual environment (optional)
echo [INFO] Creating virtual environment...
python -m venv "%SWORDPHISH_DIR%\venv"
call "%SWORDPHISH_DIR%\venv\Scripts\activate.bat"
python -m pip install -r "%SWORDPHISH_DIR%\requirements.txt"
call deactivate

:: Create launcher batch file
echo [INFO] Creating launcher...
(
echo @echo off
echo call "%SWORDPHISH_DIR%\venv\Scripts\activate.bat"
echo python "%SWORDPHISH_DIR%\swordphish.py" %%*
) > "%SWORDPHISH_DIR%\swordphish.bat"

:: Create config file
(
echo {
echo     "version": "1.0.0",
echo     "install_date": "%date% %time%",
echo     "database": {
echo         "type": "sqlite",
echo         "path": "%SWORDPHISH_DIR%\\.swordphish\\swordphish.db"
echo     }
echo }
) > "%SWORDPHISH_DIR%\config.json"

:: Create shortcut on Desktop
echo [INFO] Creating desktop shortcut...
powershell -Command "$WS = New-Object -ComObject WScript.Shell; $SC = $WS.CreateShortcut('%USERPROFILE%\Desktop\SWORDPHISH.lnk'); $SC.TargetPath = '%SWORDPHISH_DIR%\swordphish.bat'; $SC.Save()"

:: Add to PATH
echo [INFO] Adding to PATH...
setx PATH "%PATH%;%SWORDPHISH_DIR%" /M

:: Verification
echo [INFO] Verifying installation...
python "%SWORDPHISH_DIR%\requirements_check.py"

echo.
echo ================================================
echo    SWORDPHISH Installation Complete!
echo ================================================
echo.
echo Installation Directory: %SWORDPHISH_DIR%
echo.
echo Quick Start:
echo   Run: %SWORDPHISH_DIR%\swordphish.bat
echo   Or use the desktop shortcut
echo.
pause