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
