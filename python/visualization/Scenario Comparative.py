import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Repository root
REPO_ROOT = Path(__file__).resolve().parents[2]

# Example to be processed
EXAMPLE = "IEEE39"

#Generation type
GENTIP = "IND" # If inductive "IND", if capacitive "CAP"

# Folder where indicator results will be saved
# ------------------------------------------------------------
OUTPUT_PATH = REPO_ROOT / "results" / EXAMPLE / GENTIP

# Define the base path where all scenarios are located
ruta_base = OUTPUT_PATH
ruta_salida_final = os.path.join(OUTPUT_PATH, f"resumen_combinado_completo_{GENTIP}.csv")

# List to store results from all scenarios
todos_los_datos = []

# Get all scenario folders
carpetas_escenarios = [carpeta for carpeta in os.listdir(ruta_base) 
                      if os.path.isdir(os.path.join(ruta_base, carpeta)) and carpeta.startswith('Escenario_')]

print(f"Scenarios encountered: {carpetas_escenarios}")

for escenario in carpetas_escenarios:
    print(f"\n{'='*60}")
    print(f"PROCESSING: {escenario}")
    print(f"{'='*60}")
    
    # Define the specific paths for this scenario
    ruta_escenario = os.path.join(ruta_base, escenario)
    ruta_gsim = os.path.join(ruta_escenario, 'GSIM_results.csv')
    ruta_nrscr = os.path.join(ruta_escenario, 'NRSCR_results.csv')
    ruta_sdscr = os.path.join(ruta_escenario, 'SDSCR_results.csv')
    ruta_lscr = os.path.join(ruta_escenario, 'LSCR_results.csv')
    ruta_scr = os.path.join(ruta_escenario, 'SCR_results.csv')
    
    # Check that all files exist for this scenario
    archivos_faltantes = []
    for archivo, ruta in [('GSIM_results.csv', ruta_gsim), 
                          ('NRSCR_results.csv', ruta_nrscr),
                          ('SDSCR_results.csv', ruta_sdscr),
                          ('LSCR_results.csv', ruta_lscr),
                          ('SCR_results.csv', ruta_scr)]:
        if not os.path.exists(ruta):
            archivos_faltantes.append(archivo)
    
    if archivos_faltantes:
        print(f"  ❌ Missing files in {escenario}: {archivos_faltantes}")
        continue
    
    try:
        # Read SCR file (SCR_results.csv)
        df_scr = pd.read_csv(ruta_scr)

        # 1) Extract the requested columns from the file
        columnas_scr = ['Escenario', 'Generador', 'Potencia_Generador_MW', 'Potencia_Cortocircuito_MVA', 'SCR_scr']
        df_scr_filtrado = df_scr[columnas_scr].copy()
        
        # Read the first file (GSIM_results.csv)
        df_gsim = pd.read_csv(ruta_gsim)

        # 1) Extract the requested columns from the first file
        columnas_gsim = ['escenario', 'bus', 'S_sc_HV', 'SCR_HV', 'GSIM_hv']
        df_gsim_filtrado = df_gsim[columnas_gsim].copy()

        # 2) Filter only buses whose names contain "PV" and "LV"
        df_gsim_final = df_gsim_filtrado[df_gsim_filtrado['bus'].str.contains('PV.*LV', na=False)]

        # Read the second file (NRSCR_results.csv)
        df_nrscr = pd.read_csv(ruta_nrscr)

        # 1) Filter only buses whose names contain "PV" and "LV"
        # 2) Extract the SCR, NRSCR, and High-Voltage Bus columns
        df_nrscr_filtrado = df_nrscr[df_nrscr['Nodo IBR'].str.contains('PV.*LV', na=False)]
        df_nrscr_final = df_nrscr_filtrado[['Nodo IBR', 'Nodo Alta', 'SCR', 'NRSCR']].copy()

        # Rename columns to identify their source
        df_gsim_final.columns = ['Escenario', 'Bus_LV', 'S_sc_HV_GSIM', 'SCR_HV_GSIM', 'GSIM_hv']
        df_nrscr_final.columns = ['Bus_LV', 'Bus_HV', 'SCR_NRSCR', 'NRSCR']

        # Merge both DataFrames using the 'Bus_LV' column
        df_combinado = pd.merge(df_gsim_final, df_nrscr_final, on='Bus_LV', how='inner')

        # =============================================================================
        # PROCESSING OF SDSCR_RESULTS.CSV
        # =============================================================================

        # Read the third file (SDSCR_results.csv)
        df_sdscr = pd.read_csv(ruta_sdscr)

        # 1) Usar los buses HV que ya extrajimos del CSV anterior
        buses_hv_extraidos = df_combinado['Bus_HV'].unique()

        # 2) Filtrar SDSCR_results para incluir solo los buses que están en nuestra lista
        buses_hv_formateados = [bus.replace('Bus', 'BUS') for bus in buses_hv_extraidos]

        df_sdscr_filtrado = df_sdscr[df_sdscr['Bus'].isin(buses_hv_formateados)]

        # 3) Extract the SCR, SDSCR_coupled, and SDSCR_no_coupling columns
        df_sdscr_final = df_sdscr_filtrado[['Bus', 'SCR', 'SDSCR_coupled', 'SDSCR_no_coupling']].copy()

        # Rename SDSCR columns
        df_sdscr_final.columns = ['Bus_HV_SDSCR', 'SCR_SDSCR', 'SDSCR_coupled', 'SDSCR_no_coupling']

        # Merge with the main DataFrame
        df_combinado['Bus_HV_SDSCR'] = df_combinado['Bus_HV'].str.replace('Bus', 'BUS')
        df_combinado = pd.merge(df_combinado, df_sdscr_final, on='Bus_HV_SDSCR', how='left')
        df_combinado = df_combinado.drop('Bus_HV_SDSCR', axis=1)

        # =============================================================================
        # PROCESSING OF LSCR_RESULTS.CSV
        # =============================================================================

        # Read the fourth file (LSCR_results.csv)
        df_lscr = pd.read_csv(ruta_lscr)

        # 1) Usar los buses HV que ya extrajimos (columna "Barra Cálculo")
        buses_hv_extraidos = df_combinado['Bus_HV'].unique()

        # 2) Filtrar LSCR_results para incluir solo los buses que están en nuestra lista
        df_lscr_filtrado = df_lscr[df_lscr['Barra Cálculo'].isin(buses_hv_extraidos)]

        # 3) Extract the Z_device, K_vtg_normal, and λSCR_normal columns
        df_lscr_final = df_lscr_filtrado[['Barra Cálculo', 'Z_device', 'K_vtg_fault', 'λSCR_fault']].copy()

        # Rename LSCR columns
        df_lscr_final.columns = ['Bus_HV', 'Z_device_LSCR', 'K_vtg_normal_LSCR', 'λSCR_normal_LSCR']

        # Merge with the main DataFrame
        df_combinado_final = pd.merge(df_combinado, df_lscr_final, on='Bus_HV', how='left')
        
        # =============================================================================
        # ADD DATA FROM SCR_RESULTS.CSV
        # =============================================================================
        # ==================== 4 LÍNEAS CORREGIDAS ====================
        # Extract the LV bus name from the generator (assuming it contains "PV" and "LV")
        # Clean names
        df_scr_filtrado['Bus_LV'] = df_scr_filtrado['Generador'] + ' LV'
        df_combinado_final['Bus_LV'] = df_combinado_final['Bus_LV']
        # Correct merge
        df_combinado_final = pd.merge(df_combinado_final, df_scr_filtrado[['Bus_LV', 'SCR_scr']], on='Bus_LV', how='left')
        # ===========================================================

        # Add this scenario's data to the general list
        print(df_combinado_final[['Bus_LV', 'SCR_scr']])
        todos_los_datos.append(df_combinado_final)
        
        print(f"  ✅ {escenario} successfully processed - {len(df_combinado_final)} records")
        
    except Exception as e:
        print(f"  ❌ Error processing {escenario}: {str(e)}")
        continue

# Combine all data from all scenarios
if todos_los_datos:
    df_final_completo = pd.concat(todos_los_datos, ignore_index=True)
    
    # Save the final result to the specified path
    df_final_completo.to_csv(ruta_salida_final, index=False)
    
    print(f"\n{'='*60}")
    print("PROCESSING COMPLETED")
    print(f"{'='*60}")
    print(f"Final file saved in: {ruta_salida_final}")
    print(f"Total scenarios processed: {len(todos_los_datos)}")
    print(f"Total records in the final file: {len(df_final_completo)}")
    print(f"\nColumns in the final file:")
    for col in df_final_completo.columns:
        print(f"  - {col}")
else:
    print("\n❌ No scenario could be processed. Verify that the files exist.")

# =============================================================================
# NEW SECTION: CREATION OF ENHANCED PLOTS FOR EACH SCENARIO
# =============================================================================

print(f"\n{'='*60}")
print("CREATING GRAPHS FOR EACH SCENARIO")
print(f"{'='*60}")

# Create folder to save plots if it does not exist
carpeta_graficas = os.path.join(ruta_base, 'Graficas_SCR')
os.makedirs(carpeta_graficas, exist_ok=True)

# Check which columns are actually available
columnas_disponibles = df_final_completo.columns.tolist()
print(f"\nColumns available in the final DataFrame: {columnas_disponibles}")

# Specific variables to plot
variables_scr = ['SCR_scr', 'GSIM_hv', 'NRSCR', 'SDSCR_coupled', 'K_vtg_normal_LSCR', 'λSCR_normal_LSCR']
variables_scr = [var for var in variables_scr if var in columnas_disponibles]

nombres_legibles = {
    'SCR_scr': 'SCR_R',
    'GSIM_hv': 'GSIM HV',
    'NRSCR': 'NRSCR',
    'SDSCR_coupled': 'SDSCR Acoplado',
    'K_vtg_normal_LSCR': 'K_vtg Normal (LSCR)',
    'λSCR_normal_LSCR': 'λSCR normal (LSCR)'
}

# Filter readable names for existing variables
nombres_legibles = {k: v for k, v in nombres_legibles.items() if k in variables_scr}


for escenario in df_final_completo['Escenario'].unique():
    print(f"Generating graph for: {escenario}")
    
    # Filter data for the current scenario
    datos_escenario = df_final_completo[df_final_completo['Escenario'] == escenario]
    
    # Configure the plot style
    plt.style.use('default')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))
    fig.suptitle(f'Comparative Analysis of SCR Methods - {escenario}', fontsize=16, fontweight='bold', y=0.95)
    
    # ===== GRÁFICA 1: COMPARACIÓN DE MÉTODOS SCR (valores altos) =====
    buses = datos_escenario['Bus_LV'].values
    x = np.arange(len(buses))
    width = 0.15
    
    # Methods with high values (main SCR methods)
    metodos_altos = ['SCR_scr', 'GSIM_hv', 'NRSCR', 'SDSCR_coupled']
    
    # Define Palette 4 (Scientific/Springer)
    paleta4 = ['#004c6d', '#346b8c', '#5a8aab', '#7eaac9']

# Create bars for each SCR method
    for i, metodo in enumerate(metodos_altos):
        valores = datos_escenario[metodo].replace([np.inf, -np.inf], np.nan).values
        # Assign palette color according to the index (cycling if there are more methods than colors)
        color = paleta4[i % len(paleta4)]
        ax1.bar(x + i * width, valores, width, label=nombres_legibles[metodo], 
                color=color, alpha=0.8, edgecolor='black', linewidth=0.5)
    
    ax1.set_xlabel('Buses', fontweight='bold', fontsize=12)
    ax1.set_ylabel('SCR Value', fontweight='bold', fontsize=12)
    ax1.set_title('Comparison of Main SCR Methods', fontweight='bold', fontsize=13)
    ax1.set_xticks(x + width * 1.5)
    ax1.set_xticklabels(buses, fontweight='bold')
    ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(0, max(datos_escenario[metodos_altos].max().max() * 1.2, 15))
    
    # Add values to the bars
    for i, metodo in enumerate(metodos_altos):
        valores = datos_escenario[metodo].values
        for j, valor in enumerate(valores):
            if np.isfinite(valor):
                ax1.text(x[j] + i * width, valor + 0.1, f'{valor:.2f}', 
                        ha='center', va='bottom', fontsize=9, rotation=45)
    
    # ===== GRÁFICA 2: INDICADOR K_vtg_normal_LSCR (valores bajos) =====
    # This variable has much lower values and needs a separate scale
    x_kvtg = np.arange(len(buses))
    width = 0.35

    valores_kvtg = datos_escenario['K_vtg_normal_LSCR'].values
    valores_lambda = datos_escenario['λSCR_normal_LSCR'].values

    # Bars for K_vtg
    bars1 = ax2.bar(x - width/2, valores_kvtg, width, color='#004c6d', alpha=0.8,
                    label=nombres_legibles['K_vtg_normal_LSCR'])
    
    # Bars for λSCR (next to it)
    bars2 = ax2.bar(x + width/2, valores_lambda, width, color='#346b8c', alpha=0.8,
                    label=nombres_legibles['λSCR_normal_LSCR'])
    
    ax2.set_xlabel('Buses', fontweight='bold', fontsize=12)
    ax2.set_ylabel('Valor', fontweight='bold', fontsize=12)
    ax2.set_title('Comparison K_vtg Normal vs λSCR (LSCR)', fontweight='bold', fontsize=13)
    ax2.set_xticks(x)
    ax2.set_xticklabels(buses, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Add values to the K_vtg bars
    for j, valor in enumerate(valores_kvtg):
        ax2.text(x[j] - width/2, valor + 0.0005, f'{valor:.4f}', 
                ha='center', va='bottom', fontsize=8, rotation=45)
    
    # Add values to the λSCR bars
    for j, valor in enumerate(valores_lambda):
        ax2.text(x[j] + width/2, valor + 0.0005, f'{valor:.4f}', 
                ha='center', va='bottom', fontsize=8, rotation=45)

    # Adjust the Y-axis limits so that the values fit within the plot
    valor_maximo = max(valores_kvtg.max(), valores_lambda.max())
    margen_superior = valor_maximo * 0.15  # 15% margin above the highest value
    ax2.set_ylim(0, valor_maximo + margen_superior)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save plot
    nombre_archivo = f"{escenario}_Analisis_SCR_Comparativo.png"
    ruta_grafica = os.path.join(carpeta_graficas, nombre_archivo)
    plt.savefig(ruta_grafica, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✅ Graph saved: {nombre_archivo}")


#####################################################################################

# =============================================================================
# NEW SECTION: CREATION OF CONSOLIDATED PLOT MATRICES
# =============================================================================

print(f"\n{'='*60}")
print("Creating Consolidated Graph Matrices")
print(f"{'='*60}")

# Create folders for plot matrices
carpeta_matriz_izquierda = os.path.join(ruta_base, 'Matriz_Graficas_Izquierda')
carpeta_matriz_derecha = os.path.join(ruta_base, 'Matriz_Graficas_Derecha')
os.makedirs(carpeta_matriz_izquierda, exist_ok=True)
os.makedirs(carpeta_matriz_derecha, exist_ok=True)

# Function to arrange scenarios in a grid
def organizar_en_cuadricula(n_escenarios):
    """Determine the grid dimensions based on the number of scenarios"""
    if n_escenarios <= 2:
        return 1, n_escenarios
    elif n_escenarios <= 4:
        return 2, 2
    elif n_escenarios <= 6:
        return 2, 3
    elif n_escenarios <= 9:
        return 3, 3
    elif n_escenarios <= 12:
        return 3, 4
    else:
        return 4, 4

# Get the sorted list of unique scenarios
escenarios_unicos = sorted(df_final_completo['Escenario'].unique())
n_escenarios = len(escenarios_unicos)

print(f"\nTotal number of scenarios: {n_escenarios}")
print(f"Scenarios: {escenarios_unicos}")

# Determine grid dimensions
filas, columnas = organizar_en_cuadricula(n_escenarios)

# ===== MATRIZ DE GRÁFICAS DE LA IZQUIERDA (Comparación de Métodos SCR Principales) =====
print(f"\nCreating matrix of graphs on the LEFT ({filas}x{columnas})...")

# Create figure for the left matrix
fig_izquierda, axes_izquierda = plt.subplots(filas, columnas, figsize=(6*columnas, 5*filas))
#fig_izquierda.suptitle('MATRIZ COMPARATIVA: Indicadores SCR por Escenario', fontsize=20, fontweight='bold', y=0.98)

# Flatten axes to facilitate iteration
if filas == 1 and columnas == 1:
    axes_izquierda = np.array([axes_izquierda])
axes_izquierda = axes_izquierda.flatten()

# Color palette for the methods
paleta4 = ['#004c6d', '#346b8c', '#5a8aab', '#7eaac9']
metodos_altos = ['SCR_scr', 'GSIM_hv', 'NRSCR', 'SDSCR_coupled']

# Variable to control the global maximum limit
max_global_izquierda = 0

# First pass: calculate the global maximum
for escenario in escenarios_unicos:
    datos_escenario = df_final_completo[df_final_completo['Escenario'] == escenario]
    for metodo in metodos_altos:
        if metodo in datos_escenario.columns:
            max_valor = datos_escenario[metodo].max()
            if max_valor > max_global_izquierda:
                max_global_izquierda = max_valor

# Add 20% margin to the global maximum
max_global_izquierda = max_global_izquierda * 1.2

# Generate each left subplot
for idx, escenario in enumerate(escenarios_unicos):
    if idx >= len(axes_izquierda):
        break
        
    ax = axes_izquierda[idx]
    datos_escenario = df_final_completo[df_final_completo['Escenario'] == escenario]
    buses = datos_escenario['Bus_LV'].values
    x = np.arange(len(buses))
    width = 0.2  # Width adjusted for matrix
    
    # Create bars for each method
    for i, metodo in enumerate(metodos_altos):
        if metodo in datos_escenario.columns:
            valores = datos_escenario[metodo].replace([np.inf, -np.inf], np.nan).values
            color = paleta4[i % len(paleta4)]
            ax.bar(x + i * width, valores, width, label=nombres_legibles.get(metodo, metodo), 
                   color=color, alpha=0.8, edgecolor='black', linewidth=0.5)
    
    # Configure the subplot
    ax.set_title(f'{escenario}', fontweight='bold', fontsize=16)
    ax.set_xlabel('Buses', fontsize=14)
    ax.set_ylabel('SCR', fontsize=14)
    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels(buses, fontsize=10, rotation=45, ha='right')
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_ylim(0, max_global_izquierda)
    
    # Add values to the bars (with fewer decimals for clarity)
    for i, metodo in enumerate(metodos_altos):
        if metodo in datos_escenario.columns:
            valores = datos_escenario[metodo].values
            for j, valor in enumerate(valores):
                if np.isfinite(valor) and valor > 0:
                    ax.text(x[j] + i * width, valor + max_global_izquierda*0.02, 
                           f'{valor:.1f}', ha='center', va='bottom', fontsize=7, rotation=45)
    
    # Only add legend to the first subplot if there is space
    if idx == 0:
        ax.legend(loc='upper left', fontsize=8)

# Hide unused axes
for idx in range(len(escenarios_unicos), len(axes_izquierda)):
    axes_izquierda[idx].axis('off')

plt.tight_layout()
ruta_matriz_izquierda = os.path.join(carpeta_matriz_izquierda, 'Matriz_SCR_Principales.png')
plt.savefig(ruta_matriz_izquierda, dpi=300, bbox_inches='tight')
plt.close()
print(f"  ✅ Left matrix saved: {ruta_matriz_izquierda}")

# ===== MATRIZ DE GRÁFICAS DE LA DERECHA (K_vtg vs λSCR) =====
print(f"\nCreating matrix of graphs on the RIGHT ({filas}x{columnas})...")

# Create figure for the right matrix
fig_derecha, axes_derecha = plt.subplots(filas, columnas, figsize=(6*columnas, 5*filas))
#fig_derecha.suptitle('MATRIZ COMPARATIVA: K_vtg Normal vs λSCR por Escenario', fontsize=20, fontweight='bold', y=0.98)

# Flatten axes
if filas == 1 and columnas == 1:
    axes_derecha = np.array([axes_derecha])
axes_derecha = axes_derecha.flatten()

# Calculate the global maximum for the right matrix
max_global_derecha = 0
for escenario in escenarios_unicos:
    datos_escenario = df_final_completo[df_final_completo['Escenario'] == escenario]
    if 'K_vtg_normal_LSCR' in datos_escenario.columns:
        max_kvtg = datos_escenario['K_vtg_normal_LSCR'].max()
        max_global_derecha = max(max_global_derecha, max_kvtg)
    if 'λSCR_normal_LSCR' in datos_escenario.columns:
        max_lambda = datos_escenario['λSCR_normal_LSCR'].max()
        max_global_derecha = max(max_global_derecha, max_lambda)

# Add 20% margin
max_global_derecha = max_global_derecha * 1.2

# Generate each right subplot
for idx, escenario in enumerate(escenarios_unicos):
    if idx >= len(axes_derecha):
        break
        
    ax = axes_derecha[idx]
    datos_escenario = df_final_completo[df_final_completo['Escenario'] == escenario]
    buses = datos_escenario['Bus_LV'].values
    x = np.arange(len(buses))
    width = 0.35
    
    # Check that the columns exist
    if 'K_vtg_normal_LSCR' in datos_escenario.columns:
        valores_kvtg = datos_escenario['K_vtg_normal_LSCR'].values
        bars1 = ax.bar(x - width/2, valores_kvtg, width, color='#004c6d',
                       alpha=0.8, label='K_vtg Normal')
        
        # Add values
        for j, valor in enumerate(valores_kvtg):
            if np.isfinite(valor):
                ax.text(x[j] - width/2, valor + max_global_derecha*0.02, 
                       f'{valor:.3f}', ha='center', va='bottom', fontsize=7, rotation=45)
    
    if 'λSCR_normal_LSCR' in datos_escenario.columns:
        valores_lambda = datos_escenario['λSCR_normal_LSCR'].values
        bars2 = ax.bar(x + width/2, valores_lambda, width, color='#346b8c',
                       alpha=0.8, label='λSCR Normal')
        
        # Add values
        for j, valor in enumerate(valores_lambda):
            if np.isfinite(valor):
                ax.text(x[j] + width/2, valor + max_global_derecha*0.02, 
                       f'{valor:.3f}', ha='center', va='bottom', fontsize=7, rotation=45)
    
    # Configure the subplot
    ax.set_title(f'{escenario}', fontweight='bold', fontsize=16)
    ax.set_xlabel('Buses', fontsize=14)
    ax.set_ylabel('Value', fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(buses, fontsize=10, rotation=45, ha='right')
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_ylim(0, max_global_derecha)
    
    # Only add legend to the first subplot
    if idx == 0:
        ax.legend(loc='upper left', fontsize=8)

# Hide unused axes
for idx in range(len(escenarios_unicos), len(axes_derecha)):
    axes_derecha[idx].axis('off')

plt.tight_layout()
ruta_matriz_derecha = os.path.join(carpeta_matriz_derecha, 'Matriz_Kvtg_vs_Lambda.png')
plt.savefig(ruta_matriz_derecha, dpi=300, bbox_inches='tight')
plt.close()
print(f"  ✅ Right matrix saved: {ruta_matriz_derecha}")

# ===== MATRIZ ADICIONAL: Gráficas de barras agrupadas por método =====
print(f"\nCreating an additional matrix of charts (bars grouped by method)...")

# Create a matrix showing the evolution of each method across scenarios
fig_evolucion, axes_evolucion = plt.subplots(len(metodos_altos), 1, 
                                              figsize=(14, 5*len(metodos_altos)))
fig_evolucion.suptitle('Evolution of SCR Methods Across Scenarios', 
                       fontsize=18, fontweight='bold', y=0.995)

for idx, metodo in enumerate(metodos_altos):
    if metodo not in df_final_completo.columns:
        continue
        
    ax = axes_evolucion[idx] if len(metodos_altos) > 1 else axes_evolucion
    
    # Prepare data for this method
    datos_metodo = []
    etiquetas_buses = []
    
    for escenario in escenarios_unicos:
        datos_escenario = df_final_completo[df_final_completo['Escenario'] == escenario]
        for bus in datos_escenario['Bus_LV'].values:
            valor = datos_escenario[datos_escenario['Bus_LV'] == bus][metodo].values[0]
            datos_metodo.append(valor)
            etiquetas_buses.append(f"{bus}\n{escenario}")
    
    # Create bar plot
    x_pos = np.arange(len(datos_metodo))
    bars = ax.bar(x_pos, datos_metodo, color=paleta4[idx % len(paleta4)], 
                  alpha=0.8, edgecolor='black', linewidth=0.5)
    
    # Configure
    ax.set_title(f'{nombres_legibles.get(metodo, metodo)}', fontweight='bold', fontsize=14)
    ax.set_ylabel('Value SCR', fontsize=12)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(etiquetas_buses, fontsize=8, rotation=45, ha='right')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add values
    for i, (bar, valor) in enumerate(zip(bars, datos_metodo)):
        if np.isfinite(valor):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                   f'{valor:.2f}', ha='center', va='bottom', fontsize=8)

plt.tight_layout()
ruta_evolucion = os.path.join(carpeta_matriz_izquierda, 'Evolucion_Metodos_SCR.png')
plt.savefig(ruta_evolucion, dpi=300, bbox_inches='tight')
plt.close()
print(f"  ✅ Trend chart saved: {ruta_evolucion}")

print(f"\n{'='*60}")
print("COMPLETED GRAPH MATRICES")
print(f"{'='*60}")
print(f"Left array (Main SCRs): {ruta_matriz_izquierda}")
print(f"Right matrix (K_vtg vs λSCR): {ruta_matriz_derecha}")
print(f"Evolution of methods: {ruta_evolucion}")

###########################################################################################
# ===== GRÁFICA COMPARATIVA ENTRE ESCENARIOS =====
###########################################################################################

print(f"\nGenerating comparative graphs across scenarios...")

# Comparative plot for main SCR methods
fig, axes = plt.subplots(2, 3, figsize=(20, 12))
#fig.suptitle('Comparativa entre Escenarios', fontsize=18, fontweight='bold') #Titulo general de la grafica

escenarios_unicos = sorted(df_final_completo['Escenario'].unique())
buses_unicos = df_final_completo['Bus_LV'].unique()

# Configure bar positions
x_escenarios = np.arange(len(escenarios_unicos))
width_esc = 0.35

# Methods to compare across scenarios
metodos_comparar = ['SCR_scr', 'GSIM_hv', 'NRSCR', 'SDSCR_coupled']

# Define Palette 4
paleta4 = ['#004c6d', '#5a8aab', '#7eaac9', '#a2cae8', '#c5eaff']

for idx, metodo in enumerate(metodos_comparar):
    ax = axes[idx // 3, idx % 3]
    
    for i, bus in enumerate(buses_unicos):
        valores_bus = []
        for escenario in escenarios_unicos:
            dato = df_final_completo[(df_final_completo['Escenario'] == escenario) & 
                                    (df_final_completo['Bus_LV'] == bus)]
            if not dato.empty:
                valores_bus.append(dato[metodo].values[0])
            else:
                valores_bus.append(0)
        
        color = paleta4[i % len(paleta4)]
        ax.bar(x_escenarios + i * width_esc, valores_bus, width_esc, 
               label=bus, alpha=0.8, color=color, edgecolor='black', linewidth=0.5)

    ax.set_xlabel('Scenarios', fontsize=14, fontweight='bold')
    ax.set_ylabel('Value', fontsize=14, fontweight='bold')
    ax.set_title(f'{nombres_legibles[metodo]} - Comparative', fontsize=16, fontweight='bold')
    ax.set_xticks(x_escenarios + width_esc / 2)
    ax.set_xticklabels(escenarios_unicos, rotation=45)
    ax.legend()
    ax.grid(True, alpha=0.3)

# Define Palette 4
paleta4 = ['#004c6d', '#5a8aab', '#7eaac9', '#a2cae8', '#c5eaff']

# Plot for K_vtg_normal_LSCR (different scale)
ax = axes[1, 1]
for i, bus in enumerate(buses_unicos):
    valores_bus = []
    for escenario in escenarios_unicos:
        dato = df_final_completo[(df_final_completo['Escenario'] == escenario) & 
                                (df_final_completo['Bus_LV'] == bus)]
        if not dato.empty:
            valores_bus.append(dato['K_vtg_normal_LSCR'].values[0])
        else:
            valores_bus.append(0)
            
    color = paleta4[i % len(paleta4)]
    ax.bar(x_escenarios + i * width_esc, valores_bus, width_esc, 
           label=bus, alpha=0.8, color=color, edgecolor='black', linewidth=0.5)

ax.set_xlabel('Scenarios', fontsize=14, fontweight='bold')
ax.set_ylabel('Value K_vtg', fontsize=14, fontweight='bold')
ax.set_title('K_vtg Normal (LSCR) - Comparative', fontsize=16, fontweight='bold')
ax.set_xticks(x_escenarios + width_esc / 2)
ax.set_xticklabels(escenarios_unicos, rotation=45)
ax.legend()
ax.grid(True, alpha=0.3)

# Plot for normal λSCR LSCR (different scale)
ax = axes[1, 2]
for i, bus in enumerate(buses_unicos):
    valores_bus = []
    for escenario in escenarios_unicos:
        dato = df_final_completo[(df_final_completo['Escenario'] == escenario) & 
                                (df_final_completo['Bus_LV'] == bus)]
        if not dato.empty:
            valores_bus.append(dato['λSCR_normal_LSCR'].values[0])
        else:
            valores_bus.append(0)
            
    color = paleta4[i % len(paleta4)]
    ax.bar(x_escenarios + i * width_esc, valores_bus, width_esc, 
           label=bus, alpha=0.8, color=color, edgecolor='black', linewidth=0.5)

ax.set_xlabel('Scenarios', fontsize=14, fontweight='bold')
ax.set_ylabel('Valor λSCR', fontsize=14, fontweight='bold')
ax.set_title('λSCR Normal (LSCR) - Comparative', fontsize=16, fontweight='bold')
ax.set_xticks(x_escenarios + width_esc / 2)
ax.set_xticklabels(escenarios_unicos, rotation=45)
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()

# Save comparative plot
ruta_comparativa = os.path.join(carpeta_graficas, 'Comparativa_Completa_Escenarios.png')
plt.savefig(ruta_comparativa, dpi=300, bbox_inches='tight')
plt.close()

print(f"✅ Comparative graph saved: Comparativa_Completa_Escenarios.png")
print(f"\n📁 All the graphs were saved in: {carpeta_graficas}")