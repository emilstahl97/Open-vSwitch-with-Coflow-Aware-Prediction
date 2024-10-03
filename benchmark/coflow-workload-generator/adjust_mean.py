import os
import json
import argparse

from statistics import mean
from pathlib import Path
import sys

class AdjustMean:

    def __init__(self):
        self.target_mean = 300 # target mean coflow length

    def invert_number(self, n) -> float:
        if 0 <= n <= 1:
            return round(1 - n, 1)
        else:
            return "Number must be between 0 and 1."
     
    def adjust_mean(self, json_file: str, output_file_path: str) -> str:
        
        if not os.path.exists(json_file):
            print(f"File '{json_file}' not found.")
            raise FileNotFoundError

        # Load JSON coflow trace
        with open(json_file, 'r') as f:
            coflow_trace = json.load(f)

        coflow_lengths = []

        for coflow in coflow_trace['coflows']:
            
            num_flows = len(coflow['flows'])
            coflow_lengths.append(min(num_flows, self.target_mean))
            
            if num_flows > self.target_mean:
                new_coflow_length = self.get_new_coflow_length(coflow_lengths, target_mean=self.target_mean)
                coflow_lengths.append(new_coflow_length)
                coflow['flows'] = coflow['flows'][:new_coflow_length]


        with open(output_file_path, 'w') as f:
            json.dump(coflow_trace, f, indent=2)

        return output_file_path
    

    def get_mean_coflow_length(self, coflow_lengths) -> float:
        return sum(coflow_lengths) / len(coflow_lengths)


    def get_new_coflow_length(self, original_list, target_mean) -> int:
        new_value_count = len(original_list) + 1
        required_sum = target_mean * new_value_count
        additional_value = required_sum - sum(original_list)
        return additional_value
    

    def run(self, json_file_path: str, output_dir: str) -> str:

        self.json_file_name_without_extension = Path(os.path.basename(json_file_path)).stem

        output_file = f'{self.json_file_name_without_extension}_100_mean.json'

        output_file_path = os.path.join(output_dir, output_file)

        output_file_path = self.adjust_mean(json_file_path, output_file_path)

        mean_coflow_length = self.check_mean_coflow_length(output_file_path)

        print(f'New mean coflow length: {mean_coflow_length}')

        return output_file_path
    

    def check_mean_coflow_length(self, json_file: str) -> float:
    
        if not os.path.exists(json_file):
            print(f"File '{json_file}' not found.")
            raise FileNotFoundError

        # Load JSON coflow trace
        with open(json_file, 'r') as f:
            coflow_trace = json.load(f)

        coflow_lengths = []

        for coflow in coflow_trace['coflows']:
            num_flows = len(coflow['flows'])
            coflow_lengths.append(num_flows)

        mean_coflow_length = mean(coflow_lengths)
        return mean_coflow_length
    
    
    

if __name__ == "__main__":

    #argparser = argparse.ArgumentParser(description='Adjust mean coflow length of a trace.')
    #argparser.add_argument('--coflow-trace', type=str, help='Path to the coflow trace file.')
    #args = argparser.parse_args()

    #coflow_trace_path = args.coflow_trace
    coflow_trace_path = sys.argv[1]

    # check if coflow trace file exists
    if not os.path.exists(coflow_trace_path):
        print(f"File '{coflow_trace_path}' not found.")
        exit()

    output_dir = '/mnt/traces/emil/json_traces/mean'

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    adjusted_mean_output_file = AdjustMean().run(coflow_trace_path, output_dir)

    print(f'New mean coflow length: {AdjustMean().check_mean_coflow_length(adjusted_mean_output_file)}')

    print(f'Adjusted mean coflow trace saved to: {adjusted_mean_output_file}')