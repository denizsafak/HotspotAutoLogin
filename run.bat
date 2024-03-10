@echo off
set NAME=HotspotAutoLogin
set RUN=HotspotAutoLogin.pyw
set "requirementsFile=requirements.txt"
set VENV_PATH=.venv
set ACTIVATE_PATH=%VENV_PATH%\Scripts\activate

IF NOT EXIST %ACTIVATE_PATH% (
    echo Creating virtual environment...
    virtualenv %VENV_PATH%
)

echo Activating virtual environment...
call %ACTIVATE_PATH%

echo Checking the requirements...
for /f "delims=" %%i in (%requirementsFile%) do (
    pip freeze | findstr /c:%%i > nul
    if errorlevel 1 (
        echo Installing package: %%i
        pip install %%i --upgrade --quiet
    )
)

echo Starting %NAME%...
start /B "" "%VENV_PATH%/Scripts/pythonw.exe" %RUN%
