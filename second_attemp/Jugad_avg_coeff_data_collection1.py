from avg_coeff_simulation import  simulation
import numpy as np
import csv
import pterasoftware as ps

def Mark4Simulation(Airfoils, FlappingPeriods, Angles_of_Attacks, Air_Speeds):
    file_name = "AverageFlightData9.csv"
    
    for i in FlappingPeriods:
        for j in Air_Speeds:
            for k in Angles_of_Attacks:
                for t in Airfoils:
                    w = 0.8
                    e = 2
                    r = 0.4
                    lift, induced_drag  = simulation(mw_airfoil = t, fp = i, va = j, aoa = k, 
                                                     mw_wingspan = w, aspect_ratio = e, taper_ratio = r)
                    print("Average Lift & Induced Drag : ", lift, induced_drag )

                    with open(file_name, mode='a', newline='') as file:
                        writer = csv.writer(file)
                        # Save data to CSV 
                        writer.writerow([ t, w, e, r, i, j, k, lift, induced_drag])

    print("Data Collection is Over")


Airfoils = [ "goe225", "naca2412", "naca0012"]
FlappingPeriods = [ 0.2, 0.3, 0.5, 0.7, 0.9, 1.1]
Angles_of_Attacks = [5, 10, 15, 20, 25, 30, 35]
Air_Speeds =  [ 2, 3.5, 4.5, 5.5, 6.5]



Mark4Simulation(Airfoils, FlappingPeriods, Angles_of_Attacks, Air_Speeds)