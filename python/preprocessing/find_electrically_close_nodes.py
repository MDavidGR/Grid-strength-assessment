import pandas as pd
import numpy as np
from pathlib import Path

def find_electrically_close_nodes(
    input_file="Zbus.csv",
    output_file="pares_nodos_cercanos.csv",
    number_of_pairs=35
):
    """
    Identify electrically close bus pairs using |Zij/Zjj|.

    Parameters
    ----------
    input_file : str
        Path to the Zbus CSV file.
    output_file : str
        Path where the results will be saved.
    number_of_pairs : int
        Number of closest bus pairs to display.
    """

    # Read Zbus
    zbus_df = pd.read_csv(input_file, index_col=0)

    # Convert values to complex numbers
    zbus = zbus_df.applymap(
        lambda value: complex(str(value).replace("i", "j"))
    ).to_numpy()

    n = zbus.shape[0]
    pairs = []

    # Calculate |Zij/Zjj| for every pair of buses
    for i in range(n):
        for j in range(i + 1, n):

            zij = zbus[i, j]
            zjj = zbus[j, j]

            if zjj == 0:
                continue

            ratio = abs(zij / zjj)

            pairs.append(
                ((i + 1, j + 1), ratio)
            )

    # Sort by the calculated metric
    pairs_sorted = sorted(
        pairs,
        key=lambda item: -item[1]
    )

    print("Electrically closest bus pairs:")

    for (i, j), value in pairs_sorted[:number_of_pairs]:
        print(
            f"Bus {i} - Bus {j}: "
            f"|Zij/Zjj| = {value:.6f} pu"
        )

    # Export all pairs
    pairs_df = pd.DataFrame(
        [
            (i, j, value)
            for (i, j), value in pairs_sorted
        ],
        columns=["Bus_i", "Bus_j", "|Zij/Zjj|"]
    )

    pairs_df.to_csv(output_file, index=False)

    print(
        f"Results saved to: {output_file}"
    )

if __name__ == "__main__":

    # Root directory of the repository
    ROOT_DIR = Path(__file__).resolve().parents[2]

    # Directory containing the example systems
    EXAMPLES_DIR = ROOT_DIR / "data" / "example"

    # Search for all example directories containing Zbus.csv
    zbus_files = list(EXAMPLES_DIR.glob("*/Zbus.csv"))

    if not zbus_files:
        print("No Zbus.csv files were found in data/example/")
    else:

        for input_file in zbus_files:

            output_file = input_file.parent / "pares_nodos_cercanos.csv"

            print("\n----------------------------------------")
            print(f"Processing example: {input_file.parent.name}")
            print("----------------------------------------")

            find_electrically_close_nodes(
                input_file=input_file,
                output_file=output_file
            )