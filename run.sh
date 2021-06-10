#!/bin/bash

export FLASK_APP=main.py
export FLASK_DEBUG=1
export FLASK_RUN_PORT=5000
export FLASK_RUN_HOST=0.0.0.0
export FLASK_ENV=development

echo "Interfaces:"
ifconfig | grep "inet " | awk '{printf " (-) %s\n", $2}'

flask run