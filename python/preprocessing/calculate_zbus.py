import re
import pandas as pd
import numpy as np
from pathlib import Path

def parse_complex(value):
    """
    Convert a string representation of a complex number into a Python
    complex number.

    The function handles the format exported by PowerFactory, such as:
    '0.2475+j-7.0731'.
    """
    if not isinstance(value, str):
        return complex(value)

    value = value.strip()

    # Convert PowerFactory-style notation to Python notation
    value = value.replace("+j-", "-")
    value = value.replace("+j", "+")
    value = value.replace("-j", "-")

    # Add the imaginary unit when necessary
    if re.match(r".*[+-]\d+(\.\d+)?$", value):
        value = value + "j"

    try:
        return complex(value)
    except ValueError:
        print(f"Warning: could not parse '{value}'")
        return complex(0)


def calculate_zbus(input_file="Ybus_export.csv",
                   output_file="Zbus.csv"):
    """
    Calculate Zbus as the inverse of Ybus.

    Parameters
    ----------
    input_file : str
        Path to the Ybus CSV file.
    output_file : str
        Path where the Zbus CSV file will be saved.
    """

    # Read Ybus
    ybus = pd.read_csv(input_file, index_col=0)

    # Convert the matrix to complex numbers
    ybus_complex = ybus.applymap(parse_complex).to_numpy()

    # Calculate Zbus
    try:
        zbus_complex = np.linalg.inv(ybus_complex)
    except np.linalg.LinAlgError:
        print("Warning: Ybus is singular. Using pseudo-inverse.")
        zbus_complex = np.linalg.pinv(ybus_complex)

    # Preserve bus names
    zbus = pd.DataFrame(
        zbus_complex,
        index=ybus.index,
        columns=ybus.columns
    )

    # Export
    zbus.to_csv(output_file)

    print(f"Zbus generated successfully: {output_file}")


if __name__ == "__main__":

    # Root directory of the repository
    ROOT_DIR = Path(__file__).resolve().parents[2]

    # Directory containing the example systems
    EXAMPLES_DIR = ROOT_DIR / "data" / "example"

    # Search for all example directories containing Ybus_export.csv
    ybus_files = list(EXAMPLES_DIR.glob("*/Ybus_export.csv"))

    if not ybus_files:
        print("No Ybus_export.csv files were found in data/example/")
    else:

        for input_file in ybus_files:

            output_file = input_file.parent / "Zbus.csv"

            print("\n----------------------------------------")
            print(f"Processing example: {input_file.parent.name}")
            print("----------------------------------------")

            calculate_zbus(
                input_file=input_file,
                output_file=output_file
            )