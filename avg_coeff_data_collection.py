from avg_coeff_simulation import simulation
from functions import write_to_csv



def Mark4Simulation(Airfoils, FlappingPeriods, Angles_of_Attacks, Air_Speeds, wingspans, aspect_ratios, taper_ratios):
    filename = "Data/AverageFlightData10.csv"
    
    # Function call
    row = 0 
    for af in Airfoils:
        for ws in  wingspans:
            for ar in aspect_ratios:
                for tr in taper_ratios:
                    for fp in FlappingPeriods:
                        for ap in Air_Speeds:
                            for aa in Angles_of_Attacks:
                                    
                                    # increament row 
                                    row+=1
                                    
                                    # Function call for simulation 
                                    lift, induced_drag  = simulation(mw_airfoil = af, fp = fp, va = ap, aoa = aa, 
                                                                    mw_wingspan = ws, aspect_ratio = ar, taper_ratio = tr)
                                    print("Average Lift & Induced Drag : of ",row," is ", lift, induced_drag )
                                    
                                    # Function call for write into csv
                                    write_to_csv(filename, af, ws, ar, tr, fp, ap, aa, lift, induced_drag)


    print("\n------------------------\n")
    print("Data Completion comleted")
    print("\n------------------------\n")


# Airfoils = ["naca8304", "goe225", "naca2412", "naca0012"]
# FlappingPeriods = [0.2, 0.4, 0.6, 0.8, 1.0, 1.2]
# Angles_of_Attacks = [5, 15, 25, 35]
# Air_Speeds =  [ 2, 3, 4, 5, 6]
# wingspans = [0.4, 0.8, 1.2, 1.6]
# aspect_ratios = [1.5, 2.5, 3.5, 4.5, 5.5]
# taper_ratios = [0.2,  0.4,  0.6, 0.8]

# csv 5
# FlappingPeriods = [0.2, 0.3, 0.4]
# Angles_of_Attacks = [15, 20, 25]
# Air_Speeds =  [ 3, 4, 5]
# wingspans = [1.2,  1.4, 1.6]
# aspect_ratios = [1.5, 2, 2.5]
# taper_ratios = [0.4, 0.5, 0.6, 0.8]



Airfoils = [ "naca2412"]
FlappingPeriods = [0.65, 0.75, 0.85]
Angles_of_Attacks = [10, 20, 30]
Air_Speeds =  [ 3, 4, 5]
wingspans = [ 0.4]
aspect_ratios = [1.25, 1.9, 3]
taper_ratios = [0.3, 0.4]
 
# Airfoils = ["goe225"]
# FlappingPeriods = [ 0.6]
# Angles_of_Attacks = [25]
# Air_Speeds =  [ 2.5]
# wingspans = [0.4]
# aspect_ratios = [4.5]
# taper_ratios = [0.5]


Mark4Simulation(Airfoils, FlappingPeriods, Angles_of_Attacks, Air_Speeds, wingspans, aspect_ratios, taper_ratios)