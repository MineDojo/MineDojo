#!/bin/bash

# iterate until a port is open
PORT=1044
echo >&1 "waiting for port $PORT to be open"
while true; do

  nc -z 127.0.0.1 $PORT
  if [ $? -eq 0 ]; then
    break
  else 
    echo >&1 "port $PORT is still closed"
    sleep 1
  fi
done

# add an extra sleep because we may be too fast detecting the port, and JVM crashes
sleep 3
