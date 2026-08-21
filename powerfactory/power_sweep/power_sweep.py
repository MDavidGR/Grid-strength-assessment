import powerfactory as pf
import itertools
import csv
import os
import re
import numpy as np
import matplotlib.pyplot as plt

# === Inicialización de PowerFactory ===

app = pf.GetApplication()
app.ClearOutputWindow()

# ============================================================
# CONFIGURACIÓN DEL USUARIO
# Modificar estos valores antes de ejecutar el algoritmo
# ============================================================

# ------------------------------------------------------------
# RUTAS
# ------------------------------------------------------------

# Archivo generado por find_electrically_close_nodes.py
Z_IMPORT_PATH = r"...\data\example\IEEE39\pares_nodos_cercanos.csv"

# Carpeta donde se guardarán los resultados del barrido
EXPORT_PATH = r"...\data\results\IEEE39"
os.makedirs(EXPORT_PATH, exist_ok=True)

# ------------------------------------------------------------
# CRITERIO DE CERCANÍA ELÉCTRICA
# ------------------------------------------------------------

Z_THRESHOLD = 0.2 #Determinar valor que determina la cercania electrica

# ------------------------------------------------------------
# PUNTO CONOCIDO Y PUNTO OPUESTO
# ------------------------------------------------------------
# KNOWN_POINT:
# Punto de operación previamente identificado que se encuentra aproximadamente sobre el límite de tensión definido.
# Estos valores dependen del sistema de prueba, de los generadores seleccionados y del escenario analizado.
# El usuario debe ajustarlos antes de ejecutar el algoritmo.

# OPPOSITE_POINT:
# Punto utilizado como extremo opuesto para generar los valores de P mediante np.linspace().
# Estos valores deben ajustarse al rango de potencia del sistema y del escenario analizado.

KNOWN_POINT = {
    "P1_MW": 405.0,
    "P2_MW": 1.0
}

OPPOSITE_POINT = {
    "P1_MW": 1.0,
    "P2_MW": 1050.0
}

# ------------------------------------------------------------
# PARÁMETROS DEL BARRIDO
# ------------------------------------------------------------

MAX_VOLTAGE = 1.1
P_STEP = 20
P_MAX = 400
NUM_POINTS = 30

impedance_data = {}

try:
    with open(Z_IMPORT_PATH, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            nodo_i = row['Nodo_i']
            nodo_j = row['Nodo_j']
            zij = float(row['|Zij/zjj|'])
            impedance_data[(nodo_i, nodo_j)] = zij
            impedance_data[(nodo_j, nodo_i)] = zij
    app.PrintInfo(f"Datos de impedancia cargados: {len(impedance_data)//2} pares")
except Exception as e:
    app.PrintError(f"Error cargando archivo de impedancias: {str(e)}")
    raise SystemExit

# === Identificación de generadores ===
nonsync_types = ["ElmAsy", "ElmGenstat", "ElmPvsys", "ElmGenpv"]
gen_nonsync = []

for gtype in nonsync_types:
    gens = app.GetCalcRelevantObjects(f"*.{gtype}")
    if gens:
        gen_nonsync.extend([g for g in gens if hasattr(g, 'outserv') and g.outserv == 0])

app.PrintInfo(f"Generadores no síncronos encontrados: {len(gen_nonsync)}")

if len(gen_nonsync) < 2:
    app.PrintError("Se necesitan al menos 2 generadores no síncronos")
    raise SystemExit

# Guardar valores base
pgini_base = {g: float(g.pgini) for g in gen_nonsync}

# === Función para extraer número del bus ===
def extract_bus_number(bus_name):
    numbers = re.findall(r'\d+', bus_name)
    return numbers[0] if numbers else bus_name

# === Función simplificada para obtener bus de evaluación ===
def get_evaluation_bus_for_generator(generator):
    try:
        if hasattr(generator, 'bus1') and generator.bus1.cterm:
            return generator.bus1.cterm.loc_name
    except Exception as e:
        app.PrintWarn(f"Error obteniendo bus para {generator.loc_name}: {str(e)}")
    return None

# === Función para obtener impedancia ===
def get_impedance_between_nodes(node1_name, node2_name):
    node1_num = extract_bus_number(node1_name)
    node2_num = extract_bus_number(node2_name)
    key = (node1_num, node2_num)
    return impedance_data.get(key, float('inf'))

# === Configuración del flujo de carga ===
ldf = app.GetFromStudyCase("ComLdf")
if ldf is None:
    raise RuntimeError("No se encontró ComLdf")

# === FUNCIÓN MODIFICADA PARA LIMITE SUPERIOR ===
def test_allocation_upper(p1_mw, p2_mw, g1, g2):
    """
    Prueba una asignación y devuelve:
    - feasible: True si U_max <= 1.1 pu
    - u_max: Tensión máxima en p.u.
    - bus_critico: Bus con máxima tensión
    """
    # Guardar valores originales
    p1_orig = float(g1.pgini)
    p2_orig = float(g2.pgini)
    
    # CONVERTIR MW A kW (PowerFactory usa kW) - asegurar que sean float
    g1.pgini = float(p1_mw * 1000.0)
    g2.pgini = float(p2_mw * 1000.0)
    
    # Ejecutar flujo de carga
    err = ldf.Execute()
    converged = (err == 0)
    
    # Obtener tensión MÁXIMA
    u_max = None
    bus_critico = None
    
    if converged:
        buses = app.GetCalcRelevantObjects("*.ElmTerm")
        for b in buses:
            try:
                u = float(b.GetAttribute("m:u"))  # Convertir a float
                if u is not None:
                    if u_max is None or u > u_max:
                        u_max = u
                        bus_critico = b.loc_name
            except Exception:
                continue
    
    # Restaurar valores
    g1.pgini = float(p1_orig)
    g2.pgini = float(p2_orig)
    
    if not converged or u_max is None:
        return False, None, None
    
    # Para límite superior: factible si U <= 1.1
    feasible = u_max <= MAX_VOLTAGE
    return feasible, float(u_max), bus_critico

# === FUNCIÓN PARA ENCONTRAR LÍMITE (BUSQUEDA BINARIA) ===
def find_limit_upper(g1, g2, fixed_p_mw, fixed_is_g1, target_voltage=1.1):
    """
    Encuentra el límite donde U_max = target_voltage usando búsqueda binaria.
    fixed_is_g1: True si P1 está fijo, False si P2 está fijo
    """
    
    if fixed_is_g1:
        # P1 fijo, buscar P2
        p1_fixed = float(fixed_p_mw)
        
        # Buscar rango inicial
        p2_low = 0.0
        p2_high = float(P_MAX)
        
        # Primero encontrar un punto con U < 1.1
        app.PrintInfo(f"Buscando punto inicial con U < {target_voltage} p.u.")
        for p2_test in np.arange(0.0, float(P_MAX), 10.0):
            p2_test_float = float(p2_test)  # Convertir explícitamente
            feasible, u_max, _ = test_allocation_upper(p1_fixed, p2_test_float, g1, g2)
            if u_max is not None and u_max < target_voltage:
                p2_low = float(p2_test_float)
                app.PrintInfo(f"Encontrado P2_low = {p2_low} MW, U = {u_max:.4f} p.u.")
                break
        
        # Luego encontrar un punto con U > 1.1
        app.PrintInfo(f"Buscando punto con U > {target_voltage} p.u.")
        for p2_test in np.arange(p2_low + 10.0, float(P_MAX) + 10.0, 10.0):
            p2_test_float = float(p2_test)
            feasible, u_max, _ = test_allocation_upper(p1_fixed, p2_test_float, g1, g2)
            if u_max is not None and u_max > target_voltage:
                p2_high = float(p2_test_float)
                app.PrintInfo(f"Encontrado P2_high = {p2_high} MW, U = {u_max:.4f} p.u.")
                break
        
        app.PrintInfo(f"Rango inicial: P1={p1_fixed} MW, P2=[{p2_low:.1f}, {p2_high:.1f}] MW")
        
        # Verificar que tenemos un rango válido
        if p2_high <= p2_low:
            app.PrintWarn(f"No se encontró rango válido para P1={p1_fixed} MW")
            return 0.0, None, None
        
        # Búsqueda binaria
        for iteration in range(20):
            p2_mid = float((p2_low + p2_high) / 2.0)
            feasible, u_mid, bus_mid = test_allocation_upper(p1_fixed, p2_mid, g1, g2)
            
            if u_mid is None:
                app.PrintWarn("Flujo de carga no convergió")
                return 0.0, None, None
            
            app.PrintInfo(f"Iteración {iteration+1}: P2={p2_mid:.1f} MW, U={u_mid:.4f} p.u.")
            
            if abs(u_mid - target_voltage) < 0.001:
                app.PrintInfo(f"✓ Límite encontrado: P2={p2_mid:.1f} MW, U={u_mid:.4f} p.u.")
                return float(p2_mid), float(u_mid), bus_mid
            elif u_mid < target_voltage:
                p2_low = float(p2_mid)
                app.PrintInfo(f"  U demasiado bajo, aumentando P2_low a {p2_low:.1f} MW")
            else:
                p2_high = float(p2_mid)
                app.PrintInfo(f"  U demasiado alto, disminuyendo P2_high a {p2_high:.1f} MW")
        
        # Si no converge exactamente, usar el punto más cercano
        p2_final = float((p2_low + p2_high) / 2.0)
        feasible, u_final, bus_final = test_allocation_upper(p1_fixed, p2_final, g1, g2)
        if u_final is not None:
            app.PrintInfo(f"Usando aproximación: P2={p2_final:.1f} MW, U={u_final:.4f} p.u.")
            return float(p2_final), float(u_final), bus_final
        
        return 0.0, None, None
    
    else:
        # P2 fijo, buscar P1 (lógica similar)
        p2_fixed = float(fixed_p_mw)
        
        p1_low = 0.0
        p1_high = float(P_MAX)
        
        # Encontrar punto con U < 1.1
        for p1_test in np.arange(0.0, float(P_MAX), 10.0):
            p1_test_float = float(p1_test)
            feasible, u_max, _ = test_allocation_upper(p1_test_float, p2_fixed, g1, g2)
            if u_max is not None and u_max < target_voltage:
                p1_low = float(p1_test_float)
                break
        
        # Encontrar punto con U > 1.1
        for p1_test in np.arange(p1_low + 10.0, float(P_MAX) + 10.0, 10.0):
            p1_test_float = float(p1_test)
            feasible, u_max, _ = test_allocation_upper(p1_test_float, p2_fixed, g1, g2)
            if u_max is not None and u_max > target_voltage:
                p1_high = float(p1_test_float)
                break
        
        # Búsqueda binaria
        for iteration in range(20):
            p1_mid = float((p1_low + p1_high) / 2.0)
            feasible, u_mid, bus_mid = test_allocation_upper(p1_mid, p2_fixed, g1, g2)
            
            if u_mid is None:
                return 0.0, None, None
            
            if abs(u_mid - target_voltage) < 0.001:
                return float(p1_mid), float(u_mid), bus_mid
            elif u_mid < target_voltage:
                p1_low = float(p1_mid)
            else:
                p1_high = float(p1_mid)
        
        p1_final = float((p1_low + p1_high) / 2.0)
        feasible, u_final, bus_final = test_allocation_upper(p1_final, p2_fixed, g1, g2)
        return float(p1_final), float(u_final), bus_final

# === FUNCIÓN PARA PRUEBA RÁPIDA ===
def find_known_point():
    """Función para ayudar a encontrar un punto conocido"""
    app.PrintInfo("\n" + "="*60)
    app.PrintInfo("BUSCANDO PUNTO CONOCIDO PARA LÍMITE SUPERIOR")
    app.PrintInfo("="*60)
    
    if len(gen_nonsync) >= 2:
        g1 = gen_nonsync[0]
        g2 = gen_nonsync[1]
        
        app.PrintInfo(f"\nGeneradores: {g1.loc_name} y {g2.loc_name}")
        app.PrintInfo("Probando diferentes combinaciones...")
        
        # Probar algunas combinaciones típicas
        test_combinations = [
            (1.0, 1.0),   # Ambos muy bajos
            (50.0, 1.0),  # Uno alto, otro bajo
            (1.0, 50.0),  # Uno bajo, otro alto
            (100.0, 1.0), # Uno más alto
            (1.0, 100.0), # Otro más alto
        ]
        
        for p1, p2 in test_combinations:
            feasible, voltage, bus = test_allocation_upper(p1, p2, g1, g2)
            if voltage is not None:
                status = "✓ CERCANO A 1.1" if 1.09 <= voltage <= 1.11 else "  "
                app.PrintInfo(f"{status} P1={p1} MW, P2={p2} MW → U={voltage:.4f} p.u. en {bus}")
        
        app.PrintInfo("\nInstrucciones:")
        app.PrintInfo("1. Busca una combinación donde U esté entre 1.09 y 1.11 p.u.")
        app.PrintInfo("2. Esa será tu KNOWN_POINT")
        app.PrintInfo("3. Ajusta los valores en el código")
        app.PrintInfo("4. Ejecuta de nuevo el análisis completo")

# === FUNCIÓN PRINCIPAL ===
def run_upper_limit_analysis():
    """Ejecuta el análisis completo de límite superior"""
    
    app.PrintInfo("="*60)
    app.PrintInfo("ANÁLISIS DE LÍMITE SUPERIOR DE TENSIÓN")
    app.PrintInfo(f"Umbral: {MAX_VOLTAGE} p.u.")
    app.PrintInfo(f"Puntos a encontrar: {NUM_POINTS}")
    app.PrintInfo("="*60)
    
    # Primero, intentar encontrar un punto conocido si no tenemos uno bueno
    app.PrintInfo(f"\nPunto conocido actual: P1={KNOWN_POINT['P1_MW']} MW, P2={KNOWN_POINT['P2_MW']} MW")
    
    if len(gen_nonsync) >= 2:
        g1 = gen_nonsync[0]
        g2 = gen_nonsync[1]
        feasible, voltage, bus = test_allocation_upper(
            KNOWN_POINT['P1_MW'], KNOWN_POINT['P2_MW'], g1, g2
        )
        
        if voltage is not None:
            app.PrintInfo(f"Voltaje actual: {voltage:.4f} p.u.")
            if not (1.09 <= voltage <= 1.11):
                app.PrintWarn("¡ADVERTENCIA! El punto conocido no está cerca de 1.1 p.u.")
                app.PrintWarn("Ejecuta find_known_point() primero para encontrar un buen punto")
                return
    
    # === Encontrar pares cercanos ===
    pairs_close = []
    for g1, g2 in itertools.combinations(gen_nonsync, 2):
        try:
            node1 = get_evaluation_bus_for_generator(g1)
            node2 = get_evaluation_bus_for_generator(g2)
            
            if not node1 or not node2:
                continue
            
            z_ij = get_impedance_between_nodes(node1, node2)
            
            if z_ij >= Z_THRESHOLD:
                pairs_close.append((g1, g2, z_ij))
                app.PrintInfo(f"Par cercano: {g1.loc_name}-{g2.loc_name}, |Z|={z_ij:.6f}")
        except Exception as e:
            app.PrintError(f"Error con par {g1.loc_name}-{g2.loc_name}: {str(e)}")
    
    if not pairs_close:
        app.PrintError("No se encontraron pares cercanos")
        return
    
    # === Para cada par, encontrar la frontera ===
    for g1, g2, z_ij in pairs_close:
        app.PrintInfo(f"\n{'='*60}")
        app.PrintInfo(f"Analizando: {g1.loc_name} vs {g2.loc_name}")
        app.PrintInfo(f"Impedancia: {z_ij:.6f}")
        app.PrintInfo(f"{'='*60}")
        
        boundary_points = []
        
        # 1. Primero verificar si el punto conocido funciona
        app.PrintInfo(f"\nProbando punto conocido: P1={KNOWN_POINT['P1_MW']} MW, P2={KNOWN_POINT['P2_MW']} MW")
        feasible, voltage, bus = test_allocation_upper(
            KNOWN_POINT['P1_MW'], KNOWN_POINT['P2_MW'], g1, g2
        )
        
        if voltage is None:
            app.PrintError("No se pudo calcular el punto conocido. Verificar conexiones.")
            continue
        
        app.PrintInfo(f"Resultado: U={voltage:.4f} p.u., Factible={feasible}")
        
        if not (1.09 <= voltage <= 1.11):
            app.PrintError(f"El punto conocido está muy lejos de 1.1 p.u. ({voltage:.4f})")
            app.PrintError("Ejecuta find_known_point() para encontrar un mejor punto")
            continue
        
        # 2. Generar puntos P1 distribuidos - asegurar que sean float
        p1_start = float(KNOWN_POINT['P1_MW'])
        p1_end = float(OPPOSITE_POINT['P1_MW'])
        p1_values = np.linspace(p1_start, p1_end, NUM_POINTS)
        
        app.PrintInfo(f"\nBuscando {len(p1_values)} puntos desde P1={p1_start} hasta P1={p1_end} MW...")
        
        for i, p1 in enumerate(p1_values):
            p1_float = float(p1)  # Convertir explícitamente a float
            
            app.PrintInfo(f"\n[{i+1}/{len(p1_values)}] Buscando para P1={p1_float} MW")
            
            # Buscar P2 que haga U_max = 1.1
            p2_found, voltage_found, bus_found = find_limit_upper(
                g1, g2, p1_float, True, target_voltage=MAX_VOLTAGE
            )
            
            if p2_found > 0 and voltage_found is not None:
                if abs(voltage_found - MAX_VOLTAGE) < 0.02:
                    node1 = get_evaluation_bus_for_generator(g1)
                    node2 = get_evaluation_bus_for_generator(g2)
                    
                    point = {
                        "Indice": i+1,
                        "P1_MW": round(p1_float, 2),
                        "P2_MW": round(float(p2_found), 2),
                        "Bus_Critico": bus_found,
                        "U_Critico_pu": round(float(voltage_found), 4),
                        "Bus_G1": node1,
                        "Bus_G2": node2,
                        "Anomalia_Detectada": "NO"
                    }
                    
                    boundary_points.append(point)
                    app.PrintInfo(f"✓ Encontrado: P2={p2_found:.1f} MW, U={voltage_found:.4f} p.u.")
                else:
                    app.PrintWarn(f"✗ Voltaje fuera de rango: {voltage_found:.4f} p.u.")
            else:
                app.PrintWarn(f"✗ No se encontró límite para P1={p1_float} MW")
        
        if not boundary_points:
            app.PrintWarn("No se encontraron puntos válidos")
            continue
        
        # === Exportar resultados ===
        pair_folder = os.path.join(EXPORT_PATH, f"{g1.loc_name}_{g2.loc_name}")
        os.makedirs(pair_folder, exist_ok=True)
        
        # Exportar CSV
        csv_file = os.path.join(pair_folder, f"limite_superior_{g1.loc_name}_{g2.loc_name}.csv")
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ["Indice", "P1_MW", "P2_MW", "Bus_Critico", 
                         "U_Critico_pu", "Bus_G1", "Bus_G2", "Anomalia_Detectada"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for point in boundary_points:
                writer.writerow(point)
        
        app.PrintInfo(f"\n✓ Resultados exportados a: {csv_file}")
        app.PrintInfo(f"  Puntos encontrados: {len(boundary_points)}/{NUM_POINTS}")
        
        # Solo crear gráfica si tenemos puntos
        if len(boundary_points) > 1:
            try:
                # Crear gráfica
                plt.figure(figsize=(12, 8))
                
                p1_vals = [p["P1_MW"] for p in boundary_points]
                p2_vals = [p["P2_MW"] for p in boundary_points]
                voltages = [p["U_Critico_pu"] for p in boundary_points]
                
                plt.plot(p1_vals, p2_vals, 'r-', linewidth=2, label='Frontera U=1.1 p.u.')
                scatter = plt.scatter(p1_vals, p2_vals, c=voltages, cmap='RdYlBu_r',
                                    s=100, edgecolor='black', vmin=1.08, vmax=1.12)
                
                plt.xlabel(f"Potencia {g1.loc_name} (MW)", fontsize=12)
                plt.ylabel(f"Potencia {g2.loc_name} (MW)", fontsize=12)
                
                title = f"Límite Superior de Tensión\n{g1.loc_name} vs {g2.loc_name}\n"
                title += f"|Z|={z_ij:.4f}, Puntos={len(boundary_points)}, Tension Máxima 1.1 pu"
                plt.title(title, fontsize=14, fontweight='bold')
                
                #plt.grid(True, linestyle='--', alpha=0.7)
                #plt.colorbar(scatter, label='Tensión máxima (p.u.)')
                
                plt.tight_layout()
                
                plot_file = os.path.join(pair_folder, f"grafica_limite_superior_{g1.loc_name}_{g2.loc_name}.png")
                plt.savefig(plot_file, dpi=300)
                plt.close()
                
                app.PrintInfo(f"✓ Gráfica exportada a: {plot_file}")
            except Exception as e:
                app.PrintWarn(f"No se pudo crear la gráfica: {str(e)}")

# === EJECUCIÓN ===
try:
    # PRIMERO: Encontrar un punto conocido
     #find_known_point()
    
    # LUEGO: Ejecutar análisis completo
    run_upper_limit_analysis()
    
except Exception as e:
    app.PrintError(f"Error en ejecución: {str(e)}")
    import traceback
    app.PrintError(traceback.format_exc())

# Restaurar estado original
app.PrintInfo("\nRestaurando estado original...")
for g in gen_nonsync:
    g.pgini = float(pgini_base[g])
ldf.Execute()

app.PrintInfo("\n" + "="*60)
app.PrintInfo("ANÁLISIS COMPLETADO")
app.PrintInfo("="*60)