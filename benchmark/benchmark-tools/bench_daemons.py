import os
import logging
import subprocess

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

def get_process_pids():
    """Retrieve PIDs for processes matching a given name."""
    process_name = 'delay-daemon.py'
    pids = execute_command(f"pgrep -f {process_name}").strip().split()
    logging.info(f"Found PIDs for '{process_name}': {pids}")
    logging.info(f'Number of daemons: {len(pids)}')
    return pids

def start_cpu_monitoring(destination_directory):
    """Start CPU monitoring using pidstat for each process, writing to individual files."""
    logging.info("Starting CPU monitoring.")
    pids = get_process_pids()
    for index, pid in enumerate(pids, 1):
        if index > 8:
            break  # Limit to 8 files as per specification
        output_file = os.path.join(destination_directory, f"cpu_stats_daemon_{index}.txt")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)  # Ensure the directory exists
        open(output_file, 'w').close() if not os.path.exists(output_file) else None
        command = f"nohup pidstat -u -t -p {pid} 1 > {output_file} 2> /dev/null &"
        execute_command(command)

def stop_cpu_monitoring():
    """Stop CPU monitoring by terminating pidstat."""
    logging.info("Stopping CPU monitoring.")
    command = "kill -s INT `pidof pidstat`"
    execute_command(command)


if __name__ == "__main__":

    coflowiness = input('Specify coflowiness: ')
    #flow_size_distribution = input('Specify flow size distribution: ')
    flow_size_distribution = 'Google-Search-RPC'

    output_dir = "/home/emilstahl/DA240X/Benchmark/bench-tools/daemon-bench-results"
    coflowiness_dir = f'{coflowiness}-coflowiness'
    destination_directory = os.path.join(output_dir, flow_size_distribution, coflowiness_dir)
    
    # create the directory if it doesn't exist
    if not os.path.exists(destination_directory):
        os.makedirs(destination_directory)

    start_cpu_monitoring(destination_directory)
    input("Press Enter to stop monitoring...")    
    stop_cpu_monitoring()
    print("CPU monitoring stopped and files moved.")