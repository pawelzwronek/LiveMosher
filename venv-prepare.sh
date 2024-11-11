#!/bin/bash

if uname -a | grep -q Darwin; then
    OS="mac"
elif uname -a | grep -q MINGW || uname -a | grep -q MSYS; then
    OS="win"
elif uname -a | grep -q Linux; then
    OS="linux"
else
    echo "Unknown OS: $(uname -a)"
    echo "Setting OS to linux."
    OS="linux"
fi

echo "Setting up virtual environment for $OS"

python3 -m venv venv-$OS
source venv-$OS/bin/activate
pip install -r requirements-$OS.txt
