import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import scipy.stats as stats
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from pathlib import Path


# Repository root
REPO_ROOT = Path(__file__).resolve().parents[2]

# Example to be processed
EXAMPLE = "IEEE39"
#Generation type
GENTIP = "IND" # If inductive "IND", if capacitive "CAP"
#Generation type
SCENARIO = EXAMPLE + "I" # If inductive "I", if capacitive "C"

######################################################################
################ 1.Definicion Margen Real de Potencia ################
######################################################################

# =========================
# PATH CONFIGURATION
# =========================

INPUT_PATH1 = REPO_ROOT / "data" / "results" / EXAMPLE / SCENARIO
INPUT_PATH2 = REPO_ROOT / "data" / "scenarios" / EXAMPLE / GENTIP
OUTPUT_PATH1 = REPO_ROOT / "results" / EXAMPLE / GENTIP

#BASE_PATH = r"C:\Users\medag\OneDrive\Escritorio\Maestria\Tesis\Codigos\Resultados Comv"

boundary_file = os.path.join(INPUT_PATH1, "boundary_PV1_PV2.csv")
powers_file = os.path.join(INPUT_PATH2, "Potencias_Comp_PV1_PV2.xlsx")
output_file = os.path.join(OUTPUT_PATH1, "Margenes_PV1_PV2.csv")

# =========================
# DATA LOADING
# =========================

boundary_df = pd.read_csv(boundary_file)
powers_df = pd.read_excel(powers_file)

# Rename columns for clarity
boundary_df = boundary_df.rename(columns={
    "P1_MW": "PV1_Pmax",
    "P2_MW": "PV2_Pmax"
})

powers_df = powers_df.rename(columns={
    "PV1": "PV1_Pbase",
    "PV2": "PV2_Pbase"
})

# =========================
# MARGIN CALCULATION
# =========================

results = []

for _, scen in powers_df.iterrows():
    pv1_base = scen["PV1_Pbase"]
    pv2_base = scen["PV2_Pbase"]

    # Euclidean distance to the Pimax boundary
    boundary_df["dist"] = np.sqrt(
        (boundary_df["PV1_Pmax"] - pv1_base)**2 +
        (boundary_df["PV2_Pmax"] - pv2_base)**2
    )

    # Closest point on the boundary
    closest = boundary_df.loc[boundary_df["dist"].idxmin()].copy()

    # Save scenario data
    closest["Escenario"] = scen["Escenario"]
    closest["PV1_Pbase"] = pv1_base
    closest["PV2_Pbase"] = pv2_base

    # Real power margin
    closest["Margin_PV1"] = closest["PV1_Pmax"] - pv1_base
    closest["Margin_PV2"] = closest["PV2_Pmax"] - pv2_base

    # Total margin (norm)
    closest["Margin_Total"] = np.sqrt(
        closest["Margin_PV1"]**2 + closest["Margin_PV2"]**2
    )

    results.append(closest)

# =========================
# EXPORT RESULTS
# =========================

result_df = pd.DataFrame(results)
result_df.to_csv(output_file, index=False)

print("File successfully generated:")
print(output_file)

######################################################################
################ 2.Normalizacion de Indicadores ######################
######################################################################

INPUT_PATH3 = REPO_ROOT / "results" / EXAMPLE / GENTIP

Indicadores_file = os.path.join(INPUT_PATH3,f"resumen_combinado_completo_{GENTIP}.csv")
outputInd_file = os.path.join(OUTPUT_PATH1, "Indicadores_Normalizados.csv")

# =========================
# DATA LOADING
# =========================

Ind_df = pd.read_csv(Indicadores_file)
#print("Columnas disponibles en el archivo:")
#print(Ind_df.columns.tolist())

indicator_cols = [
    "SCR_scr",
    "GSIM_hv",
    "NRSCR",
    "SDSCR_coupled",
    "λSCR_normal_LSCR",
    "K_vtg_normal_LSCR"
]

escenario_col = Ind_df["Escenario"] #Scenario column is stored separately
Bus_PV = Ind_df["Bus_LV"] #Scenario column is stored separately
indicators_df = Ind_df[indicator_cols].copy()

# =========================
# NORMALIZATION 1 — MINMAX
# =========================

minmax_Ind_df = (indicators_df - indicators_df.min()) / (indicators_df.max() - indicators_df.min())

# =========================
# NORMALIZATION 2 — Z-SCORE (review the assumption about the results and how to verify it)
# =========================

zscore_df = (indicators_df - indicators_df.mean()) / indicators_df.std() #Find a way to support the behavior of the results

#######################################################################################################
####################### Sustentacion de comportamiento de los resultados ##############################
#######################################################################################################

# ------------------------------------------------
# 1. Statistics before normalization
# ------------------------------------------------

stats_original = pd.DataFrame({
    "Media": indicators_df.mean(),
    "Desviacion_std": indicators_df.std(),
    "Min": indicators_df.min(),
    "Max": indicators_df.max()
})

stats_original.to_csv("Estadisticas_Originales.csv")

# ------------------------------------------------
# 2. Verification of Z-score properties
# ------------------------------------------------

stats_zscore = pd.DataFrame({
    "Media_Z": zscore_df.mean(),
    "Desviacion_std_Z": zscore_df.std(),
    "Min_Z": zscore_df.min(),
    "Max_Z": zscore_df.max()
})

stats_zscore.to_csv("Estadisticas_Zscore.csv")

print("Average mean after normalization:",
      round(stats_zscore["Media_Z"].mean(), 6))

print("Average standard deviation after normalization:",
      round(stats_zscore["Desviacion_std_Z"].mean(), 6))

#######################################################################################################
#######################################################################################################

# =========================
# NORMALIZATION 3
# =========================

critical_values = {
    "SCR_scr": 3,
    "GSIM_hv": 0.6,
    "NRSCR": 3,
    "SDSCR_coupled": 3,
    "λSCR_normal_LSCR": 3,
    "K_vtg_normal_LSCR":0.6
}

# =========================
# NORMALIZATION 4 — Normalization based on SCR_scr
# =========================

# SCR reference critical parameter
SCR_crit = critical_values["SCR_scr"]

# DataFrame copy
scr_norm_df = indicators_df.copy()

# SCR by scenario
SCR_ref = indicators_df["SCR_scr"]

for col in indicator_cols:

    if col == "SCR_scr":
        # SCR is normalized with respect to itself
        scr_norm_df[col] = SCR_ref / SCR_crit
    else:
        # Normalization relative to SCR
        scr_norm_df[col] = (
            (indicators_df[col] / critical_values[col]) /
            (SCR_ref / SCR_crit)
        )

# Avoid problematic divisions
scr_norm_df = scr_norm_df.replace([np.inf, -np.inf], np.nan)

eng_norm_df = indicators_df.copy()

for col in indicator_cols:
    eng_norm_df[col] = indicators_df[col] / critical_values[col]

# =========================
# SAVE RESULTS
# =========================

combined = pd.concat([
    escenario_col,
    Bus_PV,
    indicators_df,
    minmax_Ind_df.add_suffix("_minmax"),
    zscore_df.add_suffix("_zscore"),
    eng_norm_df.add_suffix("_eng"),
    scr_norm_df.add_suffix("_scr")
], axis=1)

combined.to_csv(outputInd_file, index=False)

print("File generated:")
print(outputInd_file)


######################################################################
############ 6. NORMALIZACIÓN Inorm Y GRÁFICAS #######################
######################################################################

print("\n==============================")
print("Inorm calculation and graphs")
print("==============================")

# ============================================================
# DEFINITION OF CRITICAL PARAMETERS
# (adjust if necessary)
# ============================================================

critical_values = {
    "SCR_scr": 3,
    "GSIM_hv": 0.6,
    "NRSCR": 3,
    "SDSCR_coupled": 3,
    "λSCR_normal_LSCR": 3,
    "K_vtg_normal_LSCR":0.6
}

# ============================================================
# LOAD BASE FILE
# ============================================================

indicators_file = os.path.join(INPUT_PATH3,f"resumen_combinado_completo_{GENTIP}.csv")

Inorm_output_file = os.path.join(OUTPUT_PATH1,"Indicadores_Inorm.csv")

df = pd.read_csv(indicators_file)

indicator_cols = list(critical_values.keys())

# ============================================================
# Inorm CALCULATION
# Inorm = Indicator / Critical_value
# ============================================================

Inorm_df = df[["Escenario", "Bus_LV"]].copy()

for col in indicator_cols:

    crit = critical_values[col]

    Inorm_df[col + "_Inorm"] = df[col] / crit

# Clean problematic values
Inorm_df = Inorm_df.replace([np.inf, -np.inf], np.nan)

# Save results
Inorm_df.to_csv(Inorm_output_file, index=False)

print("Inorm file generated:")
print(Inorm_output_file)

# ============================================================
# CREATE FIGURE FOLDER
# ============================================================

FIG_PATH = OUTPUT_PATH1
FIG_INORM_PATH = os.path.join(FIG_PATH, "Normalized graphs")
os.makedirs(FIG_INORM_PATH, exist_ok=True)

# ============================================================
# FIGURE 1 — Inorm by scenario
# ============================================================

for bus in Inorm_df["Bus_LV"].unique():

    df_bus = Inorm_df[Inorm_df["Bus_LV"] == bus]

    plt.figure(figsize=(10, 6))

    for col in indicator_cols:

        plt.plot(
            df_bus["Escenario"],
            df_bus[col + "_Inorm"],
            label=col
        )

    plt.axhline(1, linestyle="--")

    plt.title(f"Inorm by Scenario — Bus {bus}", fontsize=16)
    plt.xlabel("Scenario", fontsize=14)
    plt.ylabel("Inorm", fontsize=14)
    plt.xticks(rotation=45)

    plt.legend()
    plt.tight_layout()

    filename = f"Inorm_Bus_{bus}.png"

    plt.savefig(
        os.path.join(FIG_INORM_PATH, filename),
        dpi=300
    )

    plt.close()

# ============================================================
# FIGURE 2 — RATIO WITH RESPECT TO SCR
# ΔInorm = Inorm_i / Inorm_SCR
# ============================================================

for bus in Inorm_df["Bus_LV"].unique():

    df_bus = Inorm_df[Inorm_df["Bus_LV"] == bus]

    SCR_ref = df_bus["SCR_scr_Inorm"]

    plt.figure(figsize=(10, 6))

    for col in indicator_cols:

        if col == "SCR_scr":
            continue

        delta = df_bus[col + "_Inorm"] / SCR_ref

        plt.plot(
            df_bus["Escenario"],
            delta,
            label=f"{col} − SCR"
        )

    plt.axhline(0, linestyle="--")

    plt.title(f"Inorm reason regarding SCR — Bus {bus}", fontsize=16)
    plt.xlabel("Scenario", fontsize=14)
    plt.ylabel("Inorm Indicator/Inorm SCR", fontsize=14)

    plt.xticks(rotation=45)

    plt.legend()
    plt.tight_layout()

    filename = f"Delta_Inorm_Bus_{bus}.png"

    plt.savefig(
        os.path.join(FIG_INORM_PATH, filename),
        dpi=300
    )

    plt.close()

# ============================================================
# FIGURE 3 — GLOBAL BOXPLOT (WITH ZOOM)
# ============================================================

Inorm_cols = [
    col + "_Inorm"
    for col in indicator_cols
]

fig, ax = plt.subplots(figsize=(10, 6))

# --- Boxplot principal ---
Inorm_df.boxplot(
    column=Inorm_cols,
    rot=45,
    ax=ax
)

ax.axhline(1, linestyle="--")

ax.set_title("Global distribution of Inorm", fontsize=16)
ax.set_ylabel("Inorm", fontsize=14)

# ============================================================
# INSET (ZOOM λSCR and K_vtg)
# ============================================================

zoom_cols = [
    "λSCR_normal_LSCR_Inorm",
    "K_vtg_normal_LSCR_Inorm"
]

# Create inset axis (position: upper-right corner)
axins = inset_axes(
    ax,
    width="35%",   # relative size
    height="35%",
    loc="upper right"
)

# Boxplot only for the small indicators
Inorm_df.boxplot(
    column=zoom_cols,
    ax=axins,
    rot=30
)

# --- Ajustar zoom manualmente ---
# (you can fine-tune these values according to your data)
axins.set_ylim(0, 2)

axins.set_title("Zoom λSCR y K_vtg", fontsize=9)

# Optional: reference line also in inset
axins.axhline(1, linestyle="--")

# Reduce label size
axins.tick_params(axis='x', labelsize=8)
axins.tick_params(axis='y', labelsize=8)

plt.tight_layout()

plt.savefig(
    os.path.join(
        FIG_INORM_PATH,
        "Boxplot_Inorm_Global.png"
    ),
    dpi=300
)

plt.close()

print("Inorm figures generated in:")
print(FIG_INORM_PATH)