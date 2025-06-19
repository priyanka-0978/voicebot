#!/usr/bin/env bash

# Step 1: Install system dependency for PyAudio
apt-get update && apt-get install -y portaudio19-dev

# Step 2: Install Python dependencies
pip install -r requirements.txt
