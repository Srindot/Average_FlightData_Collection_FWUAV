import numpy as np
import pterasoftware as ps
from functions import get_average_results

# --- Airfoil Cache (persistent across runs) ---
_airfoil_cache = {}

def simulation(
    mw_airfoil: str = "naca8304",
    fp: float = 0.2,         # flapping frequency
    va: float = 5.0,         # velocity
    aoa: float = 5.0,        # angle of attack
    mw_wingspan: float = 1.4,
    aspect_ratio: float = 4.66,
    taper_ratio: float = 0.6,
):
    """
    Runs a single unsteady aerodynamic simulation using PteraSoftware.
    
    Args:
        mw_airfoil (str): Airfoil designation.
        fp (float): Flapping frequency (Hz).
        va (float): Freestream velocity (m/s).
        aoa (float): Angle of attack (degrees).
        mw_wingspan (float): Wing span (m).
        aspect_ratio (float): Wing aspect ratio (span^2 / area).
        taper_ratio (float): Tip chord / Root chord.

    Returns:
        tuple: (avg_lift, avg_drag)
    """

    # --- Wing Geometry ---
    root_chord = round(mw_wingspan / aspect_ratio, 3)
    tip_chord = round(taper_ratio * root_chord, 3)

    # --- Airfoil Object (cached) ---
    if mw_airfoil in _airfoil_cache:
        airfoil_obj = _airfoil_cache[mw_airfoil]
    else:
        airfoil_obj = ps.geometry.Airfoil(name=mw_airfoil, n_points_per_side=400)
        _airfoil_cache[mw_airfoil] = airfoil_obj

    # --- Define Airplane Geometry ---
    airplane = ps.geometry.Airplane(
        name=f"{mw_airfoil}_wing",
        wings=[
            ps.geometry.Wing(
                name="Main Wing",
                symmetric=True,
                num_chordwise_panels=8,  # baseline discretization
                wing_cross_sections=[
                    ps.geometry.WingCrossSection(
                        chord=root_chord,
                        airfoil=airfoil_obj,
                        num_spanwise_panels=16,
                    ),
                    ps.geometry.WingCrossSection(
                        y_le=mw_wingspan / 2.0,
                        chord=tip_chord,
                        airfoil=airfoil_obj,
                    ),
                ],
            ),
        ],
    )

    # --- Define Movement ---
    movement = ps.movement.Movement(
        airplane_movements=[
            ps.movement.AirplaneMovement(
                base_airplane=airplane,
                wing_movements=[
                    ps.movement.WingMovement(
                        base_wing=airplane.wings[0],
                        wing_cross_sections_movements=[
                            ps.movement.WingCrossSectionMovement(
                                base_wing_cross_section=airplane.wings[0].wing_cross_sections[0],
                            ),
                            ps.movement.WingCrossSectionMovement(
                                base_wing_cross_section=airplane.wings[0].wing_cross_sections[1],
                                sweeping_period=fp,
                                sweeping_amplitude=30.0,
                                sweeping_spacing="sine",
                            ),
                        ],
                    )
                ],
            )
        ],
        operating_point_movement=ps.movement.OperatingPointMovement(
            base_operating_point=ps.operating_point.OperatingPoint(
                velocity=va,
                alpha=aoa,
            )
        ),
    )

    # --- Define Problem & Solver ---
    problem = ps.problems.UnsteadyProblem(movement=movement)
    solver = ps.unsteady_ring_vortex_lattice_method.UnsteadyRingVortexLatticeMethodSolver(
        unsteady_problem=problem
    )

    solver.run(
        logging_level="Warning",
        prescribed_wake=True,  # less accurate but faster
    )

    ps.output.animate(  # Set the unsteady solver to the one we just ran.
    unsteady_solver=solver,
    # Tell the animate function to color the aircraft's wing panels with the local
    # lift coefficient. The valid arguments for this parameter are None, "induced drag",
    # "side force", or "lift".
    scalar_type="lift",
    # Tell the animate function to show the wake vortices. This value defaults to
    # False.
    show_wake_vortices=True,
    # Tell the animate function to not save the animation as file. This way,
    # the animation will still be displayed but not saved. This value defaults to
    # False.
    save=False,
    )
    # --- Post-Processing ---
    lifts_list, drags_list = get_average_results(solver)

    return lifts_list[0], drags_list[0]


## Debug/Test Run
if __name__ == "__main__":
    print(simulation())
