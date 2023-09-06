#!/bin/bash

# Check if the virtual environment already exists
if [ ! -d "sherlock-venv" ]; then
    echo "Creating a virtual environment..."
    python3 -m venv sherlock-venv

    # Activate the virtual environment
    source sherlock-venv/bin/activate

    echo "Installing the required packages..."
    pip install -r requirements.txt
else
    # Activate the virtual environment
    source sherlock-venv/bin/activate
fi

# Run the bot
python3 watson.py