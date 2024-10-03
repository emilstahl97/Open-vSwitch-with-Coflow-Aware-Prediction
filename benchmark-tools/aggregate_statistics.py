import argparse
import os
import json
import statistics

def parse_json_files(directory):
    # Dictionaries to store lists of values from all files for computation
    aggregated_delay_stats = {
        'min': [],
        'max': [],
        'mean': []
    }
    first_base_packet_delay_stats = {
        'min': [],
        'max': [],
        'mean': []
    }

    first_associated_packet_delay_stats = {
        'min': [],
        'max': [],
        'mean': []
    }

    # List to store all first packet delay values
    all_first_base_packet_delays = []
    all_first_associated_packet_delays = []
    
    # Dictionary to hold per-run statistics
    run_stats = {}

    # Traverse the directory
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r') as file:
                data = json.load(file)
                
                # Extract needed statistics for aggregated delays
                aggregated_delay_stats['min'].append(data['aggregated_delay_statistics']['min'])
                aggregated_delay_stats['max'].append(data['aggregated_delay_statistics']['max'])
                aggregated_delay_stats['mean'].append(data['aggregated_delay_statistics']['mean'])

                # Extract needed statistics for first packet delays
                first_base_packet_delay_stats['min'].append(data['aggregated_base_first_packet_statistics']['min'])
                first_base_packet_delay_stats['max'].append(data['aggregated_base_first_packet_statistics']['max'])
                first_base_packet_delay_stats['mean'].append(data['aggregated_base_first_packet_statistics']['mean'])

                first_associated_packet_delay_stats['min'].append(data['aggregated_associated_first_packet_statistics']['min'])
                first_associated_packet_delay_stats['max'].append(data['aggregated_associated_first_packet_statistics']['max'])
                first_associated_packet_delay_stats['mean'].append(data['aggregated_associated_first_packet_statistics']['mean'])

                # Append all individual packet delay values
                all_first_base_packet_delays.extend(data['base_first_packet_delays'].values())
                all_first_associated_packet_delays.extend(data['associated_first_packet_delays'].values())

                # Record detailed individual run statistics
                run_number = "run_" + str(data['run_number'])
                run_stats[run_number] = {
                    "aggregated_delay_statistics": {
                        "min": data['aggregated_delay_statistics']['min'],
                        "max": data['aggregated_delay_statistics']['max'],
                        "mean": data['aggregated_delay_statistics']['mean'],
                        "median": data['aggregated_delay_statistics']['median'],
                        "std_dev": data['aggregated_delay_statistics']['std_dev'],
                        "variance": data['aggregated_delay_statistics']['variance'],
                        "coefficient_of_variation": data['aggregated_delay_statistics']['coefficient_of_variation']
                    },
                    "aggregated_base_first_packet_statistics": {
                        "min": data['aggregated_base_first_packet_statistics']['min'],
                        "max": data['aggregated_base_first_packet_statistics']['max'],
                        "mean": data['aggregated_base_first_packet_statistics']['mean'],
                        "median": data['aggregated_base_first_packet_statistics']['median'],
                        "std_dev": data['aggregated_base_first_packet_statistics']['std_dev'],
                        "variance": data['aggregated_base_first_packet_statistics']['variance'],
                        "coefficient_of_variation": data['aggregated_base_first_packet_statistics']['coefficient_of_variation']
                    },
                    "aggregated_associated_first_packet_statistics": {
                        "min": data['aggregated_associated_first_packet_statistics']['min'],
                        "max": data['aggregated_associated_first_packet_statistics']['max'],
                        "mean": data['aggregated_associated_first_packet_statistics']['mean'],
                        "median": data['aggregated_associated_first_packet_statistics']['median'],
                        "std_dev": data['aggregated_associated_first_packet_statistics']['std_dev'],
                        "variance": data['aggregated_associated_first_packet_statistics']['variance'],
                        "coefficient_of_variation": data['aggregated_associated_first_packet_statistics']['coefficient_of_variation']
                    }
                }

    # Calculate statistics for each set of data
    result = {
        'aggregated_delay_statistics': {},
        'aggregated_first_base_packet_delay_statistics': {},
        'aggregated_first_associated_packet_delay_statistics': {},
    }
    
    for key, values in aggregated_delay_stats.items():
        if values:
            mean_value = statistics.mean(values)
            std_dev_value = statistics.stdev(values)
            result['aggregated_delay_statistics'][key + '_std_dev'] = std_dev_value
            result['aggregated_delay_statistics'][key + '_cv'] = std_dev_value / mean_value if mean_value != 0 else float('inf')
            result['aggregated_delay_statistics'][key + '_min'] = min(values)
            result['aggregated_delay_statistics'][key + '_max'] = max(values)

    for key, values in first_base_packet_delay_stats.items():
        if values:
            mean_value = statistics.mean(values)
            std_dev_value = statistics.stdev(values)
            result['aggregated_first_base_packet_delay_statistics'][key + '_std_dev'] = std_dev_value
            result['aggregated_first_base_packet_delay_statistics'][key + '_cv'] = std_dev_value / mean_value if mean_value != 0 else float('inf')
            result['aggregated_first_base_packet_delay_statistics'][key + '_min'] = min(values)
            result['aggregated_first_base_packet_delay_statistics'][key + '_max'] = max(values)

    for key, values in first_associated_packet_delay_stats.items():
        if values:
            mean_value = statistics.mean(values)
            std_dev_value = statistics.stdev(values)
            result['aggregated_first_associated_packet_delay_statistics'][key + '_std_dev'] = std_dev_value
            result['aggregated_first_associated_packet_delay_statistics'][key + '_cv'] = std_dev_value / mean_value if mean_value != 0 else float('inf')
            result['aggregated_first_associated_packet_delay_statistics'][key + '_min'] = min(values)
            result['aggregated_first_associated_packet_delay_statistics'][key + '_max'] = max(values)

    # Compute the standard deviation and CV for all first packet delays
    if all_first_base_packet_delays:
        mean_all_first_packet_delays = statistics.mean(all_first_base_packet_delays)
        std_dev_all_first_packet_delays = statistics.stdev(all_first_base_packet_delays)
        result['first_base_packet_delay_overall_std_dev'] = std_dev_all_first_packet_delays
        result['first_base_packet_delay_overall_cv'] = std_dev_all_first_packet_delays / mean_all_first_packet_delays if mean_all_first_packet_delays != 0 else float('inf')
    
    if all_first_associated_packet_delays:
        mean_all_first_packet_delays = statistics.mean(all_first_associated_packet_delays)
        std_dev_all_first_packet_delays = statistics.stdev(all_first_associated_packet_delays)
        result['first_associated_packet_delay_overall_std_dev'] = std_dev_all_first_packet_delays
        result['first_associated_packet_delay_overall_cv'] = std_dev_all_first_packet_delays / mean_all_first_packet_delays if mean_all_first_packet_delays != 0 else float('inf')
    
    # Place the run specific stats under 'run_stats'
    result['run_stats'] = run_stats
    
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a directory of JSON files for network delay statistics.")
    parser.add_argument("--directory", type=str, help="Directory containing JSON files")
    parser.add_argument('--output_directory', type=str, help='Output directory for statistics.')

    args = parser.parse_args()
    directory = args.directory
    output_directory = args.output_directory

    result = parse_json_files(directory)

    output_file_path = os.path.join(output_directory, 'aggregated_statistics.json')
    
    # Create the output directory if it does not exist
    os.makedirs(output_directory, exist_ok=True)

    # Write the result statistics to a new JSON file
    with open(output_file_path, 'w') as outfile:
        json.dump(result, outfile, indent=4)

    print(f"Aggregated statistics written to {output_file_path}")
