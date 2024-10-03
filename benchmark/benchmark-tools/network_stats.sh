#!/bin/bash

INTERFACE="ens16f1np1"
STATS_FILE="/tmp/network_stats_$INTERFACE.txt"

# Function to read current statistics
read_stats() {
    sudo ip -s link show dev "$INTERFACE" | awk '
    /RX:/ { rx=1; tx=0; next }
    /TX:/ { rx=0; tx=1; next }
    rx { rx_bytes=$1; rx_packets=$2; rx_errors=$3; rx_dropped=$4; next }
    tx { tx_bytes=$1; tx_packets=$2; tx_errors=$3; tx_dropped=$4 }
    END { print rx_bytes, rx_packets, rx_errors, rx_dropped, tx_bytes, tx_packets, tx_errors, tx_dropped }
    '
}

# Function to calculate differences
calculate_diff() {
    prev_stats=("$@")
    curr_stats=($(read_stats))

    diff_stats=()
    for i in "${!prev_stats[@]}"; do
        diff_stats[$i]=$(( curr_stats[$i] - prev_stats[$i] ))
    done

    echo "${diff_stats[@]}"
}

# Function to format numbers with commas
format_number() {
    printf "%'d" "$1"
}

# Initialize previous stats if file doesn't exist
if [[ ! -f "$STATS_FILE" ]]; then
    read_stats > "$STATS_FILE"
    echo "Initialized stats. Please run the script again to see differences."
    exit 0
fi

# Read previous stats
read -r -a prev_stats < "$STATS_FILE"

# Calculate differences
diff_stats=($(calculate_diff "${prev_stats[@]}"))

# Print the differences with formatted numbers
echo "Interface: $INTERFACE"
echo "RX: bytes=$(format_number ${diff_stats[0]}) packets=$(format_number ${diff_stats[1]}) errors=$(format_number ${diff_stats[2]}) dropped=$(format_number ${diff_stats[3]})"
echo "TX: bytes=$(format_number ${diff_stats[4]}) packets=$(format_number ${diff_stats[5]}) errors=$(format_number ${diff_stats[6]}) dropped=$(format_number ${diff_stats[7]})"

# Save current stats for next run
read_stats > "$STATS_FILE"
