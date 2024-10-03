# change x mac addresses to get 3x more unique flows

import json
import os
from time import perf_counter
from uppdate_metadata import UpdateMetadata
import create_pcap_file_CDF
import humanize

class AdjustTrace:

    def __init__(self):
        pass

    def get_mac_by_id(self, mid) -> str:
            return "00:EC:00:{:x}:{:x}:{:x}".format(mid >> 16 & 0xff,
                                                mid >> 8 & 0xff, mid & 0xff)

    def create_mac_address_list(self, num_macs: int) -> list:
        mac_list = []

        start_mac_id = 100000
        end_mac_id = start_mac_id + num_macs

        for i in range(start_mac_id, end_mac_id):
            mac = self.get_mac_by_id(i)
            mac_list.append(mac)

        return mac_list

        
    def create_flow_dict(self, json_file: str) -> dict:
        src_mac_dict = {}
        
        if not os.path.exists(json_file):
            print(f"File '{json_file}' not found.")
            raise FileNotFoundError

        # Load JSON coflow trace
        with open(json_file, 'r') as f:
            coflow_trace = json.load(f)

        for coflow in coflow_trace['coflows']:
            for flow in coflow['flows']:
                src_mac = flow['src_mac']
                # Count the number of occurrences of src_mac
                if src_mac in src_mac_dict:
                    src_mac_dict[src_mac] += 1
                else:
                    src_mac_dict[src_mac] = 1
        
        # Filter src_mac_dict to only include src_mac addresses that occur 3 times or more
        frequent_src_mac_dict = {mac: count for mac, count in src_mac_dict.items() if count >= 3}

        # Print length of the original src_mac_dict and frequent_src_mac_dict
        print(f"Length of original src_mac_dict: {len(src_mac_dict)}")
        print(f"Length of frequent src_mac_dict: {len(frequent_src_mac_dict)}")
        
        return frequent_src_mac_dict
    

    def add_new_src_MACs_to_coflow_trace(self, json_file: str, output_file_path: str, num_macs: int) -> str:

        src_mac_dict = self.create_flow_dict(json_file)

        new_mac_list = self.create_mac_address_list(num_macs=num_macs)

        # Load JSON coflow trace
        with open(json_file, 'r') as f:
            coflow_trace = json.load(f)

        for coflow in coflow_trace['coflows']:
            
            for flow in coflow['flows']:
                src_mac = flow['src_mac']

                if new_mac_list:

                    # update src_mac if it is in src_mac_dict, only update src_mac once
                    if src_mac in src_mac_dict:
                        src_mac_dict.pop(src_mac)
                        flow['src_mac'] = new_mac_list.pop()

                else:
                    break

        with open(output_file_path, 'w') as f:
            json.dump(coflow_trace, f, indent=2)

        return output_file_path
    

    def run(self, json_file_path: str, output_dir: str, num_macs: int) -> str:
        self.json_file_name_without_extension = os.path.splitext(os.path.basename(json_file_path))[0]

        output_file = f'{self.json_file_name_without_extension}_added_{num_macs}_src_MACs.json'

        output_file_path = os.path.join(output_dir, output_file)

        output_file_path = self.add_new_src_MACs_to_coflow_trace(json_file_path, output_file_path, num_macs)
        
        updated_output_file_path = UpdateMetadata().run(json_file_path=output_file_path, output_dir=output_dir, NUM_PODS=8)

        return updated_output_file_path

    def create_pcap(self, json_file_path: str, pcap_dir: str):
        print(f'Starting to create pcap files for flows in {json_file_path}')
        pcap_file_paths = create_pcap_file_CDF.CoflowTraceGenerator().run(json_file_path, pcap_dir, cores=1)

        for i, pcap_file_path in enumerate(pcap_file_paths):
            print(f"\nPcap file {i} saved to: {pcap_file_path}")
            print(f"Size of pcap file {i}: {humanize.naturalsize(os.path.getsize(pcap_file_path))}\n")


if __name__ == '__main__':

    json_file_path = '/home/emilstahl/traces/production-traces/1000-FB-UP/original-1000-FB-UP.json'
    output_dir = '/home/emilstahl/traces/production-traces/1000-FB-UP/add_more_macs'
    num_macs = 30000
    create_pcap = True

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    new_trace_file_path = AdjustTrace().run(json_file_path, output_dir, num_macs)


    if create_pcap:
        start_time = perf_counter()
        print(f'Creating pcap files for flows in {new_trace_file_path}')
        AdjustTrace().create_pcap(new_trace_file_path, output_dir)
        end_time = perf_counter()
        print(f'Pcap files created in {end_time - start_time} seconds.')