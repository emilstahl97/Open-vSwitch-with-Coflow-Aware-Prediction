import os
import json
import random

class AddPortsToCoflowTrace:

    def __init__(self):
        self.dst_ports = [2110, 2120, 2130, 2140, 2150, 2160, 2170, 2180]

    def add_ports_to_coflow_trace(self, json_file, output_dir):
        if not os.path.exists(json_file):
            print(f"File '{json_file}' not found.")
            return

        # Load JSON coflow trace
        with open(json_file, 'r') as f:
            coflow_trace = json.load(f)

        # Function to get a random port for an IP from the respective dictionary
        def get_src_port(ip, src_ip_ports_dict) -> int:
            current_port = src_ip_ports_dict[ip]
            # if 18, set to 1
            if current_port == 10030: # number of max src ports, currently 11
            #if current_port == 109000:
                src_ip_ports_dict[ip] = 10000
                return 10000
            else:
                src_ip_ports_dict[ip] += 1
                return current_port


        # Dictionary to store common ports for each IP in the coflow
        common_src_ports = {}
        common_dst_ports = {}

        src_ip_ports_dict = {}  # Dictionary to store the current port for each IP

        # Update JSON coflow trace with source and destination ports
        for coflow in coflow_trace['coflows']:
            for flow in coflow['flows']:
                # Get source and destination IPs
                src_ip = float(flow['source_id'])
                dst_ip = float(flow['dest_id'])

                # If source IP is not in the dictionary, add it
                if src_ip not in src_ip_ports_dict:
                    src_ip_ports_dict[src_ip] = 10000

                # If common source port is not assigned for this IP in the coflow, assign one
                if src_ip not in common_src_ports:
                    common_src_ports[src_ip] = get_src_port(src_ip, src_ip_ports_dict)

                # If common destination port is not assigned for this IP in the coflow, assign one
                if dst_ip not in common_dst_ports:
                    # select a random destination port from the list of destination ports
                    common_dst_ports[dst_ip] = random.choice(self.dst_ports)

                # Update the flow with source and destination ports
                flow['src_port'] = common_src_ports[src_ip]
                flow['dst_port'] = common_dst_ports[dst_ip]
            
            # clear the common ports dictionaries
            common_src_ports.clear()
            common_dst_ports.clear()

        # Save the modified JSON coflow trace
        # create output file name by adding '_ports' to the original file name
        output_file = os.path.basename(json_file).replace('.json', '_ports.json')
        output_file_path = os.path.join(output_dir, output_file)

        with open(output_file_path, 'w') as f:
            json.dump(coflow_trace, f, indent=2)

        return output_file_path
    
    def run(self, json_file_path: str, output_dir: str) -> str:

        output_file_path = self.add_ports_to_coflow_trace(json_file_path, output_dir)

        return output_file_path
    

if __name__ == "__main__":

    coflow_trace_dir = '/home/emilstahl/DA240X/Benchmark/workload-generator/json_traces'

    coflow_trace_filename = '5-0.9-FB-UP.json'

    coflow_trace_path = os.path.join(coflow_trace_dir, coflow_trace_filename)

    AddPortsToCoflowTrace().run(coflow_trace_path)