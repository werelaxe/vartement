#!/bin/bash

python3 translate.py test.vta>out.cpp
g++ --std=c++17 out.cpp -o tests
./tests
rm out.cpp
rm tests
