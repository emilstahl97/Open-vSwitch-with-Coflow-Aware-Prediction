
from pathlib import Path
import os
import json

from utils.check_coflowiness import CheckCoflowiness

class UpdateMetadata:

    def update_metadata(self, json_file: str, output_file_path: str, NUM_PODS: int) -> str:

        print(f"\nUpdating metadata for file: {Path(json_file)}")

        if not os.path.exists(json_file):
            print(f"File '{json_file}' not found.")
            raise FileNotFoundError
        
        total_base_flows, coflowiness, fraction_of_base_flows = CheckCoflowiness().check_coflowiness(json_file)

        # Load JSON coflow trace
        with open(json_file, 'r') as f:
            coflow_trace = json.load(f)

        flow_set = set()
        src_mac_set = set()
        total_src_ips = set()
        total_dst_ips = set()
        total_dst_ports = set()
        total_src_ports = set()
        total_flows = 0

        for coflow in coflow_trace['coflows']:
            
            src_ips = set()  # Store distinct source IPs
            dst_ips = set()  # Store distinct destination IPs
            num_flows = 0     # Counter for total flows

            for flow in coflow['flows']:
                src_ip = flow['src_ip']
                src_port = flow['src_port']
                dst_ip = flow['dst_ip']
                dst_port = flow['dst_port']
                
                if 'src_mac' in flow:
                    src_mac = flow['src_mac']
                    src_mac_set.add(src_mac)
                
                src_ips.add(src_ip)
                dst_ips.add(dst_ip)
                flow_set.add((src_ip, src_port, dst_ip, dst_port))

                total_src_ips.add(src_ip)
                total_dst_ips.add(dst_ip)
                total_dst_ports.add(dst_port)
                total_src_ports.add(src_port)

                num_flows += 1
                total_flows += 1

            # Update coflow metadata
            coflow['num_sources'] = len(src_ips)
            coflow['num_destinations'] = len(dst_ips)
            coflow['num_flows'] = num_flows

        if 'num_pods' not in coflow_trace:
            coflow_trace['num_pods'] = NUM_PODS

        #check if src_mac set is empty
        if not src_mac_set:
            len_src_mac_set = 0
        else:
            len_src_mac_set = len(src_mac_set)
        
        new_data = {
            "num_pods": coflow_trace['num_pods'],
            "num_coflows": len(coflow_trace['coflows']),
            "unique_flows": len(flow_set),
            "total_flows": total_flows,
            "unique_src_macs": len_src_mac_set,
            "total_base_flows": total_base_flows,
            "coflowiness": coflowiness,
            "fraction_of_base_flows": fraction_of_base_flows,
            "unique_src_ips": len(total_src_ips),
            "unique_src_ports": len(total_src_ports),
            "unique_dst_ips": len(total_dst_ips),
            "unique_dst_ports": len(total_dst_ports),
            "coflows": coflow_trace['coflows']
        }

        with open(output_file_path, 'w') as f:
            json.dump(new_data, f, indent=2)

        return output_file_path
    

    def run(self, json_file_path: str, output_dir: str, NUM_PODS: int = 8) -> str:

        self.json_file_name_without_extension = Path(os.path.basename(json_file_path)).stem

        output_file = f'{self.json_file_name_without_extension}_updated.json'

        output_file_path = os.path.join(output_dir, output_file)

        output_file_path = self.update_metadata(json_file_path, output_file_path, NUM_PODS)

        print(f"Updated metadata saved to: {output_file_path}")

        return output_file_path