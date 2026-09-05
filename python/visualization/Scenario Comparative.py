import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Raíz del repositorio
REPO_ROOT = Path(__file__).resolve().parents[2]

# Ejemplo que se desea procesar
EXAMPLE = "IEEE39"

#Tipo de genración
GENTIP = "IND" # Si es Inductivo "IND", si es capacitivo "CAP"

# Carpeta donde se guardarán los resultados de los indicadores
# ------------------------------------------------------------
OUTPUT_PATH = REPO_ROOT / "results" / EXAMPLE / GENTIP

# Definir la ruta base donde están todos los escenarios
ruta_base = OUTPUT_PATH
ruta_salida_final = os.path.join(OUTPUT_PATH, f"resumen_combinado_completo_{GENTIP}.csv")

# Lista para almacenar los resultados de todos los escenarios
todos_los_datos = []

# Obtener todas las carpetas de escenarios
carpetas_escenarios = [carpeta for carpeta in os.listdir(ruta_base) 
                      if os.path.isdir(os.path.join(ruta_base, carpeta)) and carpeta.startswith('Escenario_')]

print(f"Escenarios encontrados: {carpetas_escenarios}")

for escenario in carpetas_escenarios:
    print(f"\n{'='*60}")
    print(f"PROCESANDO: {escenario}")
    print(f"{'='*60}")
    
    # Definir las rutas específicas para este escenario
    ruta_escenario = os.path.join(ruta_base, escenario)
    ruta_gsim = os.path.join(ruta_escenario, 'GSIM_results.csv')
    ruta_nrscr = os.path.join(ruta_escenario, 'NRSCR_results.csv')
    ruta_sdscr = os.path.join(ruta_escenario, 'SDSCR_results.csv')
    ruta_lscr = os.path.join(ruta_escenario, 'LSCR_results.csv')
    ruta_scr = os.path.join(ruta_escenario, 'SCR_results.csv')
    
    # Verificar que todos los archivos existan en este escenario
    archivos_faltantes = []
    for archivo, ruta in [('GSIM_results.csv', ruta_gsim), 
                          ('NRSCR_results.csv', ruta_nrscr),
                          ('SDSCR_results.csv', ruta_sdscr),
                          ('LSCR_results.csv', ruta_lscr),
                          ('SCR_results.csv', ruta_scr)]:
        if not os.path.exists(ruta):
            archivos_faltantes.append(archivo)
    
    if archivos_faltantes:
        print(f"  ❌ Archivos faltantes en {escenario}: {archivos_faltantes}")
        continue
    
    try:
        # Leer archivo SCR (SCR_results.csv)
        df_scr = pd.read_csv(ruta_scr)

        # 1) Extraer las columnas solicitadas del archivo
        columnas_scr = ['Escenario', 'Generador', 'Potencia_Generador_MW', 'Potencia_Cortocircuito_MVA', 'SCR_scr']
        df_scr_filtrado = df_scr[columnas_scr].copy()
        
        # Leer el primer archivo (GSIM_results.csv)
        df_gsim = pd.read_csv(ruta_gsim)

        # 1) Extraer las columnas solicitadas del primer archivo
        columnas_gsim = ['escenario', 'bus', 'S_sc_HV', 'SCR_HV', 'GSIM_hv']
        df_gsim_filtrado = df_gsim[columnas_gsim].copy()

        # 2) Filtrar solo los buses que contienen "PV" y "LV" en su nombre
        df_gsim_final = df_gsim_filtrado[df_gsim_filtrado['bus'].str.contains('PV.*LV', na=False)]

        # Leer el segundo archivo (NRSCR_results.csv)
        df_nrscr = pd.read_csv(ruta_nrscr)

        # 1) Filtrar solo los buses que contienen "PV" y "LV" en su nombre
        # 2) Extraer las columnas SCR, NRSCR y Nodo Alta
        df_nrscr_filtrado = df_nrscr[df_nrscr['Nodo IBR'].str.contains('PV.*LV', na=False)]
        df_nrscr_final = df_nrscr_filtrado[['Nodo IBR', 'Nodo Alta', 'SCR', 'NRSCR']].copy()

        # Renombrar columnas para identificar de qué archivo vienen
        df_gsim_final.columns = ['Escenario', 'Bus_LV', 'S_sc_HV_GSIM', 'SCR_HV_GSIM', 'GSIM_hv']
        df_nrscr_final.columns = ['Bus_LV', 'Bus_HV', 'SCR_NRSCR', 'NRSCR']

        # Combinar ambos dataframes por la columna 'Bus_LV'
        df_combinado = pd.merge(df_gsim_final, df_nrscr_final, on='Bus_LV', how='inner')

        # =============================================================================
        # PROCESAMIENTO DEL ARCHIVO SDSCR_RESULTS.CSV
        # =============================================================================

        # Leer el tercer archivo (SDSCR_results.csv)
        df_sdscr = pd.read_csv(ruta_sdscr)

        # 1) Usar los buses HV que ya extrajimos del CSV anterior
        buses_hv_extraidos = df_combinado['Bus_HV'].unique()

        # 2) Filtrar SDSCR_results para incluir solo los buses que están en nuestra lista
        buses_hv_formateados = [bus.replace('Bus', 'BUS') for bus in buses_hv_extraidos]

        df_sdscr_filtrado = df_sdscr[df_sdscr['Bus'].isin(buses_hv_formateados)]

        # 3) Extraer las columnas SCR, SDSCR_coupled y SDSCR_no_coupling
        df_sdscr_final = df_sdscr_filtrado[['Bus', 'SCR', 'SDSCR_coupled', 'SDSCR_no_coupling']].copy()

        # Renombrar columnas SDSCR
        df_sdscr_final.columns = ['Bus_HV_SDSCR', 'SCR_SDSCR', 'SDSCR_coupled', 'SDSCR_no_coupling']

        # Combinar con el dataframe principal
        df_combinado['Bus_HV_SDSCR'] = df_combinado['Bus_HV'].str.replace('Bus', 'BUS')
        df_combinado = pd.merge(df_combinado, df_sdscr_final, on='Bus_HV_SDSCR', how='left')
        df_combinado = df_combinado.drop('Bus_HV_SDSCR', axis=1)

        # =============================================================================
        # PROCESAMIENTO DEL ARCHIVO LSCR_RESULTS.CSV
        # =============================================================================

        # Leer el cuarto archivo (LSCR_results.csv)
        df_lscr = pd.read_csv(ruta_lscr)

        # 1) Usar los buses HV que ya extrajimos (columna "Barra Cálculo")
        buses_hv_extraidos = df_combinado['Bus_HV'].unique()

        # 2) Filtrar LSCR_results para incluir solo los buses que están en nuestra lista
        df_lscr_filtrado = df_lscr[df_lscr['Barra Cálculo'].isin(buses_hv_extraidos)]

        # 3) Extraer las columnas Z_device, K_vtg_normal y λSCR_normal
        df_lscr_final = df_lscr_filtrado[['Barra Cálculo', 'Z_device', 'K_vtg_fault', 'λSCR_fault']].copy()

        # Renombrar columnas LSCR
        df_lscr_final.columns = ['Bus_HV', 'Z_device_LSCR', 'K_vtg_normal_LSCR', 'λSCR_normal_LSCR']

        # Combinar con el dataframe principal
        df_combinado_final = pd.merge(df_combinado, df_lscr_final, on='Bus_HV', how='left')
        
        # =============================================================================
        # AGREGAR DATOS DE SCR_RESULTS.CSV
        # =============================================================================
        # ==================== 4 LÍNEAS CORREGIDAS ====================
        # Extraer el nombre del bus LV desde el generador (asumiendo que contiene "PV" y "LV")
        # Limpiar nombres
        df_scr_filtrado['Bus_LV'] = df_scr_filtrado['Generador'] + ' LV'
        df_combinado_final['Bus_LV'] = df_combinado_final['Bus_LV']
        # Merge correcto
        df_combinado_final = pd.merge(df_combinado_final, df_scr_filtrado[['Bus_LV', 'SCR_scr']], on='Bus_LV', how='left')
        # ===========================================================

        # Agregar los datos de este escenario a la lista general
        print(df_combinado_final[['Bus_LV', 'SCR_scr']])
        todos_los_datos.append(df_combinado_final)
        
        print(f"  ✅ {escenario} procesado exitosamente - {len(df_combinado_final)} registros")
        
    except Exception as e:
        print(f"  ❌ Error procesando {escenario}: {str(e)}")
        continue

# Combinar todos los datos de todos los escenarios
if todos_los_datos:
    df_final_completo = pd.concat(todos_los_datos, ignore_index=True)
    
    # Guardar el resultado final en la ruta especificada
    df_final_completo.to_csv(ruta_salida_final, index=False)
    
    print(f"\n{'='*60}")
    print("PROCESAMIENTO COMPLETADO")
    print(f"{'='*60}")
    print(f"Archivo final guardado en: {ruta_salida_final}")
    print(f"Total de escenarios procesados: {len(todos_los_datos)}")
    print(f"Total de registros en el archivo final: {len(df_final_completo)}")
    print(f"\nColumnas en el archivo final:")
    for col in df_final_completo.columns:
        print(f"  - {col}")
else:
    print("\n❌ No se pudo procesar ningún escenario. Verifica que los archivos existan.")

# =============================================================================
# SECCIÓN NUEVA: CREACIÓN DE GRÁFICAS MEJORADAS PARA CADA ESCENARIO
# =============================================================================

print(f"\n{'='*60}")
print("CREANDO GRÁFICAS PARA CADA ESCENARIO")
print(f"{'='*60}")

# Crear carpeta para guardar las gráficas si no existe
carpeta_graficas = os.path.join(ruta_base, 'Graficas_SCR')
os.makedirs(carpeta_graficas, exist_ok=True)

# Verificar qué columnas están realmente disponibles
columnas_disponibles = df_final_completo.columns.tolist()
print(f"\nColumnas disponibles en el DataFrame final: {columnas_disponibles}")

# Variables específicas a graficar
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

# Filtrar nombres legibles para las variables que existen
nombres_legibles = {k: v for k, v in nombres_legibles.items() if k in variables_scr}


for escenario in df_final_completo['Escenario'].unique():
    print(f"Generando gráfica para: {escenario}")
    
    # Filtrar datos del escenario actual
    datos_escenario = df_final_completo[df_final_completo['Escenario'] == escenario]
    
    # Configurar el estilo de la gráfica
    plt.style.use('default')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))
    fig.suptitle(f'Análisis Comparativo de Métodos SCR - {escenario}', fontsize=16, fontweight='bold', y=0.95)
    
    # ===== GRÁFICA 1: COMPARACIÓN DE MÉTODOS SCR (valores altos) =====
    buses = datos_escenario['Bus_LV'].values
    x = np.arange(len(buses))
    width = 0.15
    
    # Métodos con valores altos (SCR principales)
    metodos_altos = ['SCR_scr', 'GSIM_hv', 'NRSCR', 'SDSCR_coupled']
    
    # Definir la Paleta 4 (Científica/Springer)
    paleta4 = ['#004c6d', '#346b8c', '#5a8aab', '#7eaac9']

# Crear barras para cada método de SCR
    for i, metodo in enumerate(metodos_altos):
        valores = datos_escenario[metodo].replace([np.inf, -np.inf], np.nan).values
        # Asignar color de la paleta según el índice (con ciclo si hay más métodos que colores)
        color = paleta4[i % len(paleta4)]
        ax1.bar(x + i * width, valores, width, label=nombres_legibles[metodo], 
                color=color, alpha=0.8, edgecolor='black', linewidth=0.5)
    
    ax1.set_xlabel('Buses', fontweight='bold', fontsize=12)
    ax1.set_ylabel('Valor SCR', fontweight='bold', fontsize=12)
    ax1.set_title('Comparación de Métodos SCR Principales', fontweight='bold', fontsize=13)
    ax1.set_xticks(x + width * 1.5)
    ax1.set_xticklabels(buses, fontweight='bold')
    ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(0, max(datos_escenario[metodos_altos].max().max() * 1.2, 15))
    
    # Añadir valores en las barras
    for i, metodo in enumerate(metodos_altos):
        valores = datos_escenario[metodo].values
        for j, valor in enumerate(valores):
            if np.isfinite(valor):
                ax1.text(x[j] + i * width, valor + 0.1, f'{valor:.2f}', 
                        ha='center', va='bottom', fontsize=9, rotation=45)
    
    # ===== GRÁFICA 2: INDICADOR K_vtg_normal_LSCR (valores bajos) =====
    # Esta variable tiene valores mucho más bajos, necesita escala separada
    x_kvtg = np.arange(len(buses))
    width = 0.35

    valores_kvtg = datos_escenario['K_vtg_normal_LSCR'].values
    valores_lambda = datos_escenario['λSCR_normal_LSCR'].values

    # Barras para K_vtg
    bars1 = ax2.bar(x - width/2, valores_kvtg, width, color='#004c6d', alpha=0.8, 
                    label=nombres_legibles['K_vtg_normal_LSCR'])
    
    # Barras para λSCR (al lado)
    bars2 = ax2.bar(x + width/2, valores_lambda, width, color='#346b8c', alpha=0.8,
                    label=nombres_legibles['λSCR_normal_LSCR'])
    
    ax2.set_xlabel('Buses', fontweight='bold', fontsize=12)
    ax2.set_ylabel('Valor', fontweight='bold', fontsize=12)
    ax2.set_title('Comparativa K_vtg Normal vs λSCR (LSCR)', fontweight='bold', fontsize=13)
    ax2.set_xticks(x)
    ax2.set_xticklabels(buses, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Añadir valores en las barras de K_vtg
    for j, valor in enumerate(valores_kvtg):
        ax2.text(x[j] - width/2, valor + 0.0005, f'{valor:.4f}', 
                ha='center', va='bottom', fontsize=8, rotation=45)
    
    # Añadir valores en las barras de λSCR
    for j, valor in enumerate(valores_lambda):
        ax2.text(x[j] + width/2, valor + 0.0005, f'{valor:.4f}', 
                ha='center', va='bottom', fontsize=8, rotation=45)

    # Ajustar límites del eje Y para que los valores queden dentro
    valor_maximo = max(valores_kvtg.max(), valores_lambda.max())
    margen_superior = valor_maximo * 0.15  # 15% de margen arriba del valor más alto
    ax2.set_ylim(0, valor_maximo + margen_superior)
    
    # Ajustar layout
    plt.tight_layout()
    
    # Guardar gráfica
    nombre_archivo = f"{escenario}_Analisis_SCR_Comparativo.png"
    ruta_grafica = os.path.join(carpeta_graficas, nombre_archivo)
    plt.savefig(ruta_grafica, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✅ Gráfica guardada: {nombre_archivo}")


#####################################################################################

# =============================================================================
# SECCIÓN NUEVA: CREACIÓN DE MATRICES DE GRÁFICAS CONSOLIDADAS
# =============================================================================

print(f"\n{'='*60}")
print("CREANDO MATRICES DE GRÁFICAS CONSOLIDADAS")
print(f"{'='*60}")

# Crear carpetas para las matrices de gráficas
carpeta_matriz_izquierda = os.path.join(ruta_base, 'Matriz_Graficas_Izquierda')
carpeta_matriz_derecha = os.path.join(ruta_base, 'Matriz_Graficas_Derecha')
os.makedirs(carpeta_matriz_izquierda, exist_ok=True)
os.makedirs(carpeta_matriz_derecha, exist_ok=True)

# Función para organizar escenarios en una cuadrícula
def organizar_en_cuadricula(n_escenarios):
    """Determina las dimensiones de la cuadrícula basada en el número de escenarios"""
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

# Obtener la lista única de escenarios ordenada
escenarios_unicos = sorted(df_final_completo['Escenario'].unique())
n_escenarios = len(escenarios_unicos)

print(f"\nNúmero total de escenarios: {n_escenarios}")
print(f"Escenarios: {escenarios_unicos}")

# Determinar dimensiones de la cuadrícula
filas, columnas = organizar_en_cuadricula(n_escenarios)

# ===== MATRIZ DE GRÁFICAS DE LA IZQUIERDA (Comparación de Métodos SCR Principales) =====
print(f"\nCreando matriz de gráficas de la IZQUIERDA ({filas}x{columnas})...")

# Crear figura para la matriz izquierda
fig_izquierda, axes_izquierda = plt.subplots(filas, columnas, figsize=(6*columnas, 5*filas))
#fig_izquierda.suptitle('MATRIZ COMPARATIVA: Indicadores SCR por Escenario', fontsize=20, fontweight='bold', y=0.98)

# Aplanar axes para facilitar la iteración
if filas == 1 and columnas == 1:
    axes_izquierda = np.array([axes_izquierda])
axes_izquierda = axes_izquierda.flatten()

# Paleta de colores para los métodos
paleta4 = ['#004c6d', '#346b8c', '#5a8aab', '#7eaac9']
metodos_altos = ['SCR_scr', 'GSIM_hv', 'NRSCR', 'SDSCR_coupled']

# Variable para controlar el límite máximo global
max_global_izquierda = 0

# Primera pasada: calcular el máximo global
for escenario in escenarios_unicos:
    datos_escenario = df_final_completo[df_final_completo['Escenario'] == escenario]
    for metodo in metodos_altos:
        if metodo in datos_escenario.columns:
            max_valor = datos_escenario[metodo].max()
            if max_valor > max_global_izquierda:
                max_global_izquierda = max_valor

# Añadir 20% de margen al máximo global
max_global_izquierda = max_global_izquierda * 1.2

# Generar cada subgráfica de la izquierda
for idx, escenario in enumerate(escenarios_unicos):
    if idx >= len(axes_izquierda):
        break
        
    ax = axes_izquierda[idx]
    datos_escenario = df_final_completo[df_final_completo['Escenario'] == escenario]
    buses = datos_escenario['Bus_LV'].values
    x = np.arange(len(buses))
    width = 0.2  # Ancho ajustado para matriz
    
    # Crear barras para cada método
    for i, metodo in enumerate(metodos_altos):
        if metodo in datos_escenario.columns:
            valores = datos_escenario[metodo].replace([np.inf, -np.inf], np.nan).values
            color = paleta4[i % len(paleta4)]
            ax.bar(x + i * width, valores, width, label=nombres_legibles.get(metodo, metodo), 
                   color=color, alpha=0.8, edgecolor='black', linewidth=0.5)
    
    # Configurar la subgráfica
    ax.set_title(f'{escenario}', fontweight='bold', fontsize=16)
    ax.set_xlabel('Buses', fontsize=14)
    ax.set_ylabel('SCR', fontsize=14)
    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels(buses, fontsize=10, rotation=45, ha='right')
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_ylim(0, max_global_izquierda)
    
    # Añadir valores en las barras (con menos decimales para claridad)
    for i, metodo in enumerate(metodos_altos):
        if metodo in datos_escenario.columns:
            valores = datos_escenario[metodo].values
            for j, valor in enumerate(valores):
                if np.isfinite(valor) and valor > 0:
                    ax.text(x[j] + i * width, valor + max_global_izquierda*0.02, 
                           f'{valor:.1f}', ha='center', va='bottom', fontsize=7, rotation=45)
    
    # Solo añadir leyenda en la primera subgráfica si hay espacio
    if idx == 0:
        ax.legend(loc='upper left', fontsize=8)

# Ocultar ejes no utilizados
for idx in range(len(escenarios_unicos), len(axes_izquierda)):
    axes_izquierda[idx].axis('off')

plt.tight_layout()
ruta_matriz_izquierda = os.path.join(carpeta_matriz_izquierda, 'Matriz_SCR_Principales.png')
plt.savefig(ruta_matriz_izquierda, dpi=300, bbox_inches='tight')
plt.close()
print(f"  ✅ Matriz izquierda guardada: {ruta_matriz_izquierda}")

# ===== MATRIZ DE GRÁFICAS DE LA DERECHA (K_vtg vs λSCR) =====
print(f"\nCreando matriz de gráficas de la DERECHA ({filas}x{columnas})...")

# Crear figura para la matriz derecha
fig_derecha, axes_derecha = plt.subplots(filas, columnas, figsize=(6*columnas, 5*filas))
#fig_derecha.suptitle('MATRIZ COMPARATIVA: K_vtg Normal vs λSCR por Escenario', fontsize=20, fontweight='bold', y=0.98)

# Aplanar axes
if filas == 1 and columnas == 1:
    axes_derecha = np.array([axes_derecha])
axes_derecha = axes_derecha.flatten()

# Calcular el máximo global para la derecha
max_global_derecha = 0
for escenario in escenarios_unicos:
    datos_escenario = df_final_completo[df_final_completo['Escenario'] == escenario]
    if 'K_vtg_normal_LSCR' in datos_escenario.columns:
        max_kvtg = datos_escenario['K_vtg_normal_LSCR'].max()
        max_global_derecha = max(max_global_derecha, max_kvtg)
    if 'λSCR_normal_LSCR' in datos_escenario.columns:
        max_lambda = datos_escenario['λSCR_normal_LSCR'].max()
        max_global_derecha = max(max_global_derecha, max_lambda)

# Añadir 20% de margen
max_global_derecha = max_global_derecha * 1.2

# Generar cada subgráfica de la derecha
for idx, escenario in enumerate(escenarios_unicos):
    if idx >= len(axes_derecha):
        break
        
    ax = axes_derecha[idx]
    datos_escenario = df_final_completo[df_final_completo['Escenario'] == escenario]
    buses = datos_escenario['Bus_LV'].values
    x = np.arange(len(buses))
    width = 0.35
    
    # Verificar que las columnas existan
    if 'K_vtg_normal_LSCR' in datos_escenario.columns:
        valores_kvtg = datos_escenario['K_vtg_normal_LSCR'].values
        bars1 = ax.bar(x - width/2, valores_kvtg, width, color='#004c6d', 
                       alpha=0.8, label='K_vtg Normal')
        
        # Añadir valores
        for j, valor in enumerate(valores_kvtg):
            if np.isfinite(valor):
                ax.text(x[j] - width/2, valor + max_global_derecha*0.02, 
                       f'{valor:.3f}', ha='center', va='bottom', fontsize=7, rotation=45)
    
    if 'λSCR_normal_LSCR' in datos_escenario.columns:
        valores_lambda = datos_escenario['λSCR_normal_LSCR'].values
        bars2 = ax.bar(x + width/2, valores_lambda, width, color='#346b8c', 
                       alpha=0.8, label='λSCR Normal')
        
        # Añadir valores
        for j, valor in enumerate(valores_lambda):
            if np.isfinite(valor):
                ax.text(x[j] + width/2, valor + max_global_derecha*0.02, 
                       f'{valor:.3f}', ha='center', va='bottom', fontsize=7, rotation=45)
    
    # Configurar la subgráfica
    ax.set_title(f'{escenario}', fontweight='bold', fontsize=16)
    ax.set_xlabel('Buses', fontsize=14)
    ax.set_ylabel('Valor', fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(buses, fontsize=10, rotation=45, ha='right')
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_ylim(0, max_global_derecha)
    
    # Solo añadir leyenda en la primera subgráfica
    if idx == 0:
        ax.legend(loc='upper left', fontsize=8)

# Ocultar ejes no utilizados
for idx in range(len(escenarios_unicos), len(axes_derecha)):
    axes_derecha[idx].axis('off')

plt.tight_layout()
ruta_matriz_derecha = os.path.join(carpeta_matriz_derecha, 'Matriz_Kvtg_vs_Lambda.png')
plt.savefig(ruta_matriz_derecha, dpi=300, bbox_inches='tight')
plt.close()
print(f"  ✅ Matriz derecha guardada: {ruta_matriz_derecha}")

# ===== MATRIZ ADICIONAL: Gráficas de barras agrupadas por método =====
print(f"\nCreando matriz de gráficas adicional (barras agrupadas por método)...")

# Crear matriz que muestre la evolución de cada método a través de los escenarios
fig_evolucion, axes_evolucion = plt.subplots(len(metodos_altos), 1, 
                                              figsize=(14, 5*len(metodos_altos)))
fig_evolucion.suptitle('EVOLUCIÓN DE MÉTODOS SCR A TRAVÉS DE ESCENARIOS', 
                       fontsize=18, fontweight='bold', y=0.995)

for idx, metodo in enumerate(metodos_altos):
    if metodo not in df_final_completo.columns:
        continue
        
    ax = axes_evolucion[idx] if len(metodos_altos) > 1 else axes_evolucion
    
    # Preparar datos para este método
    datos_metodo = []
    etiquetas_buses = []
    
    for escenario in escenarios_unicos:
        datos_escenario = df_final_completo[df_final_completo['Escenario'] == escenario]
        for bus in datos_escenario['Bus_LV'].values:
            valor = datos_escenario[datos_escenario['Bus_LV'] == bus][metodo].values[0]
            datos_metodo.append(valor)
            etiquetas_buses.append(f"{bus}\n{escenario}")
    
    # Crear gráfica de barras
    x_pos = np.arange(len(datos_metodo))
    bars = ax.bar(x_pos, datos_metodo, color=paleta4[idx % len(paleta4)], 
                  alpha=0.8, edgecolor='black', linewidth=0.5)
    
    # Configurar
    ax.set_title(f'{nombres_legibles.get(metodo, metodo)}', fontweight='bold', fontsize=14)
    ax.set_ylabel('Valor SCR', fontsize=12)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(etiquetas_buses, fontsize=8, rotation=45, ha='right')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Añadir valores
    for i, (bar, valor) in enumerate(zip(bars, datos_metodo)):
        if np.isfinite(valor):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                   f'{valor:.2f}', ha='center', va='bottom', fontsize=8)

plt.tight_layout()
ruta_evolucion = os.path.join(carpeta_matriz_izquierda, 'Evolucion_Metodos_SCR.png')
plt.savefig(ruta_evolucion, dpi=300, bbox_inches='tight')
plt.close()
print(f"  ✅ Gráfica de evolución guardada: {ruta_evolucion}")

print(f"\n{'='*60}")
print("MATRICES DE GRÁFICAS COMPLETADAS")
print(f"{'='*60}")
print(f"Matriz izquierda (SCR Principales): {ruta_matriz_izquierda}")
print(f"Matriz derecha (K_vtg vs λSCR): {ruta_matriz_derecha}")
print(f"Evolución de métodos: {ruta_evolucion}")

###########################################################################################
# ===== GRÁFICA COMPARATIVA ENTRE ESCENARIOS =====
###########################################################################################

print(f"\nGenerando gráficas comparativas entre escenarios...")

# Gráfica comparativa para métodos SCR principales
fig, axes = plt.subplots(2, 3, figsize=(20, 12))
#fig.suptitle('Comparativa entre Escenarios', fontsize=18, fontweight='bold') #Titulo general de la grafica

escenarios_unicos = sorted(df_final_completo['Escenario'].unique())
buses_unicos = df_final_completo['Bus_LV'].unique()

# Configurar posiciones para las barras
x_escenarios = np.arange(len(escenarios_unicos))
width_esc = 0.35

# Métodos a comparar entre escenarios
metodos_comparar = ['SCR_scr', 'GSIM_hv', 'NRSCR', 'SDSCR_coupled']

# Definir la Paleta 4
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

    ax.set_xlabel('Escenarios', fontsize=14, fontweight='bold')
    ax.set_ylabel('Valor', fontsize=14, fontweight='bold')
    ax.set_title(f'{nombres_legibles[metodo]} - Comparativa', fontsize=16, fontweight='bold')
    ax.set_xticks(x_escenarios + width_esc / 2)
    ax.set_xticklabels(escenarios_unicos, rotation=45)
    ax.legend()
    ax.grid(True, alpha=0.3)

# Definir la Paleta 4
paleta4 = ['#004c6d', '#5a8aab', '#7eaac9', '#a2cae8', '#c5eaff']

# Gráfica para K_vtg_normal_LSCR (escala diferente)
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

ax.set_xlabel('Escenarios', fontsize=14, fontweight='bold')
ax.set_ylabel('Valor K_vtg', fontsize=14, fontweight='bold')
ax.set_title('K_vtg Normal (LSCR) - Comparativa', fontsize=16, fontweight='bold')
ax.set_xticks(x_escenarios + width_esc / 2)
ax.set_xticklabels(escenarios_unicos, rotation=45)
ax.legend()
ax.grid(True, alpha=0.3)

# Gráfica para λSCR normal LSCR (escala diferente)
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

ax.set_xlabel('Escenarios', fontsize=14, fontweight='bold')
ax.set_ylabel('Valor λSCR', fontsize=14, fontweight='bold')
ax.set_title('λSCR Normal (LSCR) - Comparativa', fontsize=16, fontweight='bold')
ax.set_xticks(x_escenarios + width_esc / 2)
ax.set_xticklabels(escenarios_unicos, rotation=45)
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()

# Guardar gráfica comparativa
ruta_comparativa = os.path.join(carpeta_graficas, 'Comparativa_Completa_Escenarios.png')
plt.savefig(ruta_comparativa, dpi=300, bbox_inches='tight')
plt.close()

print(f"✅ Gráfica comparativa guardada: Comparativa_Completa_Escenarios.png")
print(f"\n📁 Todas las gráficas se guardaron en: {carpeta_graficas}")