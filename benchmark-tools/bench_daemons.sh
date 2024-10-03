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

echo 'starting'

cd $bench_tools_dir

OVS_setup

# Setup daemons and perform the benchmark
sudo sh $bench_tools_dir/benchmark.sh

sudo sh ../OVN-configuration/ocp_simulate.sh cleanup 
sudo systemctl stop openvswitch

echo "Exiting..."