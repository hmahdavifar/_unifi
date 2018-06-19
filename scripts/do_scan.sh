#!/usr/bin/env bash

HOST_NAME=$1
PORT=$2
INTERVAL=$3
INTERFACE=$4

while true;do
    now=$(date +%s)
    echo -e "<< put iwlist scan results >>\n$now\n$(iwlist ${INTERFACE} scan 2> /dev/null)\n<< end >>\n" | telnet ${HOST_NAME} ${PORT}
    sleep ${INTERVAL}
done;
