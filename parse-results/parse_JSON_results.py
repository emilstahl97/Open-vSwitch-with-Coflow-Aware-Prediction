import os
import json
import re

def list_json_files(directory):
    """ List all JSON files in the specified directory. """
    return [f for f in os.listdir(directory) if f.endswith('.json')]

def read_json(file_path):
    """ Read and return the JSON content from the file. """
    with open(file_path, 'r') as file:
        return json.load(file)

def select_option(prompt, options):
    """ Generic function for allowing the user to select an option. """
    print(prompt)
    for idx, option in enumerate(options):
        print(f"{idx + 1}. {option}")
    selection = int(input("Enter your choice: ")) - 1
    return options[selection]

def extract_float_key(name):
    """ Extract the float key and coflowiness from the benchmark name. """
    match = re.search(r'(\d+\.\d+)', name)
    if match:
        return float(match.group(1)), match.group(0)
    return None

def process_files(directory):
    """ Process all JSON files in the directory to .dat format. """
    files = list_json_files(directory)
    if not files:
        print("No JSON files found in the directory.")
        return
    
    flow_size_distribution = input("Enter the flow size distribution: ")

    # Get run keys from the first JSON file (assuming all JSONs are consistent)
    sample_data = read_json(os.path.join(directory, files[0]))
    run_keys = list(sample_data['run_stats'].keys())
    
    # Select a statistic group and specific statistic
    first_run_data = sample_data['run_stats'][run_keys[0]]
    stat_groups = list(first_run_data.keys())
    chosen_group = select_option("Choose a statistic group:", stat_groups)
    stats = list(first_run_data[chosen_group].keys())
    chosen_stat = select_option("Choose the specific statistic:", stats)

    # Define output filename based on chosen group and statistic
    output_filename = f"{flow_size_distribution}_{chosen_stat}_{chosen_group}.dat"

    # Gather data including extracted float keys and sort by them
    benchmark_data = []
    for json_file in files:
        data = read_json(os.path.join(directory, json_file))
        float_key = extract_float_key(data['benchmark_name'])
        if float_key:
            benchmark_data.append((float_key, json_file))

    # Sort by the float part of the benchmark names
    benchmark_data.sort()

    # Open a .dat file for output
    with open(output_filename, 'w') as dat_file:
        headers = ["Run_Number"]  # Start with a Run_Number header
        sorted_files = [b[1] for b in benchmark_data]
        # Remove the quotes from headers
        headers.extend([extract_float_key(read_json(os.path.join(directory, f))['benchmark_name'])[1] for f in sorted_files])
        dat_file.write("\t".join(headers) + "\n")

        # Collect data for each run and write rows
        for run_key in run_keys:
            row = [run_key.replace('run_', '')]  # Extract the run number part and use it
            for json_file in sorted_files:
                data = read_json(os.path.join(directory, json_file))
                try:
                    value = data['run_stats'][run_key][chosen_group][chosen_stat]
                except KeyError:
                    value = 'NaN'
                row.append(str(value))
            dat_file.write("\t".join(row) + "\n")

    print(f"Data written to {output_filename}")



if __name__ == '__main__':
    directory_path = '/home/emilstahl/DA240X/Benchmark/results/prediction-runs/Facebook-Hadoop-Prediction-Run-Min-Max-Results/aggregated-results-Min-Max-Facebook-Hadoop/'
    process_files(directory_path)
