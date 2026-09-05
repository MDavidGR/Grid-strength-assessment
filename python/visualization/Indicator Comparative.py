import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import scipy.stats as stats
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from pathlib import Path


# Raíz del repositorio
REPO_ROOT = Path(__file__).resolve().parents[2]

# Ejemplo que se desea procesar
EXAMPLE = "IEEE39"
#Tipo de genración
GENTIP = "IND" # Si es Inductivo "IND", si es capacitivo "CAP"
#Tipo de genración
SCENARIO = EXAMPLE + "I" # Si es Inductivo "I", si es capacitivo "C"

######################################################################
################ 1.Definicion Margen Real de Potencia ################
######################################################################

# =========================
# CONFIGURACIÓN DE RUTAS
# =========================

INPUT_PATH1 = REPO_ROOT / "data" / "results" / EXAMPLE / SCENARIO
INPUT_PATH2 = REPO_ROOT / "data" / "scenarios" / EXAMPLE / GENTIP
OUTPUT_PATH1 = REPO_ROOT / "results" / EXAMPLE / GENTIP

#BASE_PATH = r"C:\Users\medag\OneDrive\Escritorio\Maestria\Tesis\Codigos\Resultados Comv"

boundary_file = os.path.join(INPUT_PATH1, "boundary_PV1_PV2.csv")
powers_file = os.path.join(INPUT_PATH2, "Potencias_Comp_PV1_PV2.xlsx")
output_file = os.path.join(OUTPUT_PATH1, "Margenes_PV1_PV2.csv")

# =========================
# CARGA DE DATOS
# =========================

boundary_df = pd.read_csv(boundary_file)
powers_df = pd.read_excel(powers_file)

# Renombrar columnas para claridad
boundary_df = boundary_df.rename(columns={
    "P1_MW": "PV1_Pmax",
    "P2_MW": "PV2_Pmax"
})

powers_df = powers_df.rename(columns={
    "PV1": "PV1_Pbase",
    "PV2": "PV2_Pbase"
})

# =========================
# CÁLCULO DE MÁRGENES
# =========================

results = []

for _, scen in powers_df.iterrows():
    pv1_base = scen["PV1_Pbase"]
    pv2_base = scen["PV2_Pbase"]

    # Distancia euclidiana a la frontera Pimax
    boundary_df["dist"] = np.sqrt(
        (boundary_df["PV1_Pmax"] - pv1_base)**2 +
        (boundary_df["PV2_Pmax"] - pv2_base)**2
    )

    # Punto más cercano sobre la frontera
    closest = boundary_df.loc[boundary_df["dist"].idxmin()].copy()

    # Guardar datos del escenario
    closest["Escenario"] = scen["Escenario"]
    closest["PV1_Pbase"] = pv1_base
    closest["PV2_Pbase"] = pv2_base

    # Margen real de potencia
    closest["Margin_PV1"] = closest["PV1_Pmax"] - pv1_base
    closest["Margin_PV2"] = closest["PV2_Pmax"] - pv2_base

    # Margen total (norma)
    closest["Margin_Total"] = np.sqrt(
        closest["Margin_PV1"]**2 + closest["Margin_PV2"]**2
    )

    results.append(closest)

# =========================
# EXPORTAR RESULTADOS
# =========================

result_df = pd.DataFrame(results)
result_df.to_csv(output_file, index=False)

print("Archivo generado exitosamente:")
print(output_file)

######################################################################
################ 2.Normalizacion de Indicadores ######################
######################################################################

INPUT_PATH3 = REPO_ROOT / "results" / EXAMPLE / GENTIP

Indicadores_file = os.path.join(INPUT_PATH3,f"resumen_combinado_completo_{GENTIP}.csv")
outputInd_file = os.path.join(OUTPUT_PATH1, "Indicadores_Normalizados.csv")

# =========================
# CARGA DE DATOS
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

escenario_col = Ind_df["Escenario"] #Se guarda columna Escenario por separado
Bus_PV = Ind_df["Bus_LV"] #Se guarda columna Escenario por separado
indicators_df = Ind_df[indicator_cols].copy()

# =========================
# NORMALIZACIÓN 1 — MINMAX
# =========================

minmax_Ind_df = (indicators_df - indicators_df.min()) / (indicators_df.max() - indicators_df.min())

# =========================
# NORMALIZACIÓN 2 — ZSCORE (revisar la presuncion de los resultados, como comprobarlo)
# =========================

zscore_df = (indicators_df - indicators_df.mean()) / indicators_df.std() #Buscar la forma de sustentar el comportamiento de los resultados

#######################################################################################################
####################### Sustentacion de comportamiento de los resultados ##############################
#######################################################################################################

# ------------------------------------------------
# 1. Estadísticas antes de normalizar
# ------------------------------------------------

stats_original = pd.DataFrame({
    "Media": indicators_df.mean(),
    "Desviacion_std": indicators_df.std(),
    "Min": indicators_df.min(),
    "Max": indicators_df.max()
})

stats_original.to_csv("Estadisticas_Originales.csv")

# ------------------------------------------------
# 2. Verificación de propiedades del Z-score
# ------------------------------------------------

stats_zscore = pd.DataFrame({
    "Media_Z": zscore_df.mean(),
    "Desviacion_std_Z": zscore_df.std(),
    "Min_Z": zscore_df.min(),
    "Max_Z": zscore_df.max()
})

stats_zscore.to_csv("Estadisticas_Zscore.csv")

print("Media promedio tras normalización:",
      round(stats_zscore["Media_Z"].mean(), 6))

print("Desviación estándar promedio tras normalización:",
      round(stats_zscore["Desviacion_std_Z"].mean(), 6))

#######################################################################################################
#######################################################################################################

# =========================
# NORMALIZACIÓN 3
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
# NORMALIZACIÓN 4 — Normalización en función del SCR_scr
# =========================

# Parámetro crítico de referencia del SCR
SCR_crit = critical_values["SCR_scr"]

# Copia del dataframe
scr_norm_df = indicators_df.copy()

# SCR por escenario
SCR_ref = indicators_df["SCR_scr"]

for col in indicator_cols:

    if col == "SCR_scr":
        # El SCR se normaliza respecto a sí mismo
        scr_norm_df[col] = SCR_ref / SCR_crit
    else:
        # Normalización relativa al SCR
        scr_norm_df[col] = (
            (indicators_df[col] / critical_values[col]) /
            (SCR_ref / SCR_crit)
        )

# Evitar divisiones problemáticas
scr_norm_df = scr_norm_df.replace([np.inf, -np.inf], np.nan)

eng_norm_df = indicators_df.copy()

for col in indicator_cols:
    eng_norm_df[col] = indicators_df[col] / critical_values[col]

# =========================
# GUARDAR RESULTADOS
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

print("Archivo generado:")
print(outputInd_file)


######################################################################
############ 6. NORMALIZACIÓN Inorm Y GRÁFICAS #######################
######################################################################

print("\n==============================")
print("Cálculo de Inorm y gráficas")
print("==============================")

# ============================================================
# DEFINICIÓN DE PARÁMETROS CRÍTICOS
# (ajustar si es necesario)
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
# CARGAR ARCHIVO BASE
# ============================================================

indicators_file = os.path.join(INPUT_PATH3,f"resumen_combinado_completo_{GENTIP}.csv")

Inorm_output_file = os.path.join(OUTPUT_PATH1,"Indicadores_Inorm.csv")

df = pd.read_csv(indicators_file)

indicator_cols = list(critical_values.keys())

# ============================================================
# CÁLCULO Inorm
# Inorm = Indicador / Valor_critico
# ============================================================

Inorm_df = df[["Escenario", "Bus_LV"]].copy()

for col in indicator_cols:

    crit = critical_values[col]

    Inorm_df[col + "_Inorm"] = df[col] / crit

# Limpiar valores problemáticos
Inorm_df = Inorm_df.replace([np.inf, -np.inf], np.nan)

# Guardar resultados
Inorm_df.to_csv(Inorm_output_file, index=False)

print("Archivo Inorm generado:")
print(Inorm_output_file)

# ============================================================
# CREAR CARPETA DE FIGURAS
# ============================================================

FIG_PATH = OUTPUT_PATH1
FIG_INORM_PATH = os.path.join(FIG_PATH, "Normalized graphs")
os.makedirs(FIG_INORM_PATH, exist_ok=True)

# ============================================================
# FIGURA 1 — Inorm por escenario
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

    plt.title(f"Inorm por Escenario — Bus {bus}", fontsize=16)
    plt.xlabel("Escenario", fontsize=14)
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
# FIGURA 2 — RAZON RESPECTO A SCR
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

    plt.title(f"Razón Inorm respecto a SCR — Bus {bus}", fontsize=16)
    plt.xlabel("Escenario", fontsize=14)
    plt.ylabel("Inorm Indicador/Inorm SCR", fontsize=14)

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
# FIGURA 3 — BOXLOT GLOBAL (CON ZOOM)
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

ax.set_title("Distribución global de Inorm", fontsize=16)
ax.set_ylabel("Inorm", fontsize=14)

# ============================================================
# INSET (ZOOM λSCR y K_vtg)
# ============================================================

zoom_cols = [
    "λSCR_normal_LSCR_Inorm",
    "K_vtg_normal_LSCR_Inorm"
]

# Crear eje inset (posición: esquina superior derecha)
axins = inset_axes(
    ax,
    width="35%",   # tamaño relativo
    height="35%",
    loc="upper right"
)

# Boxplot solo de los indicadores pequeños
Inorm_df.boxplot(
    column=zoom_cols,
    ax=axins,
    rot=30
)

# --- Ajustar zoom manualmente ---
# (puedes afinar estos valores según tus datos)
axins.set_ylim(0, 2)

axins.set_title("Zoom λSCR y K_vtg", fontsize=9)

# Opcional: línea de referencia también en inset
axins.axhline(1, linestyle="--")

# Reducir tamaño de labels
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

print("Figuras Inorm generadas en:")
print(FIG_INORM_PATH)