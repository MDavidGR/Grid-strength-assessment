# -*- coding: utf-8 -*-
import powerfactory as pf
import pandas as pd
import os
import numpy as np
import csv

# ============================================================
# CONFIGURACIÓN DEL USUARIO
# ============================================================

# Archivo Excel con los escenarios seleccionados
SCENARIOS_FILE = r"...\data\scenarios\IEEE39\escenarios.xlsx"

# Carpeta donde se guardarán los resultados de extracción
OUTPUT_FOLDER = r"...\data\results\IEEE39"

# === CONFIGURACIÓN ===
excel_path = SCENARIOS_FILE
base_output_path = OUTPUT_FOLDER

# === CONEXIÓN CON POWERFACTORY ===
app = pf.GetApplication()
if not app:
    raise Exception("No se pudo conectar con PowerFactory. Ejecute este script desde PowerFactory.")

app.PrintPlain("=== INICIO DEL SCRIPT DE CAMBIO DE POTENCIAS ===")

######## === FUNCIONES DE DATOS GSIM INTEGRADAS === #########
def get_element_data(element):
    """Extrae datos básicos de un elemento"""
    data = {
        'name': element.loc_name,
        'p': element.GetAttribute('P:bus1'),
        'q': element.GetAttribute('Q:bus1'),
        's': element.GetAttribute('m:S:bus1'),
        'v': element.GetAttribute('m:U1l:bus1'),
        'angle': element.GetAttribute('phiu:bus1'),
    }
    return data

# Function to get bus data
def get_bus_data(bus):
    """Extrae datos de buses"""
    try:
        # Obtener voltaje y ángulo actual (puede variar según el estudio)
        v_mag = bus.GetAttribute('m:U1l:bus')
        v_angle = bus.GetAttribute('phiu:bus')
    except:
        # Si falla, usar valores nominales
        v_mag = bus.uknom
        v_angle = 0.0
    
    data = {
        'name': bus.loc_name,
        'voltage_nom': bus.uknom,
        'voltage_actual': v_mag,
        'angle_actual': v_angle,
        'p_load': 0,
        'q_load': 0,
        'p_gen': 0,
        'q_gen': 0
    }
    return data

# Function to get generator data (ElmSym)
def get_generator_data(gen):
    """Extrae datos de generadores síncronos"""
    try:
        # Usar atributos específicos para P y Q
        p_gen = gen.GetAttribute('n:Pgen:bus1') if hasattr(gen, 'n:Pgen:bus1') else None
        q_gen = gen.GetAttribute('n:Qgen:bus1') if hasattr(gen, 'n:Qgen:bus1') else None
        
        data = {
            'name': gen.loc_name,
            'type': 'Synchronous',
            'p': p_gen,
            'q': q_gen,
            's_nom': gen.sgn if hasattr(gen, 'sgn') else None,
            'v_set': gen.usetp if hasattr(gen, 'usetp') else None,
            'bus': gen.bus1.cterm.loc_name if gen.bus1 else None,
            'v_actual': gen.GetAttribute('m:U1l:bus1') if hasattr(gen, 'm:U1l:bus1') else None
        }
    except Exception as e:
        app.PrintWarn(f"Error obteniendo datos del generador {gen.loc_name}: {str(e)}")
        data = {
            'name': gen.loc_name,
            'type': 'Synchronous',
            'p': None,
            'q': None,
            's_nom': None,
            'v_set': None,
            'bus': None,
            'v_actual': None
        }
    return data

# Function to get line data
def get_line_data(line):
    """Extrae datos de líneas"""
    try:
        # Intentar obtener parámetros de la línea
        r_line = line.GetAttribute('t:rline')  # Resistencia por unidad de longitud
        x_line = line.GetAttribute('t:xline')  # Reactancia por unidad de longitud
        b_line = line.GetAttribute('t:bline')  # Susceptancia por unidad de longitud
        length = line.GetAttribute('dline')    # Longitud de la línea
        
        # Calcular valores totales
        r_total = r_line * length if length and r_line else r_line
        x_total = x_line * length if length and x_line else x_line
        b_total = b_line * length if length and b_line else b_line
        
    except:
        # Si falla, intentar obtener valores totales directamente
        try:
            r_total = line.GetAttribute('Rline')
            x_total = line.GetAttribute('Xline')
            b_total = line.GetAttribute('Bline')
            length = line.GetAttribute('dline') if hasattr(line, 'dline') else None
        except:
            # Si aún falla, usar valores por defecto
            r_total = 0.0
            x_total = 0.0
            b_total = 0.0
            length = 0.0
    
    data = {
        'name': line.loc_name,
        'from_bus': line.bus1.cterm.loc_name if line.bus1 else None,
        'to_bus': line.bus2.cterm.loc_name if line.bus2 else None,
        'r_per_km': r_line if 'r_line' in locals() else 0.0,
        'x_per_km': x_line if 'x_line' in locals() else 0.0,
        'b_per_km': b_line if 'b_line' in locals() else 0.0,
        'length_km': length,
        'r_total': r_total,
        'x_total': x_total,
        'b_total': b_total,
        'current': line.GetAttribute('m:I:bus1') if hasattr(line, 'm:I:bus1') else None
    }
    return data

# Function to get transformer data
def get_transformer_data(trafo):
    """Extrae datos de transformadores con atributos específicos"""
    try:
        # Obtener buses conectados al transformador
        bus_hv = trafo.bushv.cterm.loc_name if hasattr(trafo, 'bushv') and trafo.bushv else None
        bus_lv = trafo.buslv.cterm.loc_name if hasattr(trafo, 'buslv') and trafo.buslv else None
        
        # Obtener parámetros con los atributos específicos
        r_pu = trafo.GetAttribute('t:r1pu') if hasattr(trafo, 't:r1pu') else None
        x_pu = trafo.GetAttribute('t:x1pu') if hasattr(trafo, 't:x1pu') else None
        s_nom = trafo.GetAttribute('e:Snom') if hasattr(trafo, 'e:Snom') else None
        tap = trafo.GetAttribute('nntap') if hasattr(trafo, 'nntap') else None
        
        # Obtener voltajes de los buses conectados
        voltage_hv = trafo.bushv.GetAttribute('m:Ul') if hasattr(trafo, 'bushv') and trafo.bushv else None
        voltage_lv = trafo.buslv.GetAttribute('m:Ul') if hasattr(trafo, 'buslv') and trafo.buslv else None
        
    except Exception as e:
        app.PrintWarn(f"Error obteniendo datos del transformador {trafo.loc_name}: {str(e)}")
        bus_hv = None
        bus_lv = None
        r_pu = None
        x_pu = None
        s_nom = None
        tap = None
        voltage_hv = None
        voltage_lv = None
    
    data = {
        'name': trafo.loc_name,
        'from_bus': bus_hv,
        'to_bus': bus_lv,
        'r_pu': r_pu,
        'x_pu': x_pu,
        's_nom': s_nom,
        'tap': tap,
        'voltage_hv': voltage_hv,
        'voltage_lv': voltage_lv
    }
    return data

# Function to get PV system data (ElmPvsys)
def get_pvsys_data(pvsys):
    """Extrae datos de sistemas PV (inversores)"""
    try:
        data = {
            'name': pvsys.loc_name,
            'type': 'PV System',
            'p': pvsys.pgini,
            'q': pvsys.qgini,
            's': pvsys.sgn,
            'v_set': pvsys.usetp if hasattr(pvsys, 'usetp') else None,
            'bus': pvsys.bus1.cterm.loc_name if pvsys.bus1 else None,
            'v_actual': pvsys.GetAttribute('m:U1l:bus1'),
            'control_mode': 'Grid-Following'
        }
        
        # Intentar obtener más información del tipo de control
        try:
            if hasattr(pvsys, 'typ_id') and pvsys.typ_id:
                data['control_type'] = str(pvsys.typ_id)
        except:
            pass
            
    except Exception as e:
        app.PrintWarn(f"Error obteniendo datos del PV system {pvsys.loc_name}: {str(e)}")
        data = {
            'name': pvsys.loc_name,
            'type': 'PV System',
            'p': None,
            'q': None,
            's': None,
            'v_set': None,
            'bus': None,
            'v_actual': None,
            'control_mode': None
        }
        
    return data

# Function to get load data
def get_load_data(load):
    """Extrae datos de cargas"""
    try:
        data = {
            'name': load.loc_name,
            'p': load.plini,
            'q': load.qlini,
            's': load.GetAttribute('m:S:bus1') if hasattr(load, 'm:S:bus1') else None,
            'bus': load.bus1.cterm.loc_name if load.bus1 else None,
            'v_actual': load.GetAttribute('m:U1l:bus1') if hasattr(load, 'm:U1l:bus1') else None
        }
    except Exception as e:
        app.PrintWarn(f"Error obteniendo datos de la carga {load.loc_name}: {str(e)}")
        data = {
            'name': load.loc_name,
            'p': None,
            'q': None,
            's': None,
            'bus': None,
            'v_actual': None
        }
    return data

def ejecutar_flujo_carga():
    """Ejecuta flujo de carga antes de extraer datos"""
    try:
        app.PrintInfo("📊 Ejecutando flujo de carga...")
        
        # Obtener el objeto de flujo de carga del estudio actual
        ldf = app.GetFromStudyCase("ComLdf")
        if ldf:
            ldf.Execute()
            app.PrintInfo("✅ Flujo de carga ejecutado correctamente")
            return True
        else:
            app.PrintWarn("⚠ No se encontró el objeto de flujo de carga")
            return False
            
    except Exception as e:
        app.PrintWarn(f"⚠ Error al ejecutar flujo de carga: {e}")
        return False

# Main data extraction
def extract_network_data():
    """Extrae todos los datos de la red"""
    
    app.PrintInfo("Extrayendo datos de la red...")
    
    # Ejecutar flujo de carga primero
    if not ejecutar_flujo_carga():
        app.PrintWarn("⚠ No se pudo ejecutar el flujo de carga, los datos pueden estar incompletos")
    
    # Get active project
    project = app.GetActiveProject()
    if not project:
        app.PrintError("No hay proyecto activo")
        return None
    
    # Get all relevant elements - buscar diferentes tipos de generadores
    buses = app.GetCalcRelevantObjects('*.ElmTerm')
    lines = app.GetCalcRelevantObjects('*.ElmLne')
    transformers = app.GetCalcRelevantObjects('*.ElmTr2')
    
    # Buscar diferentes tipos de generadores
    generators_sync = app.GetCalcRelevantObjects('*.ElmSym')  # Generadores síncronos
    generators_gen = app.GetCalcRelevantObjects('*.ElmGen')   # Generadores generales
    generators = generators_sync + generators_gen  # Combinar ambos tipos
    
    pvsys = app.GetCalcRelevantObjects('*.ElmPvsys')
    loads = app.GetCalcRelevantObjects('*.ElmLod')
    
    # Collect data
    network_data = {
        'buses': [],
        'lines': [],
        'transformers': [],
        'generators': [],
        'pvsys': [],
        'loads': []
    }
    
    # Extract bus data
    for bus in buses:
        network_data['buses'].append(get_bus_data(bus))
    
    # Extract line data
    for line in lines:
        network_data['lines'].append(get_line_data(line))
    
    # Extract transformer data
    for trafo in transformers:
        network_data['transformers'].append(get_transformer_data(trafo))
    
    # Extract generator data
    for gen in generators:
        network_data['generators'].append(get_generator_data(gen))
    
    # Extract PV system data
    for pv in pvsys:
        network_data['pvsys'].append(get_pvsys_data(pv))
    
    # Extract load data
    for load in loads:
        network_data['loads'].append(get_load_data(load))
    
    # Calculate power injections at buses
    calculate_power_balance(network_data)
    
    return network_data

def calculate_power_balance(network_data):
    """Calcula balance de potencia en cada bus"""
    
    # Create bus dictionary for easy access
    bus_dict = {bus['name']: bus for bus in network_data['buses']}
    
    # Initialize power values
    for bus_name in bus_dict:
        bus_dict[bus_name]['p_load'] = 0
        bus_dict[bus_name]['q_load'] = 0
        bus_dict[bus_name]['p_gen'] = 0
        bus_dict[bus_name]['q_gen'] = 0
    
    # Sum load power
    for load in network_data['loads']:
        if load['bus'] and load['bus'] in bus_dict and load['p'] is not None:
            bus_dict[load['bus']]['p_load'] += load['p']
        if load['bus'] and load['bus'] in bus_dict and load['q'] is not None:
            bus_dict[load['bus']]['q_load'] += load['q']
    
    # Sum generator power
    for gen in network_data['generators']:
        if gen['bus'] and gen['bus'] in bus_dict and gen['p'] is not None:
            bus_dict[gen['bus']]['p_gen'] += gen['p']
        if gen['bus'] and gen['bus'] in bus_dict and gen['q'] is not None:
            bus_dict[gen['bus']]['q_gen'] += gen['q']
    
    # Sum PV system power
    for pv in network_data['pvsys']:
        if pv['bus'] and pv['bus'] in bus_dict and pv['p'] is not None:
            bus_dict[pv['bus']]['p_gen'] += pv['p']
        if pv['bus'] and pv['bus'] in bus_dict and pv['q'] is not None:
            bus_dict[pv['bus']]['q_gen'] += pv['q']
    
    # Calculate net power
    for bus in network_data['buses']:
        bus['p_net'] = bus['p_gen'] - bus['p_load']
        bus['q_net'] = bus['q_gen'] - bus['q_load']

def export_to_csv(network_data, output_folder, escenario_num):
    """Exporta datos a archivos CSV en la ruta especificada"""
    
    # Crear carpeta "Datos GSIM" dentro de la carpeta del escenario
    gsim_folder = os.path.join(output_folder, "Datos GSIM")
    os.makedirs(gsim_folder, exist_ok=True)
    
    app.PrintInfo(f"Exportando datos a: {gsim_folder}")
    
    # Export buses
    df_buses = pd.DataFrame(network_data['buses'])
    df_buses.to_csv(os.path.join(gsim_folder, f'ieee9bus_buses.csv'), index=False, encoding='utf-8')
    
    # Export lines
    df_lines = pd.DataFrame(network_data['lines'])
    df_lines.to_csv(os.path.join(gsim_folder, f'ieee9bus_lines.csv'), index=False, encoding='utf-8')
    
    # Export transformers - reemplazar NaN con cadenas vacías
    df_trafos = pd.DataFrame(network_data['transformers'])
    df_trafos = df_trafos.fillna('')  # Reemplazar NaN con cadenas vacías
    df_trafos.to_csv(os.path.join(gsim_folder, f'ieee9bus_transformers.csv'), index=False, encoding='utf-8')
    
    # Export generators - reemplazar NaN con cadenas vacías
    df_gens = pd.DataFrame(network_data['generators'])
    df_gens = df_gens.fillna('')  # Reemplazar NaN con cadenas vacías
    df_gens.to_csv(os.path.join(gsim_folder, f'ieee9bus_generators.csv'), index=False, encoding='utf-8')
    
    # Export PV systems
    df_pvsys = pd.DataFrame(network_data['pvsys'])
    df_pvsys.to_csv(os.path.join(gsim_folder, f'ieee9bus_pvsys.csv'), index=False, encoding='utf-8')
    
    # Export loads
    df_loads = pd.DataFrame(network_data['loads'])
    df_loads.to_csv(os.path.join(gsim_folder, f'ieee9bus_loads.csv'), index=False, encoding='utf-8')
    
    app.PrintInfo("Datos exportados exitosamente a archivos CSV en la carpeta 'Datos GSIM'")

def print_summary(network_data):
    """Imprime resumen de la red"""
    
    app.PrintInfo("\n=== RESUMEN DE LA RED ===")
    app.PrintInfo(f"Número de buses: {len(network_data['buses'])}")
    app.PrintInfo(f"Número de líneas: {len(network_data['lines'])}")
    app.PrintInfo(f"Número de transformadores: {len(network_data['transformers'])}")
    app.PrintInfo(f"Número de generadores síncronos: {len(network_data['generators'])}")
    app.PrintInfo(f"Número de sistemas PV (inversores): {len(network_data['pvsys'])}")
    app.PrintInfo(f"Número de cargas: {len(network_data['loads'])}")
    
    # Info de los inversores con manejo seguro de valores None
    app.PrintInfo("\n=== INFORMACIÓN DE INVERSORES ===")
    for pv in network_data['pvsys']:
        app.PrintInfo(f"PV System: {pv['name']}")
        app.PrintInfo(f"  Bus: {pv.get('bus', 'N/A')}")
        
        # Manejar valores None en P y Q
        p_val = pv.get('p')
        q_val = pv.get('q')
        
        p_str = f"{p_val:.3f}" if p_val is not None else "N/A"
        q_str = f"{q_val:.3f}" if q_val is not None else "N/A"
        s_str = f"{pv.get('s', 'N/A'):.3f}" if pv.get('s') is not None else "N/A"
        v_str = f"{pv.get('v_actual', 'N/A'):.3f}" if pv.get('v_actual') is not None else "N/A"
        
        app.PrintInfo(f"  P: {p_str} MW, Q: {q_str} Mvar")
        app.PrintInfo(f"  S nominal: {s_str} MVA")
        app.PrintInfo(f"  Voltaje actual: {v_str} kV")
        
        if 'control_type' in pv and pv['control_type']:
            app.PrintInfo(f"  Tipo de control: {pv['control_type']}")
    
    # Info de transformadores con manejo seguro de valores None
    app.PrintInfo("\n=== INFORMACIÓN DE TRANSFORMADORES ===")
    for trafo in network_data['transformers']:
        app.PrintInfo(f"Transformador: {trafo['name']}")
        app.PrintInfo(f"  Bus HV: {trafo.get('from_bus', 'N/A')}")
        app.PrintInfo(f"  Bus LV: {trafo.get('to_bus', 'N/A')}")
        
        # Manejo seguro de valores None
        r_pu = trafo.get('r_pu')
        x_pu = trafo.get('x_pu')
        
        if r_pu is not None and x_pu is not None:
            app.PrintInfo(f"  R%: {r_pu:.3f}, X%: {x_pu:.3f}")
        else:
            app.PrintInfo(f"  R%: {r_pu if r_pu is not None else 'N/A'}, X%: {x_pu if x_pu is not None else 'N/A'}")

def ejecutar_datos_gsim_completo(escenario_num, output_folder):
    """Ejecuta la funcionalidad completa de Datos GSIM"""
    try:
        app.PrintInfo(f"🎯 Ejecutando Datos GSIM para escenario {escenario_num}")
        
        # Extraer datos de la red (sin parámetros)
        network_data = extract_network_data()
        
        if network_data:
            # Imprimir resumen
            print_summary(network_data)
            
            # Exportar a CSV
            export_to_csv(network_data, output_folder, escenario_num)
            
            app.PrintInfo(f"\n✅ EXTRACCIÓN COMPLETADA PARA ESCENARIO {escenario_num}")
            return True
        else:
            app.PrintError("❌ No se pudieron extraer los datos de la red")
            return False
            
    except Exception as e:
        app.PrintError(f"❌ Error durante la extracción: {str(e)}")
        import traceback
        app.PrintError(traceback.format_exc())
        return False

######## === FUNCIONES POSITIVE INTEGRADAS === #########
def z_to_y(r, x):
    """Convierte impedancia a admitancia"""
    if r == 0 and x == 0:
        return 0
    return 1 / complex(r, x)

def ejecutar_positive_completo(output_folder, escenario_num):
    """Ejecuta la funcionalidad completa de Positive"""
    try:
        app.PrintInfo(f"🧮 Ejecutando Positive para escenario {escenario_num}")
        
        # Crear carpeta "Positive" dentro de la carpeta del escenario
        positive_folder = os.path.join(output_folder, "Positive")
        os.makedirs(positive_folder, exist_ok=True)
        
        app.PrintInfo("✅ Iniciando cálculo de Ybus (con líneas, trafos, generadores y cargas)...")

        # Obtener objetos
        buses = app.GetCalcRelevantObjects("*.ElmTerm")
        lines = app.GetCalcRelevantObjects("*.ElmLne")
        trafos = app.GetCalcRelevantObjects("*.ElmTr2")
        gens = app.GetCalcRelevantObjects("*.ElmSym")
        pvsys_gens = app.GetCalcRelevantObjects("*.ElmPvsys")
        loads = app.GetCalcRelevantObjects("*.ElmLod")

        # Indexar buses
        bus_names = [bus.loc_name for bus in buses]
        bus_idx = {name: i for i, name in enumerate(bus_names)}
        n = len(bus_names)
        Ybus = np.zeros((n, n), dtype=complex)

        # ➤ Líneas
        for line in lines:
            bus1 = line.bus1.cterm
            bus2 = line.bus2.cterm
            if not bus1 or not bus2:
                continue
            i, j = bus_idx.get(bus1.loc_name), bus_idx.get(bus2.loc_name)
            if i is None or j is None:
                continue
            model = line.typ_id
            if not model:
                app.PrintInfo(f"⚠️ Línea sin tipo: {line.loc_name}")
                continue
            length = line.dline
            r = model.rline * length
            x = model.xline * length
            y = z_to_y(r, x)
            Ybus[i, i] += y
            Ybus[j, j] += y
            Ybus[i, j] -= y
            Ybus[j, i] -= y

        # ➤ Transformadores (usando impedancia en pu desde el tipo)
        for trafo in trafos:
            term1 = trafo.buslv
            term2 = trafo.bushv
            if not term1 or not term2:
                app.PrintInfo(f"⚠️ Trafo {trafo.loc_name} sin conexión válida")
                continue
            bus1 = term1.cterm
            bus2 = term2.cterm
            if not bus1 or not bus2:
                app.PrintInfo(f"⚠️ Trafo {trafo.loc_name} con terminales no conectados a nodos")
                continue
            i, j = bus_idx.get(bus1.loc_name), bus_idx.get(bus2.loc_name)
            if i is None or j is None:
                app.PrintInfo(f"⚠️ Trafo {trafo.loc_name} con buses fuera del índice")
                continue

            typ = trafo.typ_id
            if not typ:
                app.PrintInfo(f"⚠️ Trafo {trafo.loc_name} sin tipo asignado.")
                continue

            try:
                r = typ.r1pu
                x = typ.x1pu
                y = z_to_y(r, x)
                Ybus[i, i] += y
                Ybus[j, j] += y
                Ybus[i, j] -= y
                Ybus[j, i] -= y
            except Exception as e:
                app.PrintInfo(f"⚠️ Error extrayendo impedancia de trafo {trafo.loc_name}: {str(e)}")

        # ➤ Generadores
        for gen in gens:
            bus = gen.bus1
            if not bus:
                app.PrintInfo(f"⚠️ Generador {gen.loc_name} sin conexión válida")
                continue
            bus_term = bus.cterm
            if not bus_term:
                app.PrintInfo(f"⚠️ Generador {gen.loc_name} no conectado a nodo")
                continue
            i = bus_idx.get(bus_term.loc_name)
            if i is None:
                continue

            typ = gen.typ_id
            if typ and hasattr(typ, "xd1"):
                # Generador síncrono -> usar parámetros Xd1, Ra
                x = typ.xd1
                r = typ.ra
                y = z_to_y(r, x)
                Ybus[i, i] += y
            else:
                # Generadores estáticos (PVsys, PQ, etc.)
                try:
                    # Obtener potencia activa y reactiva del flujo de carga en el nodo
                    P = gen.GetAttribute("n:Pgen:bus1")  # [MW]
                    Q = gen.GetAttribute("n:Qgen:bus1")  # [Mvar]
                except Exception as e:
                    app.PrintInfo(f"⚠️ No se pudieron obtener P/Q de {gen.loc_name}: {e}")
                    continue

                if P == 0 and Q == 0:
                    continue

                S = complex(P, Q) / 1000  # convertir a pu con base 1000 MVA si corresponde
                Ysh = S / (1.0 ** 2)
                Ybus[i, i] += Ysh.conjugate()

        # ➤ Generadores tipo ElmPvsys
        for gen in pvsys_gens:
            bus = gen.bus1
            if not bus:
                app.PrintInfo(f"⚠️ PVsys {gen.loc_name} sin conexión válida")
                continue
            bus_term = bus.cterm
            if not bus_term:
                app.PrintInfo(f"⚠️ PVsys {gen.loc_name} no conectado a nodo")
                continue
            i = bus_idx.get(bus_term.loc_name)
            if i is None:
                continue

            P = gen.pgini  # MW
            Q = gen.qgini  # MVAr
            if P == 0 and Q == 0:
                continue
            S = complex(P, Q) / 1000  # [MVA]
            Ysh = S / (1.0 ** 2)      # Admitancia en pu (asumiendo V=1.0 pu)
            Ybus[i, i] += Ysh.conjugate()

        # ➤ Cargas
        for load in loads:
            bus = load.bus1
            if not bus:
                continue
            bus_term = bus.cterm
            if not bus_term:
                continue
            i = bus_idx.get(bus_term.loc_name)
            if i is None:
                continue
            P = load.plini
            Q = load.qlini
            S = complex(P, Q) / 1000
            Yload = S / (1.0 ** 2)
            Ybus[i, i] += Yload.conjugate()

        # ➤ Exportar Ybus a CSV
        ybus_path = os.path.join(positive_folder, f"Ybus_export.csv")
        with open(ybus_path, mode="w", newline="") as file:
            writer = csv.writer(file)

            # Encabezado con nombres de columnas
            header = ["Bus"] + bus_names
            writer.writerow(header)

            # Escribir cada fila con su nombre de barra y las admitancias complejas
            for i in range(n):
                row = [bus_names[i]]
                for j in range(n):
                    y = Ybus[i, j]
                    cell = f"{y.real:.4f}+j{y.imag:.4f}"
                    row.append(cell)
                writer.writerow(row)

        app.PrintInfo(f"📁 Archivo Ybus exportado correctamente a:\n{ybus_path}")

        # ➤ Exportar tensiones y corrientes
        app.PrintInfo("✅ Exportando resultados de generadores y tensiones de nodos...")

        # Ejecutar flujo de carga
        ldf = app.GetFromStudyCase("ComLdf")
        if not ldf:
            app.PrintInfo("❌ No se encontró el objeto ComLdf.")
            return False

        ldf.iopt_net = 0
        status = ldf.Execute()
        if status != 0:
            app.PrintInfo("❌ Error al ejecutar el flujo de carga.")
            return False

        app.PrintInfo("✅ Flujo de carga ejecutado correctamente.")

        # 🔹 Generadores
        gen_classes = ["ElmSym", "ElmGenstat", "ElmPvsys", "ElmPvg", "ElmVsccon"]
        generadores = []
        for cls in gen_classes:
            generadores += app.GetCalcRelevantObjects(f"*.{cls}")

        # 🔹 Terminales de nodo
        terminales = app.GetCalcRelevantObjects("*.ElmTerm")

        # ➤ Exportar corrientes de generadores
        gen_path = os.path.join(positive_folder, f"corrientes_generadores.csv")
        with open(gen_path, mode="w", newline="") as f_gen:
            writer = csv.writer(f_gen, delimiter=";")
            writer.writerow(["Nombre", "Corriente m:I:bus1 [A]"])

            for gen in generadores:
                name = gen.loc_name
                try:
                    corriente = gen.GetAttribute("m:I:bus1")
                    writer.writerow([name, f"{corriente.real:.4f}+j{corriente.imag:.4f}"])
                except Exception as e:
                    app.PrintInfo(f"⚠️ {name} sin corriente medida: {e}")

        # ➤ Exportar tensiones desde terminales
        term_path = os.path.join(positive_folder, f"tensiones_nodos.csv")
        with open(term_path, mode="w", newline="") as f_bus:
            writer = csv.writer(f_bus, delimiter=";")
            writer.writerow(["Nodo (Terminal)", "Tensión m:u [p.u.]"])

            for term in terminales:
                try:
                    name = term.loc_name
                    tension = term.GetAttribute("m:u")
                    writer.writerow([name, f"{tension:.4f}"])
                except Exception as e:
                    app.PrintInfo(f"⚠️ Terminal {term.loc_name} sin tensión medida: {e}")

        # ➤ Exportar potencias activas de generadores
        pot_path = os.path.join(positive_folder, f"potencias_activas_generadores.csv")
        with open(pot_path, mode="w", newline="") as f_pot:
            writer = csv.writer(f_pot, delimiter=";")
            writer.writerow(["Nombre", "Tipo", "Nodo Conectado", "Potencia Activa pgini [MW]"])

            for gen in generadores:
                name = gen.loc_name
                gen_type = gen.GetClassName()

                try:
                    terminal = gen.bus1.cterm
                    nodo = terminal.loc_name if terminal else "N/A"
                except:
                    nodo = "N/A"

                try:
                    P = gen.GetAttribute("n:Pgen:bus1")  # [MW]
                    if gen_type in ["ElmPvsys", "ElmPvg"]:
                        P_MW = P  # Están en kW
                    else:
                        P_MW = P

                    P_str = f"{P_MW:.4f}".replace(".", ",")
                    writer.writerow([name, gen_type, nodo, P_str])
                except Exception as e:
                    app.PrintInfo(f"⚠️ {name} sin atributo pgini: {e}")

        # ➤ Ejecutar cortocircuito trifásico y exportar Ikss y Skss
        app.PrintInfo("⚡ Ejecutando cálculo de cortocircuito trifásico...")

        # Obtener objeto de cortocircuito
        sc = app.GetFromStudyCase("ComShc")
        if not sc:
            app.PrintInfo("❌ No se encontró el objeto ComShc en el caso de estudio.")
            return False

        # Configurar para trifásico en todos los nodos
        sc.iopt_mde = 1     # 1 = IEC60909
        #sc.iopt_shc = 3psc     # 1 = simétrico (trifásico)
        sc.iopt_allbus = 1  # Calcular en todos los nodos

        # Ejecutar cálculo
        status = sc.Execute()
        if status != 0:
            app.PrintInfo("❌ Error al ejecutar el cálculo de cortocircuito.")
            return False

        app.PrintInfo("✅ Cálculo de cortocircuito trifásico ejecutado correctamente.")

        # Obtener nodos
        nodos_sc = app.GetCalcRelevantObjects("*.ElmTerm")

        # Archivo CSV de cortocircuito
        sc_path = os.path.join(positive_folder, f"cortocircuito_trifasico.csv")
        with open(sc_path, mode="w", newline="") as f_sc:
            writer = csv.writer(f_sc, delimiter=";")
            writer.writerow([
                "Nodo",
                "Corriente Cortocircuito Ikss [kA]",
                "Potencia Cortocircuito Skss [MVA]"
            ])

            for nodo in nodos_sc:
                try:
                    # Corriente trifásica simétrica inicial en kA
                    ikss = nodo.GetAttribute("m:Ikss")
                    # Potencia de cortocircuito simétrica inicial en MVA
                    skss = nodo.GetAttribute("m:Skss")

                    # Evitar None
                    if ikss is None:
                        ikss = 0.0
                    if skss is None:
                        skss = 0.0

                    # Formato con coma decimal
                    ikss_str = f"{ikss:.4f}".replace(".", ",")
                    skss_str = f"{skss:.4f}".replace(".", ",")

                    writer.writerow([nodo.loc_name, ikss_str, skss_str])

                except Exception as e:
                    app.PrintInfo(f"⚠️ Nodo {nodo.loc_name} sin datos: {e}")

        app.PrintInfo(f"📄 Resultados de cortocircuito exportados en:\n{sc_path}")
        app.PrintInfo(f"✅ Positive completado para escenario {escenario_num}")
        return True

    except Exception as e:
        app.PrintError(f"❌ Error durante la ejecución de Positive: {str(e)}")
        import traceback
        app.PrintError(traceback.format_exc())
        return False

######## === FUNCIONES SDSCR INFO INTEGRADAS === #########
def get_system_base_mva():
    """Get system base MVA"""
    try:
        # Try to get from study case
        study_case = app.GetActiveStudyCase()
        return study_case.sbase
    except:
        try:
            # Try to get from any generator
            gen = app.GetCalcRelevantObjects('*.ElmSym')[0]
            return gen.GetAttribute('t:sgn') if hasattr(gen, 't:sgn') else 100.0
        except:
            app.PrintWarn("Using default 100 MVA as base")
            return 100.0

def get_terminal_name(bus_obj):
    """Helper function to get terminal name using the specified structure"""
    if bus_obj is None:
        return None
    terminal = bus_obj.cterm if hasattr(bus_obj, "cterm") else None
    if terminal and terminal.GetClassName() == "ElmTerm":
        return terminal.loc_name
    return None

def get_connection_node(component, bus_attr='bus1', bar_attr='e:bus1_bar'):
    """
    Get connection node name using the specified structure
    with fallback to alternative methods
    """
    # First try the terminal method
    bus_obj = getattr(component, bus_attr, None)
    if bus_obj:
        terminal_name = get_terminal_name(bus_obj)
        if terminal_name:
            return terminal_name
    
    # Then try the bar attribute
    if hasattr(component, bar_attr):
        bar_name = component.GetAttribute(bar_attr)
        if bar_name:
            return bar_name
    
    # Finally fall back to bus loc_name
    if bus_obj and hasattr(bus_obj, 'loc_name'):
        return bus_obj.loc_name
    
    return "Unknown"

def extract_sdscr_network_data():
    """Extract essential network data with consistent node naming"""
    network_data = {
        'base_mva': get_system_base_mva(),
        'buses': [],
        'generators': [],
        'branches': [],
        'transformers': [],  # New section for transformers
        'loads': [],
        'renewables': []
    }

    # Extract buses
    buses = app.GetCalcRelevantObjects('*.ElmTerm')
    for bus in buses:
        try:
            bus_data = {
                'name': bus.loc_name,
                'voltage_kv': bus.uknom,
                'vm_pu': bus.GetAttribute('m:u') if hasattr(bus, 'm:u') else 1.0,
                'va_deg': bus.GetAttribute('m:phiu') if hasattr(bus, 'm:phiu') else 0.0
            }
            network_data['buses'].append(bus_data)
        except Exception as e:
            app.PrintWarn(f"Skipping bus {bus.loc_name}: {str(e)}")

    # Extract synchronous generators
    generators = app.GetCalcRelevantObjects('*.ElmSym')
    for gen in generators:
        try:
            gen_data = {
                'name': gen.loc_name,
                'bus': get_connection_node(gen),
                'pg_mw': gen.GetAttribute('m:Psum:bus1') if hasattr(gen, 'm:Psum:bus1') else 0.0,
                'qg_mvar': gen.GetAttribute('m:Qsum:bus1') if hasattr(gen, 'm:Qsum:bus1') else 0.0,
                'rated_mva': gen.GetAttribute('t:sgn') if hasattr(gen, 't:sgn') else 0.0,
                'status': 'InService' if not gen.outserv else 'OutOfService'
            }
            network_data['generators'].append(gen_data)
        except Exception as e:
            app.PrintWarn(f"Skipping generator {gen.loc_name}: {str(e)}")

    # CORRECTED: Extract renewable generators (all types)
    renewables = app.GetCalcRelevantObjects('*.ElmPvsys')
    for renewable in renewables:
        try:
            renewable_data = {
                'name': renewable.loc_name,
                'bus': get_connection_node(renewable),
                'pg_mw': renewable.GetAttribute('m:Psum:bus1') if hasattr(renewable, 'm:Psum:bus1') else 0.0,
                'qg_mvar': renewable.GetAttribute('m:Qsum:bus1') if hasattr(renewable, 'm:Qsum:bus1') else 0.0,
                'rated_mva': renewable.GetAttribute('e:sgn') if hasattr(renewable, 'e:sgn') else 0.0,
                'status': 'InService' if not renewable.outserv else 'OutOfService'
            }
            network_data['renewables'].append(renewable_data)
        except Exception as e:
            app.PrintWarn(f"Skipping generator {renewable.loc_name}: {str(e)}")

    # Extract lines with consistent node naming for both ends
    lines = app.GetCalcRelevantObjects('*.ElmLne')
    for line in lines:
        try:
            line_data = {
                'name': line.loc_name,
                'from_bus': get_connection_node(line, 'bus1', 'e:bus1_bar'),
                'to_bus': get_connection_node(line, 'bus2', 'e:bus2_bar'),
                'R1': line.GetAttribute('e:R1') if hasattr(line, 'e:R1') else 0.0,
                'X1': line.GetAttribute('e:X1') if hasattr(line, 'e:X1') else 0.0,
                'R0': line.GetAttribute('e:R0') if hasattr(line, 'e:R0') else 0.0,
                'X0': line.GetAttribute('e:X0') if hasattr(line, 'e:X0') else 0.0,
                'Z1': line.GetAttribute('e:Z1') if hasattr(line, 'e:Z1') else 0.0,
                'phiz1': line.GetAttribute('e:phiz1') if hasattr(line, 'e:phiz1') else 0.0
            }
            network_data['branches'].append(line_data)
        except Exception as e:
            app.PrintWarn(f"Skipping line {line.loc_name}: {str(e)}")

    # Extract loads with consistent node naming
    loads = app.GetCalcRelevantObjects('*.ElmLod')
    for load in loads:
        try:
            load_data = {
                'name': load.loc_name,
                'bus': get_connection_node(load),
                'pl_mw': load.GetAttribute('m:P:bus1') if hasattr(load, 'm:P:bus1') else 0.0,
                'ql_mvar': load.GetAttribute('m:Q:bus1') if hasattr(load, 'm:Q:bus1') else 0.0
            }
            network_data['loads'].append(load_data)
        except Exception as e:
            app.PrintWarn(f"Skipping load {load.loc_name}: {str(e)}")
     
     # NEW SECTION: Extract transformers
    transformers = app.GetCalcRelevantObjects('*.ElmTr2')
    for trafo in transformers:
        try:
            # Get winding connection nodes
            hv_node = get_connection_node(trafo, 'bushv', 'e:bushv_bar')
            lv_node = get_connection_node(trafo, 'buslv', 'e:buslv_bar')
            
            trafo_data = {
                'name': trafo.loc_name,
                'hv_node': hv_node,
                'lv_node': lv_node,
                'rated_power_mva': trafo.GetAttribute('Snom') if hasattr(trafo, 'Snom') else 0.0,
                'hv_voltage_kv': trafo.GetAttribute('t:utrn_h') if hasattr(trafo, 't:utrn_h') else 0.0,
                'lv_voltage_kv': trafo.GetAttribute('t:utrn_l') if hasattr(trafo, 't:utrn_l') else 0.0,
                'tap_pos': trafo.GetAttribute('nntap') if hasattr(trafo, 'nntap') else 0,
                'r_pu': trafo.GetAttribute('t:r1pu') if hasattr(trafo, 't:r1pu') else 0.0,
                'x_pu': trafo.GetAttribute('t:x1pu') if hasattr(trafo, 't:x1pu') else 0.0,
                'status': 'InService' if not trafo.outserv else 'OutOfService'
            }
            network_data['transformers'].append(trafo_data)
        except Exception as e:
            app.PrintWarn(f"Skipping transformer {trafo.loc_name}: {str(e)}")
     
    return network_data

def save_sdscr_to_csv(network_data, output_folder, escenario_num):
    """Save SDSCR data to CSV files"""
    # Crear carpeta "SDSCR INFO" dentro de la carpeta del escenario
    sdscr_folder = os.path.join(output_folder, "SDSCR INFO")
    os.makedirs(sdscr_folder, exist_ok=True)
    
    app.PrintInfo(f"Exportando datos SDSCR a: {sdscr_folder}")
    
    # Add transformers to the data types to save
    for data_type in ['buses', 'generators', 'renewables', 'branches', 'transformers', 'loads']:
        if network_data[data_type]:
            df = pd.DataFrame(network_data[data_type])
            df.to_csv(
                os.path.join(sdscr_folder, f'{data_type}.csv'), 
                index=False,
                float_format='%.6f'
            )

def ejecutar_sdscr_info_completo(output_folder, escenario_num):
    """Ejecuta la funcionalidad completa de SDSCR INFO"""
    try:
        app.PrintInfo(f"📋 Ejecutando SDSCR INFO para escenario {escenario_num}")
        
        # Ejecutar flujo de carga primero
        if not ejecutar_flujo_carga():
            app.PrintWarn("⚠ No se pudo ejecutar el flujo de carga, los datos SDSCR pueden estar incompletos")
        
        data = extract_sdscr_network_data()
        save_sdscr_to_csv(data, output_folder, escenario_num)
        
        summary = (
            f"SDSCR Data Summary - Escenario {escenario_num}:\n"
            f"Buses: {len(data['buses'])}\n"
            f"Generators: {len(data['generators'])}\n"
            f"Renewables: {len(data['renewables'])}\n"
            f"Branches: {len(data['branches'])}\n"
            f"Transformers: {len(data['transformers'])}\n"
            f"Loads: {len(data['loads'])}\n"
            f"Base MVA: {data['base_mva']}"
        )
        app.PrintInfo(summary)
        app.PrintInfo(f"✅ SDSCR INFO completado para escenario {escenario_num}")
        return True
        
    except Exception as e:
        app.PrintError(f"❌ Script SDSCR INFO falló: {str(e)}")
        import traceback
        app.PrintError(traceback.format_exc())
        return False

######## === FUNCIONES EXPORTZ_PYTHON INTEGRADAS === #########
def ejecutar_exportz_python_completo(output_folder, escenario_num):
    """Ejecuta la funcionalidad completa de ExportZ_Python"""
    try:
        app.PrintInfo(f"🔌 Ejecutando ExportZ_Python para escenario {escenario_num}")
        
        # Crear carpeta "ExportZ_Python" dentro de la carpeta del escenario
        exportz_folder = os.path.join(output_folder, "ExportZ_Python")
        os.makedirs(exportz_folder, exist_ok=True)
        
        # Mapeo de av_mode a etiquetas legibles
        av_mode_dict = {
            0: "PV (V fija)",
            1: "PQ (Q fija)",
            2: "PQ (cosφ fija)",
            3: "PV (Q-droop)",
            4: "PV (Iq-droop)",
            5: "PV (Q=f(V))",
            6: "PQ (Q=f(P))",
            7: "PQ (cosφ=f(P))"
        }

        # Incluir todos los tipos relevantes de generadores
        generadores = app.GetProjectFolder("netdat").GetContents("*.ElmGenstat,*.ElmSym,*.ElmPvsys,*.ElmPvg", 1)

        if not generadores:
            app.PrintWarn("⚠️ No se encontraron generadores en el proyecto.")
            return False
        else:
            app.PrintInfo(f"🔍 Generadores encontrados: {len(generadores)}")

            # Archivo de generadores
            gen_file = os.path.join(exportz_folder, f"info_generadores_con_Zdevice.csv")

            with open(gen_file, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow([
                    "Nombre", "Tipo", "TipoFisico", "TipoControl",
                    "Nodo Conectado", "pgini [MW]", "V_base [kV]", "Zdevice [Ohm aprox.]"
                ])

                for gen in generadores:
                    try:
                        name = gen.loc_name
                        tipo = gen.GetClassName()

                        # Tipo físico
                        tipo_fisico = "Síncrono" if tipo in ["ElmGenstat", "ElmSym"] else "IBR"

                        # Tipo de control
                        if tipo in ["ElmGenstat", "ElmSym"]:
                            tipo_control = "Vtheta"
                        elif tipo in ["ElmPvsys", "ElmPvg"]:
                            if hasattr(gen, "av_mode"):
                                tipo_control = av_mode_dict.get(gen.av_mode, f"av_mode={gen.av_mode}")
                            else:
                                tipo_control = "PQ (default)"
                        else:
                            tipo_control = "Desconocido"

                        # Nodo de conexión
                        terminal = gen.bus1.cterm if gen.bus1 and hasattr(gen.bus1, "cterm") else None
                        if terminal and terminal.GetClassName() == "ElmTerm":
                            nodo = terminal.loc_name
                            Vbase_kV = terminal.uknom
                        else:
                            nodo = "N/A"
                            Vbase_kV = None

                        # Potencia activa
                        P = gen.pgini
                        if tipo in ["ElmPvsys", "ElmPvg"]:
                            P_MW = P / 1000.0
                        else:
                            P_MW = P

                        # Zdevice ≈ V² / P
                        if Vbase_kV and P_MW > 0:
                            Zdevice = (Vbase_kV ** 2) / P_MW
                        else:
                            Zdevice = None

                        # Escribir fila CSV
                        writer.writerow([
                            name,
                            tipo,
                            tipo_fisico,
                            tipo_control,
                            nodo,
                            f"{P_MW:.4f}" if P_MW else "N/A",
                            f"{Vbase_kV:.2f}" if Vbase_kV else "N/A",
                            f"{Zdevice:.4f}" if Zdevice else "N/A"
                        ])

                        app.PrintInfo(f"✅ Exportado: {name} ({tipo_fisico}, {tipo_control}) en nodo {nodo}")

                    except Exception as e:
                        app.PrintWarn(f"⚠️ Error procesando {gen.loc_name}: {e}")

            app.PrintInfo(f"✅ Archivo generadores generado: {gen_file}")

        # ➤ Exportar información de cargas
        cargas_file = os.path.join(exportz_folder, f"info_cargas.csv")
        cargas = app.GetProjectFolder("netdat").GetContents("*.ElmLod", 1)

        if not cargas:
            app.PrintWarn("⚠️ No se encontraron cargas en el sistema.")
        else:
            app.PrintInfo(f"🔍 Cargas encontradas: {len(cargas)}")

            with open(cargas_file, mode="w", newline="", encoding="utf-8") as f_carga:
                writer = csv.writer(f_carga, delimiter=";")
                writer.writerow(["Nombre", "Nodo Conectado", "P [MW]", "Q [Mvar]"])

                for carga in cargas:
                    try:
                        name = carga.loc_name
                        terminal = carga.bus1.cterm if carga.bus1 and hasattr(carga.bus1, "cterm") else None
                        if terminal and terminal.GetClassName() == "ElmTerm":
                            nodo = terminal.loc_name
                        else:
                            nodo = "N/A"

                        # Potencias en MW y MVAr
                        P_MW = carga.plini / 1000.0  # plini está en kW
                        Q_Mvar = carga.qlini / 1000.0  # qlini está en kVAr

                        writer.writerow([
                            name,
                            nodo,
                            f"{P_MW:.4f}",
                            f"{Q_Mvar:.4f}"
                        ])

                        app.PrintInfo(f"✅ Carga exportada: {name} en nodo {nodo}")

                    except Exception as e:
                        app.PrintWarn(f"⚠️ Error procesando carga {carga.loc_name}: {e}")

            app.PrintInfo(f"✅ Archivo cargas generado: {cargas_file}")

        app.PrintInfo(f"✅ ExportZ_Python completado para escenario {escenario_num}")
        return True

    except Exception as e:
        app.PrintError(f"❌ Error durante la ejecución de ExportZ_Python: {str(e)}")
        import traceback
        app.PrintError(traceback.format_exc())
        return False

# === FUNCIONES PARA CÁLCULO DE CORRIENTES DE CORTOCIRCUITO (TU CÓDIGO) ===
def obtener_bus_conexion_generador(app, gen_obj, gen_name):
    """Obtiene el bus de conexión del generador usando métodos más robustos"""
    try:
        app.PrintInfo(f"  🔍 Buscando bus de conexión para {gen_name}...")
        
        # Método 1: Buscar a través de cubículos (método más confiable en PowerFactory)
        try:
            cubicle = gen_obj.GetCubicle()
            if cubicle:
                bus = cubicle.GetBus()
                if bus:
                    app.PrintInfo(f"  ✅ {gen_name}: Bus encontrado por cubicle - {bus.loc_name}")
                    return bus
        except Exception as e:
            app.PrintInfo(f"  ℹ️ Método cubicle falló: {e}")
        
        # Método 2: Buscar terminales conectadas directamente
        try:
            # Buscar todos los terminales en el mismo contenedor
            terminales = app.GetCalcRelevantObjects(f"{gen_obj.loc_name}*.ElmTerm")
            for term in terminales:
                if hasattr(term, 'uknom'):
                    app.PrintInfo(f"  ✅ {gen_name}: Terminal encontrada - {term.loc_name}")
                    return term
        except Exception as e:
            app.PrintInfo(f"  ℹ️ Método terminales falló: {e}")
        
        # Método 3: Buscar por conexión física (bus1)
        try:
            if hasattr(gen_obj, 'bus1') and gen_obj.bus1:
                bus = gen_obj.bus1
                app.PrintInfo(f"  ✅ {gen_name}: Bus encontrado por bus1 - {bus.loc_name}")
                return bus
        except Exception as e:
            app.PrintInfo(f"  ℹ️ Método bus1 falló: {e}")
        
        # Método 4: Buscar en el contenedor padre
        try:
            parent = gen_obj.GetParent()
            if parent and hasattr(parent, 'uknom'):
                app.PrintInfo(f"  ✅ {gen_name}: Bus encontrado por parent - {parent.loc_name}")
                return parent
        except Exception as e:
            app.PrintInfo(f"  ℹ️ Método parent falló: {e}")
        
        # Método 5: Buscar buses cercanos por nombre
        try:
            # Buscar buses que puedan estar conectados por nombre similar
            all_buses = app.GetCalcRelevantObjects("*.ElmTerm")
            gen_name_clean = gen_name.replace('PV', '').replace('GEN', '').strip()
            
            for bus in all_buses:
                bus_name = bus.loc_name.upper()
                if (gen_name_clean in bus_name or 
                    f"PV{gen_name_clean}" in bus_name or 
                    f"BUS{gen_name_clean}" in bus_name):
                    if hasattr(bus, 'uknom'):
                        app.PrintInfo(f"  ✅ {gen_name}: Bus encontrado por nombre similar - {bus.loc_name}")
                        return bus
        except Exception as e:
            app.PrintInfo(f"  ℹ️ Método nombre similar falló: {e}")
        
        app.PrintWarn(f"  ⚠ No se pudo encontrar el bus de conexión para {gen_name}")
        return None
        
    except Exception as e:
        app.PrintWarn(f"  ⚠ Error buscando bus de conexión para {gen_name}: {e}")
        return None

def obtener_voltaje_del_bus(app, bus, gen_name):
    """Obtiene el voltaje del bus usando múltiples métodos"""
    try:
        # Método 1: uknom directo
        if hasattr(bus, 'uknom'):
            voltaje = bus.uknom
            app.PrintInfo(f"  ⚡ {gen_name}: Voltaje nominal = {voltaje} kV")
            return voltaje
        
        # Método 2: GetAttribute
        try:
            voltaje = bus.GetAttribute('uknom')
            app.PrintInfo(f"  ⚡ {gen_name}: Voltaje (GetAttribute) = {voltaje} kV")
            return voltaje
        except:
            pass
        
        # Método 3: Buscar en el tipo de bus
        try:
            if hasattr(bus, 'typ_id') and bus.typ_id:
                bus_type = bus.typ_id
                if hasattr(bus_type, 'unomkv'):
                    voltaje = bus_type.unomkv
                    app.PrintInfo(f"  ⚡ {gen_name}: Voltaje del tipo de bus = {voltaje} kV")
                    return voltaje
        except:
            pass
        
        # Método 4: Buscar propiedades del bus
        try:
            props = bus.GetProperties()
            for prop in props:
                prop_name = str(prop).lower()
                if 'uknom' in prop_name or 'voltage' in prop_name or 'unom' in prop_name:
                    try:
                        voltaje = bus.GetAttribute(prop)
                        app.PrintInfo(f"  ⚡ {gen_name}: Voltaje por propiedad {prop} = {voltaje} kV")
                        return voltaje
                    except:
                        continue
        except:
            pass
        
        app.PrintWarn(f"  ⚠ No se pudo obtener voltaje del bus {bus.loc_name}")
        return None
        
    except Exception as e:
        app.PrintWarn(f"  ⚠ Error obteniendo voltaje del bus para {gen_name}: {e}")
        return None

def determinar_voltaje_por_ubicacion(app, gen_obj, gen_name):
    """Determina el voltaje basado en la ubicación y configuración del generador"""
    try:
        app.PrintInfo(f"  🔍 Determinando voltaje por ubicación para {gen_name}...")
        
        # Verificar si es un sistema de baja tensión típico
        potencia_kw = gen_obj.pgini
        
        # Para sistemas PV, la mayoría están en baja tensión (< 1000V)
        if potencia_kw <= 1000:  # Menos de 1 MW
            voltaje = 0.48
            app.PrintInfo(f"  ⚡ {gen_name}: Voltaje determinado por potencia ({potencia_kw} kW) = 0.48 kV")
        elif potencia_kw <= 10000:  # Entre 1 MW y 10 MW
            voltaje = 13.8
            app.PrintInfo(f"  ⚡ {gen_name}: Voltaje determinado por potencia ({potencia_kw} kW) = 13.8 kV")
        else:  # Más de 10 MW
            voltaje = 34.5
            app.PrintInfo(f"  ⚡ {gen_name}: Voltaje determinado por potencia ({potencia_kw} kW) = 34.5 kV")
        
        return voltaje
        
    except Exception as e:
        app.PrintWarn(f"  ⚠ Error determinando voltaje por ubicación: {e}")
        return 0.48

def calcular_corrientes_cortocircuito(gen_objects):
    """Calcula corriente nominal y corrientes de cortocircuito para los generadores no síncronos"""
    try:
        app.PrintInfo("🔧 Calculando corrientes de cortocircuito...")
        
        corrientes_calculadas = {}
        
        for gen_name, gen_obj in gen_objects.items():
            try:
                # Obtener datos del generador
                p_nuevo_kw = gen_obj.pgini  # Potencia activa en kW
                
                # Buscar el bus de conexión
                bus_conexion = obtener_bus_conexion_generador(app, gen_obj, gen_name)
                voltaje_kv = None
                
                if bus_conexion:
                    # Obtener voltaje del bus
                    voltaje_kv = obtener_voltaje_del_bus(app, bus_conexion, gen_name)
                
                # Si no se pudo obtener el voltaje del bus, usar método alternativo
                if not voltaje_kv:
                    voltaje_kv = determinar_voltaje_por_ubicacion(app, gen_obj, gen_name)
                    app.PrintInfo(f"  ℹ️ {gen_name}: Usando voltaje determinado por ubicación")
                
                # Calcular potencia aparente (asumiendo factor de potencia 0.9)
                factor_potencia = 0.9
                s_kva = p_nuevo_kw / factor_potencia  # kVA
                
                # Calcular corriente nominal (I = S / (√3 * V))
                i_nominal = s_kva / (1.732 * voltaje_kv)  # kA (√3 ≈ 1.732)
                
                # Calcular corriente de cortocircuito (Icc = I * 1.2)
                i_cc = i_nominal * 1.2  # kA
                
                app.PrintInfo(f"  📊 {gen_name}:")
                app.PrintInfo(f"    - Potencia activa = {p_nuevo_kw:.1f} kW")
                app.PrintInfo(f"    - Potencia aparente = {s_kva:.1f} kVA")
                app.PrintInfo(f"    - Voltaje = {voltaje_kv:.3f} kV")
                app.PrintInfo(f"    - Corriente nominal = {i_nominal:.3f} kA")
                app.PrintInfo(f"    - Corriente cortocircuito = {i_cc:.3f} kA")
                
                # Guardar valores calculados
                corrientes_calculadas[gen_name] = {
                    'i_nominal': i_nominal,
                    'i_cc': i_cc,
                    'voltaje': voltaje_kv,
                    'potencia_kw': p_nuevo_kw,
                    'potencia_kva': s_kva,
                    'bus_name': bus_conexion.loc_name if bus_conexion else "Determinado por ubicación"
                }
                
            except Exception as e:
                app.PrintWarn(f"  ⚠ Error calculando corrientes para {gen_name}: {e}")
                corrientes_calculadas[gen_name] = None
        
        return corrientes_calculadas
        
    except Exception as e:
        app.PrintWarn(f"⚠ Error en cálculo de corrientes: {e}")
        return {}

def actualizar_corrientes_cortocircuito(gen_objects, corrientes_calculadas):
    """Actualiza las corrientes de cortocircuito en los generadores"""
    try:
        app.PrintInfo("🔄 Actualizando corrientes de cortocircuito en los generadores...")
        
        contador_actualizados = 0
        
        for gen_name, gen_obj in gen_objects.items():
            try:
                if gen_name in corrientes_calculadas and corrientes_calculadas[gen_name]:
                    datos_corriente = corrientes_calculadas[gen_name]
                    i_cc_nuevo = datos_corriente['i_cc']
                    
                    # Actualizar las tres componentes de corriente de cortocircuito
                    variables_actualizar = ['e:Ikss3PF', 'e:Ikss2PF', 'e:Ikss1PF']
                    
                    for variable in variables_actualizar:
                        try:
                            # Obtener valor original
                            valor_original = gen_obj.GetAttribute(variable)
                            
                            # Establecer nuevo valor
                            gen_obj.SetAttribute(variable, i_cc_nuevo)
                            
                            app.PrintInfo(f"  ✅ {gen_name}: {variable} = {i_cc_nuevo:.3f} kA (original: {valor_original:.3f} kA)")
                            
                        except Exception as var_error:
                            app.PrintWarn(f"  ⚠ Error actualizando {variable} para {gen_name}: {var_error}")
                    
                    contador_actualizados += 1
                    
                else:
                    app.PrintWarn(f"  ⚠ No se pudieron actualizar corrientes para {gen_name} - datos de cálculo no disponibles")
                    
            except Exception as e:
                app.PrintWarn(f"  ⚠ Error actualizando corrientes de {gen_name}: {e}")
        
        app.PrintInfo(f"✅ Corrientes de cortocircuito actualizadas para {contador_actualizados} de {len(gen_objects)} generadores")
        return contador_actualizados > 0
        
    except Exception as e:
        app.PrintWarn(f"⚠ Error actualizando corrientes: {e}")
        return False

# === LECTURA DEL EXCEL ===
try:
    df = pd.read_excel(excel_path)
    app.PrintInfo(f"Archivo leído correctamente: {excel_path}")
except Exception as e:
    app.PrintWarn(f"No se pudo leer el archivo Excel. Error: {e}")
    raise

if df.empty:
    app.PrintWarn("El archivo Excel no contiene datos.")
    raise SystemExit

generadores = df.columns.tolist()
app.PrintInfo(f"Generadores detectados: {', '.join(generadores)}")

# === BUSCAR SISTEMAS PV ===
gen_objects = {}
for gen_name in generadores:
    gen = app.GetCalcRelevantObjects(f"{gen_name}.ElmPvsys")
    if not gen:
        app.PrintWarn(f"No se encontró el sistema PV '{gen_name}' en el proyecto.")
    else:
        gen_objects[gen_name] = gen[0]

if not gen_objects:
    app.PrintWarn("No se encontró ningún sistema PV válido. Verifique los nombres en el Excel.")
    raise SystemExit

# === GUARDAR VALORES ORIGINALES ===
pot_originales = {}
corrientes_originales = {}

for gen_name, gen_obj in gen_objects.items():
    try:
        # Guardar potencia original
        pot_originales[gen_name] = float(gen_obj.pgini)
        app.PrintInfo(f"Potencia original de {gen_name}: {pot_originales[gen_name]:.1f} kW")
        
        # Guardar corrientes originales
        corrientes_originales[gen_name] = {}
        variables_corriente = ['e:Ikss3PF', 'e:Ikss2PF', 'e:Ikss1PF']
        
        for variable in variables_corriente:
            try:
                valor_original = gen_obj.GetAttribute(variable)
                corrientes_originales[gen_name][variable] = valor_original
                app.PrintInfo(f"Corriente original de {gen_name}: {variable} = {valor_original:.3f} kA")
            except Exception as e:
                app.PrintWarn(f"No se pudo leer {variable} de {gen_name}: {e}")
                corrientes_originales[gen_name][variable] = 0
                
    except Exception as e:
        app.PrintWarn(f"No se pudieron leer los valores originales de {gen_name}: {e}")

# === CAMBIO DE POTENCIAS POR ESCENARIO ===
for i, row in df.iterrows():
    escenario_num = i + 1
    app.PrintPlain(f"\n--- Escenario {escenario_num} ---")
    success = True

    # Carpeta de salida
    output_folder = os.path.join(base_output_path, f"Escenario_{escenario_num}")
    os.makedirs(output_folder, exist_ok=True)
    app.PrintInfo(f"Carpeta creada para resultados: {output_folder}")

    # Cambiar potencias
    for gen_name, gen_obj in gen_objects.items():
        try:
            p_mw = float(row[gen_name])
            p_kw = p_mw * 1000.0
            gen_obj.pgini = p_kw
            app.PrintInfo(f"  {gen_name}: pgini = {p_kw:.1f} kW (cambio exitoso)")
        except Exception as e:
            app.PrintWarn(f"  ⚠ No se pudo cambiar la potencia de {gen_name}: {e}")
            success = False

    if success:
        app.PrintPlain(f"✅ Cambio exitoso para {', '.join(gen_objects.keys())}")
        
        # === 2. CALCULAR Y ACTUALIZAR CORRIENTES DE CORTOCIRCUITO ===
        app.PrintPlain("→ Calculando y actualizando corrientes de cortocircuito...")
        corrientes_calculadas = calcular_corrientes_cortocircuito(gen_objects)
        
        if corrientes_calculadas:
            resultado_corrientes = actualizar_corrientes_cortocircuito(gen_objects, corrientes_calculadas)
            if resultado_corrientes:
                app.PrintInfo("✅ Corrientes de cortocircuito actualizadas correctamente")
            else:
                app.PrintWarn("⚠ Hubo problemas al actualizar las corrientes de cortocircuito")
        else:
            app.PrintWarn("❌ No se pudieron calcular las corrientes de cortocircuito")
        
        # === EJECUTAR DATOS GSIM COMPLETO ===
        app.PrintPlain("→ Ejecutando análisis completo Datos GSIM...")
        ejecutar_datos_gsim_completo(escenario_num, output_folder)
        
        # === EJECUTAR POSITIVE COMPLETO ===
        app.PrintPlain("→ Ejecutando análisis completo Positive...")
        ejecutar_positive_completo(output_folder, escenario_num)
        
        # === EJECUTAR SDSCR INFO COMPLETO ===
        app.PrintPlain("→ Ejecutando análisis completo SDSCR INFO...")
        ejecutar_sdscr_info_completo(output_folder, escenario_num)
        
        # === EJECUTAR EXPORTZ_PYTHON COMPLETO ===
        app.PrintPlain("→ Ejecutando análisis completo ExportZ_Python...")
        ejecutar_exportz_python_completo(output_folder, escenario_num)
            
    else:
        app.PrintWarn(f"❌ Error al aplicar los cambios del escenario {escenario_num}")

# === RESTAURAR POTENCIAS ORIGINALES ===
app.PrintPlain("\n--- Restaurando potencias originales ---")
for gen_name, gen_obj in gen_objects.items():
    try:
        p_kw_orig = pot_originales[gen_name]
        if p_kw_orig is not None:
            gen_obj.pgini = float(p_kw_orig)
            app.PrintInfo(f"  {gen_name}: pgini restaurado a {p_kw_orig:.1f} kW")
    except Exception as e:
        app.PrintWarn(f"  ⚠ Error al restaurar la potencia de {gen_name}: {e}")

# Restaurar corrientes originales
app.PrintPlain("→ Restaurando corrientes de cortocircuito originales...")
for gen_name, gen_obj in gen_objects.items():
    try:
        if gen_name in corrientes_originales:
            for variable, valor_original in corrientes_originales[gen_name].items():
                try:
                    gen_obj.SetAttribute(variable, valor_original)
                    app.PrintInfo(f"  ✅ {gen_name}: {variable} restaurado a {valor_original:.3f} kA")
                except Exception as e:
                    app.PrintWarn(f"  ⚠ Error restaurando {variable} de {gen_name}: {e}")
    except Exception as e:
        app.PrintWarn(f"  ⚠ Error restaurando corrientes de {gen_name}: {e}")

app.PrintPlain("\n=== FIN DEL SCRIPT ===")

app.PrintPlain("\n=== FIN DEL SCRIPT ===")