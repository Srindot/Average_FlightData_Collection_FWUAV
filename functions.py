# Functions for Collecting data for the Auto Conceptual Design
import os
import csv
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pterasoftware as ps
from pathlib import Path 



# function def to return average labels
# In functions.py

def get_average_results(unsteady_solver):
    """
    This function correctly extracts the average forces from the solver.
    """
    # This variable is a list of lists, for example: [[drag, side, lift]]
    forces = unsteady_solver.unsteady_problem.final_mean_near_field_forces_wind_axes
    
    # FIX: Use a list comprehension to extract the data instead of NumPy slicing.
    # This says: "For each 'force_set' in the main 'forces' list, get the item at index 0."
    all_induced_drags = [force_set[0] for force_set in forces]
    
    # This says: "For each 'force_set' in the main 'forces' list, get the item at index 2."
    all_lifts = [force_set[2] for force_set in forces]

    return all_lifts, all_induced_drags


# function def to write a row in csv file
def write_to_csv(filename, af, ws, ar, tr, fp, ap, aa, lift, induced_drag):
    
    # --- FIX: Ensure the directory exists before writing ---
    # Create a Path object from the filename string
    file_path = Path(filename)
    # Create the parent directory of the file if it doesn't already exist
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Now, safely open and write to the file
    with open(file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        # Save data to CSV 
        writer.writerow([ af, ws, ar, tr, fp, ap, aa, lift, induced_drag])

