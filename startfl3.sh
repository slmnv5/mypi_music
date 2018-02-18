#!/bin/bash

#if [[ $EUID != 0 ]]; then echo "Must be root"; exit 33; fi

FISHM=$(aconnect -i | grep -i "fishman tri" | cut -f1 -d ':' | cut -f2 -d ' ')
CARDN=$(aplay -l    | grep -i "usb audio"   | cut -f1 -d ':' | cut -f2 -d ' ')

if [[ $FISHM == "" ]]; then echo "Fishman not connected!"; exit 10; fi
if [[ $CARDN == "" ]]; then echo "USB audio not connected!"; exit 20; fi

if pgrep fluidsynth; then killall fluidsynth; fi


fluidsynth  -g1.0 -z128 -c2 -is -a alsa -o audio.alsa.device=hw:$CARDN \
	-o midi.realtime-prio=80 \
	-o synth.min-note-length=0 \
	-f /home/pi/mypi/bin/flrules.txt \
	/home/pi/mypi/sf2/serik6.sf2 &	
	#/usr/share/sounds/sf2/FluidR3_GM.sf2 &
	
	  

if [[ $? != 0 ]]; then  echo "Not started fluidsynth!"; exit 3; fi
sleep 15
aconnect -x
FLSYN=$(aconnect -o | grep -i "fluid synth" | cut -f1 -d ':' | cut -f2 -d ' ')
if [[ $FLSYN == "" ]]; then echo "Fluid synth not available!"; exit 4; fi

aconnect $FISHM:0 $FLSYN:0
if [[ $? != 0 ]]; then	echo "Not connected!"; exit 5; fi

amixer -c $CARDN sset "Speaker" 80%
amixer -c $CARDN sset "Mic" 0%
 