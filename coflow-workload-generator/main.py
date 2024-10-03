import os
import humanize
import argparse

from pathlib import Path
from time import perf_counter

from merge_pcaps import merge_pcap_files
import trace_producer, parse_trace, add_ports_to_trace, add_flow_size_JSON, create_pcap_file_CDF, add_IPs_JSON, add_MAC_JSON, adjust_coflowiness, copy_file, add_date, adjust_mean, uppdate_metadata


class CreateCoflowTrace:

    def run(self, coflows: int, NUM_PODS: int, coflowiness: float, unique_flows: int, load_factor: float, cores: int, flow_size_distribution_file_path: str, merge: bool):

        # Check if the directories exist
        self.check_if_dirs_exists()

        print(f'\nStarting to generate a trace with {NUM_PODS} pods, coflowiness {coflowiness}, {unique_flows} max unique flows, and flow size distribution {os.path.basename(flow_size_distribution_file_path)}')

        print(f'\nRunning Sincronia trace producer with {coflows} coflows, ALPHA=FB-UP, and load factor {load_factor}')

        path_to_sincronia_trace = trace_producer.run(NUM_COFLOWS=coflows, ALPHA='FB-UP', LOAD_FACTOR=load_factor)

        print(f'\nPath to Sincronia trace file: {path_to_sincronia_trace}')

        print(f'\nParsing the trace file: {path_to_sincronia_trace}')
        
        # Parse the trace
        json_coflow_trace_file_path = parse_trace.ParseTrace().run(path_to_sincronia_trace, self.json_parsed_dir)

        print(f"\nTrace parsed to JSON: {json_coflow_trace_file_path}")

        # Change mean coflow length to 100 

        print(f"\nAdjusting mean coflow length to 100 in {json_coflow_trace_file_path}")

        json_coflow_trace_file_path_with_mean = adjust_mean.AdjustMean().run(json_coflow_trace_file_path, self.mean_dir)

        print(f"\nMean adjusted to 100 and saved to {json_coflow_trace_file_path_with_mean}")
                  
        # add ports to the trace

        print(f"\nAdding ports to file: {json_coflow_trace_file_path_with_mean}")

        json_coflow_trace_file_path_with_ports = add_ports_to_trace.AddPortsToCoflowTrace().run(json_coflow_trace_file_path_with_mean, self.json_port_dir)
    
        print(f'\nPorts added to trace and saved to {json_coflow_trace_file_path_with_ports}')

        print(f'\nAdding IPs and base flows to {json_coflow_trace_file_path_with_ports}')

        json_coflow_trace_file_path_with_IPs = add_IPs_JSON.AddIPsToCoflowTrace().run(json_coflow_trace_file_path_with_ports, self.ip_dir, NUM_PODS=NUM_PODS)

        print(f'\nIPs and base flows added to trace and saved to {json_coflow_trace_file_path_with_IPs}')

        print(f'\nAdjusting coflowiness to {coflowiness} in {json_coflow_trace_file_path_with_IPs}')

        json_coflow_trace_file_path_with_adjusted_coflowiness = adjust_coflowiness.AdjustCoflowiness().run(json_coflow_trace_file_path_with_IPs, self.coflowiness_dir, coflowiness, unique_flows)

        print(f'\nCoflowiness adjusted to {coflowiness} and saved to {json_coflow_trace_file_path_with_adjusted_coflowiness}')

        print(f'\nAdding MACs to {json_coflow_trace_file_path_with_adjusted_coflowiness}')

        json_coflow_trace_file_path_with_MACs = add_MAC_JSON.AddMACsToCoflowTrace().run(json_coflow_trace_file_path_with_adjusted_coflowiness, self.mac_dir)

        print(f'\nMACs added to trace and saved to {json_coflow_trace_file_path_with_MACs}')

        print(f'\nAdding flow sizes to {json_coflow_trace_file_path_with_MACs}')

        json_trace_with_flow_sizes = add_flow_size_JSON.AddSizeToCoflowTrace().run(json_coflow_trace_file_path_with_MACs, flow_size_distribution_file_path, self.flow_size_dir)

        print(f'\nFlow sizes added to trace and saved to {json_trace_with_flow_sizes}')

        print(f'\nUpdating metadata in {json_trace_with_flow_sizes}')

        json_trace_with_updated_metadata = uppdate_metadata.UpdateMetadata().run(json_file_path=json_trace_with_flow_sizes, output_dir=self.updated_metadata_dir, NUM_PODS=NUM_PODS)

        # Add date to the trace file with format %Y-%m-%d
        complete_json_trace = add_date.add_date(json_trace_with_updated_metadata)

        print(f'\nComplete JSON trace saved to: {complete_json_trace}')

        # when complete_json_trace is generated, copy it to the complete_json_dir
        copy_file.copy_file_to_directory(complete_json_trace, self.complete_json_dir)

        # Generate the pcap file
    
        print(f"\nGenerating pcap file from {complete_json_trace}\n")

        pcap_file_paths = create_pcap_file_CDF.CoflowTraceGenerator().run(complete_json_trace, self.pcap_dir, cores)

        for i, pcap_file_path in enumerate(pcap_file_paths):
            print(f"\nPcap file {i} saved to: {pcap_file_path}")
            print(f"Size of pcap file {i}: {humanize.naturalsize(os.path.getsize(pcap_file_path))}\n")
        
        if merge and len(pcap_file_paths) > 1:
            filename_without_extension = Path(complete_json_trace).stem
            merged_pcap_file_path = f'{os.path.join(self.pcap_dir, f"merged_{os.path.basename(filename_without_extension)}.pcap")}'
            output_file = merge_pcap_files(pcap_file_paths, merged_pcap_file_path)
            print(f"Size of merged pcap file: {humanize.naturalsize(os.path.getsize(output_file))}\n")

    
    def check_if_dirs_exists(self):

        #self.data_dir = os.path.join(os.getcwd(), "data")
        
        self.data_dir = '/mnt/traces/emil/'
        self.json_dir = os.path.join(self.data_dir, "json_traces")
        self.json_parsed_dir = os.path.join(self.json_dir, "parsed_traces")
        self.mean_dir = os.path.join(self.json_dir, "mean")
        self.json_port_dir = os.path.join(self.json_dir, "ports")
        self.flow_size_dir = os.path.join(self.json_dir, "traces_with_size")
        self.mac_dir = os.path.join(self.json_dir, "traces_with_MAC")
        self.coflowiness_dir = os.path.join(self.json_dir, "adjusted_coflowiness")
        self.updated_metadata_dir = os.path.join(self.json_dir, "updated_metadata")
        self.complete_json_dir = os.path.join(self.json_dir, "complete_traces")
        self.ip_dir = os.path.join(self.json_dir, "traces_with_IPs")
        self.pcap_dir = os.path.join(self.data_dir, "pcap_traces")
        self.coflowiness_pcap_dir = os.path.join(self.pcap_dir, "adjusted_coflowiness")
        self.CDFs_dir = os.path.join(self.data_dir, "CDFs")

        dirs = [
            self.data_dir,
            self.json_dir,
            self.json_parsed_dir,
            self.mean_dir,
            self.json_port_dir,
            self.flow_size_dir,
            self.mac_dir,
            self.coflowiness_dir,
            self.updated_metadata_dir,
            self.complete_json_dir,
            self.ip_dir,
            self.pcap_dir,
            self.coflowiness_pcap_dir,
            self.CDFs_dir
        ]

        for dir in dirs:
            if not os.path.exists(dir):
                os.makedirs(dir)
                print(f"Created directory: {dir}")
            else:
                print(f"Directory already exists: {dir}")


if __name__ == "__main__":

    flow_size_distributions_dir = os.path.join(os.getcwd(), "data", "CDFs")
    flow_size_distributions_file_name = "Facebook_HadoopDist_All.txt"
    flow_size_distribution_file_path = os.path.join(flow_size_distributions_dir, flow_size_distributions_file_name) 

    # check if the flow size distribution file exists
    if not os.path.exists(flow_size_distribution_file_path):
        print(f"Error: Flow size distribution file '{flow_size_distribution_file_path}' does not exist.")
        exit(1)

    parser = argparse.ArgumentParser(description='Generate a trace with a specific number of destinationn pods and flow size distribution.')

    parser.add_argument('--coflows', type=int, default=10, help='Number of coflows to generate. (default: 10)')
    parser.add_argument('--NUM_PODS', type=int, default=8, help='Number of dst IPs to include in trace. (default: 8)')
    parser.add_argument('--coflowiness', type=float, default=0.9, help='Coflowiness between 0 and 1. (default: 0.9)')   
    parser.add_argument('--unique-flows', type=int, default=193000, help='Number of unique flows to generate. (default: 193000)')
    parser.add_argument('--load-factor', type=float, default=0.9, help='Load factor between 0 and 1. (default: 0.9)')
    parser.add_argument('--flow-size-distribution', type=str, default=flow_size_distribution_file_path, help='Path to flow size distribution file')
    parser.add_argument('--cores', type=int, default=1, help='Number of cores to use. (default: 1)')
    parser.add_argument('--merge', type=bool, default=False, help='Merge pcap files. (default: False)')

    args = parser.parse_args()

    coflows = args.coflows
    NUM_PODS = args.NUM_PODS
    coflowiness = args.coflowiness
    unique_flows = args.unique_flows
    load_factor = args.load_factor
    flow_size_distribution_file_path = args.flow_size_distribution
    cores = args.cores
    merge = args.merge 

    if coflowiness < 0.1 or coflowiness > 0.9:
        print("Coflowiness should be between 0 and 1.")
        ValueError("Coflowiness should be between 0 and 1.")
        exit(1)

    start = perf_counter()

    CreateCoflowTrace().run(
        coflows=coflows,
        NUM_PODS=NUM_PODS,
        coflowiness=coflowiness,
        unique_flows=unique_flows,
        load_factor=load_factor,
        cores=cores,
        flow_size_distribution_file_path=flow_size_distribution_file_path,
        merge=merge)

    end = perf_counter()

    print(f"\n\nTime taken to generate the trace: {end - start} seconds")
    