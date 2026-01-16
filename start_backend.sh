#!/bin/bash
# OpenAI API key should be set as an environment variable
# export OPENAI_API_KEY=your_key_here
# Or load from .env file if using python-dotenv
export PYTHONPATH=$PYTHONPATH:.

# Install python dependencies if needed
pip3 install -r backend/requirements.txt

# Run server
python3 backend/app/main.py
