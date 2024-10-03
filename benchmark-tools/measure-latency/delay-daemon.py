import json
import os
import socket
import signal
import selectors
import subprocess
from collections import deque, namedtuple

class Daemon:

    def __init__(self, interface: str) -> None:
        self.sockets = []
        self.selectors = selectors.DefaultSelector()
        self.interface = interface
        self.delay_deque = deque()
        self.PacketData = namedtuple('PacketData', ['name', 'start_byte', 'end_byte', 'byte_order'])
        self.fields = [
            self.PacketData('Packet id', 1, 8, 'big'),
            self.PacketData('Ingress timestamp', 9, 16, 'little'),
            self.PacketData('Egress timestamp', 17, 24, 'little')
        ]

    def process_packet(self, raw_data, destination_port, source_ip, source_port) -> None:  # Modified to accept source_port
        if len(raw_data) >= 24:
            packet_info = [
                int.from_bytes(raw_data[field.start_byte:field.end_byte], byteorder=field.byte_order, signed=False)
                for field in self.fields
            ]
            packet_info.append(destination_port)
            packet_info.append(source_ip)
            packet_info.append(source_port)  # Append source port to packet_info
            self.delay_deque.append(packet_info)

    def start(self) -> None:

        # Define the list of ports to listen on
        ports = [2100, 2110, 2120, 2130, 2140, 2150, 2160, 2170, 2180]

        pod_id = self.get_pod_id()
        ip_address = self.get_interface_ip()

        for port in ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Enable SO_REUSEADDR
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 2073741824)  # Set socket buffer to maximum size
            sock.bind((ip_address, port))
            self.selectors.register(sock, selectors.EVENT_READ, data=None)
            self.sockets.append(sock)

        print(f"{pod_id} sniffing UDP packets on ports: {ports} via interface {self.interface} with IP address {ip_address}")

        # Define a signal handler for SIGINT (Ctrl+C)
        def sigint_handler(signum, frame):
            print("\nReceived SIGINT, saving entries and exiting...")
            self.save_entries()
            print("Closing sockets...")
            for sock in self.sockets:
                print(f"Closing socket on port {sock.getsockname()[1]}")
                self.selectors.unregister(sock)
                sock.close()
            exit(0)

        # Register the signal handler
        signal.signal(signal.SIGINT, sigint_handler)

        while True:
            events = self.selectors.select(timeout=None)
            for key, _ in events:
                udp_socket = key.fileobj
                destination_port = udp_socket.getsockname()[1]  # Get the port number
                raw_data, addr = udp_socket.recvfrom(1500)  # Receive source IP address and port along with packet
                source_ip = addr[0]  # Extract source IP address
                source_port = addr[1]  # Extract source port
                self.process_packet(raw_data, destination_port, source_ip, source_port)  # Pass source port to process_packet method

    def save_entries(self) -> None:
        entries_list = [{'destination_port': entry[3], 'pkt_id': entry[0], 'ingress_ts': entry[1], 'egress_ts': entry[2], 'source_ip': entry[4], 'source_port': entry[5], 'delta': entry[2] - entry[1]} for entry in self.delay_deque]  # Include source port in entries_list

        pod_id = self.get_pod_id()
        ip_address = self.get_interface_ip()
        filename = f'{pod_id}_delay_entries.json'

        data_to_save = {'pod_id': pod_id, 'IP_address': ip_address, 'delay_timestamps': entries_list}

        cwd = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(cwd, 'delay-entries')
        os.makedirs(output_dir) if not os.path.exists(output_dir) else None
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w') as json_file:
            json.dump(data_to_save, json_file, indent=4)
        
        print(f'Entries saved to {filename}')

    def get_pod_id(self) -> str:
        IP_address = self.get_interface_ip()
        pod_id = f'pod{IP_address[-1]}'
        return pod_id

    def get_interface_ip(self) -> str:
        command = f"ip -o -4 addr show dev {self.interface} | awk '{{print $4}}' | cut -d'/' -f1"
        output = subprocess.check_output(command, shell=True, text=True)
        ip_address = output.strip()
        return ip_address
    

if __name__ == "__main__":
    interface = 'eth0'
    daemon = Daemon(interface)
    daemon.start()
