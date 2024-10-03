# Script to load and associate flows in OVS

INTERVAL="1"       # Update interval in seconds
ingress_interface="ens16f1np1"  # Ingress interface name
# ANSI color codes
GREEN='\033[0;32m'
NC='\033[0m'  # No Color

function echo_action {
    echo -e "\x1B[1m\x1B[32m$1\x1B[m"
}

function echo_error {
    echo -e "\x1B[1m\x1B[31m$1\x1B[m"
}

get_current_flows() {
    # Execute the command and extract the number of current flows
    local current_flows=$(sudo ovs-appctl upcall/show | grep -oP 'flows\s+:\s+\(current\s+\K[0-9]+')

    # Check if we successfully retrieved the flow count
    if [ -z "$current_flows" ]; then
        echo_error "Failed to retrieve current flows."
        return 1 # Return a non-zero status to indicate failure
    else
        echo_action "Current number of flows: $current_flows"
        return 0 # Return zero to indicate success
    fi
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

echo_action " "
echo_action "Preparing OVS for loading associated flows..."
echo_action " "

print_netspeed &  # Start the netspeed function in the background
print_netspeed_pid=$!  # Get the PID of the netspeed function

echo_action "OVS configuration done. Ready to receive associated flows..."
echo_action "Press 'c' to continue..."

# Wait for 'c' key to send SIGINT and continue with the test
while true; do
    read -n 1 -s key
    if [[ $key == "c" ]]; then
        echo_action "\nReceived 'c'. Continuing..."
        kill -2 "$print_netspeed_pid"  # Send SIGINT to netspeed function
        break
    fi
done

echo_action "Checking number of associated flows loaded in OVS..."

get_current_flows

echo " "
echo_action "Ready to receive full trace."