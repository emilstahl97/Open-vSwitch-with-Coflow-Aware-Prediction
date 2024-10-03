#!/bin/bash

# Check if input file argument is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <input_file>"
    exit 1
fi

traceIN=$1
sudo /home/emilstahl/fastclick/bin/click --dpdk -l 0-15 -- /home/emilstahl/pcap-to-summary.click traceOUT=/home/emilstahl/traces/summary/pcap_summary.sum traceIN=$traceIN