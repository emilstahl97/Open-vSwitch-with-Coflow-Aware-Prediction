import re
import os

def parse_directory(directory_path, output_directory):
    filename_regex = re.compile(r".*-(\d+\.\d+)-coflowiness_cpu_mpstat\.txt$")
    # Adjusted the regex pattern to explicitly capture each field
    cpu_data_regex = re.compile(r"(\d{2}:\d{2}:\d{2}) [AP]M\s+(\w+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)")

    metrics = {}

    for filename in os.listdir(directory_path):
        match = filename_regex.match(filename)
        if not match:
            continue
        coflowiness = match.group(1)

        with open(os.path.join(directory_path, filename), 'r') as file:
            lines = file.readlines()

        for line in lines:
            if "CPU" in line and "%usr" in line:
                continue
            match = cpu_data_regex.match(line.strip())
            if match and match.group(2) == 'all':
                print(f"Matched line: {line.strip()}")  # Debug: Print matched line
                metrics_list = ['usr', 'nice', 'sys', 'iowait', 'irq', 'soft', 'steal', 'guest', 'gnice', 'idle']
                for i, metric in enumerate(metrics_list, start=3):
                    value = match.group(i)
                    print(f"Metric {metric}, Value {value}")  # Debug: Print captured values
                    if metric not in metrics:
                        metrics[metric] = {}
                    if coflowiness not in metrics[metric]:
                        metrics[metric][coflowiness] = []
                    metrics[metric][coflowiness].append(value)

    os.makedirs(output_directory, exist_ok=True)

    for metric, data in metrics.items():
        with open(os.path.join(output_directory, f"{metric}_stats.dat"), 'w') as file:
            header = " ".join(sorted(data.keys()))
            file.write(header + '\n')
            for i in range(len(next(iter(data.values())))):
                row = [data[coflowiness][i] for coflowiness in sorted(data)]
                file.write(" ".join(row) + '\n')



# Usage
input_directory = '/home/emilstahl/DA240X/Benchmark/bench-tools/cpu-bench-results/Facebook-Hadoop/all/cpu_mpstat/associate'
output_directory = '/home/emilstahl/DA240X/Benchmark/bench-tools/cpu-bench-results/Facebook-Hadoop/cpu_bench_gnuplot_data_Facebook_Hadoop/cpu_mpstat/associate'

# create the output directory if it doesn't exist
os.makedirs(output_directory, exist_ok=True)

parse_directory(input_directory, output_directory)