# -*- coding: utf-8 -*-
import powerfactory as pf
import pandas as pd
import os
import numpy as np
import csv
from pathlib import Path


# ============================================================
# USER SETTINGS
# ============================================================

# Repository root
REPO_ROOT = Path(__file__).resolve().parents[2]

# Example and type of generation to be processed
GENTIP = "IND" # If it is inductive, "IND"; if it is capacitive, "CAP"
EXAMPLE = "IEEE39"

# Excel file with the selected scenarios
SCENARIOS_FILE = (REPO_ROOT / "data" / "scenarios" / EXAMPLE / "escenarios.xlsx")

# Folder where extraction results will be saved
OUTPUT_FOLDER = (REPO_ROOT / "data" / "results" / EXAMPLE / GENTIP)

# === CONFIGURATIÓN ===
excel_path = SCENARIOS_FILE
base_output_path = OUTPUT_FOLDER

# === CONNECTION TO POWERFACTORY ===
app = pf.GetApplication()
if not app:
    raise Exception("Could not connect to PowerFactory. Run this script from PowerFactory.")

app.PrintPlain("=== START OF POWER-SWITCHING SCRIPT ===")

######## === INTEGRATED GSIM DATA FUNCTIONS === #########
def get_element_data(element):
    """Extracts basic data from an element"""
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
    """Extracts data from buses"""
    try:
        # Obtain current voltage and angle (may vary depending on the study)
        v_mag = bus.GetAttribute('m:U1l:bus')
        v_angle = bus.GetAttribute('phiu:bus')
    except:
        # If it fails, use nominal values.
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
    """Extracts data from synchronous generators"""
    try:
        # Use specific attributes for P and Q.
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
        app.PrintWarn(f"Error retrieving data from the generator {gen.loc_name}: {str(e)}")
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
    """Extracts data from lines"""
    try:
        # Attempt to obtain line parameters
        r_line = line.GetAttribute('t:rline')  # Resistance per unit length
        x_line = line.GetAttribute('t:xline')  # Reactance per unit length
        b_line = line.GetAttribute('t:bline')  # Susceptance per unit length
        length = line.GetAttribute('dline')    # Line length
        
        # Calculate total values
        r_total = r_line * length if length and r_line else r_line
        x_total = x_line * length if length and x_line else x_line
        b_total = b_line * length if length and b_line else b_line
        
    except:
        # If that fails, try to obtain total values ​​directly
        try:
            r_total = line.GetAttribute('Rline')
            x_total = line.GetAttribute('Xline')
            b_total = line.GetAttribute('Bline')
            length = line.GetAttribute('dline') if hasattr(line, 'dline') else None
        except:
            # If it still fails, use default values
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
    """Extracts data from transformers with specific attributes"""
    try:
        # Obtain buses connected to the transformer
        bus_hv = trafo.bushv.cterm.loc_name if hasattr(trafo, 'bushv') and trafo.bushv else None
        bus_lv = trafo.buslv.cterm.loc_name if hasattr(trafo, 'buslv') and trafo.buslv else None
        
        # Obtain parameters with specific attributes
        r_pu = trafo.GetAttribute('t:r1pu') if hasattr(trafo, 't:r1pu') else None
        x_pu = trafo.GetAttribute('t:x1pu') if hasattr(trafo, 't:x1pu') else None
        s_nom = trafo.GetAttribute('e:Snom') if hasattr(trafo, 'e:Snom') else None
        tap = trafo.GetAttribute('nntap') if hasattr(trafo, 'nntap') else None
        
        # Obtain voltages from the connected buses
        voltage_hv = trafo.bushv.GetAttribute('m:Ul') if hasattr(trafo, 'bushv') and trafo.bushv else None
        voltage_lv = trafo.buslv.GetAttribute('m:Ul') if hasattr(trafo, 'buslv') and trafo.buslv else None
        
    except Exception as e:
        app.PrintWarn(f"Error retrieving transformer data {trafo.loc_name}: {str(e)}")
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
    """Extracts data from PV systems (inverters)"""
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
        
        # Try to obtain more information about the type of control
        try:
            if hasattr(pvsys, 'typ_id') and pvsys.typ_id:
                data['control_type'] = str(pvsys.typ_id)
        except:
            pass
            
    except Exception as e:
        app.PrintWarn(f"Error retrieving data from the PV system {pvsys.loc_name}: {str(e)}")
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
    """Extracts load data"""
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
        app.PrintWarn(f"Error retrieving load data {load.loc_name}: {str(e)}")
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
    """Run the load flow before extracting data"""
    try:
        app.PrintInfo("📊 Running load flow...")
        
        # Get the load flow object from the current study
        ldf = app.GetFromStudyCase("ComLdf")
        if ldf:
            ldf.Execute()
            app.PrintInfo("✅ Load flow executed successfully")
            return True
        else:
            app.PrintWarn("⚠ Load flow object not found")
            return False
            
    except Exception as e:
        app.PrintWarn(f"⚠ Error executing load flow: {e}")
        return False

# Main data extraction
def extract_network_data():
    """Extracts all data from the network"""
    
    app.PrintInfo("Extracting data from the network...")
    
    # Run load flow first
    if not ejecutar_flujo_carga():
        app.PrintWarn("⚠ The load flow could not be executed; the data may be incomplete")
    
    # Get active project
    project = app.GetActiveProject()
    if not project:
        app.PrintError("There is no active project")
        return None
    
    # Get all relevant elements
    buses = app.GetCalcRelevantObjects('*.ElmTerm')
    lines = app.GetCalcRelevantObjects('*.ElmLne')
    transformers = app.GetCalcRelevantObjects('*.ElmTr2')
    
    # Search for different types of generators
    generators_sync = app.GetCalcRelevantObjects('*.ElmSym')  # Synchronous generators
    generators_gen = app.GetCalcRelevantObjects('*.ElmGen')   # General generators
    generators = generators_sync + generators_gen  # Combine both types
    
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
    """Calculate the power balance at each bus"""
    
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
    """Exports data to CSV files at the specified path"""
    
    # Create a "GSIM Data" folder inside the scenario folder
    gsim_folder = os.path.join(output_folder, "Datos GSIM")
    os.makedirs(gsim_folder, exist_ok=True)
    
    app.PrintInfo(f"Exporting data to: {gsim_folder}")
    
    # Export buses
    df_buses = pd.DataFrame(network_data['buses'])
    df_buses.to_csv(os.path.join(gsim_folder, f'ieee9bus_buses.csv'), index=False, encoding='utf-8')
    
    # Export lines
    df_lines = pd.DataFrame(network_data['lines'])
    df_lines.to_csv(os.path.join(gsim_folder, f'ieee9bus_lines.csv'), index=False, encoding='utf-8')
    
    # Export transformers
    df_trafos = pd.DataFrame(network_data['transformers'])
    df_trafos = df_trafos.fillna('') 
    df_trafos.to_csv(os.path.join(gsim_folder, f'ieee9bus_transformers.csv'), index=False, encoding='utf-8')
    
    # Export generators
    df_gens = pd.DataFrame(network_data['generators'])
    df_gens = df_gens.fillna('')
    df_gens.to_csv(os.path.join(gsim_folder, f'ieee9bus_generators.csv'), index=False, encoding='utf-8')
    
    # Export PV systems
    df_pvsys = pd.DataFrame(network_data['pvsys'])
    df_pvsys.to_csv(os.path.join(gsim_folder, f'ieee9bus_pvsys.csv'), index=False, encoding='utf-8')
    
    # Export loads
    df_loads = pd.DataFrame(network_data['loads'])
    df_loads.to_csv(os.path.join(gsim_folder, f'ieee9bus_loads.csv'), index=False, encoding='utf-8')
    
    app.PrintInfo("Data successfully exported to CSV files in the 'Datos GSIM' folder")

def print_summary(network_data):
    """Print network summary"""
    
    app.PrintInfo("\n=== NETWORK SUMMARY ===")
    app.PrintInfo(f"Number of buses: {len(network_data['buses'])}")
    app.PrintInfo(f"Number of lines: {len(network_data['lines'])}")
    app.PrintInfo(f"Number of transformers: {len(network_data['transformers'])}")
    app.PrintInfo(f"Number of synchronous generators: {len(network_data['generators'])}")
    app.PrintInfo(f"Number of PV systems (inverters): {len(network_data['pvsys'])}")
    app.PrintInfo(f"Number of loads: {len(network_data['loads'])}")
    
    # Inverter information regarding secure securities handling None
    app.PrintInfo("\n=== INVERTERS INFORMACIÓN ===")
    for pv in network_data['pvsys']:
        app.PrintInfo(f"PV System: {pv['name']}")
        app.PrintInfo(f"  Bus: {pv.get('bus', 'N/A')}")
        
        # Handling None values ​​in P and Q
        p_val = pv.get('p')
        q_val = pv.get('q')
        
        p_str = f"{p_val:.3f}" if p_val is not None else "N/A"
        q_str = f"{q_val:.3f}" if q_val is not None else "N/A"
        s_str = f"{pv.get('s', 'N/A'):.3f}" if pv.get('s') is not None else "N/A"
        v_str = f"{pv.get('v_actual', 'N/A'):.3f}" if pv.get('v_actual') is not None else "N/A"
        
        app.PrintInfo(f"  P: {p_str} MW, Q: {q_str} Mvar")
        app.PrintInfo(f"  S nominal: {s_str} MVA")
        app.PrintInfo(f"  Current voltage: {v_str} kV")
        
        if 'control_type' in pv and pv['control_type']:
            app.PrintInfo(f"  Control type: {pv['control_type']}")
    
    # Information on transformers with safe handling of None values
    app.PrintInfo("\n=== TRANSFORMER INFORMATION ===")
    for trafo in network_data['transformers']:
        app.PrintInfo(f"Transformador: {trafo['name']}")
        app.PrintInfo(f"  Bus HV: {trafo.get('from_bus', 'N/A')}")
        app.PrintInfo(f"  Bus LV: {trafo.get('to_bus', 'N/A')}")
        
        # Safe handling of valuables
        r_pu = trafo.get('r_pu')
        x_pu = trafo.get('x_pu')
        
        if r_pu is not None and x_pu is not None:
            app.PrintInfo(f"  R%: {r_pu:.3f}, X%: {x_pu:.3f}")
        else:
            app.PrintInfo(f"  R%: {r_pu if r_pu is not None else 'N/A'}, X%: {x_pu if x_pu is not None else 'N/A'}")

def ejecutar_datos_gsim_completo(escenario_num, output_folder):
    """Executes the full GSIM Data functionality"""
    try:
        app.PrintInfo(f"🎯 Executing GSIM data for scenario {escenario_num}")
        
        # Extract data from the network (without parameters)
        network_data = extract_network_data()
        
        if network_data:
            # Print summary
            print_summary(network_data)
            
            # Export to CSV
            export_to_csv(network_data, output_folder, escenario_num)
            
            app.PrintInfo(f"\n✅ EXTRACTION COMPLETE FOR SCENARIO {escenario_num}")
            return True
        else:
            app.PrintError("❌ The data could not be retrieved from the network")
            return False
            
    except Exception as e:
        app.PrintError(f"❌ Error during extraction: {str(e)}")
        import traceback
        app.PrintError(traceback.format_exc())
        return False

######## === INTEGRATED POSITIVE FUNCTIONS === #########
def z_to_y(r, x):
    """Converts impedance to admittance"""
    if r == 0 and x == 0:
        return 0
    return 1 / complex(r, x)

def ejecutar_positive_completo(output_folder, escenario_num):
    """It runs the full functionality of Positive"""
    try:
        app.PrintInfo(f"🧮 Executing Positive scenario {escenario_num}")
        
        # Create a "Positive" folder inside the scenario folder
        positive_folder = os.path.join(output_folder, "Positive")
        os.makedirs(positive_folder, exist_ok=True)
        
        app.PrintInfo("✅ Starting Ybus calculation (with lines, transformers, generators, and loads)...")

        # Obtain items
        buses = app.GetCalcRelevantObjects("*.ElmTerm")
        lines = app.GetCalcRelevantObjects("*.ElmLne")
        trafos = app.GetCalcRelevantObjects("*.ElmTr2")
        gens = app.GetCalcRelevantObjects("*.ElmSym")
        pvsys_gens = app.GetCalcRelevantObjects("*.ElmPvsys")
        loads = app.GetCalcRelevantObjects("*.ElmLod")

        # Index buses
        bus_names = [bus.loc_name for bus in buses]
        bus_idx = {name: i for i, name in enumerate(bus_names)}
        n = len(bus_names)
        Ybus = np.zeros((n, n), dtype=complex)

        # ➤ Lines
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
                app.PrintInfo(f"⚠️ Untyped line: {line.loc_name}")
                continue
            length = line.dline
            r = model.rline * length
            x = model.xline * length
            y = z_to_y(r, x)
            Ybus[i, i] += y
            Ybus[j, j] += y
            Ybus[i, j] -= y
            Ybus[j, i] -= y

        # ➤ Transformers (using per-unit impedance based on type)
        for trafo in trafos:
            term1 = trafo.buslv
            term2 = trafo.bushv
            if not term1 or not term2:
                app.PrintInfo(f"⚠️ Trafo {trafo.loc_name} without a valid connection")
                continue
            bus1 = term1.cterm
            bus2 = term2.cterm
            if not bus1 or not bus2:
                app.PrintInfo(f"⚠️ Trafo {trafo.loc_name} with terminals not connected to nodes")
                continue
            i, j = bus_idx.get(bus1.loc_name), bus_idx.get(bus2.loc_name)
            if i is None or j is None:
                app.PrintInfo(f"⚠️ Trafo {trafo.loc_name} with buses outside the index")
                continue

            typ = trafo.typ_id
            if not typ:
                app.PrintInfo(f"⚠️ Trafo {trafo.loc_name} unassigned type.")
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
                app.PrintInfo(f"⚠️ Error extracting transformer impedance {trafo.loc_name}: {str(e)}")

        # ➤ Generators
        for gen in gens:
            bus = gen.bus1
            if not bus:
                app.PrintInfo(f"⚠️ Generator {gen.loc_name} without a valid connection")
                continue
            bus_term = bus.cterm
            if not bus_term:
                app.PrintInfo(f"⚠️ Generator {gen.loc_name} not connected to node")
                continue
            i = bus_idx.get(bus_term.loc_name)
            if i is None:
                continue

            typ = gen.typ_id
            if typ and hasattr(typ, "xd1"):
                # Synchronous generator -> use parameters Xd1, Ra
                x = typ.xd1
                r = typ.ra
                y = z_to_y(r, x)
                Ybus[i, i] += y
            else:
                # Static generators (PVsys, PQ, etc.)
                try:
                    # Obtain active and reactive power at the node from the load flow
                    P = gen.GetAttribute("n:Pgen:bus1")  # [MW]
                    Q = gen.GetAttribute("n:Qgen:bus1")  # [Mvar]
                except Exception as e:
                    app.PrintInfo(f"⚠️ P/Q could not be obtained from {gen.loc_name}: {e}")
                    continue

                if P == 0 and Q == 0:
                    continue

                S = complex(P, Q) / 1000  # Convert to per-unit on a 1000 MVA base, if applicable
                Ysh = S / (1.0 ** 2)
                Ybus[i, i] += Ysh.conjugate()

        # ➤ ElmPvsys-type generators
        for gen in pvsys_gens:
            bus = gen.bus1
            if not bus:
                app.PrintInfo(f"⚠️ PVsys {gen.loc_name} without a valid connection")
                continue
            bus_term = bus.cterm
            if not bus_term:
                app.PrintInfo(f"⚠️ PVsys {gen.loc_name} not connected to node")
                continue
            i = bus_idx.get(bus_term.loc_name)
            if i is None:
                continue

            P = gen.pgini  # MW
            Q = gen.qgini  # MVAr
            if P == 0 and Q == 0:
                continue
            S = complex(P, Q) / 1000  # [MVA]
            Ysh = S / (1.0 ** 2)      # Admittance in p.u. (assuming V = 1.0 p.u.)
            Ybus[i, i] += Ysh.conjugate()

        # ➤ Loads
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

        # ➤ Export Ybus to CSV
        ybus_path = os.path.join(positive_folder, f"Ybus_export.csv")
        with open(ybus_path, mode="w", newline="") as file:
            writer = csv.writer(file)

            # Header with column names
            header = ["Bus"] + bus_names
            writer.writerow(header)

            # Write each row with its bus name and the complex admittances
            for i in range(n):
                row = [bus_names[i]]
                for j in range(n):
                    y = Ybus[i, j]
                    cell = f"{y.real:.4f}+j{y.imag:.4f}"
                    row.append(cell)
                writer.writerow(row)

        app.PrintInfo(f"📁 Ybus file successfully exported to:\n{ybus_path}")

        # ➤ Export voltages and currents
        app.PrintInfo("✅ Exporting generator results and node voltages...")

        # Run load flow
        ldf = app.GetFromStudyCase("ComLdf")
        if not ldf:
            app.PrintInfo("❌ The ComLdf object was not found.")
            return False

        ldf.iopt_net = 0
        status = ldf.Execute()
        if status != 0:
            app.PrintInfo("❌ Error executing the load flow.")
            return False

        app.PrintInfo("✅ Load flow executed successfully.")

        # 🔹 Generators
        gen_classes = ["ElmSym", "ElmGenstat", "ElmPvsys", "ElmPvg", "ElmVsccon"]
        generadores = []
        for cls in gen_classes:
            generadores += app.GetCalcRelevantObjects(f"*.{cls}")

        # 🔹 Node terminals
        terminales = app.GetCalcRelevantObjects("*.ElmTerm")

        # ➤ Export generator currents
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
                    app.PrintInfo(f"⚠️ {name} no measured current: {e}")

        # ➤ Export voltages from terminals
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
                    app.PrintInfo(f"⚠️ Terminal {term.loc_name} without measured tension: {e}")

        # ➤ Export active power from generators
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
                    app.PrintInfo(f"⚠️ {name} without pgini attribute: {e}")

        # ➤ Perform a three-phase short-circuit analysis and export Ikss and Skss
        app.PrintInfo("⚡ Performing three-phase short-circuit calculation...")

        # Get short-circuit object
        sc = app.GetFromStudyCase("ComShc")
        if not sc:
            app.PrintInfo("❌ The ComShc object was not found in the case study.")
            return False

        # Configure for three-phase at all nodes
        sc.iopt_mde = 1     # 1 = IEC60909
        #sc.iopt_shc = 3psc     # 1 = simétric (3ph)
        sc.iopt_allbus = 1  # Calculate at all nodes

        # Run calculation
        status = sc.Execute()
        if status != 0:
            app.PrintInfo("❌ Error while executing the short-circuit calculation.")
            return False

        app.PrintInfo("✅ Three-phase short-circuit calculation performed correctly.")

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
                    # Initial symmetrical three-phase current in kA
                    ikss = nodo.GetAttribute("m:Ikss")
                    # Initial symmetrical short-circuit power in MVA
                    skss = nodo.GetAttribute("m:Skss")

                    # Avoid None
                    if ikss is None:
                        ikss = 0.0
                    if skss is None:
                        skss = 0.0

                    # Decimal comma format
                    ikss_str = f"{ikss:.4f}".replace(".", ",")
                    skss_str = f"{skss:.4f}".replace(".", ",")

                    writer.writerow([nodo.loc_name, ikss_str, skss_str])

                except Exception as e:
                    app.PrintInfo(f"⚠️ Nodo {nodo.loc_name} sin datos: {e}")

        app.PrintInfo(f"📄 Exported short circuit results in:\n{sc_path}")
        app.PrintInfo(f"✅ Positive completed for scenario {escenario_num}")
        return True

    except Exception as e:
        app.PrintError(f"❌ Error during the execution of Positive: {str(e)}")
        import traceback
        app.PrintError(traceback.format_exc())
        return False

######## === INTEGRATED SDSCR INFO FUNCTIONS === #########
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
    # Create "SDSCR INFO" folder inside the scenario folder
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
        
        # Run load flow first
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

######## === INTEGRATED EXPORTZ_PYTHON FUNCTIONS === #########
def ejecutar_exportz_python_completo(output_folder, escenario_num):
    """Ejecuta la funcionalidad completa de ExportZ_Python"""
    try:
        app.PrintInfo(f"🔌 Ejecutando ExportZ_Python para escenario {escenario_num}")
        
        # Create "ExportZ_Python" folder inside the scenario folder
        exportz_folder = os.path.join(output_folder, "ExportZ_Python")
        os.makedirs(exportz_folder, exist_ok=True)
        
        # Mapping of av_mode to readable labels
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

        # Include all relevant generator types
        generadores = app.GetProjectFolder("netdat").GetContents("*.ElmGenstat,*.ElmSym,*.ElmPvsys,*.ElmPvg", 1)

        if not generadores:
            app.PrintWarn("⚠️ No se encontraron generadores en el proyecto.")
            return False
        else:
            app.PrintInfo(f"🔍 Generadores encontrados: {len(generadores)}")

            # Generator file
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

                        # Physical type
                        tipo_fisico = "Síncrono" if tipo in ["ElmGenstat", "ElmSym"] else "IBR"

                        # Control type
                        if tipo in ["ElmGenstat", "ElmSym"]:
                            tipo_control = "Vtheta"
                        elif tipo in ["ElmPvsys", "ElmPvg"]:
                            if hasattr(gen, "av_mode"):
                                tipo_control = av_mode_dict.get(gen.av_mode, f"av_mode={gen.av_mode}")
                            else:
                                tipo_control = "PQ (default)"
                        else:
                            tipo_control = "Desconocido"

                        # Connection node
                        terminal = gen.bus1.cterm if gen.bus1 and hasattr(gen.bus1, "cterm") else None
                        if terminal and terminal.GetClassName() == "ElmTerm":
                            nodo = terminal.loc_name
                            Vbase_kV = terminal.uknom
                        else:
                            nodo = "N/A"
                            Vbase_kV = None

                        # Active power
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

                        # Write CSV row
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

        # ➤ Export load information
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

                        # Powers in MW and MVAr
                        P_MW = carga.plini / 1000.0  # plini is in kW
                        Q_Mvar = carga.qlini / 1000.0  # qlini is in kVAr

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

# === FUNCTIONS FOR SHORT-CIRCUIT CURRENT CALCULATION (YOUR CODE) ===
def obtener_bus_conexion_generador(app, gen_obj, gen_name):
    """Gets the generator connection bus using more robust methods"""
    try:
        app.PrintInfo(f"  🔍 Buscando bus de conexión para {gen_name}...")
        
        # Method 1: Search through cubicles (most reliable method in PowerFactory)
        try:
            cubicle = gen_obj.GetCubicle()
            if cubicle:
                bus = cubicle.GetBus()
                if bus:
                    app.PrintInfo(f"  ✅ {gen_name}: Bus encontrado por cubicle - {bus.loc_name}")
                    return bus
        except Exception as e:
            app.PrintInfo(f"  ℹ️ Método cubicle falló: {e}")
        
        # Method 2: Search for directly connected terminals
        try:
            # Search for all terminals in the same container
            terminales = app.GetCalcRelevantObjects(f"{gen_obj.loc_name}*.ElmTerm")
            for term in terminales:
                if hasattr(term, 'uknom'):
                    app.PrintInfo(f"  ✅ {gen_name}: Terminal encontrada - {term.loc_name}")
                    return term
        except Exception as e:
            app.PrintInfo(f"  ℹ️ Método terminales falló: {e}")
        
        # Method 3: Search by physical connection (bus1)
        try:
            if hasattr(gen_obj, 'bus1') and gen_obj.bus1:
                bus = gen_obj.bus1
                app.PrintInfo(f"  ✅ {gen_name}: Bus encontrado por bus1 - {bus.loc_name}")
                return bus
        except Exception as e:
            app.PrintInfo(f"  ℹ️ Método bus1 falló: {e}")
        
        # Method 4: Search in the parent container
        try:
            parent = gen_obj.GetParent()
            if parent and hasattr(parent, 'uknom'):
                app.PrintInfo(f"  ✅ {gen_name}: Bus encontrado por parent - {parent.loc_name}")
                return parent
        except Exception as e:
            app.PrintInfo(f"  ℹ️ Método parent falló: {e}")
        
        # Method 5: Search for nearby buses by name
        try:
            # Search for buses that may be connected by similar name
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
    """Gets the bus voltage using multiple methods"""
    try:
        # Method 1: Direct uknom
        if hasattr(bus, 'uknom'):
            voltaje = bus.uknom
            app.PrintInfo(f"  ⚡ {gen_name}: Voltaje nominal = {voltaje} kV")
            return voltaje
        
        # Method 2: GetAttribute
        try:
            voltaje = bus.GetAttribute('uknom')
            app.PrintInfo(f"  ⚡ {gen_name}: Voltaje (GetAttribute) = {voltaje} kV")
            return voltaje
        except:
            pass
        
        # Method 3: Search in the bus type
        try:
            if hasattr(bus, 'typ_id') and bus.typ_id:
                bus_type = bus.typ_id
                if hasattr(bus_type, 'unomkv'):
                    voltaje = bus_type.unomkv
                    app.PrintInfo(f"  ⚡ {gen_name}: Voltaje del tipo de bus = {voltaje} kV")
                    return voltaje
        except:
            pass
        
        # Method 4: Search bus properties
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
    """Determines the voltage based on the generator location and configuration"""
    try:
        app.PrintInfo(f"  🔍 Determinando voltaje por ubicación para {gen_name}...")
        
        # Check whether it is a typical low-voltage system
        potencia_kw = gen_obj.pgini
        
        # For PV systems, most are at low voltage (< 1000 V)
        if potencia_kw <= 1000:  # Less than 1 MW
            voltaje = 0.48
            app.PrintInfo(f"  ⚡ {gen_name}: Voltaje determinado por potencia ({potencia_kw} kW) = 0.48 kV")
        elif potencia_kw <= 10000:  # Between 1 MW and 10 MW
            voltaje = 13.8
            app.PrintInfo(f"  ⚡ {gen_name}: Voltaje determinado por potencia ({potencia_kw} kW) = 13.8 kV")
        else:  # More than 10 MW
            voltaje = 34.5
            app.PrintInfo(f"  ⚡ {gen_name}: Voltaje determinado por potencia ({potencia_kw} kW) = 34.5 kV")
        
        return voltaje
        
    except Exception as e:
        app.PrintWarn(f"  ⚠ Error determinando voltaje por ubicación: {e}")
        return 0.48

def calcular_corrientes_cortocircuito(gen_objects):
    """Calculates rated current and short-circuit currents for non-synchronous generators"""
    try:
        app.PrintInfo("🔧 Calculando corrientes de cortocircuito...")
        
        corrientes_calculadas = {}
        
        for gen_name, gen_obj in gen_objects.items():
            try:
                # Get generator data
                p_nuevo_kw = gen_obj.pgini  # Active power en kW
                
                # Find the connection bus
                bus_conexion = obtener_bus_conexion_generador(app, gen_obj, gen_name)
                voltaje_kv = None
                
                if bus_conexion:
                    # Get bus voltage
                    voltaje_kv = obtener_voltaje_del_bus(app, bus_conexion, gen_name)
                
                # If the bus voltage could not be obtained, use an alternative method
                if not voltaje_kv:
                    voltaje_kv = determinar_voltaje_por_ubicacion(app, gen_obj, gen_name)
                    app.PrintInfo(f"  ℹ️ {gen_name}: Usando voltaje determinado por ubicación")
                
                # Calculate apparent power (assuming a 0.9 power factor)
                factor_potencia = 0.9
                s_kva = p_nuevo_kw / factor_potencia  # kVA
                
                # Calculate rated current (I = S / (√3 * V))
                i_nominal = s_kva / (1.732 * voltaje_kv)  # kA (√3 ≈ 1.732)
                
                # Calculate short-circuit current (Icc = I * 1.2)
                i_cc = i_nominal * 1.2  # kA
                
                app.PrintInfo(f"  📊 {gen_name}:")
                app.PrintInfo(f"    - Potencia activa = {p_nuevo_kw:.1f} kW")
                app.PrintInfo(f"    - Potencia aparente = {s_kva:.1f} kVA")
                app.PrintInfo(f"    - Voltaje = {voltaje_kv:.3f} kV")
                app.PrintInfo(f"    - Corriente nominal = {i_nominal:.3f} kA")
                app.PrintInfo(f"    - Corriente cortocircuito = {i_cc:.3f} kA")
                
                # Save calculated values
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
    """Updates the short-circuit currents in the generators"""
    try:
        app.PrintInfo("🔄 Actualizando corrientes de cortocircuito en los generadores...")
        
        contador_actualizados = 0
        
        for gen_name, gen_obj in gen_objects.items():
            try:
                if gen_name in corrientes_calculadas and corrientes_calculadas[gen_name]:
                    datos_corriente = corrientes_calculadas[gen_name]
                    i_cc_nuevo = datos_corriente['i_cc']
                    
                    # Update the three short-circuit current components
                    variables_actualizar = ['e:Ikss3PF', 'e:Ikss2PF', 'e:Ikss1PF']
                    
                    for variable in variables_actualizar:
                        try:
                            # Get original value
                            valor_original = gen_obj.GetAttribute(variable)
                            
                            # Set new value
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

# === READ EXCEL FILE ===
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

# === FIND PV SYSTEMS ===
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

# === SAVE ORIGINAL VALUES ===
pot_originales = {}
corrientes_originales = {}

for gen_name, gen_obj in gen_objects.items():
    try:
        # Save original power
        pot_originales[gen_name] = float(gen_obj.pgini)
        app.PrintInfo(f"Potencia original de {gen_name}: {pot_originales[gen_name]:.1f} kW")
        
        # Save original currents
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

# === CHANGE POWER VALUES BY SCENARIO ===
for i, row in df.iterrows():
    escenario_num = i + 1
    app.PrintPlain(f"\n--- Escenario {escenario_num} ---")
    success = True

    # Output folder
    output_folder = os.path.join(base_output_path, f"Escenario_{escenario_num}")
    os.makedirs(output_folder, exist_ok=True)
    app.PrintInfo(f"Carpeta creada para resultados: {output_folder}")

    # Change power values
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
        
        # === 2. CALCULATE AND UPDATE SHORT-CIRCUIT CURRENTS ===
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
        
        # === RUN COMPLETE GSIM DATA ===
        app.PrintPlain("→ Ejecutando análisis completo Datos GSIM...")
        ejecutar_datos_gsim_completo(escenario_num, output_folder)
        
        # === RUN COMPLETE POSITIVE ===
        app.PrintPlain("→ Ejecutando análisis completo Positive...")
        ejecutar_positive_completo(output_folder, escenario_num)
        
        # === RUN COMPLETE SDSCR INFO ===
        app.PrintPlain("→ Ejecutando análisis completo SDSCR INFO...")
        ejecutar_sdscr_info_completo(output_folder, escenario_num)
        
        # === RUN COMPLETE EXPORTZ_PYTHON ===
        app.PrintPlain("→ Ejecutando análisis completo ExportZ_Python...")
        ejecutar_exportz_python_completo(output_folder, escenario_num)
            
    else:
        app.PrintWarn(f"❌ Error al aplicar los cambios del escenario {escenario_num}")

# === RESTORE ORIGINAL POWER VALUES ===
app.PrintPlain("\n--- Restaurando potencias originales ---")
for gen_name, gen_obj in gen_objects.items():
    try:
        p_kw_orig = pot_originales[gen_name]
        if p_kw_orig is not None:
            gen_obj.pgini = float(p_kw_orig)
            app.PrintInfo(f"  {gen_name}: pgini restaurado a {p_kw_orig:.1f} kW")
    except Exception as e:
        app.PrintWarn(f"  ⚠ Error al restaurar la potencia de {gen_name}: {e}")

# Restore original currents
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