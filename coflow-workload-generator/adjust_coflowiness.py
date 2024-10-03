import os
import math
import json
import argparse
import humanize
import create_pcap_file_CDF

from pathlib import Path
from time import perf_counter
from utils.check_coflowiness import CheckCoflowiness
from create_unique_base_IP import BaseIPv4Generator
from remove_flows import RemoveFlows
import uppdate_metadata


class AdjustCoflowiness:

    def __init__(self):
        excluded_subnets = ['1.0.0.0', '2.0.0.0', '3.0.0.0', '40.0.0.0', '4.255.255.254']
        self.ipv4_generator = BaseIPv4Generator(excluded_subnets=excluded_subnets)
        self.changed_flows = 0       
        self.base_flow_index = 0

    def invert_number(self, n) -> float:
        if 0 <= n <= 1:
            return round(1 - n, 1)
        else:
            return "Number must be between 0 and 1."
     
    def adjust_coflowiness(self, json_file: str, output_file_path: str, coflowiness: float) -> str:
        
        if not os.path.exists(json_file):
            print(f"File '{json_file}' not found.")
            raise FileNotFoundError

        # Load JSON coflow trace
        with open(json_file, 'r') as f:
            coflow_trace = json.load(f)

        inverted_coflowiness = self.invert_number(coflowiness)

        for coflow in coflow_trace['coflows']:
            
            num_flows = len(coflow['flows'])
            self.first_flow = True
            
            number_of_flows_to_change = math.floor(num_flows * inverted_coflowiness)
            self.changed_flows = 0

            for flow in coflow['flows']:
                if self.first_flow:
                    src_ip = flow['src_ip']
                    flow['dst_port'] = 2100
                    self.ipv4_generator.add_excluded_subnet(src_ip)
                    self.first_flow = False
                    continue

                if self.changed_flows < number_of_flows_to_change:
                    flow['dst_port'] = 2100
                    unique_base_src_ip = self.ipv4_generator.get_unique_base_src_ip(self.base_flow_index)
                    flow['src_ip'] = unique_base_src_ip
                    self.changed_flows += 1
                    self.base_flow_index += 1


        with open(output_file_path, 'w') as f:
            json.dump(coflow_trace, f, indent=2)

        return output_file_path
    

    def run(self, json_file_path: str, output_dir: str, coflowiness: float, desired_unique_flows: int) -> str:

        if coflowiness <= 0 or coflowiness > 1:
            print("Coflowiness should be between 0 and 1.")
            raise ValueError("Coflowiness should be between 0 and 1.")

        self.json_file_name_without_extension = Path(os.path.basename(json_file_path)).stem

        output_file = f'{self.json_file_name_without_extension}_coflowiness_{coflowiness}.json'

        output_file_path = os.path.join(output_dir, output_file)

        output_file_path = self.adjust_coflowiness(json_file_path, output_file_path, coflowiness)

        ## Add check if unique flows are more than desired

        flow_set = RemoveFlows().create_flow_set(output_file_path)
        number_of_unique_flows = len(flow_set)

        if number_of_unique_flows > desired_unique_flows:

            print(f"Number of unique flows, {number_of_unique_flows}, is more than the desired number of unique flows, {desired_unique_flows}.")
            print(f"Removing {number_of_unique_flows - desired_unique_flows} flows.")
            updated_output_file_path = RemoveFlows().run(output_file_path, output_dir, desired_unique_flows)
        
        else:
            print(f'No flows removed. Number of unique flows: {number_of_unique_flows}')
            update_metadata_instance = uppdate_metadata.UpdateMetadata()
            updated_output_file_path = update_metadata_instance.run(json_file_path=output_file_path, output_dir=output_dir, NUM_PODS=8)

        return updated_output_file_path
    

    def create_pcap(json_file_path: str, pcap_dir: str):
        print(f'Starting to create pcap files for flows in {json_file_path}')
        pcap_file_paths = create_pcap_file_CDF.CoflowTraceGenerator().run(json_file_path, pcap_dir, cores=1)

        for i, pcap_file_path in enumerate(pcap_file_paths):
            print(f"\nPcap file {i} saved to: {pcap_file_path}")
            print(f"Size of pcap file {i}: {humanize.naturalsize(os.path.getsize(pcap_file_path))}\n")
    

if __name__ == "__main__":

    argparser = argparse.ArgumentParser(description='Adjust coflowiness of a trace.')
    argparser.add_argument('--coflowiness', type=float, required=False, default=0.5, help='Coflowiness between 0 and 1. (default: 0.5)')
    argparser.add_argument('--coflow-trace', type=str, required=True, help='Path to the coflow trace file.')
    argparser.add_argument('--create-pcap', type=bool, default=False, help='Create pcap files for flows. (default: False)')
    args = argparser.parse_args()

    coflow_trace_path = args.coflow_trace
    coflowiness = args.coflowiness
    create_pcap = args.create_pcap

    if coflowiness < 0 or coflowiness > 1:
        print("Coflowiness should be between 0 and 1.")
        exit()

    # check if coflow trace file exists
    if not os.path.exists(coflow_trace_path):
        print(f"File '{coflow_trace_path}' not found.")
        exit()

    output_dir = '/mnt/traces/emil/json_traces/adjusted_coflowiness'
    pcap_dir = '/mnt/traces/emil/pcap_traces/adjusted_coflowiness'

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if not os.path.exists(pcap_dir):
        os.makedirs(pcap_dir)

    print(f'Adjusting coflowiness in {coflow_trace_path} to {coflowiness}')

    adjusted_coflowiness_output_file = AdjustCoflowiness().run(coflow_trace_path, output_dir, coflowiness)

    print(f'------------------------------------')
    print(f"Coflowiness adjusted to {coflowiness}")
    print(f"Output file: {adjusted_coflowiness_output_file}")

    # check coflowiness of the adjusted trace
    CheckCoflowiness().check_coflowiness(adjusted_coflowiness_output_file)

    if create_pcap:
        start_time = perf_counter()
        print(f'Creating pcap files for flows in {adjusted_coflowiness_output_file}')
        AdjustCoflowiness.create_pcap(adjusted_coflowiness_output_file, pcap_dir)
        end_time = perf_counter()
        print(f'Pcap files created in {end_time - start_time} seconds.')