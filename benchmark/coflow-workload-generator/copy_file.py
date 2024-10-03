import os
import shutil

def copy_file_to_directory(file_path, target_directory):
    # Check if the file exists
    if not os.path.exists(file_path):
        print("File does not exist.")
        return
    
    # Check if the target directory exists, create it if not
    if not os.path.exists(target_directory):
        os.makedirs(target_directory)
    
    try:
        # Extracting the file name from the file path
        file_name = os.path.basename(file_path)
        
        # Constructing the destination path
        destination_path = os.path.join(target_directory, file_name)
        
        # Copying the file
        shutil.copy(file_path, destination_path)
        
    except Exception as e:
        print(f"Error occurred: {e}")