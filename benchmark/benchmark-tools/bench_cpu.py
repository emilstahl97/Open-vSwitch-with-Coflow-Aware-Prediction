import argparse
import os
import shutil
import subprocess
import re
import logging
from datetime import datetime
import sys

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def execute_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.stderr:
            logging.error(f"STDERR for '{command}': {result.stderr}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {command} with error: {e}")
        return None


def start_cpu_monitoring():
    """Start CPU monitoring using separate pidstat commands for each process."""
    logging.info("Starting CPU monitoring for OVS.")
    commands = [
        "rm -f /var/tmp/cpu_ovs.txt /var/tmp/cpu_mpstat.txt",
        "nohup pidstat -u -t -p $(pidof ovs-vswitchd) 1 > /var/tmp/cpu_ovs.txt 2> /dev/null &",
        "nohup pidstat -u -t -p $(pidof ovsdb-server) 1 >> /var/tmp/cpu_ovs.txt 2> /dev/null &",
        "nohup mpstat -P ALL 1 > /var/tmp/cpu_mpstat.txt 2> /dev/null &"
    ]
    for cmd in commands:
        execute_command(cmd)


def stop_cpu_monitoring():
    """Stop CPU monitoring by terminating pidstat and mpstat."""
    logging.info("Stopping CPU monitoring.")
    command = "kill -s INT `pidof pidstat`; kill -s INT `pidof mpstat`"
    execute_command(command)

def parse_cpu_stats_from_pidstat(output):
    """Parse pidstat output to extract CPU usage details for various OVS components."""
    cpu_details = {
        'pmd': 0.0,
        'revalidator': 0.0,
        'handler': 0.0,
        'urcu': 0.0,
        'other': 0.0
    }
    regex = re.compile(r"^Average:\s+\d+\s+-\s+\d+\s+\d+\.\d+\s+\d+\.\d+\s+(\d+\.\d+).+__(\w+)", re.MULTILINE)
    for match in regex.finditer(output):
        component = match.group(2)
        usage = float(match.group(1))
        key = component.split('_')[0]  # Get the prefix before underscore
        if key in cpu_details:
            cpu_details[key] += usage
        else:
            cpu_details['other'] += usage
    return cpu_details

def parse_cpu_stats_from_mpstat(output):
    """Parse mpstat output to extract system-wide CPU usage details."""
    regex = re.compile(r"^Average:\s+\d+\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)$", re.MULTILINE)
    match = regex.search(output)
    if match:
        return {
            'usr': float(match.group(1)),
            'nice': float(match.group(2)),
            'sys': float(match.group(3)),
            'iowait': float(match.group(4)),
            'irq': float(match.group(5)),
            'soft': float(match.group(6)),
            'steal': float(match.group(7)),
            'guest': float(match.group(8)),
            'gnice': float(match.group(9)),
            'idle': float(match.group(10))
        }
    return {}

def get_cpu_monitoring_stats():
    """Retrieve and parse CPU monitoring stats from temporary files."""
    logging.info("Fetching CPU monitoring statistics.")
    ovs_output = execute_command("cat /var/tmp/cpu_ovs.txt")
    mpstat_output = execute_command("cat /var/tmp/cpu_mpstat.txt")

    if ovs_output and mpstat_output:
        ovs_stats = parse_cpu_stats_from_pidstat(ovs_output)
        system_stats = parse_cpu_stats_from_mpstat(mpstat_output)
        logging.debug(f"OVS CPU Stats: {ovs_stats}")
        logging.debug(f"System CPU Stats: {system_stats}")
        return ovs_stats, system_stats
    return {}, {}

def move_and_rename_files(filename, destination):
    """Move and rename monitoring files to a specified directory."""
    source_files = ['/var/tmp/cpu_ovs.txt', '/var/tmp/cpu_mpstat.txt']
    for source in source_files:
        base_name = os.path.basename(source)
        new_name = f"{filename}_{base_name}"
        destination_path = os.path.join(destination, new_name)
        # remove the file if it already exists
        if os.path.exists(destination_path):
            os.remove(destination_path)
        shutil.move(source, destination_path)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Process a directory of JSON files for network delay statistics.")
    parser.add_argument("--coflowiness", type=float, required=True, help="Coflowiness value.")
    parser.add_argument('--flow_size_distribution', type=str, required=True, help='Flow size distribution.')
    parser.add_argument('--bench-type', type=str, required=True, help='Benchmark type (associated or base flows).')

    args = parser.parse_args()
    coflowiness = args.coflowiness
    flow_size_distribution = args.flow_size_distribution
    bench_type = args.bench_type

    cpu_bench_results_directory = "/home/emilstahl/DA240X/Benchmark/bench-tools/cpu-bench-results"
    coflowiness_dir = f'{coflowiness}-coflowiness'
    destination_directory = os.path.join(cpu_bench_results_directory, flow_size_distribution, coflowiness_dir)
    filename = f'{bench_type}-{flow_size_distribution}-{coflowiness}-coflowiness'
    
    # create the directory if it doesn't exist
    if not os.path.exists(destination_directory):
        os.makedirs(destination_directory)

    start_cpu_monitoring()
    input("Press Enter to stop monitoring...")    
    stop_cpu_monitoring()
    move_and_rename_files(filename, destination_directory)
    print("CPU monitoring stopped and files moved.")