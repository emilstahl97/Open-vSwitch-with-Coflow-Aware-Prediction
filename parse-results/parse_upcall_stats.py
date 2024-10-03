import subprocess
import time
import re
import argparse
import signal
import sys
from datetime import datetime

# Regex patterns to extract port, pod name, UPCALL packets, and errors
port_pattern = re.compile(r'port (\d+): (\S+)')
upcall_pattern = re.compile(r'UPCALL packets:(\d+)\s+errors:(\d+)')

def run_command():
    """Run the 'sudo ovs-appctl dpctl/show -s' command and return its output."""
    try:
        result = subprocess.run(['sudo', 'ovs-appctl', 'dpctl/show', '-s'], capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        print(f"Error running command: {e}")
        return ""

def parse_output(output):
    """Parse the output of the command to extract port, pod, UPCALL packets, and errors."""
    parsed_lines = []
    port_stats = {}

    # Split output into lines for sequential processing
    lines = output.splitlines()
    current_port = None

    # Iterate through lines and associate UPCALL stats with their respective port/pod
    for line in lines:
        port_match = port_pattern.search(line)
        if port_match:
            current_port, pod_name = port_match.groups()
        elif current_port and "UPCALL packets" in line:
            upcall_match = upcall_pattern.search(line)
            if upcall_match:
                upcall_packets, errors = upcall_match.groups()
                # Get the current time in hour:minute:second format
                current_time = datetime.now().strftime("%H:%M:%S")
                # Include the time, port, pod name, and stats in the output line
                parsed_lines.append(f"[{current_time}] port {current_port}: {pod_name}, UPCALL packets:{upcall_packets} errors:{errors}")
                # Update port stats with current values
                port_stats[current_port] = {'upcall_packets': int(upcall_packets), 'errors': int(errors)}
                # Reset current_port after processing to avoid mismatches
                current_port = None

    return parsed_lines, port_stats

def signal_handler(sig, frame):
    """Handle keyboard interrupt signal (Ctrl+C) to stop the script."""
    print("\nMonitoring stopped by user.")
    sys.exit(0)

def main(coflowiness, flow_size_distribution):
    # Define the output files with dynamic filenames based on input arguments
    output_file = f'ovs_upcall_stats_coflowiness_{coflowiness}_{flow_size_distribution}.txt'
    aggregated_output_file = f'ovs_upcall_stats_coflowiness_{coflowiness}_{flow_size_distribution}_aggregated.txt'
    
    # Clear the content of the files if they already exist
    open(output_file, 'w').close()
    open(aggregated_output_file, 'w').close()
    
    # Register the signal handler for interrupt signal
    signal.signal(signal.SIGINT, signal_handler)
    
    # Initialize previous stats for UPCALL packets and errors by port
    prev_port_stats = {}

    while True:
        output = run_command()
        if output:
            parsed_lines, current_port_stats = parse_output(output)
            
            # Calculate differences for each port from the previous stats
            differences = {}
            for port, stats in current_port_stats.items():
                if port in prev_port_stats:
                    diff_upcall_packets = stats['upcall_packets'] - prev_port_stats[port]['upcall_packets']
                    diff_errors = stats['errors'] - prev_port_stats[port]['errors']
                    differences[port] = {'diff_upcall_packets': diff_upcall_packets, 'diff_errors': diff_errors}
                else:
                    # If no previous stats exist, set the differences to the current values
                    differences[port] = {'diff_upcall_packets': stats['upcall_packets'], 'diff_errors': stats['errors']}

            # Write parsed lines to the individual output file
            with open(output_file, 'a') as f:
                for line in parsed_lines:
                    f.write(line + '\n')
            
            # Write aggregated data differences to the aggregated output file
            with open(aggregated_output_file, 'a') as f_agg:
                current_time = datetime.now().strftime("%H:%M:%S")
                total_packets_diff = sum([diffs['diff_upcall_packets'] for diffs in differences.values()])
                total_errors_diff = sum([diffs['diff_errors'] for diffs in differences.values()])
                f_agg.write(f"[{current_time}] UPCALL packets diff: {total_packets_diff}, errors diff: {total_errors_diff}\n")
                            
            # Update previous stats for the next iteration
            prev_port_stats = current_port_stats.copy()
        else:
            print("No output from command.")
        
        # Sleep for 1 second before running the command again
        time.sleep(1)

if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Monitor OVS UPCALL packets and errors.")
    parser.add_argument('--coflowiness', type=str, required=True, help='Specify the coflowiness value.')
    parser.add_argument('--flow_size_distribution', type=str, required=True, help='Specify the flow size distribution value.')
    
    args = parser.parse_args()

    # Call main function with parsed arguments
    main(args.coflowiness, args.flow_size_distribution)
