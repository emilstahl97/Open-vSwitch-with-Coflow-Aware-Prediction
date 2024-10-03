import json
import os

def extract_ips_from_json(json_data):
    src_ips = set()
    dst_ips = set()

    num_coflows = json_data["num_coflows"]
    coflows = json_data["coflows"]

    for coflow in coflows:
        flows = coflow["flows"]
        for flow in flows:
            src_ips.add(flow["source_id"])
            dst_ips.add(flow["dest_id"])

    return src_ips, dst_ips

def get_src_dst_IPs(file_path: str):
    try:
        with open(file_path, 'r') as file:
            json_data = json.load(file)

        src_ips, dst_ips = extract_ips_from_json(json_data)

    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except json.JSONDecodeError:
        print(f"Error decoding JSON from file: {file_path}")

    return src_ips, dst_ips

if __name__ == "__main__":
    dir_path = "/home/emilstahl/DA240X/Benchmark/workload-generator/json_traces"
    file_name = '10-0.9-FB-UP.json'
    file_path = os.path.join(dir_path, file_name)
    print('File path:', file_path, '\n')

    src_ips, dst_ips = get_src_dst_IPs(file_path)

    print("\nDistinct Source IPs:", list(src_ips), '\n')
    print("Distinct Destination IPs:", list(dst_ips))