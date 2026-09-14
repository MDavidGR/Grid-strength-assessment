# Introduction

This repository is associated with the research article on the assessment of **Grid Strength** in electrical transmission systems with high penetration of **Inverter-Based Resources (IBR)**.

The repository contains the **code, input files, configuration data, and directory structure** required to implement and reproduce the methodology proposed in the article. The methodology integrates **DIgSILENT PowerFactory** and **Python** for power system modeling, data processing, and calculation of different grid strength indicators.

The methodology is applied and validated using the **IEEE 9-bus and 39-bus test systems**, considering different operating scenarios and IBR penetration conditions.

# Repository Structure

The repository is organized into multiple directories according to the function they perform within the methodology. This structure allows **input files**, **processing code**, **DIgSILENT PowerFactory models**, and **generated results** to be separated, facilitating the execution and reproduction of the results.

The main repository structure is as follows:

```text
Grid-strength-assessment/
│
├── data/
│   ├── example/
│   │   ├── IEEE9/
│   │   └── IEEE39/
│   │
│   ├── scenarios/
│   │   ├── IEEE9/
│   │   │   ├── CAP/
│   │   │   └── IND/
│   │   └── IEEE39/
│   │       ├── CAP/
│   │       └── IND/
│   │
│   └── results/
│       ├── IEEE9/
│       └── IEEE39/
│
├── powerfactory/
│
├── python/
│   ├── preprocessing/
│   ├── analysis/
│   ├── indicators/
│   └── visualization/
│
├── results/
│   ├── IEEE9/
│   │   ├── CAP/
│   │   └── IND/
│   └── IEEE39/
│       ├── CAP/
│       └── IND/
│
└── README.md
```

## Directory Description

### `data/`

Contains the data used throughout the different stages of the methodology, including input files, scenario definitions, and intermediate results generated during the calculations.

#### `data/example/`

Contains the input files associated with the **IEEE 9-bus and 39-bus test systems**. These files constitute the initial information required to execute the different analysis processes.

```text
data/example/
├── IEEE9/
└── IEEE39/
```

#### `data/scenarios/`

Contains the definition of the scenarios used to assess grid strength. The scenarios are organized according to the test system and the power factor condition considered:

* `CAP/`: scenarios with **capacitive** behavior.
* `IND/`: scenarios with **inductive** behavior.

Each of these directories contains the corresponding test scenarios (`Escenario_1` to `Escenario_6`).

```text
data/scenarios/
├── IEEE9/
│   ├── CAP/
│   └── IND/
└── IEEE39/
    ├── CAP/
    └── IND/
```

#### `data/results/`

Contains the **intermediate results and data generated during the initial processing** of the scenarios. These files include, among others, information used to calculate the different grid strength indicators, impedance exports, and results associated with the analyses performed in Python.

The results are organized by test system, power sweep results according to the generation type, and the basic information extracted for the indicators for each defined scenario.

```text
data/results/
├── IEEE9/
│   ├── CAP/
│   ├── IND/
│   ├── IEEE9C/
│   └── IEEE9I/
└── IEEE39/
    ├── CAP/
    ├── IND/
    ├── IEEE39C/
    └── IEEE39I/
```

Within the directories corresponding to each scenario, specific subdirectories are included for the different types of generated information, such as:

* `Datos GSIM/`: data used to calculate the **Grid Strength Impedance Metric (GSIM)**.
* `ExportZ_Python/`: files associated with load and generator impedance information.
* `Informacion SCR/`: information used to calculate indicators based on **Short Circuit Ratio (SCR)**.
* `Positive/`: results corresponding to the base network information (generators, buses, transformers, short-circuit currents, Ybus, etc.).
* `SDSCR INFO/`: information used to calculate the **SDSCR**.

### `powerfactory/`

Contains the files associated with **DIgSILENT PowerFactory** used in the development of the methodology. This directory includes the scripts and files required to execute network analyses and export the information required by the Python scripts.

### `python/`

Contains the scripts developed in **Python**. The code is organized according to the processing stage in which it is used:

| Directory        | Function                                                                         |
| ---------------- | -------------------------------------------------------------------------------- |
| `preprocessing/` | Initial preparation, organization, and processing of input data.                 |
| `indicators/`    | Calculation of the indicators used to assess grid strength.                      |
| `visualization/` | Generation of plots and representations used to analyze and compare the results. |

This separation keeps the different stages of the processing workflow independent and facilitates script reuse.

### `results/`

Contains the **final results and figures generated for the analysis of the test systems**. Unlike `data/results/`, this directory is mainly intended for the final results used for the presentation, comparison, and analysis of the indicators.

The results are organized by test system and scenario type:

```text
results/
├── IEEE9/
│   ├── CAP/
│   └── IND/
└── IEEE39/
    ├── CAP/
    └── IND/
```

Within each directory corresponding to a generation type, the associated plots and final results are stored. Additionally, directories intended for different types of visualization are included, such as:

* `Graficas_SCR/`: plots related to the evaluation of the indicators by scenario.
* `Matriz_Graficas_Derecha/`: matrix of plots corresponding to comparative results for voltage-based indicators.
* `Matriz_Graficas_Izquierda/`: matrix of plots corresponding to comparative results for short-circuit current-based indicators.
* `Normalized graphs/`: comparative plots of normalized indicators.

Finally, `README.md` contains the general repository documentation, including the methodology description, requirements, file structure, and instructions required to reproduce the analyses.

# Requirements

To execute the methodology and reproduce the analyses presented in the article, **DIgSILENT PowerFactory** and a **Python** environment with the libraries used by the repository scripts are required.

## Software

* **DIgSILENT PowerFactory 2024 SP1** or a version compatible with the files and scripts included in the repository.
* **Python 3.9 or higher**.
* A Python development environment, such as **Visual Studio Code**, Jupyter Notebook, or another compatible environment.

## Python Libraries

The scripts mainly use the following libraries:

* `numpy`: numerical operations and matrix manipulation.
* `pandas`: reading, processing, and organization of tabular data.
* `scipy`: operations and methods used for mathematical processing and result analysis.
* `matplotlib`: plot generation and result visualization.

The dependencies can be installed using `pip`:

```bash
pip install numpy pandas scipy matplotlib
```

## DIgSILENT PowerFactory

Part of the methodology is executed directly in **DIgSILENT PowerFactory**, where electrical studies are performed and the data files subsequently used by the Python scripts are generated.

The PowerFactory-related files are located in:

```text
powerfactory/
```

The general execution workflow is:

```text
DIgSILENT PowerFactory
        │
        │ Electrical studies
        ▼
Data export
        │
        ▼
Python
        │
        ├── Preprocessing
        ├── Indicator calculation
        ├── Analysis
        └── Visualization
        │
        ▼
Results
```

# Installation and Configuration

## 1. Clone the Repository

The repository can be cloned using Git:

```bash
git clone <URL_DEL_REPOSITORIO>
cd Grid-strength-assessment
```

## 2. Create a Virtual Environment

It is recommended to use a Python virtual environment to keep the project dependencies isolated:

```bash
python -m venv .venv
```

To activate the virtual environment on Windows:

```powershell
.venv\Scripts\activate
```

## 3. Install the Dependencies

Once the virtual environment has been activated, install the required libraries:

```bash
pip install numpy pandas scipy matplotlib
```

## 4. Path Configuration

The repository scripts are organized to work using relative paths based on the main project structure. This allows the code to be executed without depending on specific absolute paths on the computer where the analysis is performed.

The base structure used is:

```text
Grid-strength-assessment/
├── data/
├── powerfactory/
├── python/
└── results/
```

The input files are mainly located in:

```text
data/example/
data/scenarios/
```

while the results generated by the analysis processes are stored in:

```text
data/results/
results/
```

Therefore, it is recommended to preserve the repository directory structure without modifying the names of the main folders.

## 5. DIgSILENT PowerFactory Configuration

Studies requiring DIgSILENT PowerFactory must be executed using the models and scripts included in:

```text
powerfactory/
```

Before executing these studies, verify that:

1. DIgSILENT PowerFactory is correctly installed.
2. The version being used is compatible with the repository files.
3. The test system models are available.
4. The input and output paths used by the scripts correspond to the repository structure.

The data exported from PowerFactory are subsequently used by the Python scripts for processing, indicator calculation, and result generation.

# Methodology Description

The proposed methodology allows the assessment of grid strength in transmission systems with high penetration of inverter-based resources (IBR) through the calculation and comparison of different grid strength indicators.

The procedure combines electrical information obtained from **DIgSILENT PowerFactory** with tools developed in **Python**. The methodological workflow starts from the test system model and continues with the extraction of network data, calculation of the `Ybus` and `Zbus` matrices, identification of electrically close buses, and integration of IBR sources at the selected buses.

Subsequently, power sweeps are performed to identify the operating boundary of the system and select different operating points. These points are used to define the study scenarios under **capacitive (CAP)** and **inductive (IND)** operating conditions of the IBRs.

For each scenario, the required electrical information is extracted and the following grid strength indicators are calculated:

* **SCR** — Short Circuit Ratio.
* **GSIM** — Grid Strength Impedance Metric.
* **NRSCR** — Network Reduction Short Circuit Ratio.
* **SDSCR** — indicator based on voltage sensitivity.
* **λSCR** — indicator based on the eigenvalue associated with the system.
* **K<sub>vtg</sub>** — indicator based on voltage sensitivity.

Finally, the indicators are compared across scenarios and normalized with respect to their critical values, allowing their differences in behavior under different operating conditions to be analyzed.

The general methodology workflow can be summarized as:

```text
Test system model
          │
          ▼
    Data extraction
          │
          ▼
       Ybus → Zbus
          │
          ▼
Identification of
electrically close buses
          │
          ▼
    IBR modeling
          │
          ▼
     Power sweep
          │
          ▼
 Scenario selection
          │
          ▼
 Scenario data
   extraction
          │
          ▼
Indicator calculation
          │
          ▼
Comparison and normalization
```

The execution details for each stage are presented in the [Execution](#execution) section.

## 1. Test System Selection

The methodology is implemented using the **IEEE 9-bus and 39-bus test systems**; however, it can be applied to any other test system that can provide the basic information required for the assessment.

The files corresponding to the test systems are located in:

```text
data/example/
├── IEEE9/
└── IEEE39/
```

## 2. Power System Modeling

The test systems are implemented in **DIgSILENT PowerFactory**, where the electrical studies required to obtain the information subsequently used by the Python scripts are performed.

To represent inverter-based generation, photovoltaic plant models based on the **WECC PVsys** model are used. The studies consider different operating conditions and power factors, including **inductive (IND)** and **capacitive (CAP)** scenarios.

## 3. Obtaining the Impedance Matrix

The network **Ybus** matrix is obtained from the network model. This information is exported from PowerFactory and subsequently processed using Python to obtain the nodal impedance matrix **Zbus**.

The `Zbus` matrix is used as the basis for characterizing the electrical relationships between the buses of the system.

The script associated with this stage is located at:

```text
python/preprocessing/calculate_zbus.py
```

## 4. Identification of Electrically Close Buses

Using the information obtained from `Zbus`, the electrical proximity between all buses in the network is determined. From this list, the electrically close buses where the inverter-based generation sources will be manually modeled must be selected.

This stage allows the identification of buses with greater electrical interaction and, therefore, that should be considered jointly in the grid strength assessment.

The results of this processing are subsequently used to define the generator groups considered in the calculation of the indicators.

The script associated with this stage is located at:

```text
python/preprocessing/find_electrically_close_nodes.py
```

## 5. Determination of Operating Limits

A **power sweep** is performed to analyze the system response under different levels of active power injection from the IBR sources.

During this procedure, the electrical variables of the system are monitored and the points associated with the operating limits established for the study are identified.

The sweep results are used to define different operating conditions that are subsequently used to construct the analysis scenarios.

The scripts associated with this stage are located at:

```text
powerfactory/
├── Power Sweep IND.py
└── Power Sweep CAP.py
```

## 6. Scenario Definition

The scenarios are constructed from the operating conditions identified during the analysis of the test systems.

For each system, different IBR penetration levels and power factor conditions are considered. The scenarios are organized according to the system, power factor type, and operating level considered.

The scenario information is located in:

```text
data/scenarios/
├── IEEE9/
│   ├── CAP/
│   └── IND/
└── IEEE39/
    ├── CAP/
    └── IND/
```

Each condition contains six operating scenarios, named `Escenario_1` to `Escenario_6`.

## 7. Grid Strength Indicator Calculation

For each scenario, different indicators used to assess grid strength are calculated. The proposed methodology for calculating these indicators can be applied to any indicator with a sound mathematical formulation whose equations are fully identified and defined for implementation.

The indicators considered include:

* **SCR** — Short Circuit Ratio.
* **GSIM** — Grid Strength Impedance Metric.
* **NRSCR** — Network Reduction Short Circuit Ratio.
* **SDSCR** — Site Depend Short Circuit Ratio.
* **λSCR** — Critical Short-Circuit Ratio.
* **K<sub>vtg</sub>** — Voltage Support Capability Indication.

The code associated with the calculation of these indicators is located in:

```text
python/indicators/
```

The use of different indicators allows their responses to changes in operating conditions and IBR penetration to be compared.

## 8. Result Normalization and Analysis

The values obtained for the different indicators are processed to facilitate their comparison. Each indicator is normalized according to its critical value.

Subsequently, comparative and statistical analyses are performed to evaluate the relationship between the indicators and the operating conditions of the system.

The corresponding processes are mainly located in:

```text
python/visualization/Indicator Comparative.py
```

## 9. Result Visualization

Finally, the processed results are used to generate the figures and plots employed in the analysis of the methodology.

The visualization tools are located in:

```text
python/visualization/
```

The final results are stored in:

```text
results/
```

and are organized according to the test system, operating condition, and scenario type.

In this way, the repository allows the complete workflow to be followed, from **obtaining the basic network information in DIgSILENT PowerFactory**, through **data processing and indicator calculation in Python**, to the **generation of the results and visualizations used in the analysis**.

# Execution

The methodology is executed through a sequence of steps combining **DIgSILENT PowerFactory** and **Python**. The user must follow the established order because the results generated at each stage constitute the input files for subsequent stages.

The complete execution workflow is:

```text
System modeling in PowerFactory
                │
                ▼
      export_network_data.py
                │
                ▼
             Ybus
                │
                ▼
         calculate_zbus.py
                │
                ▼
              Zbus
                │
                ▼
  find_electrically_close_nodes.py
                │
                ▼
      pares_nodos_cercanos.csv
                │
                ▼
    IBR bus selection
                │
                ▼
    IBR modeling + WECC
                │
                ▼
     Power Sweep IND.py / CAP.py
                │
                ▼
  boundary_PV1_PV2.csv
  boundary_plot_PV1_PV2.png
                │
                ▼
  Operating point selection
                │
                ▼
  Potencias_Comp_PV1_PV2.xlsx
                │
                ▼
  extract_scenario_data.py
                │
                ▼
       Scenario information
                │
                ▼
     calculate_indicators.py
                │
                ▼
     Indicator results
                │
                ▼
     Scenario Comparative.py
                │
                ▼
     Comparative plots
                │
                ▼
     Indicator Comparative.py
                │
                ▼
     Normalized plots
```

## Step 1. Test System Modeling

Initially, the test system model must be available in **DIgSILENT PowerFactory**.

The methodology can be applied to the test systems included in the repository:

* IEEE 9-bus system.
* IEEE 39-bus system.

The model must contain the required electrical network information, including lines, transformers, generators, loads, and other elements required to perform the studies.

The input files associated with each system are located in:

```text
data/example/
├── IEEE9/
└── IEEE39/
```

At this stage, the model is also prepared according to the required study conditions.

## Step 2. Network Data Export from PowerFactory

Once the model has been prepared, the following script must be executed internally in **DIgSILENT PowerFactory**:

```text
export_network_data.py
```

The script is located in:

```text
powerfactory/
```

This script extracts from the PowerFactory model the basic network information required for the subsequent stages, including the information used to construct the nodal admittance matrix **Ybus**.

The script is designed to use the repository directory structure. The user **must not modify the code**, except for the name of the example being processed.

The specific location where the example name must be modified is **clearly indicated through comments within the script itself**.

Once execution is completed, the exported files are stored in the corresponding directory within:

```text
data/example/
```

Among the generated files is the **Ybus** matrix, which will be used in the next step.

## Step 3. Calculation of the Zbus Matrix

Using the data exported from PowerFactory, the following script is executed from Python:

```text
calculate_zbus.py
```

located in:

```text
python/preprocessing/
```

The script uses the **Ybus** matrix generated in the previous step to calculate the nodal impedance matrix **Zbus**.

The generated `Zbus` matrix is stored in the same example path within:

```text
data/example/
```

This matrix constitutes the input information required to identify electrically close buses.

## Step 4. Identification of Electrically Close Buses

Next, the following script is executed from Python:

```text
find_electrically_close_nodes.py
```

located in:

```text
python/preprocessing/
```

The script uses the **Zbus** matrix calculated in the previous step to determine the electrical proximity relationships between the buses in the system.

As a result, the following file is generated:

```text
pares_nodos_cercanos.csv
```

This file is stored in the same example path:

```text
data/example/
```

The file contains the bus pairs ordered according to the electrical proximity criterion used by the methodology.

## Step 5. Selection of Buses for the IBRs

The selection of the buses where the **IBR** sources will be installed is performed manually.

The user must review:

```text
pares_nodos_cercanos.csv
```

and select two electrically close buses that will subsequently be used to locate the IBR generators.

This selection is necessary because the methodology aims to assess the interaction between IBR sources connected at buses with a significant electrical relationship.

## Step 6. IBR Modeling

Once the buses have been selected, the inverter-based generators must be incorporated into the PowerFactory model at the selected buses.

The IBRs must use a **WECC-based control model** compatible with the study.

At this stage, the required parameters of the generator models must be configured and the system must be verified to ensure that power flow studies can be executed correctly.

## Step 7. Power Sweep

Once the IBRs have been incorporated, power sweeps are performed to determine the operating limits of the system.

The scripts used are:

```text
powerfactory/
├── Power Sweep IND.py
└── Power Sweep CAP.py
```

These scripts are executed internally in **DIgSILENT PowerFactory**.

The scripts correspond to the two power factor conditions considered:

* `IND`: inductive condition.
* `CAP`: capacitive condition.

For each execution, the power factor type of the IBRs must be verified and manually modified according to the scenario to be analyzed.

The sweep allows different power combinations of the two IBRs to be evaluated and the admissible operating region of the system to be determined.

The following files are generated:

```text
boundary_plot_PV1_PV2.png
boundary_PV1_PV2.csv
```

These files are stored in the corresponding path within:

```text
results/
```

The `boundary_plot_PV1_PV2.png` file provides a graphical representation of the resulting operating boundary, while `boundary_PV1_PV2.csv` contains the data associated with that boundary.

## Step 8. Selection of Operating Points

From the curve:

```text
boundary_plot_PV1_PV2.png
```

the user must manually identify and select the operating points that will be used to construct the study scenarios.

The selection must consider different positions relative to the operating boundary, according to the criteria established in the methodology.

The selected points represent the active power combinations of the two IBRs that will subsequently be analyzed.

## Step 9. Scenario Definition

The selected operating points must be manually entered in the file:

```text
Potencias_Comp_PV1_PV2.xlsx
```

located in:

```text
data/scenarios/
```

The scenarios must be defined independently for each power factor condition:

```text
data/scenarios/
├── IEEE9/
│   ├── CAP/
│   └── IND/
└── IEEE39/
    ├── CAP/
    └── IND/
```

## Step 10. Information Extraction for Each Scenario

Once the `Potencias_Comp_PV1_PV2.xlsx` file has been completed, the following script is executed internally in **DIgSILENT PowerFactory**:

```text
extract_scenario_data.py
```

located in:

```text
powerfactory/
```

Before executing the script, the power factor type of the IBR generators corresponding to the set of scenarios to be processed must be verified again.

The script reads the power combinations defined in:

```text
Potencias_Comp_PV1_PV2.xlsx
```

and performs the processing required to obtain the electrical information necessary for the subsequent calculation of the indicators.

For each scenario, the information corresponding to the selected operating point is generated.

The results are stored in:

```text
data/results/
```

organized according to:

```text
Test system
    └── Power factor type
            └── Scenario
```

For each scenario, the different information folders used by the indicators are generated.

## Step 11. Indicator Calculation

Using the information obtained for each scenario, the following script is executed from Python:

```text
calculate_indicators.py
```

located in:

```text
python/indicators/
```

The script uses the results generated in the previous step and calculates the grid strength indicators considered in the study.

The processing is performed independently for each scenario.

The results of each indicator are stored in the corresponding scenario folders within:

```text
data/results/
```

In this way, the results are organized according to the test system, power factor type, and analyzed scenario.

## Step 12. Generation of Comparative Plots by Scenario

Once the indicators have been calculated, the following Python script is executed:

```text
Scenario Comparative.py
```

located in:

```text
python/visualization/
```

The script uses the results calculated for each scenario and generates comparative plots that allow the behavior of the different grid strength indicators to be analyzed simultaneously.

The results are stored in:

```text
results/
```

within the directory corresponding to the system and power factor type.

The script automatically creates the folder:

```text
Graficas_SCR/
```

where the generated comparative plots are stored.

## Step 13. Indicator Normalization and Comparison

Finally, the following Python script is executed:

```text
Indicator Comparative.py
```

located in:

```text
python/visualization/
```

This script uses the same indicator results obtained for each scenario.

Initially, the indicator values are processed and **normalized with respect to their critical values**, allowing indicators with different scales and numerical ranges to be compared.

Subsequently, the script generates the graphical representations used to analyze the evolution and distribution of the normalized indicators, including box-and-whisker plots and curves.

The results are stored in:

```text
results/
```

within the directory corresponding to the system and power factor type.

The script automatically creates the folder:

```text
Normalized graphs/
```

where the generated figures are stored.

# Test Systems

The methodology is implemented using two standardized test systems from the literature: the **IEEE 9-bus system** and the **IEEE 39-bus system**. These systems allow the behavior of the grid strength indicators to be evaluated under different operating conditions and levels of inverter-based generation (IBR) integration.

The files associated with the test systems are located in:

```text
data/example/
├── IEEE9/
└── IEEE39/
```

## IEEE 9-bus System

The IEEE 9-bus system is used as a smaller test system to verify the operation of the methodology and analyze the interaction between electrically close IBR sources.

Two inverter-based generation sources, named **PV1** and **PV2**, are considered in this system. They are located at the buses selected through the electrical proximity procedure based on the `Zbus` matrix.

Two power factor conditions are considered:

* `CAP`: operation with capacitive power factor.
* `IND`: operation with inductive power factor.

For each condition, six operating scenarios are analyzed:

```text
IEEE9/
├── CAP/
│   ├── Escenario_1
│   ├── Escenario_2
│   ├── Escenario_3
│   ├── Escenario_4
│   ├── Escenario_5
│   └── Escenario_6
│
└── IND/
    ├── Escenario_1
    ├── Escenario_2
    ├── Escenario_3
    ├── Escenario_4
    ├── Escenario_5
    └── Escenario_6
```

## IEEE 39-bus System

The IEEE 39-bus system is used as a larger test system to evaluate the methodology in a network with a more complex electrical structure.

As with the IEEE 9-bus system, two IBR sources, **PV1** and **PV2**, are incorporated at buses selected based on the electrical proximity analysis using `Zbus`.

The same two power factor conditions are considered:

* `CAP`: operation with capacitive power factor.
* `IND`: operation with inductive power factor.

Each condition contains six operating scenarios:

```text
IEEE39/
├── CAP/
│   ├── Escenario_1
│   ├── Escenario_2
│   ├── Escenario_3
│   ├── Escenario_4
│   ├── Escenario_5
│   └── Escenario_6
│
└── IND/
    ├── Escenario_1
    ├── Escenario_2
    ├── Escenario_3
    ├── Escenario_4
    ├── Escenario_5
    └── Escenario_6
```

## Study Case Organization

Overall, the test systems allow the following cases to be evaluated:

| System      | Condition | Scenarios |
| ----------- | --------- | --------: |
| IEEE 9-bus  | CAP       |         6 |
| IEEE 9-bus  | IND       |         6 |
| IEEE 39-bus | CAP       |         6 |
| IEEE 39-bus | IND       |         6 |

Therefore, the methodology considers **24 scenario conditions** across the two test systems and the two power factor conditions.

The information associated with the scenarios is located in:

```text
data/scenarios/
```

while the intermediate data and results generated during processing are stored in:

```text
data/results/
```

and the final results and figures are stored in:

```text
results/
```

This organization allows each test system to be executed and analyzed independently while keeping the scenarios corresponding to capacitive and inductive conditions separate.

# Input Data

The files used by the methodology are organized according to the stage of the procedure in which they are generated or used. The main data structure is:

```text
data/
├── example/
├── scenarios/
└── results/
```

## Test System Data

The data corresponding to the IEEE systems used in the study are located in:

```text
data/example/
├── IEEE9/
└── IEEE39/
```

These directories contain the network information files exported from DIgSILENT PowerFactory and used during the preprocessing and indicator calculation stages.

The main generated files include:

| File                                | Description                                                         |
| ----------------------------------- | ------------------------------------------------------------------- |
| `Ybus_export.csv`                   | Nodal admittance matrix used to calculate `Zbus`.                   |
| `corrientes_generadores.csv`        | Generator current information.                                      |
| `tensiones_nodos.csv`               | Bus voltage information.                                            |
| `potencias_activas_generadores.csv` | Generator active power information.                                 |
| `cortocircuito_trifasico.csv`       | Information associated with three-phase short-circuit calculations. |

## Scenario Definition

The scenarios used for the IEEE9 and IEEE39 systems are organized according to the test system and power factor condition:

```text
data/scenarios/
├── IEEE9/
│   ├── CAP/
│   └── IND/
└── IEEE39/
    ├── CAP/
    └── IND/
```

Each condition contains the file:

```text
Potencias_Comp_PV1_PV2.xlsx
```

This file contains the PV1 and PV2 power combinations used to define the operating scenarios.

## Data Generated by Scenario

The intermediate results associated with each scenario are stored in:

```text
data/results/
```

and are organized according to the test system, power factor condition, and corresponding scenario.

These data contain the information subsequently required by `calculate_indicators.py`.

## Operating Boundary Data

The power sweeps generate the following files:

```text
boundary_PV1_PV2.csv
boundary_plot_PV1_PV2.png
```

The CSV file contains the operating boundary data, while the image allows the boundary to be visualized and the operating points used to define the scenarios to be selected.

## Indicator Results

The results calculated for the indicators:

* SCR
* GSIM
* NRSCR
* SDSCR
* λSCR
* K<sub>vtg</sub>

are stored together with the information corresponding to each scenario.

These results constitute the input for the visualization and comparison scripts.

# Results

The results generated during the application of the methodology are organized in the directory:

```text
results/
├── IEEE9/
│   ├── CAP/
│   └── IND/
└── IEEE39/
    ├── CAP/
    └── IND/
```

The structure allows the results to be consulted independently for each test system and power factor condition.

## Results by Scenario

Within each condition, the results corresponding to the six considered scenarios are included:

```text
Escenario_1/
Escenario_2/
Escenario_3/
Escenario_4/
Escenario_5/
Escenario_6/
```

These results contain the calculated values of the grid strength indicators:

* **SCR**
* **GSIM**
* **NRSCR**
* **SDSCR**
* **λSCR**
* **K<sub>vtg</sub>**

## Graphical Results

In addition to numerical results, the repository contains the visualizations used to compare the indicators.

The main graphical result folders include:

```text
Graficas_SCR/
Matriz_Graficas_Derecha/
Matriz_Graficas_Izquierda/
Normalized graphs/
```

For the IEEE9 system, the following folder is also included:

```text
Inorm_Figuras/
```

The `Graficas_SCR/` folder contains the comparative plots of the indicators for the different scenarios.

The `Normalized graphs/` folder contains the plots obtained after normalizing the indicators with respect to their critical values, facilitating comparison between metrics with different scales.

The `Matriz_Graficas_Derecha/` and `Matriz_Graficas_Izquierda/` folders contain the matrix representations used to jointly analyze the results of the different scenarios.

## Result Organization

In general, the results can be accessed following the structure:

```text
Test system
        │
        ▼
Power factor
        │
        ▼
Scenario
        │
        ▼
Indicator results
        │
        ▼
Visualizations
```

This organization allows the results corresponding to a specific operating condition to be identified without mixing data from different systems or scenarios.

# Reproducibility

The repository has been structured to facilitate the **reproduction of the methodology and the analyses presented in the research article**. For this purpose, the processing scripts, input files, operating scenarios, intermediate data, and results corresponding to the IEEE 9-bus and 39-bus test systems are included.

The complete reproduction of the procedure requires interaction between **DIgSILENT PowerFactory** and **Python**, following the execution workflow described in the [Execution](#execution) section.

## Reproduction Workflow

In general, the reproduction of the results follows the workflow below:

```text
Test system
       │
       ▼
PowerFactory modeling
       │
       ▼
Network data export
       │
       ▼
Zbus calculation
       │
       ▼
Identification of electrically close buses
       │
       ▼
IBR selection and modeling
       │
       ▼
Power sweep
       │
       ▼
Operating point selection
       │
       ▼
Scenario definition
       │
       ▼
Scenario data extraction
       │
       ▼
Indicator calculation
       │
       ▼
Analysis and visualization
```

## Required Elements for Reproduction

To reproduce the procedure, the following elements are required:

1. **Test system model** in DIgSILENT PowerFactory.
2. **PowerFactory scripts** included in the `powerfactory/` directory.
3. **Python scripts** included in the `python/` directories.
4. **Input data** included in `data/example/`.
5. **Scenario definitions** included in `data/scenarios/`.
6. **Python dependencies** described in the [Requirements](#requirements) section.

## Stages Requiring Manual Intervention

Although a significant portion of the processing is automated through the scripts included in the repository, some stages require user intervention.

In particular:

### IBR Bus Selection

After executing `find_electrically_close_nodes.py`, the user must review:

```text
pares_nodos_cercanos.csv
```

and select the buses that will be used to connect the IBR sources.

### IBR Modeling

The two IBRs must be manually incorporated into the PowerFactory model at the selected buses and configured using the **WECC** control model.

### Operating Point Selection

After executing the power sweep scripts, the user must review:

```text
boundary_plot_PV1_PV2.png
```

and select the operating points that will be used to construct the scenarios.

### Scenario Definition

The selected points must be manually entered in:

```text
Potencias_Comp_PV1_PV2.xlsx
```

The scenarios must be defined independently for the `CAP` and `IND` conditions.

These manual interventions are part of the methodological procedure and allow the methodology to be adapted to different test systems and operating conditions.

## Reproduction of the Final Results

Once the scenarios have been defined, the results can be reproduced by following the automated stages:

```text
extract_scenario_data.py
        │
        ▼
calculate_indicators.py
        │
        ▼
Scenario Comparative.py
        │
        ▼
Indicator Comparative.py
```

The intermediate data generated during processing are stored in:

```text
data/results/
```

while the figures and final results are stored in:

```text
results/
```

The comparison between the reproduced results and the results included in the repository allows the behavior of the indicators to be verified under the same operating conditions.

## Cases Included in the Repository

The repository contains the results corresponding to the following cases:

| System      | Power factor       | Scenarios |
| ----------- | ------------------ | --------: |
| IEEE 9-bus  | Capacitive (`CAP`) |         6 |
| IEEE 9-bus  | Inductive (`IND`)  |         6 |
| IEEE 39-bus | Capacitive (`CAP`) |         6 |
| IEEE 39-bus | Inductive (`IND`)  |         6 |

In total, **24 scenario conditions** are included, corresponding to the combinations of test system, power factor, and operating scenario.

## Recommendations for Reproduction

To obtain results comparable with those included in the repository, the following recommendations should be followed:

* Maintain the original repository directory structure.
* Use a compatible version of DIgSILENT PowerFactory.
* Maintain the same configurations of the IBR models used in the study.
* Use the WECC control model for the IBRs.
* Maintain the power factor conditions corresponding to each set of scenarios.
* Do not modify automatically generated files during processing.
* Execute the scripts in the order established in the [Execution](#execution) section.
* Modify only the parameters whose modification is explicitly indicated in each script.

The combination of the files included in the repository and the documented execution workflow allows the grid strength assessment procedure presented in the article to be reproduced for the test systems considered.