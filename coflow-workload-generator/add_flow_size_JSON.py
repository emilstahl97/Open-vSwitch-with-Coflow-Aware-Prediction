import json
import os
import random
import sys

from generate_bytes_from_CDF import CDFGenerator

class AddSizeToCoflowTrace:

    def add_size_to_coflow_trace(self, json_file: str, output_file_path: str):
        if not os.path.exists(json_file):
            print(f"File '{json_file}' not found.")
            return

        # Load JSON coflow trace
        with open(json_file, 'r') as f:
            coflow_trace = json.load(f)

        # Update JSON coflow trace with source and destination ports
        for coflow in coflow_trace['coflows']:
            for flow in coflow['flows']:
                # Generate the byte size for the flow
                flow_size_bytes = self.cdf_generator.generate_byte_size()
                # Add byte size to flow
                flow['flow_size_bytes'] = flow_size_bytes

        with open(output_file_path, 'w') as f:
            json.dump(coflow_trace, f, indent=2)

        return output_file_path
    
    def run(self, json_file_path: str, CDF_file_path: str, output_dir: str) -> str:

        self.json_file_name_without_extension = os.path.splitext(os.path.basename(json_file_path))[0]

        self.CDF_file_without_extension = os.path.splitext(os.path.basename(CDF_file_path))[0]

        output_file = f'{self.json_file_name_without_extension}_{self.CDF_file_without_extension}_size.json'
        output_file_path = os.path.join(output_dir, output_file)

        self.cdf_generator = CDFGenerator(CDF_file_path)

        output_file_path = self.add_size_to_coflow_trace(json_file_path, output_file_path)

        return output_file_path
    

if __name__ == "__main__":

    coflow_trace_dir = '/home/emilstahl/DA240X/Benchmark/workload-generator/data/json_traces/parsed_traces'
    coflow_trace_filename = '2000-0.9-FB-UP.json'
    coflow_trace_path = os.path.join(coflow_trace_dir, coflow_trace_filename)

    CDF_dir = '/home/emilstahl/DA240X/Benchmark/workload-generator/data/CDFs'
    CDF_filename = 'Facebook_HadoopDist_All.txt'
    CDF_file_path = os.path.join(CDF_dir, CDF_filename)

    output_dir = '/home/emilstahl/DA240X/Benchmark/workload-generator/data/json_traces/traces_with_size'

    AddSizeToCoflowTrace().run(coflow_trace_path, CDF_file_path, output_dir)