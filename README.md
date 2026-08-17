# Grid-strength-assessment
Computational implementation of system strength assessment for transmission networks with inverter-based resources

## Overview
This repository contains the computational tools developed for the assessment of grid strength in transmission systems with inverter-based generation.
The implementation combines **DIgSILENT PowerFactory** and **Python** to perform network modeling, operating-condition simulations, network-matrix processing, calculation of grid-strength indicators, and analysis of the obtained results.
The methodology is evaluated using modified IEEE test systems, including the **IEEE 9-bus** and **IEEE 39-bus** systems.

## Methodology
The computational workflow consists of the following main stages:
1. Definition and configuration of the test system.
2. Integration of inverter-based resources.
3. Definition of operating scenarios.
4. Power-flow simulations and operating-point sweeps.
5. Extraction of network and operating data.
6. Processing of the network admittance and impedance matrices.
7. Calculation of grid-strength indicators.
8. Normalization and comparison of the indicators.
9. Generation of numerical results and graphical analyses.

## Grid Strength Indicators
The repository includes implementations of different grid-strength indicators, including:
* Short Circuit Ratio (SCR)
* Generalized System Strength Metric (GSIM)
* Network Response Short Circuit Ratio (NRSCR)
* Short-Circuit Ratio considering coupling effects (SDSCR)
* Lambda-SCR ($\lambda_{SCR}$)
* Voltage Transfer Grid Strength Coefficient ($K_{vtg}$)

## Test Systems
The methodology is evaluated using modified versions of:
* IEEE 9-bus test system
* IEEE 39-bus test system
The modifications include the integration of inverter-based generation and the definition of different operating conditions for the evaluation of grid strength.

## Software Requirements
The computational workflow uses:
* DIgSILENT PowerFactory
* Python 3.9+
* NumPy
* Pandas
* SciPy
* Matplotlib
Detailed installation and execution instructions will be provided in the repository documentation.

## Repository Structure
The repository is organized into the following main directories:
```text
Grid-strength-assessment/
│
├── data/
├── docs/
├── powerfactory/
├── python/
├── results/
├── figures/
│
├── README.md
├── requirements.txt
└── CITATION.cff
```

## Reproducibility
The objective of this repository is to provide the source code, input data, documentation, and computational workflow required to reproduce the results presented in the associated scientific publication.
The complete reproduction workflow will be documented progressively as the repository is developed.

## Associated Publication
The methodology implemented in this repository is associated with the following scientific publication:

> **[Title of the article]**

Authors:

> **[Authors]**

Publication information will be added once the article is published.

## License

License information will be added once the appropriate license for the source code and associated materials has been defined.

## PowerFactory preprocessing

The repository includes a PowerFactory Python script used to extract the
network data required by the subsequent Python-based analysis.

The script is:

`powerfactory/preprocessing/export_network_data.py`

### Requirements

- DIgSILENT PowerFactory with Python Script (`ComPython`) support.
- A compatible PowerFactory model of the test system.

### Configuration

Before executing the script, open `export_network_data.py` and modify the
`OUTPUT_DIR` variable according to the location of the repository on the
local computer.

For example:

OUTPUT_DIR = r"C:\Path\to\Grid-strength-assessment\data\example\IEEE39"

The script creates the output directory if it does not already exist.

The script generates the following files:

Ybus_export.csv
corrientes_generadores.csv
tensiones_nodos.csv
potencias_activas_generadores.csv
cortocircuito_trifasico.csv

## Preprocessing workflow

The preprocessing scripts automatically detect the available test systems
inside `data/example/`.

Each example must contain a `Ybus_export.csv` file.

For example:

data/example/
├── IEEE9/
│   └── Ybus_export.csv
└── IEEE39/
    └── Ybus_export.csv

### 1. Calculate Zbus

The script `calculate_zbus.py` reads the Ybus matrix exported from
DIgSILENT PowerFactory and calculates the corresponding bus impedance matrix
Zbus.

Run:

python python/preprocessing/calculate_zbus.py

The script searches for Ybus_export.csv in each example directory and
generates Zbus.csv in the corresponding directory.

For example:

data/example/
├── IEEE9/
│   └── Ybus_export.csv
    └── Zbus.csv
└── IEEE39/
    └── Ybus_export.csv
    └── Zbus.csv

### 2. Identify electrically close buses

The script find_electrically_close_nodes.py uses the calculated Zbus matrix
to evaluate the electrical proximity between bus pairs.

Run:

python python/preprocessing/find_electrically_close_nodes.py

The script searches for Zbus.csv in each example directory and generates
pares_nodos_cercanos.csv in the corresponding directory.

For example:

data/example/
├── IEEE9/
│   └── Ybus_export.csv
    └── Zbus.csv
    └── pares_nodos_cercanos.csv
└── IEEE39/
    └── Ybus_export.csv
    └── Zbus.csv
    └── pares_nodos_cercanos.csv

### Electrical proximity criterion

For each pair of buses, the methodology evaluates the relationship between
the mutual impedance and the self-impedance of the corresponding bus.

The resulting bus pairs are sorted according to the criterion implemented
in `find_electrically_close_nodes.py`.

The resulting file is subsequently used to identify electrically close
buses for the system-strength assessment methodology.

## Example data

The `data/example/IEEE39/` and `data/example/IEEE9/` directory contains 
intermediate files generated from the IEEE 39-bus and IEEE 9-bus test system.

These files are provided so that the Python preprocessing workflow can be
reproduced without requiring DIgSILENT PowerFactory.

The example workflow starts from:

`Ybus_export.csv`

and generates:

`Zbus.csv`

and:

`pares_nodos_cercanos.csv`.