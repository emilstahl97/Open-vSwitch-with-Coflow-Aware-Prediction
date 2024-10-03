import os
import datetime
from pathlib import Path

def add_date(json_file_path) -> str:
    # Extract the file name without extension
    json_file_name_without_extension = Path(json_file_path).stem
    
    # Extract the file extension
    file_extension = Path(json_file_path).suffix
    
    # Get the current date
    date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Create the output file name with the added date
    output_file_name = f"{json_file_name_without_extension}_{date}{file_extension}"
    
    # Get the directory of the input file
    file_directory = os.path.dirname(json_file_path)
    
    # Create the full path of the output file
    output_file_path = os.path.join(file_directory, output_file_name)

    os.rename(json_file_path, output_file_path)
    
    return output_file_path