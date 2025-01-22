from avg_coeff_simulation import simulation
import numpy as np
import csv
import pterasoftware as ps

def Mark4Simulation(Airfoils, FlappingPeriods, Angles_of_Attacks, Air_Speeds, mw_wingspans, aspect_ratios, taper_ratio):
    file_name = "AverageFlightData6.csv"
    
    # Function call
    for t in Airfoils:
        for w in  mw_wingspans:
            for e in aspect_ratios:
                for r in taper_ratio:
                    for i in FlappingPeriods:
                        for j in Air_Speeds:
                            for k in Angles_of_Attacks:
                                    
                                    lift, induced_drag  = simulation(mw_airfoil = t, fp = i, va = j, aoa = k, 
                                                                    mw_wingspan = w, aspect_ratio = e, taper_ratio = r)
                                    print("Average Lift & Induced Drag : ", lift, induced_drag )

                                    with open(file_name, mode='a', newline='') as file:
                                        writer = csv.writer(file)
                                        # Save data to CSV 
                                        writer.writerow([ t, w, e, r, i, j, k, lift, induced_drag])

    print("Data Collection is Over")


# Airfoils = ["naca8304", "goe225", "naca2412", "naca0012"]
# FlappingPeriods = [0.2, 0.4, 0.6, 0.8, 1.0, 1.2]
# Angles_of_Attacks = [5, 15, 25, 35]
# Air_Speeds =  [ 2, 3, 4, 5, 6]
# mw_wingspans = [0.4, 0.8, 1.2, 1.6]
# aspect_ratios = [1.5, 2.5, 3.5, 4.5, 5.5]
# taper_ratio = [0.2,  0.4,  0.6, 0.8]

# csv 5
# FlappingPeriods = [0.2, 0.3, 0.4]
# Angles_of_Attacks = [15, 20, 25]
# Air_Speeds =  [ 3, 4, 5]
# mw_wingspans = [1.2,  1.4, 1.6]
# aspect_ratios = [1.5, 2, 2.5]
# taper_ratio = [0.4, 0.5, 0.6, 0.8]



Airfoils = [ "naca2412"]
FlappingPeriods = [0.65, 0.75, 0.85]
Angles_of_Attacks = [10, 20, 30]
Air_Speeds =  [ 3, 4, 5]
mw_wingspans = [ 0.4]
aspect_ratios = [1.25, 1.9, 3]
taper_ratio = [0.3, 0.4]
 
# Airfoils = ["goe225"]
# FlappingPeriods = [ 0.6]
# Angles_of_Attacks = [25]
# Air_Speeds =  [ 2.5]
# mw_wingspans = [0.4]
# aspect_ratios = [4.5]
# taper_ratio = [0.5]


Mark4Simulation(Airfoils, FlappingPeriods, Angles_of_Attacks, Air_Speeds, mw_wingspans, aspect_ratios, taper_ratio)