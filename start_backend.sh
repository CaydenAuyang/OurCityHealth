#!/bin/bash
export OPENAI_API_KEY=${OPENAI_API_KEY:-"sk-placeholder"}
export PYTHONPATH=$PYTHONPATH:.

# Install python dependencies if needed
pip3 install -r backend/requirements.txt

# Run server
python3 backend/app/main.py
