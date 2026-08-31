import powerfactory as pf
import itertools
import heapq
import csv
import os
import math
import matplotlib.pyplot as plt
import re  # Importar módulo de expresiones regulares
import numpy as np  # Agregado para interpolación
from pathlib import Path

# === Inicialización de PowerFactory ===
app = pf.GetApplication()
app.ClearOutputWindow()

# === Configuración de parámetros ===
MIN_VOLTAGE = 0.9  # Umbral de voltaje mínimo (p.u.) para considerar estable
P_STEP = 20  # Paso de potencia en MW para el barrido (precisión)
P_MAX = 400  # REDUCIDO de 1200 a 400 MW
Z_THRESHOLD = 0.1  # Umbral de impedancia para considerar nodos eléctricamente cercanos


# === PARÁMETRO NUEVO: Número de puntos a extraer ===
NUM_POINTS = 70  # Cambia este valor según cuántos puntos quieras extraer

# Punto conocido inicial (basado en tu hallazgo)
KNOWN_POINT = {"P1_MW": 1, "P2_MW": 1183}  # P1=1MW, P2=425MW da U=0.9
# Punto opuesto (será el final del barrido)
OPPOSITE_POINT = {"P1_MW": 770, "P2_MW": 1}  # P1=425MW, P2=1MW

# ------------------------------------------------------------
# RUTAS
# ------------------------------------------------------------

# Raíz del repositorio
REPO_ROOT = Path(__file__).resolve().parents[2]

# Ejemplo que se desea procesar
EXAMPLE = "IEEE39"

# ------------------------------------------------------------
# ENTRADA
# Archivo generado por find_electrically_close_nodes.py
# ------------------------------------------------------------
Z_IMPORT_PATH = (REPO_ROOT / "data" / "example" / EXAMPLE / "pares_nodos_cercanos.csv")

# ------------------------------------------------------------
# SALIDA
# Carpeta donde se guardarán los resultados del barrido
# ------------------------------------------------------------
EXPORT_PATH = (REPO_ROOT / "data" / "results" / EXAMPLE)

# Crear carpeta de resultados si no existe
EXPORT_PATH.mkdir(parents=True, exist_ok=True)

# Mostrar rutas para verificar
print(f"📌 Ejemplo: {EXAMPLE}")
print(f"📥 Entrada: {Z_IMPORT_PATH}")
print(f"📤 Salida:  {EXPORT_PATH}")

##############################################################
impedance_data = {}

try:
    with open(Z_IMPORT_PATH, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            nodo_i = row['Nodo_i']
            nodo_j = row['Nodo_j']
            zij = float(row['|Zij/zjj|'])
            
            # Almacenar en ambos sentidos para búsqueda rápida
            impedance_data[(nodo_i, nodo_j)] = zij
            impedance_data[(nodo_j, nodo_i)] = zij
            
    app.PrintInfo(f"Datos de impedancia cargados: {len(impedance_data)//2} pares de nodos")
except Exception as e:
    app.PrintError(f"Error cargando archivo de impedancias: {str(e)}")
    raise SystemExit

# === Función para verificar tendencia de tensión ===
def check_voltage_trend(current_voltage, previous_voltage, current_power, previous_power, threshold=0.001):
    """
    Verifica la tendencia de la tensión vs potencia.
    
    Returns:
        tuple: (is_anomaly, anomaly_type, message)
    """
    if previous_voltage is None or previous_power is None:
        return False, None, ""
    
    power_diff = current_power - previous_power
    voltage_diff = current_voltage - previous_voltage
    
    # Comportamiento esperado: cuando la potencia aumenta, la tensión debería disminuir
    if power_diff > 0:
        # Si la tensión aumenta cuando debería disminuir
        if voltage_diff > threshold:
            return True, "increasing", f"Tensión aumentó {voltage_diff:.6f} p.u. con aumento de potencia"
        # Si la tensión se mantiene constante
        elif abs(voltage_diff) < threshold:
            return True, "flat", f"Tensión constante con aumento de potencia"
    
    return False, None, ""

# === Identificación de generadores ===
sync_types = ["ElmSym"]
nonsync_types = ["ElmAsy", "ElmGenstat", "ElmPvsys", "ElmGenpv"]

gen_sync = []
gen_nonsync = []

for gtype in sync_types:
    gens = app.GetCalcRelevantObjects(f"*.{gtype}")
    if gens:
        gen_sync.extend([g for g in gens if hasattr(g, 'outserv') and g.outserv == 0])

for gtype in nonsync_types:
    gens = app.GetCalcRelevantObjects(f"*.{gtype}")
    if gens:
        gen_nonsync.extend([g for g in gens if hasattr(g, 'outserv') and g.outserv == 0])

app.PrintInfo(f"Generadores síncronos encontrados (en servicio): {len(gen_sync)}")
app.PrintInfo(f"Generadores no síncronos encontrados (en servicio): {len(gen_nonsync)}")

if not gen_nonsync:
    app.PrintError("No se encontraron generadores no síncronos (en servicio). Verifique los tipos de generadores.")
    raise SystemExit

# Guardar pgini base para restaurar
pgini_base = {g: g.pgini for g in gen_nonsync}

# === Función para extraer número del nombre del bus ===
def extract_bus_number(bus_name):
    """Extrae el número del nombre del bus (ej: 'Bus 4' → '4', '4' → '4')"""
    # Buscar dígitos en el nombre
    numbers = re.findall(r'\d+', bus_name)
    if numbers:
        return numbers[0]  # Devolver el primer número encontrado
    return bus_name  # Si no hay números, devolver el nombre original

# === Función para determinar el nodo de evaluación para un generador ===
def get_evaluation_bus_for_generator(generator):
    """
    Determina el nodo apropiado para evaluar la impedancia del generador.
    
    Lógica:
    1. Si el generador está conectado a través de un transformador (con nombre que contiene "TR" y "LV"),
       usa el bus del lado HV del transformador.
    2. Si no hay transformador o no cumple el patrón, usa el bus directo de conexión del generador.
    """
    try:
        # Obtener el bus de conexión directo del generador
        gen_bus = generator.bus1.cterm if hasattr(generator, 'bus1') and generator.bus1.cterm else None
        
        if not gen_bus:
            app.PrintWarn(f"No se pudo obtener bus para {generator.loc_name}")
            return None
        
        # Buscar transformadores conectados a este bus
        transformers = app.GetCalcRelevantObjects("*.ElmTr2") or []
        transformers.extend(app.GetCalcRelevantObjects("*.ElmTrf") or [])
        
        for trafo in transformers:
            # Verificar si el transformador está conectado al bus del generador
            if (hasattr(trafo, 'bushv') and hasattr(trafo, 'buslv')):
                # Caso 1: Generador en lado LV, transformador conecta a red en HV
                if trafo.buslv.cterm == gen_bus:
                    # Verificar si el nombre del transformador sigue el patrón esperado
                    trafo_name = trafo.loc_name.lower()
                    gen_name = generator.loc_name.lower()
                    
                    # Buscar coincidencias en nombres (ej: "TR PV1" y "PV1")
                    if ('tr' in trafo_name and any(word in trafo_name for word in ['pv', 'wind', 'gen']) and
                        any(word in gen_name for word in ['pv', 'wind', 'gen'])):
                        app.PrintInfo(f"Generador {generator.loc_name} conectado a través de transformador {trafo.loc_name} (LV→HV)")
                        return trafo.bushv.cterm.loc_name
                
                # Caso 2: Generador en lado HV (conexión directa menos común)
                elif trafo.bushv.cterm == gen_bus:
                    app.PrintInfo(f"Generador {generator.loc_name} conectado en lado HV del transformador {trafo.loc_name}")
                    return gen_bus.loc_name
        
        # Si no se encuentra transformador o no cumple el patrón, usar conexión directa
        app.PrintInfo(f"Generador {generator.loc_name} conectado directamente al bus {gen_bus.loc_name}")
        return gen_bus.loc_name
        
    except Exception as e:
        app.PrintWarn(f"Error determinando bus de evaluación para {generator.loc_name}: {str(e)}")
        # Fallback: usar el bus directo del generador
        if hasattr(generator, 'bus1') and generator.bus1.cterm:
            return generator.bus1.cterm.loc_name
        return None

# === Función para obtener impedancia entre dos nodos ===
def get_impedance_between_nodes(node1_name, node2_name):
    """Obtiene la impedancia entre dos nodos desde los datos cargados del CSV"""
    # Extraer números de los nombres de buses
    node1_num = extract_bus_number(node1_name)
    node2_num = extract_bus_number(node2_name)
    
    key = (node1_num, node2_num)
    if key in impedance_data:
        return impedance_data[key]
    else:
        app.PrintInfo(f"No se encontró impedancia entre {node1_name} ({node1_num}) y {node2_name} ({node2_num}) en el CSV")
        return float('inf')

# === Configuración del flujo de carga ===
ldf = app.GetFromStudyCase("ComLdf")
if ldf is None:
    raise RuntimeError("No se encontró ComLdf en el estudio")

def test_allocation_simple(p1_kw, p2_kw, g1, g2, min_pu=0.9):
    """
    Función simplificada para probar una asignación de potencia.
    Devuelve si es factible, la tensión mínima y el bus crítico.
    """
    # Guardar valores originales
    p1_orig = g1.pgini
    p2_orig = g2.pgini
    
    # Asignar nuevas potencias activas
    g1.pgini = p1_kw
    g2.pgini = p2_kw
    
    # Ejecutar flujo de carga
    err = ldf.Execute()
    converged = (err == 0)
    
    # Obtener tensión mínima
    u_min = None
    bus_critico = None
    
    if converged:
        buses = app.GetCalcRelevantObjects("*.ElmTerm") or []
        for b in buses:
            try:
                u = b.GetAttribute("m:u")
                if u is not None:
                    if u_min is None or u < u_min:
                        u_min = u
                        bus_critico = b.loc_name
            except Exception:
                continue
    
    # Restaurar valores originales
    g1.pgini = p1_orig
    g2.pgini = p2_orig
    
    # Verificar factibilidad
    if not converged or u_min is None:
        return False, None, None
    
    feasible = u_min >= min_pu
    return feasible, u_min, bus_critico

# === FUNCIÓN MEJORADA PARA ENCONTRAR EL LÍMITE DONDE U = 0.9 p.u. ===
def find_limit_at_voltage(g1, g2, fixed_p, fixed_gen, target_voltage=0.9):
    """
    Encuentra el límite exacto donde la tensión mínima = target_voltage.
    Usa interpolación lineal entre puntos factibles/no factibles.
    
    Args:
        g1, g2: Generadores
        fixed_p: Potencia fija (kW)
        fixed_gen: Generador con potencia fija (g1 o g2)
        target_voltage: Tensión objetivo (0.9 p.u.)
        
    Returns:
        tuple: (power_at_limit_kw, voltage_at_limit, critical_bus)
    """
    if fixed_gen == g1:
        # Buscamos P2 para P1 fijo
        p1_fixed = fixed_p
        
        # Primero, buscar dos puntos: uno con U > target y otro con U < target
        low_power = 0
        high_power = P_MAX * 1000
        low_voltage = None
        high_voltage = None
        crit_bus = None
        
        # Buscar un punto inicial con U > target_voltage
        for p_test in range(0, int(high_power), P_STEP * 1000):
            feasible, voltage, bus = test_allocation_simple(p1_fixed, p_test, g1, g2, target_voltage)
            
            if voltage is not None:
                crit_bus = bus
                if voltage > target_voltage:
                    low_power = p_test
                    low_voltage = voltage
                else:
                    high_power = p_test
                    high_voltage = voltage
                    break
        
        # Si encontramos ambos puntos, hacer interpolación lineal
        if low_voltage is not None and high_voltage is not None and low_voltage > target_voltage > high_voltage:
            # Interpolación lineal para encontrar P donde U = target_voltage
            delta_p = high_power - low_power
            delta_v = high_voltage - low_voltage
            
            if delta_v != 0:
                # Fórmula de interpolación lineal
                p_at_target = low_power + (target_voltage - low_voltage) * (delta_p / delta_v)
                
                # Verificar el punto interpolado
                feasible_target, voltage_target, bus_target = test_allocation_simple(
                    p1_fixed, p_at_target, g1, g2, target_voltage
                )
                
                if voltage_target is not None:
                    # Ajustar iterativamente si es necesario
                    if abs(voltage_target - target_voltage) > 0.001:
                        # Búsqueda binaria refinada
                        p_low = low_power if voltage_target > target_voltage else p_at_target
                        p_high = p_at_target if voltage_target > target_voltage else high_power
                        
                        for _ in range(10):  # 10 iteraciones máximo
                            p_mid = (p_low + p_high) / 2
                            feasible_mid, voltage_mid, bus_mid = test_allocation_simple(
                                p1_fixed, p_mid, g1, g2, target_voltage
                            )
                            
                            if voltage_mid is None:
                                break
                                
                            if abs(voltage_mid - target_voltage) < 0.001:
                                return p_mid, voltage_mid, bus_mid
                            elif voltage_mid > target_voltage:
                                p_low = p_mid
                            else:
                                p_high = p_mid
                        
                        p_at_target = (p_low + p_high) / 2
                        feasible_target, voltage_target, bus_target = test_allocation_simple(
                            p1_fixed, p_at_target, g1, g2, target_voltage
                        )
                    
                    return p_at_target, voltage_target, bus_target
        
        # Si no se pudo interpolar, buscar el último punto factible
        best_p = 0
        best_v = None
        best_bus = None
        
        for p_test in range(0, int(P_MAX * 1000), P_STEP * 1000):
            feasible, voltage, bus = test_allocation_simple(p1_fixed, p_test, g1, g2, target_voltage)
            
            if voltage is not None:
                if feasible:
                    best_p = p_test
                    best_v = voltage
                    best_bus = bus
                else:
                    # Encontramos un punto no factible después de uno factible
                    if best_p > 0:
                        # Hacer búsqueda binaria entre el último factible y este no factible
                        p_low = best_p
                        p_high = p_test
                        
                        for _ in range(8):
                            p_mid = (p_low + p_high) / 2
                            feasible_mid, voltage_mid, bus_mid = test_allocation_simple(
                                p1_fixed, p_mid, g1, g2, target_voltage
                            )
                            
                            if voltage_mid is None:
                                break
                                
                            if feasible_mid:
                                best_p = p_mid
                                best_v = voltage_mid
                                best_bus = bus_mid
                                p_low = p_mid
                            else:
                                p_high = p_mid
                        
                        return best_p, best_v, best_bus
                    else:
                        # No hubo puntos factibles
                        break
        
        return best_p, best_v, best_bus
    
    else:  # fixed_gen == g2
        # Buscamos P1 para P2 fijo (lógica similar)
        p2_fixed = fixed_p
        
        # Buscar puntos para interpolación
        low_power = 0
        high_power = P_MAX * 1000
        low_voltage = None
        high_voltage = None
        crit_bus = None
        
        for p_test in range(0, int(high_power), P_STEP * 1000):
            feasible, voltage, bus = test_allocation_simple(p_test, p2_fixed, g1, g2, target_voltage)
            
            if voltage is not None:
                crit_bus = bus
                if voltage > target_voltage:
                    low_power = p_test
                    low_voltage = voltage
                else:
                    high_power = p_test
                    high_voltage = voltage
                    break
        
        # Interpolación lineal
        if low_voltage is not None and high_voltage is not None and low_voltage > target_voltage > high_voltage:
            delta_p = high_power - low_power
            delta_v = high_voltage - low_voltage
            
            if delta_v != 0:
                p_at_target = low_power + (target_voltage - low_voltage) * (delta_p / delta_v)
                
                feasible_target, voltage_target, bus_target = test_allocation_simple(
                    p_at_target, p2_fixed, g1, g2, target_voltage
                )
                
                if voltage_target is not None:
                    if abs(voltage_target - target_voltage) > 0.001:
                        p_low = low_power if voltage_target > target_voltage else p_at_target
                        p_high = p_at_target if voltage_target > target_voltage else high_power
                        
                        for _ in range(10):
                            p_mid = (p_low + p_high) / 2
                            feasible_mid, voltage_mid, bus_mid = test_allocation_simple(
                                p_mid, p2_fixed, g1, g2, target_voltage
                            )
                            
                            if voltage_mid is None:
                                break
                                
                            if abs(voltage_mid - target_voltage) < 0.001:
                                return p_mid, voltage_mid, bus_mid
                            elif voltage_mid > target_voltage:
                                p_low = p_mid
                            else:
                                p_high = p_mid
                        
                        p_at_target = (p_low + p_high) / 2
                        feasible_target, voltage_target, bus_target = test_allocation_simple(
                            p_at_target, p2_fixed, g1, g2, target_voltage
                        )
                    
                    return p_at_target, voltage_target, bus_target
        
        # Búsqueda alternativa
        best_p = 0
        best_v = None
        best_bus = None
        
        for p_test in range(0, int(P_MAX * 1000), P_STEP * 1000):
            feasible, voltage, bus = test_allocation_simple(p_test, p2_fixed, g1, g2, target_voltage)
            
            if voltage is not None:
                if feasible:
                    best_p = p_test
                    best_v = voltage
                    best_bus = bus
                else:
                    if best_p > 0:
                        p_low = best_p
                        p_high = p_test
                        
                        for _ in range(8):
                            p_mid = (p_low + p_high) / 2
                            feasible_mid, voltage_mid, bus_mid = test_allocation_simple(
                                p_mid, p2_fixed, g1, g2, target_voltage
                            )
                            
                            if voltage_mid is None:
                                break
                                
                            if feasible_mid:
                                best_p = p_mid
                                best_v = voltage_mid
                                best_bus = bus_mid
                                p_low = p_mid
                            else:
                                p_high = p_mid
                        
                        return best_p, best_v, best_bus
                    else:
                        break
        
        return best_p, best_v, best_bus

# === NUEVA FUNCIÓN: Calcular puntos distribuidos equitativamente ===
def calculate_distributed_points(num_points):
    """
    Calcula los valores de P1 distribuidos equitativamente desde el punto conocido
    hasta el punto opuesto.
    
    Args:
        num_points: Número total de puntos a extraer (incluyendo inicio y fin)
        
    Returns:
        list: Lista de valores P1_MW distribuidos
    """
    if num_points < 2:
        return [KNOWN_POINT["P1_MW"], OPPOSITE_POINT["P1_MW"]]
    
    # Crear array linealmente espaciado desde P1_inicio hasta P1_fin
    p1_start = KNOWN_POINT["P1_MW"]
    p1_end = OPPOSITE_POINT["P1_MW"]
    
    # Generar puntos distribuidos equitativamente
    p1_values = np.linspace(p1_start, p1_end, num_points)
    
    # Redondear a 1 decimal para mayor claridad
    p1_values = [round(p, 1) for p in p1_values]
    
    app.PrintInfo(f"\nDistribución de {num_points} puntos:")
    app.PrintInfo(f"P1 conocido: {p1_start} MW")
    app.PrintInfo(f"P1 opuesto: {p1_end} MW")
    app.PrintInfo(f"Puntos P1: {p1_values}")
    
    return p1_values

# === NUEVA FUNCIÓN: Encontrar puntos distribuidos ===
def find_distributed_boundary_points(g1, g2, num_points):
    """
    Encuentra puntos distribuidos equitativamente en la frontera de estabilidad.
    
    Args:
        g1, g2: Generadores
        num_points: Número de puntos a encontrar
        
    Returns:
        list: Lista de puntos en la frontera
    """
    boundary_points = []
    
    # Calcular valores P1 distribuidos
    p1_values = calculate_distributed_points(num_points)
    
    app.PrintInfo(f"\nBuscando {len(p1_values)} puntos en la frontera...")
    
    # Para cada valor de P1, encontrar el P2 correspondiente donde U = MIN_VOLTAGE
    for i, p1 in enumerate(p1_values):
        p1_kw = p1 * 1000
        
        app.PrintInfo(f"\n[{i+1}/{len(p1_values)}] Buscando P2 para P1={p1} MW:")
        
        # Buscar el P2 correspondiente
        p2_kw, voltage, bus_crit = find_limit_at_voltage(
            g1, g2, p1_kw, g1, target_voltage=MIN_VOLTAGE
        )
        
        if p2_kw > 0 and voltage is not None:
            # Verificar que el voltaje esté cerca del objetivo
            if abs(voltage - MIN_VOLTAGE) < 0.02:  # 0.02 p.u. de tolerancia
                # Obtener buses de evaluación
                eval_bus1 = get_evaluation_bus_for_generator(g1)
                eval_bus2 = get_evaluation_bus_for_generator(g2)
                
                point_data = {
                    "P1_MW": p1,
                    "P2_MW": p2_kw / 1000,
                    "Bus_Critico": bus_crit,
                    "U_Critico_pu": voltage,
                    "Bus_G1": eval_bus1,
                    "Bus_G2": eval_bus2,
                    "Anomalia_Detectada": "NO",
                    "Indice": i+1
                }
                
                boundary_points.append(point_data)
                
                app.PrintInfo(f"✓ Punto {i+1}: P1={p1} MW → P2={p2_kw/1000:.1f} MW (U={voltage:.4f} p.u.)")
            else:
                app.PrintWarn(f"✗ Punto {i+1}: P1={p1} MW → P2={p2_kw/1000:.1f} MW (U={voltage:.4f} p.u., fuera de tolerancia)")
        else:
            app.PrintWarn(f"✗ Punto {i+1}: P1={p1} MW → No se encontró límite")
    
    return boundary_points

# === Función para filtrar puntos no deseados ===
def filter_boundary_points(points):
    """Filtra puntos no deseados pero mantiene los extremos válidos."""
    filtered = []
    points = [p for p in points if not ((p['P1_MW'] == 0 and p['P2_MW'] > 0) or (p['P2_MW'] == 0 and p['P1_MW'] > 0))]
    points.sort(key=lambda x: x['P1_MW'])
    
    prev_p1 = None
    for p in points:
        if prev_p1 is not None and p['P1_MW'] == prev_p1:
            if p['P2_MW'] > filtered[-1]['P2_MW']:
                filtered[-1] = p
        else:
            filtered.append(p)
        prev_p1 = p['P1_MW']
    return filtered

# === Función para ejecutar el análisis completo ===
def run_stability_analysis(contingency_name=None, contingency_element=None):
    """Ejecuta el análisis completo de estabilidad para una condición dada"""
    
    # Aplicar contingencia si se especifica
    original_status = None
    if contingency_element:
        try:
            original_status = contingency_element.outserv
            contingency_element.outserv = 1  # Poner elemento fuera de servicio
            app.PrintInfo(f"Aplicando contingencia: {contingency_name} - {contingency_element.loc_name}")
            # Ejecutar LDF para estabilizar la red después de la contingencia
            ldf.Execute()
        except Exception as e:
            app.PrintError(f"Error aplicando contingencia: {str(e)}")
            return
    
    # === Encontrar pares eléctricamente cercanos ===
    pairs_close = []
    for g1, g2 in itertools.combinations(gen_nonsync, 2):
        try:
            # Obtener los nodos de evaluación para ambos generadores
            node1 = get_evaluation_bus_for_generator(g1)
            node2 = get_evaluation_bus_for_generator(g2)
            
            if not node1 or not node2:
                app.PrintInfo(f"Saltando par {g1.loc_name} - {g2.loc_name} (no se pudo obtener nodos de evaluación)")
                continue
            
            # Obtener impedancia entre los nodos desde el CSV
            z_ij = get_impedance_between_nodes(node1, node2)
            node1_num = extract_bus_number(node1)
            node2_num = extract_bus_number(node2)
            app.PrintInfo(f"Impedancia {g1.loc_name} ({node1} [{node1_num}]) - {g2.loc_name} ({node2} [{node2_num}]): |Z| = {z_ij:.6f}")
            
            if z_ij >= Z_THRESHOLD:
                pairs_close.append((g1, g2, round(z_ij, 6)))
                app.PrintInfo(f"  → PAR CERCANO (|Z| = {z_ij:.6f} >= {Z_THRESHOLD})")
            else:
                app.PrintInfo(f"  → Par no cercano (|Z| = {z_ij:.6f} < {Z_THRESHOLD})")
                
        except Exception as e:
            app.PrintError(f"Error calculando impedancia entre {g1.loc_name} y {g2.loc_name}: {str(e)}")
            continue

    if not pairs_close:
        app.PrintInfo(f"No se encontraron pares eléctricamente cercanos (|Z| >= {Z_THRESHOLD}).")
        # Restaurar elemento si era contingencia
        if contingency_element and original_status is not None:
            contingency_element.outserv = original_status
            ldf.Execute()
        return

    # === Análisis de pares cercanos ===
    all_boundary_data = []

    for g1, g2, z_ij in pairs_close:
        node1 = get_evaluation_bus_for_generator(g1)
        node2 = get_evaluation_bus_for_generator(g2)
        app.PrintInfo(f"\n{'='*60}")
        app.PrintInfo(f"Analizando dupla: {g1.loc_name} (Bus: {node1}) - {g2.loc_name} (Bus: {node2})")
        app.PrintInfo(f"Impedancia: |Z| = {z_ij:.6f}")
        app.PrintInfo(f"Punto inicial conocido: P1={KNOWN_POINT['P1_MW']} MW, P2={KNOWN_POINT['P2_MW']} MW")
        app.PrintInfo(f"Punto final objetivo: P1={OPPOSITE_POINT['P1_MW']} MW, P2={OPPOSITE_POINT['P2_MW']} MW")
        app.PrintInfo(f"Número de puntos a extraer: {NUM_POINTS}")
        app.PrintInfo(f"Buscando puntos donde U_min = {MIN_VOLTAGE} p.u.")
        app.PrintInfo(f"{'='*60}")
        
        # === USAR LA NUEVA FUNCIÓN PARA PUNTOS DISTRIBUIDOS ===
        boundary_points = find_distributed_boundary_points(g1, g2, NUM_POINTS)
        
        # Verificar que tenemos datos
        if not boundary_points:
            app.PrintWarn(f"No se encontraron puntos para la dupla {g1.loc_name}-{g2.loc_name}")
            continue
        
        # Asegurar que tenemos el punto conocido y el opuesto
        known_found = False
        opposite_found = False
        
        for point in boundary_points:
            if (abs(point["P1_MW"] - KNOWN_POINT["P1_MW"]) < 0.1 and 
                abs(point["P2_MW"] - KNOWN_POINT["P2_MW"]) < 0.1):
                known_found = True
            if (abs(point["P1_MW"] - OPPOSITE_POINT["P1_MW"]) < 0.1 and 
                abs(point["P2_MW"] - OPPOSITE_POINT["P2_MW"]) < 0.1):
                opposite_found = True
        
        # Agregar puntos faltantes si es necesario
        if not known_found:
            # Verificar el punto conocido directamente
            feasible, voltage, bus_crit = test_allocation_simple(
                KNOWN_POINT["P1_MW"] * 1000, 
                KNOWN_POINT["P2_MW"] * 1000, 
                g1, g2, MIN_VOLTAGE
            )
            
            if voltage is not None:
                eval_bus1 = get_evaluation_bus_for_generator(g1)
                eval_bus2 = get_evaluation_bus_for_generator(g2)
                
                boundary_points.append({
                    "P1_MW": KNOWN_POINT["P1_MW"],
                    "P2_MW": KNOWN_POINT["P2_MW"],
                    "Bus_Critico": bus_crit,
                    "U_Critico_pu": voltage,
                    "Bus_G1": eval_bus1,
                    "Bus_G2": eval_bus2,
                    "Anomalia_Detectada": "NO",
                    "Indice": 0
                })
        
        if not opposite_found:
            # Buscar el punto opuesto
            app.PrintInfo(f"\nBuscando punto opuesto: P1={OPPOSITE_POINT['P1_MW']} MW")
            p1_kw = OPPOSITE_POINT["P1_MW"] * 1000
            p2_kw, voltage, bus_crit = find_limit_at_voltage(
                g1, g2, p1_kw, g1, target_voltage=MIN_VOLTAGE
            )
            
            if p2_kw > 0 and voltage is not None:
                eval_bus1 = get_evaluation_bus_for_generator(g1)
                eval_bus2 = get_evaluation_bus_for_generator(g2)
                
                boundary_points.append({
                    "P1_MW": OPPOSITE_POINT["P1_MW"],
                    "P2_MW": p2_kw / 1000,
                    "Bus_Critico": bus_crit,
                    "U_Critico_pu": voltage,
                    "Bus_G1": eval_bus1,
                    "Bus_G2": eval_bus2,
                    "Anomalia_Detectada": "NO",
                    "Indice": NUM_POINTS + 1
                })
        
        # Filtrar y ordenar puntos
        unique_data = {}
        for point in boundary_points:
            key = (round(point["P1_MW"], 1), round(point["P2_MW"], 1))
            unique_data[key] = point
        
        sorted_data = sorted(unique_data.values(), key=lambda x: x["P1_MW"])
        filtered_data = filter_boundary_points(sorted_data)
        
        if not filtered_data:
            app.PrintWarn(f"No quedaron puntos después del filtrado para {g1.loc_name}-{g2.loc_name}")
            continue
        
        filtered_data.sort(key=lambda x: x['P1_MW'])
        
        # Guardar datos de esta dupla
        pair_data = {
            "Gen1": g1.loc_name,
            "Gen2": g2.loc_name,
            "Bus1": node1,
            "Bus2": node2,
            "Impedancia_Z": z_ij,
            "Num_Puntos_Solicitados": NUM_POINTS,
            "Puntos_Encontrados": len(filtered_data),
            "Boundary_Points": filtered_data
        }
        all_boundary_data.append(pair_data)
        
        app.PrintInfo(f"\n{'='*60}")
        app.PrintInfo(f"RESUMEN para {g1.loc_name}-{g2.loc_name}:")
        app.PrintInfo(f"- Puntos solicitados: {NUM_POINTS}")
        app.PrintInfo(f"- Puntos encontrados: {len(filtered_data)}")
        if filtered_data:
            app.PrintInfo(f"- P1 inicial: {filtered_data[0]['P1_MW']:.1f} MW, P2: {filtered_data[0]['P2_MW']:.1f} MW")
            app.PrintInfo(f"- P1 final: {filtered_data[-1]['P1_MW']:.1f} MW, P2: {filtered_data[-1]['P2_MW']:.1f} MW")
            app.PrintInfo(f"- Voltaje promedio: {sum(p['U_Critico_pu'] for p in filtered_data)/len(filtered_data):.4f} p.u.")
        app.PrintInfo(f"{'='*60}")

    # === Exportar resultados ===
    base_folder = EXPORT_PATH
    if contingency_name:
        base_folder = os.path.join(EXPORT_PATH, f"N-1_{contingency_name}")
        os.makedirs(base_folder, exist_ok=True)
    
    for pair in all_boundary_data:
        if not pair["Boundary_Points"]:
            continue
            
        pair_folder = os.path.join(EXPORT_PATH, f"CAP_{g1.loc_name}_{g2.loc_name}")
        os.makedirs(pair_folder, exist_ok=True)
        
        # Exportar CSV
        csv_filename = f"{EXAMPLE}_CAP_{g1.loc_name}_{g2.loc_name}.csv"
        csv_path = os.path.join(pair_folder, csv_filename)
        
        fieldnames = [
            "Indice", "P1_MW", "P2_MW",
            "Bus_Critico", "U_Critico_pu",
            "Bus_G1", "Bus_G2",
            "Anomalia_Detectada"
        ]
        
        with open(csv_path, "w", newline="", encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for point in pair["Boundary_Points"]:
                writer.writerow(point)
        
        # Generar gráficas
        plt.figure(figsize=(12, 8))
        p1_values = [p["P1_MW"] for p in pair["Boundary_Points"]]
        p2_values = [p["P2_MW"] for p in pair["Boundary_Points"]]
        voltages = [p["U_Critico_pu"] for p in pair["Boundary_Points"]]
        indices = [p.get("Indice", i+1) for i, p in enumerate(pair["Boundary_Points"])]
        
        # Graficar línea principal
        plt.plot(p1_values, p2_values, 'b-', linewidth=2, label='Frontera de estabilidad')
        
        # Marcar puntos individuales con etiquetas
        scatter = plt.scatter(p1_values, p2_values, c=voltages, cmap='RdYlGn', 
                             s=150, edgecolors='black', alpha=0.8,
                             vmin=MIN_VOLTAGE-0.02, vmax=MIN_VOLTAGE+0.02)
        
        # Etiquetar algunos puntos importantes
        if len(p1_values) > 0:
            # Punto inicial (conocido)
            plt.annotate(f"Inicio\nP1={p1_values[0]:.1f}\nP2={p2_values[0]:.1f}", 
                        (p1_values[0], p2_values[0]), 
                        xytext=(10, 10), textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.8),
                        fontsize=9)
            
            # Punto final (opuesto)
            plt.annotate(f"Fin\nP1={p1_values[-1]:.1f}\nP2={p2_values[-1]:.1f}", 
                        (p1_values[-1], p2_values[-1]), 
                        xytext=(-10, -10), textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='lightcoral', alpha=0.8),
                        fontsize=9)
        
        # Configurar gráfica
        plt.xlabel(f"Potencia {pair['Gen1']} (MW)", fontsize=14, fontweight='bold')
        plt.ylabel(f"Potencia {pair['Gen2']} (MW)", fontsize=14, fontweight='bold')
        
        title_lines = [
            f"Frontera de Estabilidad - {pair['Num_Puntos_Solicitados']} puntos",
            f"{pair['Gen1']} vs {pair['Gen2']}",
            f"|Z| = {pair['Impedancia_Z']:.6f}, Tensión Mínima 0.9 pu"
        ]
        
        if contingency_name:
            title_lines.append(f"Contingencia: {contingency_name}")
        
        plt.title("\n".join(title_lines), fontsize=16, fontweight='bold', pad=20)
        
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # Añadir barra de color para voltajes
        #cbar = plt.colorbar(scatter)
        #cbar.set_label('Tensión mínima (p.u.)', fontsize=12)
        #cbar.ax.axhline(MIN_VOLTAGE, color='red', linewidth=2, linestyle='--')
        
        # Añadir información
        info_text = f"Puntos: {pair['Puntos_Encontrados']}/{pair['Num_Puntos_Solicitados']}\n"
        info_text += f"Umbral: {MIN_VOLTAGE} p.u.\n"
        info_text += f"U_avg: {sum(voltages)/len(voltages):.4f} p.u."
        
        plt.text(0.02, 0.98, info_text, transform=plt.gca().transAxes,
                fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        plt.tight_layout()
        
        plot_filename = f"boundary_plot_{pair['Gen1']}_{pair['Gen2']}.png"
        plot_path = os.path.join(pair_folder, plot_filename)
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        app.PrintInfo(f"\nResultados para {pair['Gen1']}-{pair['Gen2']}:")
        app.PrintInfo(f" - CSV guardado en: {csv_path}")
        app.PrintInfo(f" - Gráfica guardada en: {plot_path}")

    # Restaurar elemento si era contingencia
    if contingency_element and original_status is not None:
        try:
            contingency_element.outserv = original_status
            ldf.Execute()
            app.PrintInfo(f"Restaurando elemento: {contingency_element.loc_name}")
        except Exception as e:
            app.PrintError(f"Error restaurando elemento: {str(e)}")

    app.PrintInfo(f"\nAnálisis {'de contingencia ' + contingency_name if contingency_name else 'completado'}.")
    app.PrintInfo(f"Resultados en: {base_folder}")

# === EJECUCIÓN PRINCIPAL ===

# 1. Ejecutar análisis en condición normal
app.PrintInfo("="*60)
app.PrintInfo("EJECUTANDO ANÁLISIS EN CONDICIÓN NORMAL")
app.PrintInfo("="*60)
app.PrintInfo(f"Umbral de tensión: {MIN_VOLTAGE} p.u.")
app.PrintInfo(f"Número de puntos a extraer: {NUM_POINTS}")
app.PrintInfo(f"Punto inicial: P1={KNOWN_POINT['P1_MW']} MW, P2={KNOWN_POINT['P2_MW']} MW")
app.PrintInfo(f"Punto final: P1={OPPOSITE_POINT['P1_MW']} MW, P2={OPPOSITE_POINT['P2_MW']} MW")
app.PrintInfo("="*60)

try:
    run_stability_analysis()
except Exception as e:
    app.PrintError(f"Error durante la ejecución: {str(e)}")
    import traceback
    app.PrintError(traceback.format_exc())

# Restaurar estado original
app.PrintInfo("\nRestaurando estado original de los generadores...")
for g in gen_nonsync:
    g.pgini = pgini_base[g]
ldf.Execute()

app.PrintInfo("\n" + "="*60)
app.PrintInfo("ANÁLISIS COMPLETADO")
app.PrintInfo("="*60)