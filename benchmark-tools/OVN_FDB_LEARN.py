#!/usr/bin/env python
#
# NOTE THIS IS A MODIFIED VERSION ONLY SENDING THE MAC ADDRESSES SO
# OVN WILL LEARN ITS FDB ENTRIES.
#
# Run this script in the external namespace when using the ocp_simulate.sh
# script:
#
#   time ip netns exec external ./traffic.py
#
# Or to start with a clean OVS instance:
#
#   systemctl restart openvswitch && sleep 1; \
#     ovs-appctl upcall/set-flow-limit 200000; sleep 1; \
#     time ip netns exec external ./traffic.py
#
#
# Set flow idle timeout longer, as it take a long time for this script
# to complete. We could optimize it, but I was just lazy ;) Also set the
# initial number of allowed flows to 200k. Something like this:
#
#   ovs-vsctl set Open_vSwitch . other_config:max-idle=3600000
#   ovs-appctl upcall/set-flow-limit 200000
#

from scapy.all import IP, ICMP, Ether, sendp
import scapy.layers.inet as inet
from get_packets import get_flow_set

# Define constants
JSON_FILE_PATH = '/mnt/traces/emil/production-traces/1000-Google-Search-RPC/adjusted_coflowiness/0.9_coflowiness/JSON/1000-Google-Search-RPC-0.9-coflowiness.json'
INTERFACE = "cx5if0"
PACKET_BATCH_SIZE = 2048
INTER_PACKET_DELAY = 0.0001

# Function to build ICMP echo packet
def build_icmp_echo_packet(src_mac, src_ip, dst_ip):
    eth_layer = Ether(src=src_mac, dst="00:00:00:03:00:00")
    ip_layer = IP(src=src_ip, dst=dst_ip)
    icmp_layer = ICMP()
    return eth_layer / ip_layer / icmp_layer

# Function to send packets in batches
def send_pkt_batch(packets):
    sendp(packets, iface=INTERFACE, count=1, inter=INTER_PACKET_DELAY)

# Main function
def main():
    flow_set = get_flow_set(JSON_FILE_PATH)
    print("Number of flows in flow_set: {}".format(len(flow_set)))

    packets = []
    packet_count = 0

    for flow in flow_set:
        src_ip, dst_ip, src_mac = flow
        print("ICMP_PKT: {} --> {}:{}".format(src_ip, src_mac, dst_ip))
        packets.append(build_icmp_echo_packet(src_mac, src_ip, dst_ip))

        if len(packets) >= PACKET_BATCH_SIZE:
            print("Sent {} packets".format(packet_count))
            send_pkt_batch(packets)
            packet_count += len(packets)
            packets = []

    if packets:
        send_pkt_batch(packets)

    print("Done sending {} packets!".format(packet_count))

if __name__ == "__main__":
    main()
