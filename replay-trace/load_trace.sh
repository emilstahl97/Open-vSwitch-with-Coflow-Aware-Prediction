#!/bin/bash

# Directory to search for .sum files, passed as an argument
SEARCH_DIR="/mnt/traces/emil/production-traces/1000-Facebook-Hadoop/adjusted_coflowiness/0.9_coflowiness/sum-files/"

# Destination file path
DESTINATION="/mnt/traces/emil/summary/pcap_summary.sum"

# Check if the search directory is provided and exists
if [[ -z "$SEARCH_DIR" || ! -d "$SEARCH_DIR" ]]; then
    echo "Invalid directory. Please provide a valid directory."
    exit 1
fi

# List all .sum files in the directory
echo "Listing all .sum files in $SEARCH_DIR:"
files=($(find "$SEARCH_DIR" -maxdepth 1 -type f -name '*.sum'))
if [[ ${#files[@]} -eq 0 ]]; then
    echo "No .sum files found in the directory."
    exit 1
fi

# Display files with a number to choose
echo "Please select a file to copy by entering its number:"
echo " "
for i in "${!files[@]}"; do
    filename=$(basename "${files[$i]}")
    echo "$((i+1)). $filename"
done

# User input for file selection
echo " "
read -p "Enter the number of the file you want to copy: " selection

# Validate user input
if ! [[ "$selection" =~ ^[0-9]+$ ]] || [ "$selection" -lt 1 ] || [ "$selection" -gt ${#files[@]} ]; then
    echo "Invalid selection. Exiting."
    exit 1
fi

# Calculate index of selected file
file_index=$((selection-1))

echo " "
echo "Selected file: $(basename "${files[$file_index]}")"
echo "Copying the selected file to $DESTINATION..."
echo " "

# Copy the selected file to the destination
cp "${files[$file_index]}" "$DESTINATION"

# Confirmation message
echo "Successfully copied $(basename "${files[$file_index]}") to $DESTINATION"
echo " "
ls -l "$DESTINATION"
