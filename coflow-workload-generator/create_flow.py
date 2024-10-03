from scapy.all import Ether, IP, UDP, wrpcap
from functools import lru_cache

destination_mac = "00:00:00:03:00:00"

@lru_cache(maxsize=65000, typed=True)
def create_ethernet_header(source_mac: str) -> Ether:
    return Ether(src=source_mac, dst=destination_mac)

@lru_cache(maxsize=10, typed=True)
def create_udp_packet(source_ip, source_port, destination_ip, destination_port, source_mac, payload_size):
    payload = b'A' * payload_size
    ethernet_header = create_ethernet_header(source_mac=source_mac)
    packet = ethernet_header / IP(src=source_ip, dst=destination_ip) / UDP(sport=source_port, dport=destination_port) / payload
        
    if not check_packet_headers(packet):
        raise ValueError("Packet headers are not correct")
    if len(packet) > 1500:
        raise RuntimeError("Packet length is above MTU of 1500 bytes")
    
    return packet

def generate_udp_traffic(source_ip, source_port, destination_ip, destination_port, source_mac, udp_payload):
    max_payload_size = 1458
    data_packets = []

    while udp_payload > 0:
        payload_size = min(udp_payload, max_payload_size)
        
        packet = create_udp_packet(source_ip, source_port, destination_ip, destination_port, source_mac, payload_size)
        
        data_packets.append(packet)
        udp_payload -= payload_size

    return data_packets

def check_packet_headers(packet):
    if Ether not in packet or IP not in packet or UDP not in packet:
        return False

    return True


def write_packets_to_pcap(packets, pcap_filename):
    wrpcap(pcap_filename, packets)

if __name__ == "__main__":
    source_ip = "192.168.1.1"
    source_port = 1234
    destination_ip = "192.168.1.2"
    destination_port = 80
    udp_payload = 1000000
    pcap_filename = "generated_traffic_udp_with_eth.pcap"

    packets = generate_udp_traffic(source_ip, source_port, destination_ip, destination_port, udp_payload)
    write_packets_to_pcap(packets, pcap_filename)