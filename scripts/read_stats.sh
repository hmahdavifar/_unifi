#!/usr/bin/env bash

HOST_NAME=$1
PORT=$2
INTERVAL=$3
WIFI_INTERFACE=$4
ATH_INTERFACE=$5

while true;do
    now=$(date +%s)
    tx_packets=$(cat /sys/class/net/${WIFI_INTERFACE}/statistics/tx_packets)
    tx_errors=$(cat /sys/class/net/${WIFI_INTERFACE}/statistics/tx_errors)
    rx_packets=$(cat /sys/class/net/${WIFI_INTERFACE}/statistics/rx_packets)
    rx_errors=$(cat /sys/class/net/${WIFI_INTERFACE}/statistics/rx_errors)
    rx_crc_errors=$(cat /sys/class/net/${WIFI_INTERFACE}/statistics/rx_crc_errors)
    tx_bytes=$(cat /sys/class/net/${ATH_INTERFACE}/statistics/tx_bytes)
    rx_bytes=$(cat /sys/class/net/${ATH_INTERFACE}/statistics/rx_bytes)
    echo -e "<< put error statistics >>\n$now\ntx_packets=$tx_packets\ntx_errors=$tx_errors\nrx_packets=$rx_packets\nrx_crc_errors(test)=$rx_crc_errors\nrx_errors=$rx_errors\ntx_bytes=$tx_bytes\nrx_bytes=$rx_bytes\n<< end >>\n" | telnet ${HOST_NAME} ${PORT}
    sleep ${INTERVAL}
done;

