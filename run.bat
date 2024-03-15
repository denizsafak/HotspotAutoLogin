@echo off
setlocal enabledelayedexpansion
set NAME=HotspotAutoLogin
set RUN=HotspotAutoLogin.pyw
set "requirementsFile=requirements.txt"
set VENV_PATH=.venv
set ACTIVATE_PATH=%VENV_PATH%\Scripts\activate

:: Check if Python is installed
pip --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed.
    set /p "userinp=Do you want to install Python (y/n)? "
    if /i "!userinp!"=="y" (
        echo Opening download link...
        start https://www.python.org/downloads/
        exit /b
    ) else (
        echo Please install Python and try again.
        pause
        exit /b
    )
)

:: Check if virtual environment exists
IF NOT EXIST %ACTIVATE_PATH% (
    echo Creating virtual environment...
    python -m venv %VENV_PATH%
) ELSE (
    goto check_python
)

:: Check if Python exists at the path stored in the virtual environment
:check_python
%VENV_PATH%\Scripts\python.exe --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found at the path stored in the virtual environment.
    echo Recreating virtual environment...
    rmdir /s /q %VENV_PATH%
    python -m venv %VENV_PATH%
)

echo Activating virtual environment...
call %ACTIVATE_PATH%s
if errorlevel 1 (
    echo Failed to activate virtual environment.
	echo Recreating virtual environment...
    rmdir /s /q %VENV_PATH%
    python -m venv %VENV_PATH%
	echo Activating virtual environment...
	call %ACTIVATE_PATH%
)

echo Checking the requirements...
:: Get the list of installed packages using pip freeze
for /f "tokens=1,* delims==" %%i in ('pip freeze') do (
    set installed[%%i]=%%j
)

:: Compare with the requirements from the requirements.txt file
for /f "tokens=1,* delims==" %%i in (%requirementsFile%) do (
    if not "!installed[%%i]!"=="%%j" (
        echo Installing package: %%i==%%j
        pip install %%i==%%j --upgrade --quiet 
    )
)

echo Starting %NAME%...
start /B "" "%VENV_PATH%/Scripts/pythonw.exe" %RUN%