import os
import json
import random

from pathlib import Path
import uppdate_metadata
from create_src_IP import IPv4Generator

class AddIPsToCoflowTrace:
        
    def __init__(self):
        excluded_subnets = ['1.0.0.0', '2.0.0.0', '3.0.0.0', '40.0.0.0', '4.255.255.254']
        self.IPv4Generator = IPv4Generator(excluded_subnets=excluded_subnets)

    def add_IPs_to_coflow_trace(self, json_file: str, output_file_path: str, NUM_PODS: int) -> str:
        
        if not os.path.exists(json_file):
            print(f"File '{json_file}' not found.")
            raise FileNotFoundError

        # Load JSON coflow trace
        with open(json_file, 'r') as f:
            coflow_trace = json.load(f)

        for coflow in coflow_trace['coflows']:
            
            first_flow = True
            coflow_id = coflow['coflow_id']

            for flow in coflow['flows']:

                host_id = random.choice([0, 1]) # Even distribution between 3.0.0.x/8 and 3.0.1.x/8
                dst_id = int(flow["dest_id"]) # dst_id provided by Sincronia coflow workload generator
                pod_index = (dst_id % NUM_PODS) + 1 # Create pod index based on dst_id to ensure dst_ip are on range [1, NUM_PODS]
                dst_ip = f"3.0.{host_id}.{pod_index}" # Create destination IP address
        
                # First flow in coflow is a unique 5-tuple base flow with 2100 as destination port and unique source IP
                if first_flow:
                    first_flow = False # Set first_flow to False after first flow is generated
                    src_port = int(coflow_id) # Use coflow_id as source port as unique identifier
                    dst_port = 2100 # Destination port for the base flow
                    src_ip = self.IPv4Generator.generate_src_ipv4_address(coflow_id) # Generate unique and determistic source IP address for the base flow
                    dst_ip = dst_ip # Destination IP address for the base flow, using id from Sincronia coflow workload generator

                    flow['src_port'] = src_port # update src_port
                    flow['dst_port'] = dst_port # update dst_port
                    flow['pod_index'] = pod_index # set pod_index
                    flow['src_ip'] = src_ip # set src_ip
                    flow['dst_ip'] = dst_ip # set dst_ip

                # Other flows in coflow are associated with the unique 5-tuple base flow
                else:
                    src_id = int(flow["source_id"])
                    src_ip = f"192.168.1.{src_id}" # Create source IP address, doesn't matter?

                    flow['pod_index'] = pod_index # set pod_index
                    flow['src_ip'] = src_ip # set src_ip
                    flow['dst_ip'] = dst_ip # set dst_ip


        with open(output_file_path, 'w') as f:
            json.dump(coflow_trace, f, indent=2)

        return output_file_path

    def run(self, json_file_path: str, output_dir: str, NUM_PODS: int) -> str:

        self.json_file_name_without_extension = Path(os.path.basename(json_file_path)).stem

        output_file = f'{self.json_file_name_without_extension}_IPs.json'

        output_file_path = os.path.join(output_dir, output_file)

        output_file_path = self.add_IPs_to_coflow_trace(json_file_path, output_file_path, NUM_PODS)

        return output_file_path
    

if __name__ == "__main__":

    coflow_trace_dir = '/mnt/traces/emil/json_traces/traces_with_size/'
    coflow_trace_filename = '5-0.9-FB-UP_ports_Facebook_HadoopDist_All_size.json'
    coflow_trace_path = os.path.join(coflow_trace_dir, coflow_trace_filename)

    output_dir = '/mnt/traces/emil/json_traces/complete_traces'

    output_file = AddIPsToCoflowTrace().run(coflow_trace_path, output_dir)

    print(f"Output file: {output_file}")