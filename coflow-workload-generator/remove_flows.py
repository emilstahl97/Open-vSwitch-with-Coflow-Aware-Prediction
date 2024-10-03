import os
import sys
import json
import math
import random

import uppdate_metadata
from pathlib import Path


class RemoveFlows:

    def __init__(self):
        pass
     
    def create_flow_set(self, json_file: str) -> set:

        flow_set = set()
        
        if not os.path.exists(json_file):
            print(f"File '{json_file}' not found.")
            raise FileNotFoundError

        with open(json_file, 'r') as f:
            coflow_trace = json.load(f)

        for coflow in coflow_trace['coflows']:
            
            for flow in coflow['flows']:
                src_ip = flow['src_ip']
                src_port = flow['src_port']
                dst_ip = flow['dst_ip']
                dst_port = flow['dst_port']
                flow = (src_ip, src_port, dst_ip, dst_port)
                flow_set.add(flow)

        return flow_set
    
    def create_candidate_flows(self, json_file: str, flow_set: set) -> list:

        with open(json_file, 'r') as f:
            coflow_trace = json.load(f)

        candidate_flows = []

        for coflow in coflow_trace['coflows']:
            
            first_flow = True

            for flow in coflow['flows']:
                if first_flow:
                    first_flow = False
                    continue
                
                else:
                    src_ip = flow['src_ip']
                    src_port = flow['src_port']
                    dst_ip = flow['dst_ip']
                    dst_port = flow['dst_port']
                    flow = (src_ip, src_port, dst_ip, dst_port)
                    if flow in flow_set:
                        candidate_flows.append(flow)
        
        return candidate_flows

    def create_lists(self, candidate_flows: list) -> tuple:
        candidate_flows_dst_port_2100 = []
        candidate_flows_other_dst_port = []

        for flow in candidate_flows:
            if flow[3] == 2100:
                candidate_flows_dst_port_2100.append(flow)
            else:
                candidate_flows_other_dst_port.append(flow)

        return candidate_flows_dst_port_2100, candidate_flows_other_dst_port


    def remove_flows(self, json_file: str, output_file_path: str, nr_of_wanted_unique_flows: int = 193000) -> str:  

        flow_set = self.create_flow_set(json_file)

        nr_of_unique_flows = len(flow_set)
        print(f"Number of unique flows before removal: {nr_of_unique_flows}")

        if nr_of_unique_flows < nr_of_wanted_unique_flows:
            print(f"Number of unique flows, {nr_of_unique_flows}, is less than the desired number of unique flows, {nr_of_wanted_unique_flows}.")
            raise ValueError("Number of unique flows is less than the desired number of unique flows.")

        if nr_of_unique_flows > nr_of_wanted_unique_flows:
            print(f"Removing {nr_of_unique_flows - nr_of_wanted_unique_flows} flows.")
        
        flows_to_remove = nr_of_unique_flows - nr_of_wanted_unique_flows

        candidate_flows = self.create_candidate_flows(json_file, flow_set)

        candidate_flows_dst_port_2100, candidate_flows_other_dst_port = self.create_lists(candidate_flows)

        removal_list = []
        removal_list.extend(random.sample(candidate_flows_dst_port_2100, math.ceil(flows_to_remove/2)))
        removal_list.extend(random.sample(candidate_flows_other_dst_port, math.floor(flows_to_remove/2)))

        with open(json_file, 'r') as f:
            coflow_trace = json.load(f)
        
        flows_to_remove = []
        for coflow in coflow_trace['coflows']:
            for flow in coflow['flows']:
                src_ip = flow['src_ip']
                src_port = flow['src_port']
                dst_ip = flow['dst_ip']
                dst_port = flow['dst_port']
                flow_tuple = (src_ip, src_port, dst_ip, dst_port)
                if flow_tuple in removal_list:
                    flows_to_remove.append(flow_tuple)
        
            coflow['flows'] = [flow for flow in coflow['flows'] if (flow['src_ip'], flow['src_port'], flow['dst_ip'], flow['dst_port']) not in removal_list]
        
        flow_set = set()
        
        with open(output_file_path, 'w') as f:
            json.dump(coflow_trace, f, indent=2)

        flow_set = self.create_flow_set(output_file_path)

        print(f"Number of unique flows after removal: {len(flow_set)}")
        print(f"Number of flows removed: {len(removal_list)}")
        print(f'Number of desired unique flows: {nr_of_wanted_unique_flows}')

        return output_file_path
    

    def run(self, json_file_path: str, output_dir: str, desired_number_of_flows: int = 193000) -> str:

        self.json_file_name_without_extension = Path(os.path.basename(json_file_path)).stem

        output_file = f'{self.json_file_name_without_extension}_removed.json'

        output_file_path = os.path.join(output_dir, output_file)

        output_file_path = self.remove_flows(json_file_path, output_file_path, desired_number_of_flows)

        # Instantiate the UpdateMetadata class
        update_metadata_instance = uppdate_metadata.UpdateMetadata()

        # Call the run() method on the instance
        updated_output_file_path = update_metadata_instance.run(json_file_path=output_file_path, output_dir=output_dir, NUM_PODS=8)

        return updated_output_file_path
    

if __name__ == "__main__":

    coflow_trace_path = sys.argv[1]

    # check if coflow trace file exists
    if not os.path.exists(coflow_trace_path):
        print(f"File '{coflow_trace_path}' not found.")
        exit()

    output_dir = '/mnt/traces/emil/json_traces/removed_flows_dir/'

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    removed_flows_output_file = RemoveFlows().run(coflow_trace_path, output_dir)

    print(f"\nRemoved flows file: {removed_flows_output_file}")