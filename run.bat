@echo off

REM Check if the virtual environment already exists
if not exist "sherlock-venv\" (
    echo Creating a virtual environment...
    python -m venv sherlock-venv

    REM Activate the virtual environment
    call sherlock-venv\Scripts\activate

    echo Installing the required packages...
    pip install -r requirements.txt
) else (
    REM Activate the virtual environment
    call sherlock-venv\Scripts\activate
)

REM Run the bot
python watson.py
