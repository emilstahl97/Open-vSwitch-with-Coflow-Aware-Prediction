import os
import json

from pathlib import Path

class AddMACsToCoflowTrace:
        
    def __init__(self):
        pass

    def get_mac_by_id(self, mid) -> str:
            return "00:EC:00:{:x}:{:x}:{:x}".format(mid >> 16 & 0xff,
                                                mid >> 8 & 0xff, mid & 0xff)

    def create_shared_values_dictionary(self, unique_flows) -> dict:

        shared_values_count = (len(unique_flows)) // 3
        shared_values_count = min(shared_values_count, 32400) # leaving some room for existing 3k dp flows
        
        values = list(range(shared_values_count + 1))
        
        shared_values_dict = {}
        
        for i, key in enumerate(unique_flows):

            mac_id_index = values[i % shared_values_count]
            #print(f'mac_id_index: {mac_id_index}')
            mac_id = self.get_mac_by_id(mac_id_index)
            shared_values_dict[key] = mac_id
        
        return shared_values_dict
    
    def create_flow_set(self, json_file: str) -> set:

        flow_set = set()
        
        if not os.path.exists(json_file):
            print(f"File '{json_file}' not found.")
            raise FileNotFoundError

        # Load JSON coflow trace
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

        print(f"Flow set size: {len(flow_set)}")

        return flow_set


    def add_MACs_to_coflow_trace(self, json_file: str, output_file_path: str) -> str:

        flow_set = self.create_flow_set(json_file)
        flow_mac_dict = self.create_shared_values_dictionary(flow_set)
        
        if not os.path.exists(json_file):
            print(f"File '{json_file}' not found.")
            raise FileNotFoundError

        # Load JSON coflow trace
        with open(json_file, 'r') as f:
            coflow_trace = json.load(f)

        for coflow in coflow_trace['coflows']:
            
            for flow in coflow['flows']:
                src_ip = flow['src_ip']
                src_port = flow['src_port']
                dst_ip = flow['dst_ip']
                dst_port = flow['dst_port']

                flow_key_tuple = (src_ip, src_port, dst_ip, dst_port)
                flow_mac = flow_mac_dict[flow_key_tuple]

                flow['src_mac'] = flow_mac

                
        with open(output_file_path, 'w') as f:
            json.dump(coflow_trace, f, indent=2)

        return output_file_path
    

    def run(self, json_file_path: str, output_dir: str) -> str:

        self.json_file_name_without_extension = Path(os.path.basename(json_file_path)).stem

        output_file = f'{self.json_file_name_without_extension}_MACs.json'

        output_file_path = os.path.join(output_dir, output_file)

        output_file_path = self.add_MACs_to_coflow_trace(json_file_path, output_file_path)

        return output_file_path
    

if __name__ == "__main__":

    coflow_trace_dir = '/mnt/traces/emil/json_traces/complete_traces/'
    coflow_trace_filename = '2000-0.9-FB-UP_ports_Facebook_HadoopDist_All_size_IPs_complete.json'
    coflow_trace_path = os.path.join(coflow_trace_dir, coflow_trace_filename)

    output_dir = '/mnt/traces/emil/json_traces/traces_with_mac'

    output_file = AddMACsToCoflowTrace().run(coflow_trace_path, output_dir)

    print(f"Output file: {output_file}")
    