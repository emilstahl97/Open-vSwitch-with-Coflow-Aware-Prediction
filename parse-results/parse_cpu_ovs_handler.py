import os
import csv

def filter_cpu_stats(input_file):

    # Extract directory and base name from input file
    dir_name = os.path.dirname(input_file)
    base_name = os.path.basename(input_file)
    
    # Construct the output filename by prepending 'filtered_handlers'
    output_file = 'filtered_handlers_' + base_name.replace('.txt', '.csv')

    headers = ['Time', '%usr', '%sys', '%CPU']

    with open(input_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(headers)  # Write the headers

        for line in infile:
            parts = line.strip().split()  # Using strip to remove any leading/trailing whitespace
            if len(parts) > 9 and "handler" in parts[-1] and parts[0] != "Average:":  # Check conditions
                print(parts)
                time = parts[0]
                usr = parts[5] 
                sys = parts[6]  
                cpu = parts[9] 
                writer.writerow([time, usr, sys, cpu])

    print("Filtered data has been written to", output_file)

# Define the full path to the input file and output file
input_filename = '/home/emilstahl/DA240X/Benchmark/results/cpu-bench-results/Facebook-Hadoop/all/cpu_ovs/associate/associated-Facebook-Hadoop-0.9-coflowiness_cpu_ovs.txt'

filter_cpu_stats(input_filename)