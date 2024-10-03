import re

def parse_mpstat_to_dat(filepath):
    """
    Convert mpstat output into a structured .dat file format, capturing specific aggregated CPU usage details without AM/PM.
    """
    with open(filepath, 'r') as file:
        lines = file.readlines()

    data = []
    # Adjusted header to include only the selected metrics
    header = "time CPU usr sys irq soft steal idle"
    cpu_data_regex = re.compile(r"(\d{2}:\d{2}:\d{2}) [AP]M\s+(\w+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)")

    for line in lines:
        if "CPU" in line and "%usr" in line:  # Skip header lines
            continue
        match = cpu_data_regex.match(line.strip())
        if match:
            time = match.group(1)  # Extract time
            cpu_id = match.group(2)  # Extract CPU ID
            if cpu_id == 'all':  # Filter for aggregated data
                usr = match.group(3)
                # Skipping 'nice' which is group(4)
                sys = match.group(5)
                # Skipping 'iowait' which is group(6)
                irq = match.group(7)
                soft = match.group(8)
                steal = match.group(9)
                # Skipping 'guest' which is group(10) and 'gnice' which is group(11)
                idle = match.group(12)
                data.append(f"{time} {cpu_id} {usr} {sys} {irq} {soft} {steal} {idle}")

    # Write data to a .dat file
    with open(filepath.replace('.txt', '.dat'), 'w') as file:
        file.write(header + '\n' + "\n".join(data))


parse_mpstat_to_dat('/home/emilstahl/DA240X/Benchmark/bench-tools/cpu-bench-results/Facebook-Hadoop/0.9-coflowiness/associated-Facebook-Hadoop-0.9-coflowiness_cpu_mpstat.txt')
