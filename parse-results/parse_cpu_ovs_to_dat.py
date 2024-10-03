import pandas as pd
import os

def aggregate_data(file_path):
    # Load the CSV file
    df = pd.read_csv(file_path)

    # Assuming the first column is the timestamp and is unnamed
    # Rename it if necessary or adjust the column name accordingly
    df.rename(columns={df.columns[0]: 'Time'}, inplace=True)

    # Convert the 'Time' column to datetime format if it's not already
    # df['Time'] = pd.to_datetime(df['Time'], format='%H:%M:%S').dt.time  # uncomment if necessary

    # Group the data by the 'Time' column and calculate the mean for each group
    aggregated_df = df.groupby('Time').agg({
        '%usr': 'mean',
        '%sys': 'mean',
        '%CPU': 'mean'
    }).reset_index()

    # Round the results to two decimal places
    aggregated_df['%usr'] = aggregated_df['%usr'].round(2)
    aggregated_df['%sys'] = aggregated_df['%sys'].round(2)
    aggregated_df['%CPU'] = aggregated_df['%CPU'].round(2)

    # get basename of file
    filename = os.path.basename(file_path)

    # Save each column to a separate CSV file
    aggregated_df[['%usr']].to_csv('aggregated_usr_' + filename, index=False, header=False)
    aggregated_df[['%sys']].to_csv('aggregated_sys_' + filename, index=False, header=False)
    aggregated_df[['%CPU']].to_csv('aggregated_cpu_' + filename, index=False, header=False)

    print("Aggregation complete. User, System, and CPU data saved to separate files.")

# Example usage:
# aggregate_data('path_to_your_file.csv')

def main():
    filename = '/home/emilstahl/DA240X/Benchmark/results/cpu-bench-results/Facebook-Hadoop/all/cpu_ovs_filtered_handlers/associate/filtered_handlers_associated-Facebook-Hadoop-0.1-coflowiness_cpu_ovs.csv'
    aggregate_data(filename)

if __name__ == '__main__':
    main()
