import os
import subprocess
from time import perf_counter

def merge_pcap_files(input_files, output_file):

    print(f"\nMerging pcap files: ")
    for input_file in input_files:
        print(os.path.basename(input_file))

    # delete output file if it already exists
    if os.path.exists(output_file):
        print(f'\nOutput file {output_file} already exists. Deleting...')
        os.remove(output_file)

    print(f'\nInput directory: {os.path.dirname(input_files[0])}')
    print(f'Output directory: {os.path.dirname(output_file)}')
    print(f"Output file: {os.path.basename(output_file)}\n")
    print('Merging files...')

    edited_files = []

    for offset, file in enumerate(input_files):
        print(f'Editing file {os.path.basename(file)} with offset {offset}')
        edited_file = f'{file}_offset_{offset}.pcap'
        edited_files.append(edited_file)
        command = ['/usr/bin/editcap', '-t', str(offset), file, edited_file]
        subprocess.run(command, check=True)

    command = ['/usr/bin/mergecap', '-w', output_file] + edited_files

    start = perf_counter()

    try:
        # Run the subprocess command
        subprocess.run(command, check=True)
        print(f'Merge completed. Output file: {output_file}')
    except subprocess.CalledProcessError as e:
        print(f'Error during merging: {e}')

    end = perf_counter()

    print(f'\nMerged {len(input_files)} files in {end - start:.2f} seconds')
    
    return output_file

if __name__ == "__main__":
    # List of input pcap files to merge

    file0 = "/home/emilstahl/DA240X/Benchmark/workload-generator/data/pcap_traces/0_3-0.9-FB-UP_ports_Facebook_HadoopDist_All_size.pcap"

    file1 = "/home/emilstahl/DA240X/Benchmark/workload-generator/data/pcap_traces/1_3-0.9-FB-UP_ports_Facebook_HadoopDist_All_size.pcap"

    file2 = "/home/emilstahl/DA240X/Benchmark/workload-generator/data/pcap_traces/2_3-0.9-FB-UP_ports_Facebook_HadoopDist_All_size.pcap"

    input_files = [file0, file1, file2]

    # check if input files exist
    for file in input_files:
        if not os.path.exists(file):
            print(f'File {file} does not exist')
            exit(1)

    # Output merged pcap file
    output_file = os.path.join(os.getcwd(), f"merged_{os.path.basename(file1)}")

    # Merge pcap files
    merge_pcap_files(input_files, output_file)

