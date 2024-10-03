#!/bin/bash

# Check if the number of arguments provided is correct
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <iterations>"
    exit 1
fi

bench_tools_dir=$(pwd)

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

check_dropped_packets() {
    echo " "
    echo "Number of dropped packets during run $1:"
    echo " "
    sudo sh $bench_tools_dir/network_stats.sh
    echo " "
}

reset_packet_counters() {
    echo "Resetting packet counters..."
    sudo sh $bench_tools_dir/network_stats.sh
}

# Assign the argument to a variable
iterations=$1

bench_tools_dir=$(pwd)

cd ../measure-latency
cwd=$(pwd)

cd $bench_tools_dir

user="emilstahl"

echo "cwd: $cwd"

parent_dir=$(dirname "$(pwd)")

echo "Enter coflowiness value: "
read coflowiness
echo "Coflowiness value: $coflowiness"
echo " "
flow_size_distribution="Facebook-Hadoop"

results_dir="$parent_dir/results/base-runs/base-run-$flow_size_distribution-$coflowiness-coflowiness"
mkdir -p $results_dir

stats_dir="$results_dir/statistics"
mkdir -p $stats_dir

aggregated_statistics_dir="$results_dir/aggregated-statistics"
mkdir -p $aggregated_statistics_dir

delay_entries_path="$results_dir/delay-entries"
mkdir -p $delay_entries_path

OVS_setup

sudo sh $bench_tools_dir/OVN_FDB_LEARN.sh

# Loop for the specified number of iterations
for ((i = 1; i <= iterations; i++)); do

    echo "Iteration: $i"

    reset_packet_counters
    
    rm -rf delay-entries

    revalidation_setup

    restart_OVS

    check_OVS_sync

    check_nr_of_MAC_addresses

    # Setup daemons and perform the benchmark
    sudo sh $bench_tools_dir/benchmark.sh

    check_dropped_packets $i

    drop_privileges

    cd $bench_tools_dir

    echo " "
    echo "Run $i: Writing delay entries to file..."
    sleep 10

    delay_entries_destination="$delay_entries_path/delay-entries-run-$i"

    mkdir -p $delay_entries_destination

    mv -T $cwd/delay-entries $delay_entries_destination

done


echo " "
echo "All $iterations iterations completed."
echo " "

sudo sh ../OVN-configuration/ocp_simulate.sh cleanup 
sudo systemctl stop openvswitch

echo "Producing statistics..."

/usr/bin/python3 produce_statistics.py --directory $delay_entries_path --output_directory $stats_dir

echo "Done producing statistics."

echo "Producing aggregated statistics..."

/usr/bin/python3 aggregate_statistics.py --directory $stats_dir --output_directory $aggregated_statistics_dir

echo "Done producing aggregated statistics."

echo "Results directory: $results_dir"
ls $results_dir
echo " "
echo "Statistics directory: $stats_dir"
ls $stats_dir
echo " "
echo "Delay entries directory: $delay_entries_path"
ls $delay_entries_path
echo " "
echo "Aggregated statistics directory: $aggregated_statistics_dir"
ls $aggregated_statistics_dir

echo " "
echo "Exiting..."