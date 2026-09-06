import inspect
import re
import os
import math
import numpy as np
import pandas as pd
from numpy import pi
import matplotlib.pyplot as plt
from numpy.linalg import inv, eigvalsh, norm
from pathlib import Path

Xfil=0.15
VarTen=(230/0.48)**2
VbL = 230
SbL = 100

# Repository root
REPO_ROOT = Path(__file__).resolve().parents[2]

# Example to be processed
EXAMPLE = "IEEE39"

#Generation type
GENTIP = "CAP" # If inductive "IND", if capacitive "CAP"

# ------------------------------------------------------------
# INPUT:
# Folder where extract_scenario_data.py saved the scenarios
# ------------------------------------------------------------
INPUT_PATH = REPO_ROOT / "data" / "results" / EXAMPLE / GENTIP

# ------------------------------------------------------------
# OUTPUT:
# Folder where the indicator results will be saved
# ------------------------------------------------------------
OUTPUT_PATH = REPO_ROOT / "results" / EXAMPLE / GENTIP

# Create the output folder if it does not exist
OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

print(f"📥 Input: {INPUT_PATH}")
print(f"📤 Output:  {OUTPUT_PATH}")

# GSIM technical parameters (constant for all scenarios)
FN = 50.0
WB = 2 * pi * FN
V_LV = 480.0
V_HV = 230e3
X_R_SYS = 10.0
X_R_CONV = 10.0
EPS = 1e-12

# =============================================================================
# BLOCK 2: SHARED FUNCTIONS
# =============================================================================

def encontrar_escenarios(ruta_base):
    """Find all the scenario folders"""
    escenarios = []
    for item in os.listdir(ruta_base):
        item_path = os.path.join(ruta_base, item)
        if os.path.isdir(item_path) and item.startswith("Escenario"):
            escenarios.append(item_path)
    return escenarios

# =============================================================================
# BLOCK 3: FUNCTIONS FOR ZBUS CALCULATION
# =============================================================================

def parse_complex(x):
    if not isinstance(x, str):
        return complex(x)
    s = x.strip()

    # Case "a+j-b" -> "a-bj"
    s = s.replace("+j-", "-")
    # Case "a+j b" -> "a+bj"
    s = s.replace("+j", "+")
    # Case "a-j b" -> "a-bj"
    s = s.replace("-j", "-")

    # If it does not end with "j", append it
    if re.match(r".*[+-]\d+(\.\d+)?$", s):
        s = s + "j"

    try:
        return complex(s)
    except ValueError:
        print(f"❌ Could not be parsed: '{x}' -> '{s}'")
        return complex(0)

def parse_complex_simple(x):
    if not isinstance(x, str):
        return complex(x)
    
    s = x.strip()
    
    # Convert "a+j-b" format to standard format
    if "+j-" in s:
        s = s.replace("+j-", "-") + "j"
    elif "-j-" in s:
        s = s.replace("-j-", "-") + "j"
    elif "+j" in s:
        s = s.replace("+j", "+") + "j"
    elif "-j" in s:
        s = s.replace("-j", "-") + "j"
    
    # If it already has j at the end, leave it as is
    elif not s.endswith('j') and 'j' not in s:
        # Check whether it looks like a complex number without j
        if re.match(r'^[+-]?\d*\.?\d+[+-]\d*\.?\d+$', s):
            s = s + 'j'
    
    try:
        return complex(s)
    except ValueError:
        print(f"❌ Could not be parsed: '{x}' -> '{s}'")
        return complex(0)

#print("Example1:", parse_complex("0.2475+j-7.0731"))
#print("Example1:", parse_complex_simple("0.2475+j-7.0731"))

def calcular_zbus_escenario(escenario_input_path, escenario_output_path):
    """Calculate Zbus for a specific scenario."""

    escenario_input_path = Path(escenario_input_path)
    escenario_output_path = Path(escenario_output_path)

    escenario_nombre = escenario_input_path.name

    print()
    print("=" * 70)
    print(f"🔄 CALCULATING ZBUS: {escenario_nombre}")
    print("=" * 70)

    # ---------------------------------------------------------
    # Paths
    # ---------------------------------------------------------
    ybus_file_path = (
        escenario_input_path
        / "Positive"
        / "Ybus_export.csv"
    )

    positive_output_path = (
        escenario_output_path
        / "Positive"
    )

    zbus_output_path = (
        positive_output_path
        / "Zbus.csv"
    )

    print(f"📥 Ybus:  {ybus_file_path}")
    print(f"📤 Zbus:  {zbus_output_path}")

    # ---------------------------------------------------------
    # Verify Ybus file
    # ---------------------------------------------------------
    if not ybus_file_path.exists():
        print(
            f"❌ Not found Ybus_export.csv:\n"
            f"   {ybus_file_path}"
        )
        return False

    # ---------------------------------------------------------
    # Create output folder
    # ---------------------------------------------------------
    try:
        positive_output_path.mkdir(
            parents=True,
            exist_ok=True
        )
    except Exception as e:
        print(
            f"❌ The output folder could not be created:\n"
            f"   {positive_output_path}\n"
            f"   Error: {e}"
        )
        return False

    # ---------------------------------------------------------
    # Read Ybus
    # ---------------------------------------------------------
    try:
        Y = pd.read_csv(
            ybus_file_path,
            index_col=0
        )

        print(
            f"📐 Ybus dimensions: "
            f"{Y.shape[0]} x {Y.shape[1]}"
        )

    except Exception as e:
        print(
            f"❌ Error reading Ybus:\n"
            f"   {e}"
        )
        return False

    # ---------------------------------------------------------
    # Verify that Ybus is square
    # ---------------------------------------------------------
    if Y.shape[0] != Y.shape[1]:
        print(
            f"❌ Ybus is not square: "
            f"{Y.shape[0]} x {Y.shape[1]}"
        )
        return False

    # ---------------------------------------------------------
    # Convert Ybus to complex numbers
    # ---------------------------------------------------------
    try:

        Yc = Y.apply(
            lambda col: col.map(parse_complex_simple)
        ).to_numpy(dtype=complex)

        print("✅ Ybus converted to a complex matrix.")

    except Exception as e:
        print(
            f"❌ Error converting Ybus to complex numbers:\n"
            f"   {e}"
        )
        return False

    # ---------------------------------------------------------
    # Check for problematic values
    # ---------------------------------------------------------
    if not np.isfinite(Yc.real).all() or not np.isfinite(Yc.imag).all():
        print("❌ Ybus contains NaN or infinite values.")
        return False

    # ---------------------------------------------------------
    # Calculate Zbus
    # ---------------------------------------------------------
    try:

        print("🧮 Calculating the inverse of Ybus...")

        condicion = np.linalg.cond(Yc)

        print(
            f"📊 Ybus condition number: "
            f"{condicion:.3e}"
        )

        if condicion > 1e12:
            print(
                "⚠️ Ybus is ill-conditioned. "
                "The pseudo-inverse will be used."
            )

            Zc = np.linalg.pinv(Yc)

        else:
            Zc = np.linalg.inv(Yc)

        print("✅ Zbus calculated correctly.")

    except np.linalg.LinAlgError:
        print(
            "⚠️ Singular Ybus. "
            "Calculating pseudo-inverse..."
        )

        try:
            Zc = np.linalg.pinv(Yc)
        except Exception as e:
            print(
                f"❌ Error calculating pseudo-inverse:\n"
                f"   {e}"
            )
            return False

    except Exception as e:
        print(
            f"❌ Error calculating Zbus:\n"
            f"   {e}"
        )
        return False

    # ---------------------------------------------------------
    # Create Zbus DataFrame
    # ---------------------------------------------------------
    try:

        Z = pd.DataFrame(
            Zc,
            index=Y.index,
            columns=Y.columns
        )

    except Exception as e:
        print(
            f"❌ Error creating Zbus DataFrame:\n"
            f"   {e}"
        )
        return False

    # ---------------------------------------------------------
    # Save Zbus
    # ---------------------------------------------------------
    try:

        Z.to_csv(
            zbus_output_path
        )

        print(
            f"💾 Zbus saved correctly in:\n"
            f"   {zbus_output_path}"
        )

    except Exception as e:
        print(
            f"❌ Error saving Zbus:\n"
            f"   {e}"
        )
        return False

    # ---------------------------------------------------------
    # Final verification
    # ---------------------------------------------------------
    if zbus_output_path.exists():

        tamaño = zbus_output_path.stat().st_size

        print(
            f"✅ File confirmed.\n"
            f"   Size: {tamaño:,} bytes"
        )

        return True

    else:

        print(
            "❌ The file was apparently saved, "
            "but it was not found subsequently."
        )

        return False

# =============================================================================
# BLOCK 4: FUNCTIONS FOR GSIM CALCULATION
# =============================================================================

def Z_dq_from_RL(R, L):
    """Convert R and L to the dq impedance matrix"""
    Zdq = WB * L
    return np.array([[R + 0j, Zdq], [-Zdq, R + 0j]], dtype=complex)

def Zb_from_power(P_MW, V_LL, X_R, f=50.0):
    """Calculate base impedance from power and voltage"""
    P = P_MW * 1e6
    if P <= 0:
        P = 1e6
    I_line = P / (math.sqrt(3) * V_LL)
    V_phase = V_LL / math.sqrt(3)
    Z = V_phase / I_line
    R = Z / math.sqrt(1 + X_R**2)
    X = X_R * R
    L = X / (2 * math.pi * f)
    return R, L

def Zb_from_power_with_filter_simple(P_MW, V_LL, X_R_conv, f=50.0):
    """
    Simplified version with fixed values ​​by power range
    """
    # 1. Base impedance
    R_base, L_base = Zb_from_power(P_MW, V_LL, X_R_conv, f)
    
    # 2. Determine filter according to power
    if P_MW < 5:
        # 1-5 MW
        L_filter = 0.10e-5  # 0.10 mH additional
    elif P_MW < 20:
        # 5-20 MW
        L_filter = 0.05e-5  # 0.05 mH additional
    elif P_MW < 50:
        # 20-50 MW
        L_filter = 0.03e-5  # 0.03 mH additional
    elif P_MW < 100:
        # 50-100 MW
        L_filter = 0.02e-5  # 0.02 mH additional
    elif P_MW < 200:
        # 100-200 MW
        L_filter = 0.015e-5  # 0.015 mH additional
    else:
        # >200 MW
        L_filter = 0.01e-5  # 0.01 mH additional
    
    # 3. Add filter inductance
    L_total = L_base + L_filter
    #print(f"  Filter: +{L_filter*1e3:.3f} mH (total L: {L_total*1e3:.3f} mH)")
    # 4. Resistance remains unchanged (the filter does not add significant resistance at 50 Hz)
    R_total = R_base
    
    return R_total, L_total

def GSIM_from_Y_and_Z(Ysys, Zb):
    """Calculate the GSIM index from matrices Y and Z"""
    eigY = np.abs(np.linalg.eigvals(Ysys))
    eigZ = np.abs(np.linalg.eigvals(Zb))
    eigY_s = np.sort(eigY)[::-1]
    eigZ_s = np.sort(eigZ)[::-1]
    if eigY_s.size < 2 or eigZ_s.size < 2:
        return float('nan'), None, None
    q = eigY_s[0] * eigZ_s[0]
    d = eigY_s[1] * eigZ_s[1]
    total = math.sqrt((q * q + d * d) / 2.0)
    return total, q, d

def procesar_gsim_escenario(escenario_input_path, escenario_output_path):
    """Processes the GSIM calculation for a specific scenario"""
    escenario_nombre = os.path.basename(escenario_input_path)
    print(f"  🔄 Calculating GSIM for {escenario_nombre}...")
    
    # Build file paths for this scenario
    ruta_positive1 = os.path.join(escenario_input_path, "Positive")
    ruta_positive2 = os.path.join(escenario_output_path, "Positive")
    ruta_datos_gsim = os.path.join(escenario_input_path, "Datos GSIM")
    
    archivos_requeridos = {
        "Zbus": os.path.join(ruta_positive2, "Zbus.csv"),
        "cortocircuito": os.path.join(ruta_positive1, "cortocircuito_trifasico.csv"),
        "pvsys": os.path.join(ruta_datos_gsim, "ieee9bus_pvsys.csv"),
        "transformers": os.path.join(ruta_datos_gsim, "ieee9bus_transformers.csv")
    }
    
    # Verify that all required files exist
    for nombre, ruta in archivos_requeridos.items():
        if not os.path.exists(ruta):
            print(f"  ❌ No se encuentra {nombre}: {ruta}")
            return False
    
    print("  ✅ All required files for GSIM found")
    
    try:
        # Load data
        Zbus_df = pd.read_csv(archivos_requeridos["Zbus"])
        cc_df = pd.read_csv(archivos_requeridos["cortocircuito"], sep=';')
        cc_df.columns = cc_df.columns.str.strip().str.replace('\xa0', ' ', regex=True)
        pvs_df = pd.read_csv(archivos_requeridos["pvsys"])
        trafo_df = pd.read_csv(archivos_requeridos["transformers"])
        
        print(f"  📊 Data loaded: {len(pvs_df)} PVs, {len(trafo_df)} transformaers")
        
        # Process each PV
        results = []
        for i, row in pvs_df.iterrows():
            bus_str = str(row.get("bus", ""))
            p_raw = row.get("p", 1.0)
            
            try:
                p_val = float(p_raw)
                P_MW = p_val / 1000.0 if p_val > 100 else p_val
            except:
                P_MW = 1.0

            # === CALCULATION AT LV (LOW VOLTAGE) ===
            match_lv = cc_df[cc_df["Nodo"].astype(str).str.contains(bus_str, case=False, regex=False)]
            if match_lv.empty:
                print(f"  ⚠ S_sc LV not found for bus {bus_str}")
                continue
                
            S_sc_LV = float(str(match_lv.iloc[0]["Potencia Cortocircuito Skss [MVA]"]).replace(',', '.'))
            SCR_LV = S_sc_LV / P_MW
            Zth_mag_LV = (V_LV**2) / (S_sc_LV * 1e6)
            R_th_LV = Zth_mag_LV / math.sqrt(1 + X_R_SYS**2)
            X_th_LV = X_R_SYS * R_th_LV
            L_th_LV = X_th_LV / (2 * pi * FN)
            Zsys_lv = Z_dq_from_RL(R_th_LV, L_th_LV)
            Yg_lv = np.linalg.inv(Zsys_lv)
            Rb, Lb = Zb_from_power_with_filter_simple(P_MW, V_LV, X_R_CONV, FN)
            Zb_lv = Z_dq_from_RL(Rb, Lb)
            GSIM_lv, q_lv, d_lv = GSIM_from_Y_and_Z(Yg_lv, Zb_lv)

            # === CALCULATION AT HV (HIGH VOLTAGE) ===
            trafo_match = trafo_df[
                (trafo_df["from_bus"].astype(str).str.contains(bus_str, case=False, regex=False)) |
                (trafo_df["to_bus"].astype(str).str.contains(bus_str, case=False, regex=False))
            ]
            if trafo_match.empty:
                print(f"  ⚠ No transformer found for bus {bus_str}")
                continue

            tr = trafo_match.iloc[0]
            hv_bus = str(tr["from_bus"]).strip() if bus_str.lower() in str(tr["to_bus"]).lower() else str(tr["to_bus"]).strip()

            match_hv = cc_df[cc_df["Nodo"].astype(str).str.contains(hv_bus, case=False, regex=False)]
            if match_hv.empty:
                print(f"  ⚠ S_sc HV not found for bus {hv_bus}")
                continue
                
            S_sc_HV = float(str(match_hv.iloc[0]["Potencia Cortocircuito Skss [MVA]"]).replace(',', '.'))
            SCR_HV = S_sc_HV / P_MW

            # Recalculate completely based on HV
            Zth_mag_HV = (V_HV**2) / (S_sc_HV * 1e6)
            R_th_HV = Zth_mag_HV / math.sqrt(1 + X_R_SYS**2)
            X_th_HV = X_R_SYS * R_th_HV
            L_th_HV = X_th_HV / (2 * pi * FN)
            Zsys_hv = Z_dq_from_RL(R_th_HV, L_th_HV)
            Yg_hv = np.linalg.inv(Zsys_hv)
            Zb_hv = Zb_lv * (V_HV / V_LV)**2
            GSIM_hv, q_hv, d_hv = GSIM_from_Y_and_Z(Yg_hv, Zb_hv)

            # Save results
            results.append({
                "escenario": escenario_nombre,
                "bus": bus_str,
                "P_MW": P_MW,
                "S_sc_LV": S_sc_LV,
                "S_sc_HV": S_sc_HV,
                "SCR_LV": SCR_LV,
                "SCR_HV": SCR_HV,
                "GSIM_lv": GSIM_lv,
                "GSIM_hv": GSIM_hv,
                "q_lv": q_lv, 
                "d_lv": d_lv,
                "q_hv": q_hv, 
                "d_hv": d_hv,
                "transformador": tr["name"]
            })

        # Save GSIM results
        if results:
            out_df = pd.DataFrame(results)
            output_path = os.path.join(escenario_output_path, "GSIM_results.csv")
            out_df.to_csv(output_path, index=False)
            print(f"  ✅ Calculated GSIM: {len(results)} Processed PVs")
            print(f"  💾 Results saved in: {output_path}")
            return True
        else:
            print("  ❌ No GSIM results were generated for this scenario")
            return False
            
    except Exception as e:
        print(f"  ❌ Error calculating GSIM for {escenario_nombre}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# =============================================================================
# BLOCK 5: FUNCTIONS FOR NRSCR CALCULATION
# =============================================================================

def safe_complex(val):
    """Robust function for converting complex strings into actual complex numbers"""
    try:
        val = str(val).replace(" ", "").replace("i", "j")
        match = re.match(r"([-+]?[0-9.]+)?\+?j([-+]?[0-9.]+)", val)
        if match:
            real = float(match.group(1)) if match.group(1) else 0.0
            imag = float(match.group(2))
            return complex(real, imag)
        else:
            return complex(val)
    except:
        return np.nan

def split_Ybus(Ybus, sync_nodes, ibr_nodes):
    """Divide the Ybus matrix into submatrices"""
    Ygg = Ybus[np.ix_(sync_nodes, sync_nodes)]
    Ygl = Ybus[np.ix_(sync_nodes, ibr_nodes)]
    Ylg = Ybus[np.ix_(ibr_nodes, sync_nodes)]
    Yll = Ybus[np.ix_(ibr_nodes, ibr_nodes)]
    return Ygg, Ygl, Ylg, Yll

def procesar_nrscr_escenario(escenario_input_path, escenario_output_path):
    """Calculate NRSCR for a specific scenario"""
    escenario_nombre = os.path.basename(escenario_input_path)
    print(f"  🔄 Calculating NRSCR for {escenario_nombre}...")
    
    # Build file paths for this scenario
    ruta_positive = os.path.join(escenario_input_path, "Positive")
    ruta_sdscr_info = os.path.join(escenario_input_path, "SDSCR INFO")
    
    archivos_requeridos = {
        "Ybus": os.path.join(ruta_positive, "Ybus_export.csv"),
        "potencias": os.path.join(ruta_positive, "potencias_activas_generadores.csv"),
        "cortocircuito": os.path.join(ruta_positive, "cortocircuito_trifasico.csv"),
        "transformers": os.path.join(ruta_sdscr_info, "transformers.csv")
    }
    
    # Verify that all required files exist
    for nombre, ruta in archivos_requeridos.items():
        if not os.path.exists(ruta):
            print(f"  ❌ Not found {nombre}: {ruta}")
            return False
    
    print("  ✅ All required files for NRSCR found")
    
    try:
        # ========== 1. INITIAL READING AND CONFIGURATION ==========
        df = pd.read_csv(archivos_requeridos["Ybus"], index_col=0)
        
        # Apply complex-number conversion
        Ybus = df.map(safe_complex).values

        # Create mapping from bus names to indices
        bus_names = df.index.tolist()
        bus_to_index = {name: idx for idx, name in enumerate(bus_names)}
        index_to_bus = {idx: name for name, idx in bus_to_index.items()}

        print(f"  📊 Bus mapping: {len(bus_to_index)} bus")

        # ========== 2. NODE IDENTIFICATION ==========
        transformers_df = pd.read_csv(archivos_requeridos["transformers"])
        pot_df = pd.read_csv(archivos_requeridos["potencias"], sep=";")
        pot_df.columns = pot_df.columns.str.strip()
        
        col_nodo = "Nodo Conectado"
        col_tipo = "Tipo"
        col_potencia = "Potencia Activa pgini [MW]"

        # Clean node and power values
        pot_df[col_nodo] = pot_df[col_nodo].str.strip()

        # Identify synchronous nodes
        sync_nodes_names = pot_df[pot_df[col_tipo] == "ElmSym"][col_nodo].tolist()
        sync_nodes = [bus_to_index[name] for name in sync_nodes_names if name in bus_to_index]

        # Identify IBR nodes (transformer low-voltage side)
        ibr_nodes_names = pot_df[pot_df[col_tipo].isin(["ElmGenstat", "ElmPvsys"])][col_nodo].tolist()
        ibr_nodes = [bus_to_index[name] for name in ibr_nodes_names if name in bus_to_index]

        print(f"  🔌 Synchronous nodes: {len(sync_nodes)}")
        print(f"  🔌 IBR Nodes (low): {len(ibr_nodes)}")

        # Identify HV nodes of IBR transformers
        high_voltage_nodes = []
        ibr_to_hv_map = {}

        for _, transformer in transformers_df.iterrows():
            lv_node = transformer['lv_node'].strip()
            hv_node = transformer['hv_node'].strip()
            name = transformer['name'].strip()
            
            if 'PV' in name or any(ibr_name in lv_node for ibr_name in ibr_nodes_names):
                if hv_node in bus_to_index and lv_node in bus_to_index:
                    hv_index = bus_to_index[hv_node]
                    lv_index = bus_to_index[lv_node]
                    high_voltage_nodes.append(hv_index)
                    ibr_to_hv_map[lv_index] = hv_index

        print(f"  🔌 IBR transformer energization nodes: {len(high_voltage_nodes)}")

        # ========== 3. NRSCR CALCULATION ==========
        def calcular_nrscr_en_alta(Ybus, pot_df, corto_df, sync_nodes, ibr_nodes, ibr_to_hv_map, 
                                  col_nodo="Nodo Conectado", col_tipo="Tipo", 
                                  col_potencia="Potencia Activa pgini [MW]",
                                  col_nodo_corto="Nodo", col_scc="Potencia Cortocircuito Skss [MVA]"):
            """Calcula el NRSCR para todos los nodos IBR en el lado de alta"""
            resultados = []

            for nodo_ibr in ibr_nodes:
                if nodo_ibr not in ibr_to_hv_map:
                    print(f"  ⚠ Nodo IBR {nodo_ibr} ({index_to_bus[nodo_ibr]}) no tiene nodo de alta asociado")
                    continue
                    
                nodo_alta = ibr_to_hv_map[nodo_ibr]
                
                # Create new lists with the HV node as synchronous
                sync_mod = sync_nodes + [nodo_alta]
                ibr_mod = [n for n in ibr_nodes if n != nodo_ibr]

                # Recalculate submatrices
                Ygg, Ygl, Ylg, Yll = split_Ybus(Ybus, sync_mod, ibr_mod)

                if Yll.shape[0] == 0:
                    print(f"  ⚠ Nodo {nodo_ibr}: Yll vacía. Saltando.")
                    continue
                    
                if Yll.shape[0] != Yll.shape[1]:
                    print(f"  ⚠ Nodo {nodo_ibr}: Yll no es cuadrada ({Yll.shape}). Saltando.")
                    continue

                try:
                    # Calculate Flg
                    Flg = np.linalg.inv(-Yll) @ Ylg
                except np.linalg.LinAlgError:
                    print(f"  ⚠ Node {nodo_ibr}: Yll non-invertible. Skipping.")
                    continue

                # Get active powers of modified synchronous nodes
                pot_sync_mod = []
                for n in sync_mod:
                    bus_name = index_to_bus[n]
                    potencia = pot_df.loc[pot_df[col_nodo] == bus_name, col_potencia]
                    if not potencia.empty:
                        pot_val = float(str(potencia.values[0]).replace(",", "."))
                        pot_sync_mod.append(pot_val)
                    else:
                        pot_sync_mod.append(0.0)

                # Calculate Pdg matrix
                Pdg = Flg * np.array(pot_sync_mod)[np.newaxis, :]

                # Index of the column associated with the HV node
                col_idx = len(sync_mod) - 1

                # Active power of the IBR node (low-voltage side)
                bus_name_ibr = index_to_bus[nodo_ibr]
                P_dg_i = pot_df.loc[pot_df[col_nodo] == bus_name_ibr, col_potencia]
                if P_dg_i.empty:
                    print(f"  ⚠ No power found for IBR node {bus_name_ibr}")
                    continue
                    
                P_dg_i = float(str(P_dg_i.values[0]).replace(",", "."))

                # Sum of contributions (excluding self-contribution)
                columna_contrib = np.abs(Pdg[:, col_idx])
                suma_contrib = np.sum(columna_contrib)

                # Find short-circuit power at the HV node
                bus_name_alta = index_to_bus[nodo_alta]
                corto_df.columns = corto_df.columns.str.strip()
                fila_scc = corto_df[corto_df[col_nodo_corto] == bus_name_alta]
                if fila_scc.empty:
                    print(f"  ⚠ No SCC found for high node {bus_name_alta}")
                    continue

                S_scc_i = float(str(fila_scc[col_scc].values[0]).replace(",", "."))

                # Calculate NRSCR
                NRSCR_i = S_scc_i / (P_dg_i + suma_contrib)
                
                # Also calculate traditional SCR for comparison
                SCR_i = S_scc_i / P_dg_i

                resultados.append({
                    'nodo_ibr': nodo_ibr,
                    'nodo_ibr_name': bus_name_ibr,
                    'nodo_alta': nodo_alta,
                    'nodo_alta_name': bus_name_alta,
                    'nrscr': NRSCR_i,
                    'scr': SCR_i,
                    'scc': S_scc_i,
                    'potencia': P_dg_i,
                    'contribuciones': suma_contrib
                })

            return resultados

        # ========== 4. EXECUTION AND RESULTS ==========
        corto_df = pd.read_csv(archivos_requeridos["cortocircuito"], sep=";")
        corto_df.columns = corto_df.columns.str.strip()

        # Calculate NRSCR on the HV side
        resultados = calcular_nrscr_en_alta(Ybus, pot_df, corto_df, sync_nodes, ibr_nodes, ibr_to_hv_map)

        # Display results
        print(f"\n  📊 NRSCR Results - {escenario_nombre}")
        print(f"  {'Nodo IBR':<12} {'Nodo Alta':<12} {'P [MW]':<8} {'SCC [MVA]':<10} {'Contrib.':<10} {'NRSCR':<8} {'SCR':<8}")
        print(f"  {'-'*70}")

        for res in resultados:
            print(f"  {res['nodo_ibr_name']:<12} {res['nodo_alta_name']:<12} "
                  f"{res['potencia']:<8.2f} {res['scc']:<10.2f} "
                  f"{res['contribuciones']:<10.2f} {res['nrscr']:<8.2f} "
                  f"{res['scr']:<8.2f}")

        # ========== 5. SAVE RESULTS ==========
        if resultados:
            # Create ordered and complete DataFrame
            data = []
            for res in resultados:
                diferencia = res['scr'] - res['nrscr']
                data.append({
                    "Nodo IBR": res['nodo_ibr_name'],
                    "Nodo Alta": res['nodo_alta_name'],
                    "P [MW]": round(res['potencia'], 2),
                    "SCC [MVA]": round(res['scc'], 2),
                    "Contrib.": round(res['contribuciones'], 2),
                    "NRSCR": round(res['nrscr'], 2),
                    "SCR": round(res['scr'], 2),
                    "Diferencia": round(diferencia, 2)
                })

            out_df = pd.DataFrame(data, columns=["Nodo IBR", "Nodo Alta", "P [MW]", "SCC [MVA]", "Contrib.", "NRSCR", "SCR", "Diferencia"])

            # Save to CSV
            output_path = os.path.join(escenario_output_path, "NRSCR_results.csv")
            out_df.to_csv(output_path, index=False, encoding="utf-8-sig")

            # Statistical analysis
            if resultados:
                nrscr_values = [res['nrscr'] for res in resultados]
                scr_values = [res['scr'] for res in resultados]
                
                print(f"\n  📈 STATISTICAL ANALYSIS:")
                print(f"     Average NRSCR: {np.mean(nrscr_values):.2f}")
                print(f"     Average SCR: {np.mean(scr_values):.2f}")
                print(f"     Percentage reduction: {(1 - np.mean(nrscr_values)/np.mean(scr_values))*100:.1f}%")
                
                # Grid strength classification
                fuerte = sum(1 for x in nrscr_values if x >= 3.0)
                debil = sum(1 for x in nrscr_values if 1.5 <= x < 3.0)
                muy_debil = sum(1 for x in nrscr_values if x < 1.5)
                
                print(f"     🔋 Strong system (NRSCR ≥ 3.0): {fuerte} nodes")
                print(f"     ⚠️  Weak system (1.5 ≤ NRSCR < 3.0): {debil} nodes")
                print(f"     ❌ Very weak system (NRSCR < 1.5): {muy_debil} nodes")

            print(f"  💾 NRSCR results saved in: {output_path}")
            return True
        else:
            print("  ❌ No NRSCR results were generated for this scenario")
            return False
            
    except Exception as e:
        print(f"  ❌ Error calculating NRSCR for {escenario_nombre}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# =============================================================================
# BLOCK 6: FUNCTIONS FOR LSCR CALCULATION
# =============================================================================

def parse_complex_safe(val):
    """Robust function for converting complex strings to complex numbers"""
    if isinstance(val, str):
        val = val.replace(" ", "")
        match = re.match(r"([-+]?[0-9]*\.?[0-9]+)\+j([-+]?[0-9]*\.?[0-9]+)", val)
        if match:
            real, imag = match.groups()
            return complex(float(real), float(imag))
        else:
            return np.nan
    return val

def procesar_lscr_escenario(escenario_input_path, escenario_output_path):
    """Calculate the LSCR for a specific scenario"""
    escenario_nombre = os.path.basename(escenario_input_path)
    print(f"  🔄 Calculating LSCR for {escenario_nombre}...")
    
    # Build file paths for this scenario
    ruta_positive = os.path.join(escenario_input_path, "Positive")
    ruta_sdscr_info = os.path.join(escenario_input_path, "SDSCR INFO")
    ruta_ZPython_info = os.path.join(escenario_input_path, "ExportZ_Python")
    
    archivos_requeridos = {
        "Ybus": os.path.join(ruta_positive, "Ybus_export.csv"),
        "generadores": os.path.join(ruta_ZPython_info, "info_generadores_con_Zdevice.csv"),
        "cargas": os.path.join(ruta_ZPython_info, "info_cargas.csv"),
        "transformers": os.path.join(ruta_sdscr_info, "transformers.csv")
    }
    
    # Verify that all required files exist
    for nombre, ruta in archivos_requeridos.items():
        if not os.path.exists(ruta):
            print(f"  ❌ Not found {nombre}: {ruta}")
            return False
    
    print("  ✅ All required files for LSCR found")
    
    try:
        # ========== 1. INITIAL READING AND CONFIGURATION ==========
        ybus_df = pd.read_csv(archivos_requeridos["Ybus"])
        if 'Bus' in ybus_df.columns:
            ybus_df.set_index('Bus', inplace=True)

        Ybus_complex = ybus_df.map(parse_complex_safe).to_numpy()
        buses = ybus_df.index.tolist()

        gen_df = pd.read_csv(archivos_requeridos["generadores"], delimiter=";")
        load_df = pd.read_csv(archivos_requeridos["cargas"], delimiter=";")
        transformers_df = pd.read_csv(archivos_requeridos["transformers"])

        # --- Create IBR transformer mapping (low-voltage side -> high-voltage side) ---
        ibr_transformer_map = {}
        for _, transformer in transformers_df.iterrows():
            name = transformer['name'].strip()
            hv_node = transformer['hv_node'].strip()
            lv_node = transformer['lv_node'].strip()
            
            # Find transformers connecting IBRs (based on LV node names)
            if 'PV' in lv_node or 'LV' in lv_node:
                ibr_transformer_map[lv_node] = hv_node
                print(f"  🔌 Transformer found: {name} - {lv_node} -> {hv_node}")

        # --- Advanced generator classification ---
        gen_df['Tipo'] = gen_df['Tipo'].str.strip()
        gen_df['TipoControl'] = gen_df['TipoControl'].str.strip()

        # Identify slack buses (Vθ)
        slack_buses = gen_df[(gen_df['Tipo'] == "ElmSym") & 
                            (gen_df['TipoControl'] == "Vtheta")]['Nodo Conectado'].str.strip().tolist()

        # Identify PV buses (synchronous)
        pv_sync_buses = gen_df[(gen_df['Tipo'] == "ElmSym") & 
                              (gen_df['TipoControl'] == "PV")]['Nodo Conectado'].str.strip().tolist()

        # Identify IBRs (PVsys)
        ibr_buses = gen_df[gen_df['Tipo'] == "ElmPvsys"]['Nodo Conectado'].str.strip().tolist()

        # --- Index mapping ---
        bus_to_index = {bus.strip(): i for i, bus in enumerate(buses)}

        # --- Function to calculate Zth at a bus ---
        def calculate_zth(bus_name, state='normal'):
            """
            Calculate the Thevenin impedance for a specific bus
            state: 'normal' or 'fault'
            """
            bus_idx = bus_to_index[bus_name]
            
            # Create reduced Ybus matrix
            # For normal state, IBRs are modeled as voltage sources (short circuit)
            # For fault state, IBRs are modeled as current sources (open circuit)
            
            # Identify nodes to retain
            keep_nodes = []
            for i, bus in enumerate(buses):
                bus = bus.strip()
                if bus == bus_name:
                    continue  # Remove the bus of interest
                    
                if bus in ibr_buses:
                    if state == 'normal':
                        # In normal state, IBRs are voltage sources (remove from Ybus)
                        continue
                    # In fault state, IBRs are current sources (keep in Ybus)
                
                keep_nodes.append(i)
            
            Yred = Ybus_complex[np.ix_(keep_nodes, keep_nodes)]
            
            # Calculate Zth as the equivalent impedance seen from the bus
            try:
                Yth = Ybus_complex[bus_idx, bus_idx] - (
                    Ybus_complex[bus_idx, keep_nodes] @ 
                    inv(Yred) @ 
                    Ybus_complex[keep_nodes, bus_idx]
                )
                return 1/Yth
            except:
                return np.inf

        # --- Function to calculate K_vtg ---
        def calculate_kvtg(bus_name, z_device, state='normal'):
            zth = calculate_zth(bus_name, state)
            if zth == np.inf:
                return 0
            return abs(z_device / (zth + z_device))

        # --- Function to calculate λSCR ---
        def calculate_lambda_scr(bus_name, z_device, state='normal'):
            zth = calculate_zth(bus_name, state)
            if zth == np.inf:
                return 0
            return abs(z_device / zth)

        # ========== 2. MAIN CALCULATIONS ==========
        results = []
        for _, gen in gen_df.iterrows():
            bus_name = gen['Nodo Conectado'].strip()
            if bus_name not in bus_to_index:
                continue
                
            z_device = float(str(gen['Zdevice [Ohm aprox.]']).replace(",", "."))*VarTen*Xfil
            z_devicepu = z_device/((VbL**2)/SbL)
            
            # Determine the bus where grid strength is calculated
            calculation_bus = bus_name
            
            # For IBRs, use the high-voltage side of the transformer if available
            if gen['Tipo'] == 'ElmPvsys' and bus_name in ibr_transformer_map:
                calculation_bus = ibr_transformer_map[bus_name]
                print(f"  🔌 IBR {gen['Nombre']} calculating on the high-voltage side: {bus_name} -> {calculation_bus}")
            
            # Calculate for normal state
            k_vtg_normal = calculate_kvtg(calculation_bus, z_devicepu, 'normal')
            lambda_scr_normal = calculate_lambda_scr(calculation_bus, z_devicepu, 'normal')
            
            # Calculate for fault state
            k_vtg_fault = calculate_kvtg(calculation_bus, z_devicepu, 'fault')
            lambda_scr_fault = calculate_lambda_scr(calculation_bus, z_devicepu, 'fault')
            
            results.append({
                'Generador': gen['Nombre'],
                'Barra Conexión': bus_name,
                'Barra Cálculo': calculation_bus,
                'Tipo': gen['Tipo'],
                'Control': gen['TipoControl'],
                'Z_device': z_device,
                'K_vtg_normal': k_vtg_normal,
                'λSCR_normal': lambda_scr_normal,
                'K_vtg_fault': k_vtg_fault,
                'λSCR_fault': lambda_scr_fault
            })

        # ========== 3. DISPLAY AND SAVE RESULTS ==========
        results_df = pd.DataFrame(results)
        print(f"\n  📊 LSCR RESULTS - {escenario_nombre}")
        print(f"  {'='*80}")
        print(results_df.to_string(index=False))

        # --- Complete system analysis ---
        print(f"\n  📈 Analysis of the complete system")
        print(f"  {'='*60}")
        print(f"    Slack bars (Vθ): {slack_buses}")
        print(f"    Synchronous PV busbars: {pv_sync_buses}")
        print(f"    IBR Bars (PVsys): {ibr_buses}")

        # Calculate synchronous vs. non-synchronous generation ratio
        total_sync = gen_df[gen_df['Tipo'] == 'ElmSym']['pgini [MW]'].sum()
        total_ibr = gen_df[gen_df['Tipo'] == 'ElmPvsys']['pgini [MW]'].sum()
        if total_ibr > 0:
            print(f"    Synchronous/non-synchronous generation ratio: {total_sync/total_ibr:.2f}")
        else:
            print(f"    There is no non-synchronous generation (IBR)")

        # Save to CSV
        output_path = os.path.join(escenario_output_path, "LSCR_results.csv")
        results_df.to_csv(output_path, index=False, encoding="utf-8-sig")

        print(f"\n  💾 LSCR results saved in: {output_path}")
        return True
        
    except Exception as e:
        print(f"  ❌ Error calculating LSCR for {escenario_nombre}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# =============================================================================
# BLOCK 7: FUNCTIONS FOR SDSCR CALCULATION
# =============================================================================

import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
import re

# ==================== AUXILIARY FUNCTIONS ====================

def parse_complex(x):
    """Converts text in the format 'a+bj' or 'a+j b' into a complex number."""
    if not isinstance(x, str):
        return complex(x)
    s = x.strip().lower().replace(' ', '')
    s = s.replace('+-', '-')
    s = s.replace('++', '+')
    s = s.replace('j', 'j')
    s = s.replace('–', '-')  # em dash
    try:
        if 'j' not in s:
            if '+' in s or '-' in s[1:]:
                s += 'j'
            else:
                s = s + '+0j'
        return complex(s)
    except Exception:
        #print(f"❌ Could not parse: {x}")
        return complex(0)

def norm_name(name):
    """Normalizes node names (removes spaces, uppercase letters, etc.)."""
    return str(name).strip().upper()


# ==================== MAIN CLASS ====================

class SDSCRAnalyzer:
    def __init__(self, data_folder):
        self.data_folder = data_folder
        self.base_mva = 100.0
        self.buses = pd.read_csv(f"{data_folder}/buses.csv")
        self.generators = pd.read_csv(f"{data_folder}/generators.csv")
        self.renewables = pd.read_csv(f"{data_folder}/renewables.csv")
        self.branches = pd.read_csv(f"{data_folder}/branches.csv")
        self.loads = pd.read_csv(f"{data_folder}/loads.csv")
        self.transformers = pd.read_csv(f"{data_folder}/transformers.csv")
        self.short_circuit_data = self._load_short_circuit_data()
        self.Ybus, self.Zbus = self._load_matrices_from_csv()
        self.bus_names = self.buses['name'].apply(norm_name).values
        self.bus_indices = {name: idx for idx, name in enumerate(self.bus_names)}
        self._verify_base_and_data()

    # -------------------- DATA LOADING --------------------

    def _load_short_circuit_data(self):
        try:
            scc_data = pd.read_csv(f"{self.data_folder}/cortocircuito_trifasico.csv", sep=';', decimal=',')
            scc_data.columns = scc_data.columns.str.strip()
            scc_dict = {}
            for _, row in scc_data.iterrows():
                bus = norm_name(row['Nodo'])
                scc_dict[bus] = {
                    'Ikss_kA': row['Corriente Cortocircuito Ikss [kA]'],
                    'Skss_MVA': row['Potencia Cortocircuito Skss [MVA]']
                }
            print("✅ Short circuit data loaded successfully")
            print("Short circuit keys:", list(scc_dict.keys()))
            return scc_dict
        except Exception as e:
            print(f"❌ Error loading SCC data: {e}")
            return {}

    def _load_matrices_from_csv(self):
        try:
            Ybus_df = pd.read_csv(f"{self.data_folder}/Ybus_export.csv", index_col=0)
            Zbus_df = pd.read_csv(f"{self.data_folder}/Zbus.csv", index_col=0)
            Ybus = Ybus_df.map(parse_complex).to_numpy()
            Zbus = Zbus_df.map(parse_complex).to_numpy()
            print("✅ Ybus and Zbus loaded successfully from CSV files")
            return csr_matrix(Ybus), csr_matrix(Zbus)
        except Exception as e:
            print(f"❌ Error loading matrices: {e}")
            n = len(self.buses)
            return csr_matrix(np.eye(n, dtype=complex)), csr_matrix(np.eye(n, dtype=complex))

    # -------------------- VALIDATION --------------------

    def _verify_base_and_data(self):
        """Verify the consistency of Zbus with short-circuit data."""
        Zbus_dense = self.Zbus.toarray()
        scc_calc = []
        for i, bus in enumerate(self.bus_names):
            Zii = Zbus_dense[i, i]
            if abs(Zii) < 1e-9:
                continue
            V = self.buses.iloc[i]['vm_pu']
            S_calc = (V ** 2 / abs(Zii)) * self.base_mva
            if bus in self.short_circuit_data:
                S_real = self.short_circuit_data[bus]['Skss_MVA']
                scc_calc.append((S_calc, S_real))
        if not scc_calc:
            return
        ratio = np.median([r / t for r, t in scc_calc if t > 0])
        if abs(ratio - 1) > 0.1:
            print(f"⚠️ Adjusting base_mva: {self.base_mva:.2f} → {self.base_mva/ratio:.2f} (scale={1/ratio:.3f})")
            self.base_mva /= ratio

        print("\n" + "=" * 100)
        print("VERIFICATION: CALCULATED vs ACTUAL SHORT CIRCUIT DATA")
        print("=" * 100)
        for i, bus in enumerate(self.bus_names):
            Zii = Zbus_dense[i, i]
            if abs(Zii) < 1e-9:
                continue
            V = self.buses.iloc[i]['vm_pu']
            S_calc = (V ** 2 / abs(Zii)) * self.base_mva
            if bus in self.short_circuit_data:
                S_real = self.short_circuit_data[bus]['Skss_MVA']
                err = abs(S_calc - S_real) / S_real * 100
                print(f"{bus:6s}: Calc = {S_calc:10.1f} MVA, Real = {S_real:10.1f} MVA, Error = {err:6.1f}%")
        print("=" * 100)

    # -------------------- CALCULATION FUNCTIONS --------------------

    def get_scc(self, bus_name):
        bus = norm_name(bus_name)
        if bus in self.short_circuit_data:
            return self.short_circuit_data[bus]['Skss_MVA']
        idx = self.bus_indices.get(bus)
        if idx is None:
            return np.nan
        Zii = self.Zbus[idx, idx]
        V = self.buses.iloc[idx]['vm_pu']
        return (V ** 2 / abs(Zii)) * self.base_mva

    def calculate_scr(self, bus_name):
        """SCR clásic."""
        bus = norm_name(bus_name)
        SCC = self.get_scc(bus)
        total_p = 0.0
        gens = self.generators[self.generators['bus'].apply(norm_name) == bus]
        total_p += gens['pg_mw'].sum()
        for _, tr in self.transformers.iterrows():
            if norm_name(tr['hv_node']) == bus:
                lv = norm_name(tr['lv_node'])
                ren = self.renewables[self.renewables['bus'].apply(norm_name) == lv]
                total_p += ren['pg_mw'].sum()
        if total_p < 1e-6:
            return float('inf')
        return SCC / total_p

    def calculate_sdscr(self, bus_name, debug=False):
        """
        SDSCR with coupling (paper version)
        """
        bus = norm_name(bus_name)
        SCC_mva = self.get_scc(bus)
        idx = self.bus_indices.get(bus)
        if idx is None:
            return float('inf')

        Zii = self.Zbus[idx, idx]
        Vi = self.buses.iloc[idx]['vm_pu']

        # HV nodes with renewables
        ren_hv_nodes = []
        for _, tr in self.transformers.iterrows():
            if norm_name(tr['lv_node']) in self.renewables['bus'].apply(norm_name).values:
                ren_hv_nodes.append(norm_name(tr['hv_node']))
        ren_hv_nodes = list(dict.fromkeys(ren_hv_nodes))

        # PR powers
        PR = {}
        for hv in ren_hv_nodes:
            p = 0.0
            for _, tr in self.transformers.iterrows():
                if norm_name(tr['hv_node']) == hv:
                    lv = norm_name(tr['lv_node'])
                    ren = self.renewables[self.renewables['bus'].apply(norm_name) == lv]
                    p += ren['pg_mw'].sum() if not ren.empty else 0.0
            PR[hv] = p

        P_Ri = PR.get(bus, 0.0)
        denom = P_Ri + 0j
        for other in ren_hv_nodes:
            if other == bus:
                continue
            other_idx = self.bus_indices.get(other)
            if other_idx is None:
                continue
            Zij = self.Zbus[idx, other_idx]
            Zratio = Zij / Zii if abs(Zii) > 1e-9 else 0+0j
            Vj = self.buses.iloc[other_idx]['vm_pu']
            Vratio_conj = np.conj(Vi / Vj) if abs(Vj) > 1e-9 else 1.0
            wB = Zratio * Vratio_conj
            denom += PR.get(other, 0.0) * wB

        denom_mw = abs(denom)
        SDSCR = SCC_mva / denom_mw if denom_mw > 1e-9 else float('inf')

        if debug:
            print(f"SDSCR (acoplado) @ {bus}: denom={denom_mw:.4f}, SCC={SCC_mva:.2f}, SDSCR={SDSCR:.3f}")

        return SDSCR

    def calculate_sdscr_no_coupling(self, bus_name, debug=False):
        """
        SDSCR without coupling between non-synchronous generators.
        """
        bus = norm_name(bus_name)
        SCC_mva = self.get_scc(bus)
        P_Ri = 0.0
        for _, tr in self.transformers.iterrows():
            if norm_name(tr['hv_node']) == bus:
                lv = norm_name(tr['lv_node'])
                ren = self.renewables[self.renewables['bus'].apply(norm_name) == lv]
                P_Ri += ren['pg_mw'].sum() if not ren.empty else 0.0
        if P_Ri < 1e-6:
            return float('inf')
        SDSCR_nc = SCC_mva / P_Ri
        if debug:
            print(f"SDSCR (no coupling) @ {bus}: SCC={SCC_mva:.3f}/P={P_Ri:.3f}→{SDSCR_nc:.3f}")
        return SDSCR_nc

    def _classify_strength(self, val):
        if np.isinf(val):
            return "Infinite"
        elif val > 3:
            return "Strong"
        elif val >= 2:
            return "Weak"
        elif val >= 1:
            return "Very Weak"
        else:
            return "Unstable"

    # -------------------- GENERAL ANALYSIS --------------------

    def analyze_system_strength(self):
        """Compare SCR, SDSCR (coupled), and uncoupled SDSCR"""
        conn_points = set()
        for _, tr in self.transformers.iterrows():
            if norm_name(tr['lv_node']) in self.renewables['bus'].apply(norm_name).values:
                conn_points.add(norm_name(tr['hv_node']))

        gen_buses = set(self.generators['bus'].apply(norm_name).unique())
        all_points = conn_points.union(gen_buses)

        results = []
        for bus in all_points:
            try:
                scr = self.calculate_scr(bus)
                sdscr_cpl = self.calculate_sdscr(bus)
                sdscr_nc = self.calculate_sdscr_no_coupling(bus)
                SCC = self.get_scc(bus)

                strength = self._classify_strength(sdscr_cpl)

                results.append({
                    'Bus': bus,
                    'SCR': scr,
                    'SDSCR_coupled': sdscr_cpl,
                    'SDSCR_no_coupling': sdscr_nc,
                    'Strength': strength,
                    'SCC (MVA)': SCC
                })
            except Exception as e:
                print(f"⚠️ Error at {bus}: {e}")
                continue

        df = pd.DataFrame(results)
        print("\nSystem Strength Comparison (SCR vs SDSCR):")
        print(df.to_string(index=False))
        df.to_csv(f"{self.data_folder}/SDSCR_results.csv", index=False)
        print(f"\n✅ Results saved to {self.data_folder}/SDSCR_results.csv")
        return df

# =============================================================================
# SCENARIO PROCESSING FUNCTION
# =============================================================================

def procesar_sdscr_escenario(escenario_input_path, escenario_output_path):
    """Calculate SDSCR for a specific scenario using the original code"""
    escenario_nombre = os.path.basename(escenario_input_path)
    print(f"  🔄 Calculating SDSCR for {escenario_nombre}...")
    
    # Build file paths for this scenario
    ruta_positive1 = os.path.join(escenario_input_path, "Positive")
    ruta_positive2 = os.path.join(escenario_output_path, "Positive")
    #print("The Positive SDSCR path is:",ruta_positive)
    ruta_sdscr_info = os.path.join(escenario_input_path, "SDSCR INFO")
    #print("The SDSCR path is:",ruta_sdscr_info)
    
    archivos_requeridos = {
        "buses": os.path.join(ruta_sdscr_info, "buses.csv"),
        "generators": os.path.join(ruta_sdscr_info, "generators.csv"),
        "renewables": os.path.join(ruta_sdscr_info, "renewables.csv"),
        "branches": os.path.join(ruta_sdscr_info, "branches.csv"),
        "loads": os.path.join(ruta_sdscr_info, "loads.csv"),
        "transformers": os.path.join(ruta_sdscr_info, "transformers.csv"),
        "cortocircuito": os.path.join(ruta_positive1, "cortocircuito_trifasico.csv"),
        "Ybus": os.path.join(ruta_positive1, "Ybus_export.csv"),
        "Zbus": os.path.join(ruta_positive2, "Zbus.csv")
    }
    
    # Verify that all required files exist
    for nombre, ruta in archivos_requeridos.items():
        if not os.path.exists(ruta):
            print(f"  ❌ No se encuentra {nombre}: {ruta}")
            return False
    
    print("  ✅ All required files for SDSCR found")
    
    try:
        # Create temporary folder for SDSCR
        temp_sdscr_folder = os.path.join(escenario_output_path, "SDSCR_temp")
        os.makedirs(temp_sdscr_folder, exist_ok=True)
        
        # Copy required files to the temporary folder
        import shutil
        for archivo in ["buses", "generators", "renewables", "branches", "loads", "transformers"]:
            shutil.copy2(archivos_requeridos[archivo], os.path.join(temp_sdscr_folder, f"{archivo}.csv"))
        shutil.copy2(archivos_requeridos["cortocircuito"], os.path.join(temp_sdscr_folder, "cortocircuito_trifasico.csv"))
        shutil.copy2(archivos_requeridos["Ybus"], os.path.join(temp_sdscr_folder, "Ybus_export.csv"))
        shutil.copy2(archivos_requeridos["Zbus"], os.path.join(temp_sdscr_folder, "Zbus.csv"))
        
        # Run SDSCR analysis
        analyzer = SDSCRAnalyzer(data_folder=temp_sdscr_folder)
        results = analyzer.analyze_system_strength()
        
        # Move results to the scenario folder
        temp_results_path = os.path.join(temp_sdscr_folder, "SDSCR_results.csv")
        final_results_path = os.path.join(escenario_output_path, "SDSCR_results.csv")
        
        if os.path.exists(temp_results_path):
            shutil.move(temp_results_path, final_results_path)
        
        # Clean temporary folder
        shutil.rmtree(temp_sdscr_folder)
        
        print(f"  💾 SDSCR results saved in: {final_results_path}")
        return True
        
    except Exception as e:
        print(f"  ❌ Error calculating SDSCR for {escenario_nombre}: {str(e)}")
        import traceback
        traceback.print_exc()
        # Attempt to clean temporary folder in case of error
        try:
            temp_sdscr_folder = os.path.join(escenario_output_path, "SDSCR_temp")
            if os.path.exists(temp_sdscr_folder):
                shutil.rmtree(temp_sdscr_folder)
        except:
            pass
        return False

# =============================================================================
# BLOCK 9: FUNCTION FOR SCR CALCULATION (Short Circuit Ratio)
# =============================================================================

def procesar_scr_escenario(escenario_input_path, escenario_output_path):
    """
    Calculate the Short Circuit Ratio (SCR) using the SCR information files.
    
    SCR = S_cc / P_nom
    
    Where:
    - S_cc: Short-circuit power at the high-voltage node [MVA]
    - P_nom: Rated power of the faulted generator [MW]
    """
    escenario_nombre = os.path.basename(escenario_input_path)
    print(f"  🔄 Calculating SCR for {escenario_nombre}...")
    
    # SCR information file path
    scr_info_folder = os.path.join(escenario_input_path, "Informacion SCR")
    
    # Find SCR information file
    import glob
    archivos_scr = glob.glob(os.path.join(scr_info_folder, "informacion_SCR_*.csv"))
    if not archivos_scr:
        print(f"  ❌ No SCR Information file found in {scr_info_folder}")
        return False
    
    scr_csv_path = archivos_scr[0]
    
    try:
        # Read CSV file
        df = pd.read_csv(scr_csv_path, delimiter=';')
        
        # Convert decimal comma to period for numbers
        for col in ['potencia_cortocircuito_mva', 'potencia_gen1_mw', 'potencia_gen2_mw']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(',', '.').astype(float)
        
        # Calculate SCR for each generator
        resultados = []
        
        for _, row in df.iterrows():
            s_cc = row['potencia_cortocircuito_mva']
            
            # Identify generator power during the fault
            if row['generador_en_falla'] == 'PV1':
                p_gen = row['potencia_gen1_mw']
                generador = 'PV1'
            else:
                p_gen = row['potencia_gen2_mw']
                generador = 'PV2'
            
            # Calculate SCR
            scr = s_cc / p_gen if p_gen > 0 else float('inf')
            
            resultados.append({
                'Escenario': escenario_nombre,
                'Generador': generador,
                'Potencia_Generador_MW': p_gen,
                'Potencia_Cortocircuito_MVA': s_cc,
                'SCR_scr': scr
            })
        
        # Create DataFrame and save results
        if resultados:
            resultados_df = pd.DataFrame(resultados)
            
            # Save results
            output_path = os.path.join(escenario_output_path, "SCR_results.csv")
            resultados_df.to_csv(output_path, index=False, encoding='utf-8-sig')
            
            # Display results in console
            print(f"\n  📊 SCR RESULTS - {escenario_nombre}")
            print(f"  {'='*50}")
            for _, res in resultados_df.iterrows():
                print(f"    🔌 {res['Generador']}: P = {res['Potencia_Generador_MW']:.1f} MW, "
                      f"S_cc = {res['Potencia_Cortocircuito_MVA']:.2f} MVA, "
                      f"SCR = {res['SCR_scr']:.3f}")
            
            print(f"\n  💾 SCR results saved in: {output_path}")
            return True
        else:
            print(f"  ❌ No SCR results were generated for {escenario_nombre}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error calculating SCR for {escenario_nombre}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# =============================================================================
# BLOCK 8: MAIN PROCESSING FUNCTION
# =============================================================================

def procesar_escenario_completo(escenario_input_path, escenario_output_path):
    """Performs all calculations (Zbus, GSIM, NRSCR, LSCR, SDSCR, and SCR) for a scenario"""
    escenario_nombre = os.path.basename(escenario_input_path)
    print(f"\n{'='*60}")
    print(f"🎯 PROCESSING SCENARIO: {escenario_nombre}")
    print(f"{'='*60}")
    
    # Step 1: Calculate Zbus
    zbus_exitoso = calcular_zbus_escenario(escenario_input_path, escenario_output_path)
    
    # Step 2: Calculate GSIM (only if Zbus was successful)
    if zbus_exitoso:
        gsim_exitoso = procesar_gsim_escenario(escenario_input_path, escenario_output_path)
    else:
        gsim_exitoso = False
        print(f"  ⏩ Skipping GSIM due to Zbus failure")
    
    # Step 3: Calculate NRSCR (independent of the previous ones)
    nrscr_exitoso = procesar_nrscr_escenario(escenario_input_path, escenario_output_path)
    
    # Step 4: Calculate LSCR (independent of the previous ones)
    lscr_exitoso = procesar_lscr_escenario(escenario_input_path, escenario_output_path)
    
    # Step 5: Calculate SDSCR (requires Zbus)
    if zbus_exitoso:
        sdscr_exitoso = procesar_sdscr_escenario(escenario_input_path, escenario_output_path)
    else:
        sdscr_exitoso = False
        print(f"  ⏩ Bypassing SDSCR due to Zbus failure")
    
    # Step 6: Calculate SCR (new) - independent of Zbus
    scr_exitoso = procesar_scr_escenario(escenario_input_path, escenario_output_path)
    
    # Step 7: Compile results
    compilacion_exitosa = compilar_resultados_escenario(escenario_output_path)
    
    return (zbus_exitoso, gsim_exitoso, nrscr_exitoso, lscr_exitoso, 
            sdscr_exitoso, scr_exitoso, compilacion_exitosa)

# =============================================================================
# BLOCK 10: RESULTS COMPILATION FOR EACH SCENARIO
# =============================================================================

def compilar_resultados_escenario(escenario_input_path, escenario_output_path):
    """Compiles all results from a scenario into a single CSV file"""
    escenario_nombre = os.path.basename(escenario_input_path)
    print(f"  🔄 Compiling results for {escenario_nombre}...")
    
    # Result file paths
    archivos_resultados = {
        "GSIM": os.path.join(escenario_output_path, "GSIM_results.csv"),
        "NRSCR": os.path.join(escenario_output_path, "NRSCR_results.csv"),
        "SDSCR": os.path.join(escenario_output_path, "SDSCR_results.csv"),
        "LSCR": os.path.join(escenario_output_path, "LSCR_results.csv")
    }
    
    # Check which files exist
    archivos_existentes = {}
    for nombre, ruta in archivos_resultados.items():
        if os.path.exists(ruta):
            archivos_existentes[nombre] = ruta
        else:
            print(f"  ⚠️ Not found {nombre}: {ruta}")
    
    if not archivos_existentes:
        print(f"  ❌ There are no output files to compile in {escenario_nombre}")
        return False
    
    try:
        # Dictionary to store all compiled data
        datos_compilados = []
        
        # ========== PROCESS GSIM ==========
        if "GSIM" in archivos_existentes:
            gsim_df = pd.read_csv(archivos_existentes["GSIM"])
            for _, fila in gsim_df.iterrows():
                bus = fila["bus"]
                datos_compilados.append({
                    "Escenario": escenario_nombre,
                    "Bus": bus,
                    "Metodo": "GSIM",
                    "P_MW": fila["P_MW"],
                    "SCR_LV": fila["SCR_LV"],
                    "SCR_HV": fila["SCR_HV"],
                    "GSIM_LV": fila["GSIM_lv"],
                    "GSIM_HV": fila["GSIM_hv"],
                    "Valor_Principal": fila["GSIM_hv"],  # Use HV as the main value
                    "q_LV": fila["q_lv"],
                    "d_LV": fila["d_lv"],
                    "q_HV": fila["q_hv"],
                    "d_HV": fila["d_hv"],
                    "S_sc_LV": fila["S_sc_LV"],
                    "S_sc_HV": fila["S_sc_HV"],
                    "Transformador": fila["transformador"]
                })
        
        # ========== PROCESS NRSCR ==========
        if "NRSCR" in archivos_existentes:
            nrscr_df = pd.read_csv(archivos_existentes["NRSCR"])
            for _, fila in nrscr_df.iterrows():
                bus_ibr = fila["Nodo IBR"]
                datos_compilados.append({
                    "Escenario": escenario_nombre,
                    "Bus": bus_ibr,
                    "Metodo": "NRSCR",
                    "P_MW": fila["P [MW]"],
                    "SCR": fila["SCR"],
                    "NRSCR": fila["NRSCR"],
                    "Valor_Principal": fila["NRSCR"],
                    "SCC_MVA": fila["SCC [MVA]"],
                    "Contribuciones": fila["Contrib."],
                    "Diferencia": fila["Diferencia"],
                    "Nodo_Alta": fila["Nodo Alta"]
                })
        
        # ========== PROCESS SDSCR ==========
        if "SDSCR" in archivos_existentes:
            sdscr_df = pd.read_csv(archivos_existentes["SDSCR"])
            # Filter only PV1 and PV2 buses (nodes 4 and 7)
            buses_interes = ["BUS 4", "BUS 7", "4", "7", "PV1 LV", "PV2 LV"]
            for _, fila in sdscr_df.iterrows():
                bus = fila["Bus"]
                if any(bus_interes in str(bus) for bus_interes in buses_interes):
                    datos_compilados.append({
                        "Escenario": escenario_nombre,
                        "Bus": bus,
                        "Metodo": "SDSCR",
                        "SCR": fila["SCR"],
                        "SDSCR_Coupled": fila["SDSCR_coupled"],
                        "SDSCR_No_Coupling": fila["SDSCR_no_coupling"],
                        "Valor_Principal": fila["SDSCR_coupled"],  # Use coupled as the main value
                        "Strength": fila["Strength"],
                        "SCC_MVA": fila["SCC (MVA)"]
                    })
        
        # ========== PROCESS LSCR ==========
        if "LSCR" in archivos_existentes:
            lscr_df = pd.read_csv(archivos_existentes["LSCR"])
            # Filter only PV1 and PV2
            for _, fila in lscr_df.iterrows():
                generador = fila["Generador"]
                if "PV1" in generador or "PV2" in generador:
                    datos_compilados.append({
                        "Escenario": escenario_nombre,
                        "Bus": fila["Barra Conexión"],
                        "Metodo": "LSCR",
                        "Generador": generador,
                        "Barra_Calculo": fila["Barra Cálculo"],
                        "Tipo": fila["Tipo"],
                        "Control": fila["Control"],
                        "Z_device": fila["Z_device"],
                        "K_vtg_normal": fila["K_vtg_normal"],
                        "λSCR_normal": fila["λSCR_normal"],
                        "K_vtg_fault": fila["K_vtg_fault"],
                        "λSCR_fault": fila["λSCR_fault"],
                        "Valor_Principal": fila["λSCR_normal"]  # Use λSCR_normal as the main value
                    })
        
        # ========== SAVE COMPILED RESULTS ==========
        if datos_compilados:
            df_compilado = pd.DataFrame(datos_compilados)
            
            # Output path for the compiled file
            ruta_resultados_comv = escenario_output_path
            archivo_compilado = os.path.join(ruta_resultados_comv, f"Resultados_Compilados_{escenario_nombre}.csv")
            
            df_compilado.to_csv(archivo_compilado, index=False, encoding='utf-8-sig')
            
            print(f"  ✅ Compiled results saved in: {archivo_compilado}")
            print(f"  📊 Total records compiled: {len(datos_compilados)}")
            
            # Display summary by method
            metodos = df_compilado["Metodo"].value_counts()
            print(f"  📋 Summary by method:")
            for metodo, count in metodos.items():
                print(f"     • {metodo}: {count} registros")
            
            return True
        else:
            print(f"  ❌ Data could not be compiled for {escenario_nombre}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error compiling results for {escenario_nombre}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# =============================================================================
# UPDATE THE MAIN PROCESSING FUNCTION
# =============================================================================

def procesar_escenario_completo(escenario_input_path, escenario_output_path):
    """Performs all calculations (Zbus, GSIM, NRSCR, LSCR, SDSCR, and SCR) for a scenario"""
    escenario_nombre = os.path.basename(escenario_input_path)
    print(f"\n{'='*60}")
    print(f"🎯 PROCESSING SCENARIO: {escenario_nombre}")
    print(f"{'='*60}")

    print(f"📥 Input: {escenario_input_path}")
    print(f"📤 Output:  {escenario_output_path}")
    
    # Step 1: Calculate Zbus
    zbus_exitoso = calcular_zbus_escenario(escenario_input_path, escenario_output_path)
    
    # Step 2: Calculate GSIM (only if Zbus was successful)
    if zbus_exitoso:
        gsim_exitoso = procesar_gsim_escenario(escenario_input_path, escenario_output_path)
    else:
        gsim_exitoso = False
        print(f"  ⏩ Skipping GSIM due to Zbus failure")
    
    # Step 3: Calculate NRSCR (independent of the previous ones)
    nrscr_exitoso = procesar_nrscr_escenario(escenario_input_path, escenario_output_path)
    
    # Step 4: Calculate LSCR (independent of the previous ones)
    lscr_exitoso = procesar_lscr_escenario(escenario_input_path, escenario_output_path)
    
    # Step 5: Calculate SDSCR (requires Zbus)
    if zbus_exitoso:
        sdscr_exitoso = procesar_sdscr_escenario(escenario_input_path, escenario_output_path)
    else:
        sdscr_exitoso = False
        print(f"  ⏩ Bypassing SDSCR due to Zbus failure")
    
    # Step 6: Calculate SCR (new) - independent of Zbus
    scr_exitoso = procesar_scr_escenario(escenario_input_path, escenario_output_path)
    
    # Step 7: Compile results
    compilacion_exitosa = compilar_resultados_escenario(escenario_input_path, escenario_output_path)
    
    return (zbus_exitoso, gsim_exitoso, nrscr_exitoso, lscr_exitoso, 
            sdscr_exitoso, scr_exitoso, compilacion_exitosa)

# =============================================================================
# UPDATE THE MAIN FUNCTION
# =============================================================================

def main():
    """Main function that coordinates the entire processing"""
    print("🚀 STARTING FULL PROCESSING (Zbus + GSIM + NRSCR + LSCR + SDSCR + SCR + COMPILACIÓN)")
    print(f"📁 Base entry route: {INPUT_PATH}")
    print(f"📁 Exit route: {OUTPUT_PATH}")
    
    # Find all scenarios
    escenarios = encontrar_escenarios(INPUT_PATH)
    
    if not escenarios:
        print("❌ No scenario folders were found")
        return
    
    print(f"📋 Scenarios encountered: {len(escenarios)}")
    for i, esc in enumerate(escenarios, 1):
        print(f"   {i}. {os.path.basename(esc)}")
    
    # Process each scenario
    resultados = []

    for escenario_path in escenarios:

        # Scenario name
        nombre_escenario = os.path.basename(escenario_path)

        # --------------------------------------------------------
        # INPUT
        # Files generated by extract_scenario_data.py
        # --------------------------------------------------------
        escenario_input_path = Path(escenario_path)

        # --------------------------------------------------------
        # OUTPUT
        # Results generated by calculate_indicators.py
        # --------------------------------------------------------
        escenario_output_path = OUTPUT_PATH / nombre_escenario

        # Create output folder
        escenario_output_path.mkdir(parents=True, exist_ok=True)

        print(f"\n{'='*80}")
        print(f"🔹 Processing {nombre_escenario}")
        print(f"📥 Input: {escenario_input_path}")
        print(f"📤 Output:  {escenario_output_path}")
        print(f"{'='*80}")

        zbus_ok, gsim_ok, nrscr_ok, lscr_ok, sdscr_ok, scr_ok, compilacion_ok = \
            procesar_escenario_completo(
                escenario_input_path,
                escenario_output_path
            )

        resultados.append({
            "escenario": nombre_escenario,
            "zbus_exitoso": zbus_ok,
            "gsim_exitoso": gsim_ok,
            "nrscr_exitoso": nrscr_ok,
            "lscr_exitoso": lscr_ok,
            "sdscr_exitoso": sdscr_ok,
            "scr_exitoso": scr_ok,
            "compilacion_exitosa": compilacion_ok
        })
    
    # Final summary
    print(f"\n{'='*80}")
    print(f"🎉 PROCESSING COMPLETED - FINAL SUMMARY")
    print(f"{'='*80}")
    
    total_escenarios = len(resultados)
    zbus_exitosos = sum(1 for r in resultados if r["zbus_exitoso"])
    gsim_exitosos = sum(1 for r in resultados if r["gsim_exitoso"])
    nrscr_exitosos = sum(1 for r in resultados if r["nrscr_exitoso"])
    lscr_exitosos = sum(1 for r in resultados if r["lscr_exitoso"])
    sdscr_exitosos = sum(1 for r in resultados if r["sdscr_exitoso"])
    scr_exitosos = sum(1 for r in resultados if r["scr_exitoso"])
    compilacion_exitosos = sum(1 for r in resultados if r["compilacion_exitosa"])
    
    print(f"📊 Statistics:")
    print(f"   • Total number of scenarios: {total_escenarios}")
    print(f"   • Successful Zbuses: {zbus_exitosos}/{total_escenarios}")
    print(f"   • Successful GSIM: {gsim_exitosos}/{total_escenarios}")
    print(f"   • Successful NRSCR: {nrscr_exitosos}/{total_escenarios}")
    print(f"   • Successful LSCR: {lscr_exitosos}/{total_escenarios}")
    print(f"   • Successful SDSCR: {sdscr_exitosos}/{total_escenarios}")
    print(f"   • Successful SCR: {scr_exitosos}/{total_escenarios}")
    print(f"   • Successful compilations: {compilacion_exitosos}/{total_escenarios}")
    
    # Display details by scenario
    print(f"\n📋 Details by scenario:")
    for resultado in resultados:
        status = ""
        status += "✅" if resultado["zbus_exitoso"] else "❌"
        status += "✅" if resultado["gsim_exitoso"] else "❌"
        status += "✅" if resultado["nrscr_exitoso"] else "❌"
        status += "✅" if resultado["lscr_exitoso"] else "❌"
        status += "✅" if resultado["sdscr_exitoso"] else "❌"
        status += "✅" if resultado["scr_exitoso"] else "❌"
        status += "✅" if resultado["compilacion_exitosa"] else "❌"
        print(f"   {status} {resultado['escenario']}")
    
    print(f"\n💾 All results saved in their respective scenario folders")
    print(f"   - Zbus.csv in Escenario_X/Positive/")
    print(f"   - GSIM_results.csv in Scenario_X/")
    print(f"   - NRSCR_results.csv in Scenario_X/")
    print(f"   - LSCR_results.csv in Scenario_X/")
    print(f"   - SDSCR_results.csv in Scenario_X/")
    print(f"   - SCR_results.csv in Scenario_X/")
    print(f"   - Resultados compilados in: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()