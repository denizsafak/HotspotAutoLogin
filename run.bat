@echo off
IF NOT EXIST .venv\Scripts\activate (
    echo Creating virtual environment...
    virtualenv .venv
    echo Virtual environment created.
)

echo Activating virtual environment...
call .venv\Scripts\activate

echo Installing requirements...
pip install -r requirements.txt

echo Starting HotspotAutoLogin...
start /B "" ".venv/Scripts/pythonw.exe" HotspotAutoLogin.pyw