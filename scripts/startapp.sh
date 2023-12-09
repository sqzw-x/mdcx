#!/bin/bash

if [[ ! -e "/app/config.ini" ]]; then
    cp -r "/app/config.ini.default" "/app/config.ini"
fi

python3 /app/main.py