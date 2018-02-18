#!/bin/bash

CARDN=$(aplay -l    | grep -i "usb audio"   | cut -f1 -d ':' | cut -f2 -d ' ')

if [[ $CARDN == "" ]]; then echo "USB audio not connected!"; exit 20; fi

 
if pgrep ecasound; then killall ecasound; fi
 
ecasound -q  -B:rtlowlatency -a:1 -f:16,2,48000  -i alsahw,$CARDN  -ete:10,25,35 -o alsa,dmix:$CARDN &
if [[ $? != 0 ]]; then  echo "Not started ecasound!"; exit 6; fi

