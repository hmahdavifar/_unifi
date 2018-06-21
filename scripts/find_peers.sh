#!/usr/bin/env bash

HOST_NAME=$1
PORT=$2
INTERFACE=$3

echo -e "<< put iwlist peers results >>\n$(iwlist ${INTERFACE} ap 2> /dev/null)\n$(iwlist ${INTERFACE} txpower 2> /dev/null)\n$(iwlist ${INTERFACE} freq 2> /dev/null)\n<< end >>\n" | telnet ${HOST_NAME} ${PORT}

