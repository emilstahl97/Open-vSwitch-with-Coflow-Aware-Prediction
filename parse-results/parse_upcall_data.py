import re
import os

def parse_upcall_packets(input_filename, output_directory):
    # Ensure the output directory exists
    os.makedirs(output_directory, exist_ok=True)

    # Generate the output filename by appending 'parsed' before the extension and changing to .dat
    base_name = os.path.splitext(os.path.basename(input_filename))[0]
    output_filename = f"{base_name}_parsed.dat"
    output_filepath = os.path.join(output_directory, output_filename)

    # Open the input file for reading
    with open(input_filename, 'r') as infile:
        # Open the output file for writing
        with open(output_filepath, 'w') as outfile:
            # Read each line in the input file
            for line in infile:
                # Use regular expression to find the number after 'UPCALL packets diff:'
                match = re.search(r'UPCALL packets diff:\s*(\d+)', line)
                if match:
                    # Extract the number from the regular expression match group
                    upcall_packets_diff = match.group(1)
                    # Write the extracted number to the output file
                    outfile.write(upcall_packets_diff + '\n')

    print(f"Parsed data has been written to {output_filepath}")

# Example usage
# Replace 'yourfile.txt' with the actual filename you want to parse
# Replace 'your/output/directory' with the desired output directory path

coflowiness_values = [0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0]
output_directory = '/home/emilstahl/DA240X/Benchmark/results/upcalls-benchmark/Facebook-Hadoop/gnuplot_data_upcall_stats_Facebook_Hadoop'

for coflowiness in coflowiness_values:
    print(f"Processing coflowiness {coflowiness}")
    input_file = f'/home/emilstahl/DA240X/Benchmark/results/upcalls-benchmark/Facebook-Hadoop/raw_data/{coflowiness}-coflowiness/ovs_upcall_stats_coflowiness_{coflowiness}_Facebook-Hadoop_aggregated.txt'
    parse_upcall_packets(input_file, output_directory)