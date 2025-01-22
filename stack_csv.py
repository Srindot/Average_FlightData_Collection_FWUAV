import os 
import pandas as pd
import csv
def stack_csv_vertically(directory, output_file):
    # Initialize an empty list to store dataframes
    dataframes = []
    
    # Loop through files and read them into dataframes
    for i in range(len(os.listdir(directory))):  # assuming the CSV files are sequentially named
        file_path = os.path.join(directory, f'Design_data{i}.csv')
        if os.path.isfile(file_path):
            if i == 0:
                # For the first file, read normally (including headers)
                df = pd.read_csv(file_path)
                columns = df.columns  # Save the column names
            else:
                # For subsequent files, skip the header
                df = pd.read_csv(file_path, header=None)
                df.columns = columns  # Assign the column names from the first file
            dataframes.append(df)
    
    # Concatenate all dataframes vertically (axis=0)
    result_df = pd.concat(dataframes, axis=0, ignore_index=True)
    
    # Save the result to the output CSV file
    result_df.to_csv(output_file, index=False, header=True)
    
    print(f"Stacked CSV saved to {output_file}")

stack_csv_vertically("Des_Data", "Design_Data.csv")