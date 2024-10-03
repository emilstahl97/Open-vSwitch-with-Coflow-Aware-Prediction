#!/bin/bash

cwd=$(pwd)
INTERVAL="1"       # Update interval in seconds
ingress_interface="ens16f1np1"  # Ingress interface name
declare -a pids=()  # Declare an array to store PIDs

# Create the log directory in the current working directory

bench_tools_dir=$(pwd)
cd ../measure-latency
cwd=$(pwd)
cd $bench_tools_dir

log_dir=$cwd/logs
mkdir -p "$log_dir"
log_file="$log_dir/ns_logs.log" # Log file name
rm -f "$log_file"  # Remove existing log file
touch "$log_file"  # Create a new log file

# ANSI color codes
GREEN='\033[0;32m'
NC='\033[0m'  # No Color

function echo_action {
    echo -e "\x1B[1m\x1B[32m$1\x1B[m"
}

function echo_error {
    echo -e "\x1B[1m\x1B[31m$1\x1B[m"
}

print_netspeed() {
    trap 'exit' INT  # Set up a trap to exit on SIGINT (Ctrl+C)
    echo " "
    while true; do
        R1=$(cat /sys/class/net/$ingress_interface/statistics/rx_bytes)
        T1=$(cat /sys/class/net/$ingress_interface/statistics/tx_bytes)
        P1=$(cat /sys/class/net/$ingress_interface/statistics/rx_packets)
        Q1=$(cat /sys/class/net/$ingress_interface/statistics/tx_packets)
        sleep $INTERVAL
        R2=$(cat /sys/class/net/$ingress_interface/statistics/rx_bytes)
        T2=$(cat /sys/class/net/$ingress_interface/statistics/tx_bytes)
        P2=$(cat /sys/class/net/$ingress_interface/statistics/rx_packets)
        Q2=$(cat /sys/class/net/$ingress_interface/statistics/tx_packets)
        
        TBPS=$((T2 - T1))
        RBPS=$((R2 - R1))
        TXPPS=$((Q2 - Q1))
        RXPPS=$((P2 - P1))
        
        TGbps=$(bc <<< "scale=2; $TBPS * 8 / 10^9")
        RGbps=$(bc <<< "scale=2; $RBPS * 8 / 10^9")
        
        # Format output with color
        printf "\rTX $ingress_interface: ${GREEN}%0.2f Gb/s${NC} RX $ingress_interface: ${GREEN}%0.2f Gb/s${NC} TX $ingress_interface: ${GREEN}%d pkts/s${NC} RX $ingress_interface: ${GREEN}%d pkts/s${NC}" "$TGbps" "$RGbps" "$TXPPS" "$RXPPS"
    done
}


# Function to send SIGINT to processes
# Modified send_sigint function
send_sigint() {
    for pid in "${pids[@]}"; do
        if kill -0 $pid 2>/dev/null; then
            echo_action "Sending SIGINT to PID: $pid${NC}"
            kill -2 "$pid"  # SIGINT signal
        else
            echo_error "No such process with PID: $pid"
        fi
    done
}


load_xdp_ingress() {
    cd $cwd
    echo_action "Unloading XDP program on ingress..."
    sh "$cwd/unload_xdp_ingress.sh" >> "$log_file" 2>&1
    echo_action "Loading XDP program on ingress..."
    sh "$cwd/load_xdp_ingress.sh" >> "$log_file" 2>&1
    echo " "
}

start_daemons() {
    cd $cwd
    local errors=0  # Variable to track errors
    # Example of a for loop
    for i in {1..8}; do
        echo_action "[Pod$i] Unloading XDP program on egress..."
        ip netns exec pod$i sh "$cwd/unload_xdp_egress.sh" >> "$log_file" 2>&1
        echo_action "[Pod$i] Loading XDP program on egress..."
        ip netns exec pod$i sh "$cwd/load_xdp_egress.sh" >> "$log_file" 2>&1
        sleep 1
        echo_action "[Pod$i] Starting daemon..."
        ip netns exec pod$i /usr/bin/python3 "$cwd/delay-daemon.py" >> "$log_file" 2>&1 &
        local last_pid=$!
        sleep 1  # Give a short moment for the process to start and stabilize

        # Check if the process is running
        if ! kill -0 $last_pid 2>/dev/null; then
            echo_error "Failed to start process or it terminated unexpectedly on pod$i"
            ((errors++))  # Increment errors count
        else
            echo_action "[Pod$i] Daemon started successfully with PID $last_pid."
            pids+=("$last_pid")
        fi
        echo " "
    done
    
    # Check if there were any errors during startup
    if [[ $errors -eq 0 ]]; then
        echo_action "All daemons have been started successfully."
    else
        echo_error "$errors errors occurred during daemon startup."
    fi
}

# Load XDP programs on ingress 
load_xdp_ingress

# Start daemons using the function
start_daemons

print_netspeed &  # Start the netspeed function in the background
print_netspeed_pid=$!  # Get the PID of the netspeed function

# Add the netspeed PID to the pids array
pids+=("$print_netspeed_pid")

# Echo message to inform user about terminating processes
echo_action "Press 'q' to terminate processes..."

# Wait for 'q' key to send SIGINT and terminate delay-daemon processes
while true; do
    read -n 1 -s key
    if [[ $key == "q" ]]; then
        echo_action "\nReceived 'q'. Sending SIGINT to terminate processes..."
        kill -2 "$print_netspeed_pid"  # Send SIGINT to netspeed function
        send_sigint
        sleep 1
        break
    fi
done

# Optional: Cleanup log files or perform other actions here