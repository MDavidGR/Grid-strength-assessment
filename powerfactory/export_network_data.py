import powerfactory as pf
import numpy as np
import os
import csv
from pathlib import Path

# ============================================================
# CONFIGURATION
# ============================================================

# Repository root
REPO_ROOT = Path(__file__).resolve().parents[2]

# Example to be processed
EXAMPLE = "IEEE39"

# ------------------------------------------------------------
# Output Folder
# ------------------------------------------------------------
EXPORT_PATH = (REPO_ROOT / "data" / "example" / EXAMPLE)

# Path where the output CSV files will be saved.
# Modify this path according to your local environment.
OUTPUT_DIR = EXPORT_PATH

app = pf.GetApplication()
app.ClearOutputWindow()

def z_to_y(r, x):
    if r == 0 and x == 0:
        return 0
    return 1 / complex(r, x)

app.PrintPlain("✅ Starting Ybus calculation (lines, transformers, generators, and loads)...")

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
        app.PrintPlain(f"⚠️ Untyped line: {line.loc_name}")
        continue
    length = line.dline
    r = model.rline * length
    x = model.xline * length
    y = z_to_y(r, x)
    Ybus[i, i] += y
    Ybus[j, j] += y
    Ybus[i, j] -= y
    Ybus[j, i] -= y

# ➤ Transformers
for trafo in trafos:
    term1 = trafo.buslv
    term2 = trafo.bushv
    if not term1 or not term2:
        app.PrintPlain(f"⚠️ Tr {trafo.loc_name} without a valid connection")
        continue
    bus1 = term1.cterm
    bus2 = term2.cterm
    if not bus1 or not bus2:
        app.PrintPlain(f"⚠️ Tr {trafo.loc_name} with terminals not connected to nodes")
        continue
    i, j = bus_idx.get(bus1.loc_name), bus_idx.get(bus2.loc_name)
    if i is None or j is None:
        app.PrintPlain(f"⚠️ Tr {trafo.loc_name} with buses outside the index")
        continue

    typ = trafo.typ_id
    if not typ:
        app.PrintPlain(f"⚠️ Tr {trafo.loc_name} unassigned type.")
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
        app.PrintPlain(f"⚠️ Error extracting transformer impedance {trafo.loc_name}: {str(e)}")

# ➤ Generadores
for gen in gens:
    bus = gen.bus1
    if not bus:
        app.PrintPlain(f"⚠️ Generator {gen.loc_name} without a valid connection")
        continue
    bus_term = bus.cterm
    if not bus_term:
        app.PrintPlain(f"⚠️ Generator {gen.loc_name} not connected to node")
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
            app.PrintPlain(f"⚠️ They could not be obtained P/Q of {gen.loc_name}: {e}")
            continue

        if P == 0 and Q == 0:
            continue

        S = complex(P, Q) / 1000  # convert to per-unit on a 1000 MVA base, if applicable
        Ysh = S / (1.0 ** 2)
        Ybus[i, i] += Ysh.conjugate()


# ➤ ElmPvsys-type generators
for gen in pvsys_gens:
    bus = gen.bus1
    if not bus:
        app.PrintPlain(f"⚠️ PVsys {gen.loc_name} without a valid connection")
        continue
    bus_term = bus.cterm
    if not bus_term:
        app.PrintPlain(f"⚠️ PVsys {gen.loc_name} not connected to node")
        continue
    i = bus_idx.get(bus_term.loc_name)
    if i is None:
        continue

    P = gen.pgini  # MW
    Q = gen.qgini  # MVAr
    if P == 0 and Q == 0:
        continue
    S = complex(P, Q) / 1000  # [MVA]
    Ysh = S / (1.0 ** 2)      # Admittance in p.u. (V=1.0 pu)
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

# ➤ Imprimir matriz
app.PrintPlain("✔️ Final Ybus matrix:")
for i in range(n):
    row = "\t".join(f"{Ybus[i, j].real:.4f}+j{Ybus[i, j].imag:.4f}" for j in range(n))
    app.PrintPlain(row)

app.PrintPlain("\n📌 Note: Connected terminals (cterm) were used to correctly identify transformer and generator nodes.")

# ➤  DPL script to export Ybus to a CSV file
import os
import csv

# 🔧 Path where the file will be saved
output_path = os.path.join(OUTPUT_DIR, "Ybus_export.csv")
os.makedirs(os.path.dirname(output_path), exist_ok=True)

with open(output_path, mode="w", newline="") as file:
    writer = csv.writer(file)

    # Header with column names
    header = ["Bus"] + bus_names
    writer.writerow(header)

    # Write each row with its bus name and the complex admittances.
    for i in range(n):
        row = [bus_names[i]]
        for j in range(n):
            y = Ybus[i, j]
            cell = f"{y.real:.4f}+j{y.imag:.4f}"
            row.append(cell)
        writer.writerow(row)

app.PrintPlain(f"📁 Ybus file successfully exported as a full array to:\n{output_path}")

#Voltages and currents are exported
import os
import csv

app.ClearOutputWindow()
app.PrintPlain("✅ Exporting generator results and node voltages...\n")

# Run load flow
ldf = app.GetFromStudyCase("ComLdf")
if not ldf:
    app.PrintPlain("❌ The object was not found ComLdf.")
    raise Exception("There is no defined load flow.")

ldf.iopt_net = 0
status = ldf.Execute()
if status != 0:
    app.PrintPlain("❌ Error executing the load flow.\n")
    raise Exception("Load flow error")

app.PrintPlain("✅ Load flow executed successfully.\n")

# Output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

gen_path = os.path.join(OUTPUT_DIR, "corrientes_generadores.csv")
term_path = os.path.join(OUTPUT_DIR, "tensiones_nodos.csv")

# 🔹 Generators
gen_classes = ["ElmSym", "ElmGenstat", "ElmPvsys", "ElmPvg", "ElmVsccon"]
generadores = []
for cls in gen_classes:
    generadores += app.GetCalcRelevantObjects(f"*.{cls}")

# 🔹 Node terminals
terminales = app.GetCalcRelevantObjects("*.ElmTerm")

# ➤ Export generator currents
with open(gen_path, mode="w", newline="") as f_gen:
    writer = csv.writer(f_gen, delimiter=";")
    writer.writerow(["Nombre", "Corriente m:I:bus1 [A]"])

    for gen in generadores:
        name = gen.loc_name
        try:
            corriente = gen.GetAttribute("m:I:bus1")
            writer.writerow([name, f"{corriente.real:.4f}+j{corriente.imag:.4f}"])
        except Exception as e:
            app.PrintPlain(f"⚠️ {name} no measured current: {e}\n")

# ➤ Export voltages from terminals
with open(term_path, mode="w", newline="") as f_bus:
    writer = csv.writer(f_bus, delimiter=";")
    writer.writerow(["Nodo (Terminal)", "Tensión m:u [p.u.]"])

    for term in terminales:
        try:
            name = term.loc_name
            tension = term.GetAttribute("m:u")
            writer.writerow([name, f"{tension:.4f}"])
        except Exception as e:
            app.PrintPlain(f"⚠️ Terminal {term.loc_name} without measured tension: {e}\n")

# ➤ Export active power (pgini) of generators in MW, including the connected node, using bus1.cterm
pot_path = os.path.join(OUTPUT_DIR, "potencias_activas_generadores.csv")

with open(pot_path, mode="w", newline="") as f_pot:
    writer = csv.writer(f_pot, delimiter=";")
    writer.writerow(["Nombre", "Tipo", "Nodo Conectado", "Potencia Activa pgini [MW]"])

    for gen in generadores:
        name = gen.loc_name
        gen_type = gen.GetClassName()

        # ✅ Robust alternative: gen.bus1.cterm
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
            app.PrintPlain(f"⚠️ {name} without attribute pgini: {e}\n")

# ---------------------------------------------------------
# ➤ Execute a three-phase short-circuit analysis and export Ikss and Skss
# ---------------------------------------------------------

app.PrintPlain("⚡ Performing three-phase short-circuit calculation...\n")

# Obtener objeto de cortocircuito
sc = app.GetFromStudyCase("ComShc")
if not sc:
    app.PrintPlain("❌ The ComShc object was not found in the case study.")
    raise Exception("ComShc not found.")

# Configure for three-phase at all nodes
sc.iopt_mde = 0     # 0 = simétric (3ph)
sc.iopt_allbus = 1  # Calculate at all nodes

# Perform calculation
status = sc.Execute()
if status != 0:
    app.PrintPlain("❌ Error while executing the short-circuit calculation.")
    raise Exception("Short-circuit fault.")

app.PrintPlain("✅ Three-phase short-circuit calculation performed correctly.\n")

# Obtener nodos
nodos_sc = app.GetCalcRelevantObjects("*.ElmTerm")

# Archivo CSV de salida
sc_path = os.path.join(OUTPUT_DIR, "cortocircuito_trifasico.csv")

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
            app.PrintPlain(f"⚠️ Nodo {nodo.loc_name} sin datos: {e}\n")

app.PrintPlain(f"📄 Exported short circuit results in:\n{sc_path}\n")
