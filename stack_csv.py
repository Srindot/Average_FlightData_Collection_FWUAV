import os
import pandas as pd

def stack_csv_vertically(directory, output_file):
    # Initialize an empty list to store dataframes
    dataframes = []
    
    # Loop through files and read them into dataframes
    for i in range(1, len(os.listdir(directory)) + 1):  # Assuming n is the number of CSV files
        file_path = os.path.join(directory, f'AverageFlightData{i}.csv')
        if os.path.isfile(file_path):
            # Read the CSV file without headers
            df = pd.read_csv(file_path, header=None)
            dataframes.append(df)
    
    # Concatenate all dataframes vertically (axis=0)
    result_df = pd.concat(dataframes, axis=0, ignore_index=True)
    
    # Save the result to the output CSV file
    result_df.to_csv(output_file, index=False, header=False)
    
    print(f"Stacked CSV saved to {output_file}")

stack_csv_vertically("Des_Data", "Design_Data.csv")
