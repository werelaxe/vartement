#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Input .vta file is required as first cmd argument."
else
    python3 translate.py $1>out.cpp || exit 1
    g++ --std=c++17 out.cpp -o program || exit 1
    echo \'$1\' successfully translated in \'out.cpp\' and compiled into \'program\'
fi
