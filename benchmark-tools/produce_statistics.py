import os
import argparse
import re
import sys
import ijson
import json
from statistics import mean, variance, stdev, median
from multiprocessing import Pool, cpu_count

def timestamp_generator(file_path):
    with open(file_path, 'rb') as f:
        objects = ijson.items(f, 'delay_timestamps.item')
        for obj in objects:
            yield obj

def get_first_packet_delays(timestamps, destination_ip):
    first_packet_delay_base = {}
    first_packet_delay_associated = {}
    pkt_id_dict_base = {}
    pkt_id_dict_associated = {}
    unique_flow_keys = set()
    
    for packet in timestamps:
        source_port = packet['source_port']
        destination_port = packet['destination_port']
        source_ip = packet['source_ip']
        pkt_id = packet['pkt_id']
        unique_flow_key = (source_ip, source_port, destination_ip, destination_port)
        unique_flow_keys.add(unique_flow_key)  # Track unique keys
        string_key = str(unique_flow_key)
        if destination_port == 2100:
            dict_to_use = pkt_id_dict_base
            delays_dict = first_packet_delay_base
        else:
            dict_to_use = pkt_id_dict_associated
            delays_dict = first_packet_delay_associated

        if string_key in dict_to_use:
            if dict_to_use[string_key] > pkt_id:
                dict_to_use[string_key] = pkt_id
                delays_dict[string_key] = packet['delta']
        else:
            dict_to_use[string_key] = pkt_id
            delays_dict[string_key] = packet['delta']

    return first_packet_delay_base, first_packet_delay_associated, len(unique_flow_keys)

def process_file(file_path):
    with open(file_path, 'rb') as f:
        pod_id = next(ijson.items(f, 'pod_id'))
        f.seek(0)
        destination_ip = next(ijson.items(f, 'IP_address'))

    timestamps = list(timestamp_generator(file_path))
    deltas = [item['delta'] for item in timestamps]
    first_packet_delays_base, first_packet_delays_associated, unique_flow_count = get_first_packet_delays(timestamps, destination_ip)
    nr_of_packets = len(deltas)  # Number of packets is the length of deltas
    return pod_id, deltas, first_packet_delays_base, first_packet_delays_associated, unique_flow_count, nr_of_packets

def aggregate_statistics(delta_values):
    if not delta_values:
        # Handle empty list to avoid division by zero and other statistical errors
        return {
            'min': float('inf'), 'max': float('-inf'), 'mean': 0, 'variance': 0,
            'std_dev': 0, 'coeff_of_var': 0, 'median': 0
        }
    calculated_mean = mean(delta_values)
    calculated_std_dev = stdev(delta_values)
    calculated_variance = variance(delta_values)
    calculated_median = median(delta_values)
    calculated_coeff_of_var = (calculated_std_dev / calculated_mean) if calculated_mean != 0 else 0  # Handle division by zero

    return {
        'min': min(delta_values),
        'max': max(delta_values),
        'mean': calculated_mean,
        'median': calculated_median,
        'std_dev': calculated_std_dev,
        'variance': calculated_variance,
        'coefficient_of_variation': calculated_coeff_of_var
    }

def worker(file_path):
    pod_id, deltas, first_packet_delays_base, first_packet_delays_associated, unique_flow_count, nr_of_packets = process_file(file_path)
    base_values = list(first_packet_delays_base.values())
    associated_values = list(first_packet_delays_associated.values())
    return {
        'pod_id': pod_id,
        'deltas': deltas,
        'first_packet_delays_base': first_packet_delays_base,
        'first_packet_delays_associated': first_packet_delays_associated,
        'statistics': aggregate_statistics(deltas),
        'base_statistics': aggregate_statistics(base_values),
        'associated_statistics': aggregate_statistics(associated_values),
        'unique_flow_count': unique_flow_count,
        'number_of_packets': nr_of_packets
    }

def process_directory(directory: str):
    pool = Pool(processes=cpu_count())
    files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.json')]
    results = pool.map(worker, files)
    pool.close()
    pool.join()

    aggregated_deltas = []
    aggregated_base_delays = []
    aggregated_associated_delays = []
    pod_statistics = {}
    all_base_delays = {}
    all_associated_delays = {}
    total_unique_flows = 0
    total_packets = 0
    
    for result in results:
        aggregated_deltas.extend(result['deltas'])
        aggregated_base_delays.extend(list(result['first_packet_delays_base'].values()))
        aggregated_associated_delays.extend(list(result['first_packet_delays_associated'].values()))
        pod_statistics[result['pod_id']] = result['statistics']
        all_base_delays.update(result['first_packet_delays_base'])
        all_associated_delays.update(result['first_packet_delays_associated'])
        total_unique_flows += result['unique_flow_count']
        total_packets += result['number_of_packets']

    overall_stats = aggregate_statistics(aggregated_deltas)
    overall_base_stats = aggregate_statistics(aggregated_base_delays)
    overall_associated_stats = aggregate_statistics(aggregated_associated_delays)
    return overall_stats, overall_base_stats, overall_associated_stats, pod_statistics, all_base_delays, all_associated_delays, total_unique_flows, total_packets

def produce_statistics(delay_entries_dir: str, output_directory: str, run: int):
    print(f'Producing statistics for run {run} in directory {os.path.basename(delay_entries_dir)}')
    overall_stats, overall_base_stats, overall_associated_stats, pod_stats, all_base_delays, all_associated_delays, total_unique_flows, total_packets = process_directory(delay_entries_dir)
    result = {
        "run_number": run,
        "total_unique_flow_keys": total_unique_flows,
        "total_packets": total_packets, 
        "aggregated_delay_statistics": overall_stats,
        "aggregated_base_first_packet_statistics": overall_base_stats,
        "aggregated_associated_first_packet_statistics": overall_associated_stats,
        "pod_statistics": pod_stats,
        "base_first_packet_delays": all_base_delays,
        "associated_first_packet_delays": all_associated_delays
    }

    os.makedirs(output_directory, exist_ok=True)
    filename = f"statistics_run_{run}.json"
    output_file_path = os.path.join(output_directory, filename)

    with open(output_file_path, 'w') as f:
        json.dump(result, f, indent=4)

    print(f"Statistics for run {run} written to {output_file_path}")

def main():
    parser = argparse.ArgumentParser(description="Process a directory of JSON files for network delay statistics.")
    parser.add_argument("--directory", type=str, help="Directory containing JSON files")
    parser.add_argument('--output_directory', type=str, help='Output directory for statistics.')

    args = parser.parse_args()
    directory = args.directory
    output_directory = args.output_directory

    for entry in os.listdir(directory):
        delay_entries_dir = os.path.join(directory, entry)
        match = re.search(r'delay-entries-run-(\d+)$', entry)
        if match:
            run_number = int(match.group(1))
            if os.path.isdir(delay_entries_dir):
                produce_statistics(delay_entries_dir, output_directory, run_number)

if __name__ == "__main__":
    main()
