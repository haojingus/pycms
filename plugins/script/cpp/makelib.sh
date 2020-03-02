#!/bin/bash
BASE=$1
cd $BASE/plugins/script/cpp/usr
g++ -c $2.cpp
ar crv lib$2.a $2.o
g++ ../cmsmain.cpp -l$2 -L$1/plugins/script/cpp/usr -o $2
./$2
pwd
echo "$1@@@@@@$2"
