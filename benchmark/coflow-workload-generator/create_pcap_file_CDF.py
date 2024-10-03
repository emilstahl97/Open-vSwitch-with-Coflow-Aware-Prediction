import os
import ijson

from scapy.all import wrpcap
from time import perf_counter
from multiprocessing import Manager, Process

from create_flow import generate_udp_traffic

class CoflowTraceGenerator:

    def __init__(self):
        self.manager = Manager()
        self.counter = self.manager.Value('i', 0)

    # Generate packets for each flow in the coflow
    def generate_coflow_packets(self, coflow):
        for flow in coflow["flows"]:

            src_ip = flow["src_ip"]
            dst_ip = flow["dst_ip"]

            src_port = int(flow["src_port"])
            dst_port = int(flow["dst_port"])

            src_mac = flow["src_mac"]

            flow_size_bytes = int(flow["flow_size_bytes"])

            # Generate the packets for the flow, returns a list of packets for the flow
            packets = generate_udp_traffic(src_ip, src_port, dst_ip, dst_port, src_mac, flow_size_bytes)

            yield packets


    def generate_trace_from_json_parallel(self, pid, json_file, coflow_ids, pcap_file):

        with open(json_file, 'r') as f:
            coflow_items = ijson.items(f, 'coflows.item')

            for coflow in coflow_items:
                coflow_id = coflow['coflow_id']
                if coflow_id in coflow_ids:
                    print(f"Process {pid}: Generating packets for coflow {coflow_id}")
                    yield from self.generate_coflow_packets(coflow)
                    self.counter.value += 1
                    print(f"Process {pid}: Finished generating packets for coflow {coflow_id}. {self.counter.value}/{self.nr_of_coflows} coflows generated.")
        
        print(f"Process {pid}: Finished generating all packets. Writing to pcap file {pcap_file}")
    
    def generate(self, pid, json_file, coflow_ids, pcap_file):
        trace_packets = self.generate_trace_from_json_parallel(pid, json_file, coflow_ids, pcap_file)
        self.save_trace_to_pcap(trace_packets, pcap_file)


    def save_trace_to_pcap(self, trace_packets, pcap_file):
        # Flatten the list of packets using a generator expression
        flat_packets = (pkt for sublist in trace_packets for pkt in sublist)
        
        # Write the flattened packets to the pcap file using Scapy's wrpcap
        wrpcap(pcap_file, flat_packets)

    
    def run(self, json_file_path, pcap_dir, cores: int = 1):

        json_file_without_extension = os.path.splitext(os.path.basename(json_file_path))[0]

        nr_of_coflows = self.get_number_of_coflows(json_file_path)

        self.nr_of_coflows = nr_of_coflows

        nr_of_workers = min(cores, os.cpu_count())

        print(f"\nGenerating {nr_of_coflows} coflows using {nr_of_workers} workers")

        list_of_coflow_ids = self.create_2d_list(nr_of_coflows, nr_of_workers)

        print(f"\nList of coflow id for each worker:")
        print(list_of_coflow_ids)

        process_list = []
        pcap_file_paths = []

        for pid, coflow_ids in enumerate(list_of_coflow_ids):
            pcap_file_name = f'{pid}_{json_file_without_extension}.pcap'
            pcap_file_paths.append(os.path.join(pcap_dir, pcap_file_name))
            pcap_file_path = os.path.join(pcap_dir, pcap_file_name)
            process = Process(target=self.generate, args=(pid, json_file_path, coflow_ids, pcap_file_path))
            process_list.append(process)

        start = perf_counter()

        for pid, process in enumerate(process_list):
            print(f"\nStarting process {pid}")
            process.start()

        for process in process_list:
            process.join()

        end = perf_counter()

        print(f"\nFinished generating {nr_of_coflows} coflows in {end - start} seconds")

        return pcap_file_paths
    

    def get_number_of_coflows(self, json_file):
            with open(json_file, 'r') as f:
                coflow_items = ijson.items(f, 'coflows.item')
                return sum(1 for _ in coflow_items)

    def create_2d_list(self, x, y):
        if y == 0:
            raise ValueError("Parameter 'y' must not be zero.")
        
        num_lists = min(x, y)
        step_size = x // num_lists
        remainder = x % num_lists
        
        result = []
        start = 0
        
        for i in range(num_lists):
            end = start + step_size + (1 if i < remainder else 0)
            result.append(list(range(start, end)))
            start = end
        
        return result
            


if __name__ == "__main__":

    json_file_path = '/mnt/traces/emil/production-traces/1000-Google-Search-RPC/adjusted_coflowiness/smaller-0.9_coflowiness/JSON/1000-Google-Search-RPC-0.9-coflowiness_smaller.json'

    directory_containing_file = os.path.dirname(json_file_path)

    parent_directory = os.path.dirname(directory_containing_file)

    pcap_dir = os.path.join(parent_directory, "pcap") 

    os.makedirs(pcap_dir, exist_ok=True)

    coflowTraceGenerator = CoflowTraceGenerator()
    pcap_file_path = coflowTraceGenerator.run(json_file_path, pcap_dir)

    print(f"Trace saved to {pcap_file_path}")