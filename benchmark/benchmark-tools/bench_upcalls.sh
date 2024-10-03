#!/bin/bash

# ANSI color codes
GREEN='\033[0;32m'
NC='\033[0m'  # No Color

INTERVAL="1"       # Update interval in seconds
ingress_interface="ens16f1np1"  # Ingress interface name0

function echo_action {
    echo -e "\x1B[1m\x1B[32m$1\x1B[m"
}

bench_tools_dir=$(pwd)

echo_action "Enter coflowiness value (0.0-1.0):"
read coflowiness

flow_size_distribution="Google-Search-RPC"  
#flow_size_distribution="Facebook-Hadoop"

check_OVS_sync() {

    echo "Checking if OVN is fully synced to OVS..."

    sleep 2

    sudo ovn-nbctl --timeout=10 --wait=hv sync
    return_code=$?

    if [ $return_code -eq 0 ]; then
        echo "OVN fully synced to OVS"
    else
        echo "OVN not fully synced to OVS" 
        echo "Command failed with return code $return_code"
    fi
}

check_nr_of_MAC_addresses() {

    learned_macs_in_ovn=$(sudo ovn-sbctl list fdb | grep mac | wc -l )
    echo "Number of MACs learned by OVN: $learned_macs_in_ovn"
    learned_macs_in_ovs=$(sudo ovs-ofctl dump-flows br-int | grep "table=72" | wc -l)
    echo "Number of MACs learned by OVS: $learned_macs_in_ovs"   
    sleep 1
}

get_current_flows() {
    # Execute the command and extract the number of current flows
    local current_flows=$(sudo ovs-appctl upcall/show | grep -oP 'flows\s+:\s+\(current\s+\K[0-9]+')

    # Check if we successfully retrieved the flow count
    if [ -z "$current_flows" ]; then
        echo "Failed to retrieve current flows."
        return 1 # Return a non-zero status to indicate failure
    else
        echo "Current number of flows: $current_flows"
        return 0 # Return zero to indicate success
    fi
}

OVS_setup() {

sudo systemctl stop openvswitch
sudo systemctl start openvswitch

sudo sh ../OVN-configuration/ocp_simulate.sh cleanup 
sudo sh ../OVN-configuration/ocp_simulate.sh setup 

sudo ovs-appctl upcall/set-flow-limit 200000
sudo ovs-vsctl set Open_vSwitch . other_config:max-idle=3600000

sudo ovs-vsctl set Open_vSwitch . other_config:n-revalidator-threads=10
sudo ovs-vsctl set Open_vSwitch . other_config:min-revalidate-pps=0
}

revalidation_setup() {
    sudo ovs-vsctl set Open_vSwitch . other_config:n-revalidator-threads=10
    sudo ovs-vsctl set Open_vSwitch . other_config:min-revalidate-pps=0
}

restart_OVS() {
    echo "Restarting Open vSwitch and updating max flows..."
    sudo systemctl restart openvswitch 
    sudo ovs-appctl upcall/set-flow-limit 200000
    echo "OVS restarted."
}

drop_privileges() {
    if sudo -u $user true; then
        echo "Dropped privileges successfully."
    else
        echo "Failed to drop privileges. Exiting."
        exit 1
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

load_associated_flows() {

    revalidation_setup

    restart_OVS

    check_OVS_sync

    check_nr_of_MAC_addresses

    get_current_flows

    print_netspeed &  # Start the netspeed function in the background
    print_netspeed_pid=$!  # Get the PID of the netspeed function

    echo_action "Ready to receive associated flows..."
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
}


bench_upcalls() {

    get_current_flows

    print_netspeed &  # Start the netspeed function in the background
    print_netspeed_pid=$!  # Get the PID of the netspeed function

    echo_action "Ready to receive full trace."
    echo_action "Press ENTER to stop gather upcall statistics..."

    /usr/bin/python3 $bench_tools_dir/parse_upcall_stats.py --coflowiness=$1 --flow_size_distribution=$2 &
    python_script_pid=$!  # Get the PID of the python script

    # Wait for ENTER key to send SIGINT and stop the python script
    read -s
    kill -2 "$print_netspeed_pid"  # Send SIGINT to netspeed function
    kill -2 "$python_script_pid"  # Send SIGINT to python script

    echo_action " "
    echo_action "Done receiving full trace."
}

cd $bench_tools_dir

OVS_setup

sudo sh $bench_tools_dir/OVN_FDB_LEARN.sh

# benchmark CPU load when receiving associated flows
#bench_associated $coflowiness $flow_size_distribution

# load associated flows a second time at lower rate
load_associated_flows

# benchmark CPU load when receiving full trace
bench_upcalls $coflowiness $flow_size_distribution

sudo sh ../OVN-configuration/ocp_simulate.sh cleanup 
sudo systemctl stop openvswitch

echo "Exiting..."