#!/usr/bin/env bash

HOST_NAME=$1
PORT=$2

echo -e "<< put config info >>\n$(iwconfig 2> /dev/null)\n$(ifconfig 2> /dev/null)\n<< end >>\n" | telnet ${HOST_NAME} ${PORT}
