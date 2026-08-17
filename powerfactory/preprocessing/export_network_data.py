import powerfactory as pf
import numpy as np
import os
import csv

# ============================================================
# CONFIGURATION
# ============================================================

# Path where the output CSV files will be saved.
# Modify this path according to your local environment.
OUTPUT_DIR = r"C:\Users\YourUser\Path\Grid-strength-assessment\data\example\IEEE39"

app = pf.GetApplication()
app.ClearOutputWindow()

def z_to_y(r, x):
    if r == 0 and x == 0:
        return 0
    return 1 / complex(r, x)

app.PrintPlain("✅ Iniciando cálculo de Ybus (con líneas, trafos, generadores y cargas)...")

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
        app.PrintPlain(f"⚠️ Línea sin tipo: {line.loc_name}")
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
        app.PrintPlain(f"⚠️ Trafo {trafo.loc_name} sin conexión válida")
        continue
    bus1 = term1.cterm
    bus2 = term2.cterm
    if not bus1 or not bus2:
        app.PrintPlain(f"⚠️ Trafo {trafo.loc_name} con terminales no conectados a nodos")
        continue
    i, j = bus_idx.get(bus1.loc_name), bus_idx.get(bus2.loc_name)
    if i is None or j is None:
        app.PrintPlain(f"⚠️ Trafo {trafo.loc_name} con buses fuera del índice")
        continue

    typ = trafo.typ_id
    if not typ:
        app.PrintPlain(f"⚠️ Trafo {trafo.loc_name} sin tipo asignado.")
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
        app.PrintPlain(f"⚠️ Error extrayendo impedancia de trafo {trafo.loc_name}: {str(e)}")

# ➤ Generadores
for gen in gens:
    bus = gen.bus1
    if not bus:
        app.PrintPlain(f"⚠️ Generador {gen.loc_name} sin conexión válida")
        continue
    bus_term = bus.cterm
    if not bus_term:
        app.PrintPlain(f"⚠️ Generador {gen.loc_name} no conectado a nodo")
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
            app.PrintPlain(f"⚠️ No se pudieron obtener P/Q de {gen.loc_name}: {e}")
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
        app.PrintPlain(f"⚠️ PVsys {gen.loc_name} sin conexión válida")
        continue
    bus_term = bus.cterm
    if not bus_term:
        app.PrintPlain(f"⚠️ PVsys {gen.loc_name} no conectado a nodo")
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

# ➤ Imprimir matriz
app.PrintPlain("✔️ Matriz Ybus final:")
for i in range(n):
    row = "\t".join(f"{Ybus[i, j].real:.4f}+j{Ybus[i, j].imag:.4f}" for j in range(n))
    app.PrintPlain(row)

app.PrintPlain("\n📌 Nota: Se usaron los terminales conectados (cterm) para identificar correctamente los nodos de transformadores y generadores.")

# ➤  Script DPL para exportar Ybus a archivo CSV
import os
import csv

# 🔧 Ruta donde guardar el archivo
output_path = os.path.join(OUTPUT_DIR, "Ybus_export.csv")
os.makedirs(os.path.dirname(output_path), exist_ok=True)

with open(output_path, mode="w", newline="") as file:
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

app.PrintPlain(f"📁 Archivo Ybus exportado correctamente como matriz completa a:\n{output_path}")

#Se exportan tensiones y corrientes
import os
import csv

app.ClearOutputWindow()
app.PrintPlain("✅ Exportando resultados de generadores y tensiones de nodos...\n")

# Ejecutar flujo de carga
ldf = app.GetFromStudyCase("ComLdf")
if not ldf:
    app.PrintPlain("❌ No se encontró el objeto ComLdf.")
    raise Exception("No hay flujo de carga definido.")

ldf.iopt_net = 0
status = ldf.Execute()
if status != 0:
    app.PrintPlain("❌ Error al ejecutar el flujo de carga.\n")
    raise Exception("Error en flujo de carga")

app.PrintPlain("✅ Flujo de carga ejecutado correctamente.\n")

# Directorio de salida
os.makedirs(OUTPUT_DIR, exist_ok=True)

gen_path = os.path.join(OUTPUT_DIR, "corrientes_generadores.csv")
term_path = os.path.join(OUTPUT_DIR, "tensiones_nodos.csv")

# 🔹 Generadores
gen_classes = ["ElmSym", "ElmGenstat", "ElmPvsys", "ElmPvg", "ElmVsccon"]
generadores = []
for cls in gen_classes:
    generadores += app.GetCalcRelevantObjects(f"*.{cls}")

# 🔹 Terminales de nodo
terminales = app.GetCalcRelevantObjects("*.ElmTerm")

# ➤ Exportar corrientes de generadores
with open(gen_path, mode="w", newline="") as f_gen:
    writer = csv.writer(f_gen, delimiter=";")
    writer.writerow(["Nombre", "Corriente m:I:bus1 [A]"])

    for gen in generadores:
        name = gen.loc_name
        try:
            corriente = gen.GetAttribute("m:I:bus1")
            writer.writerow([name, f"{corriente.real:.4f}+j{corriente.imag:.4f}"])
        except Exception as e:
            app.PrintPlain(f"⚠️ {name} sin corriente medida: {e}\n")

# ➤ Exportar tensiones desde terminales
with open(term_path, mode="w", newline="") as f_bus:
    writer = csv.writer(f_bus, delimiter=";")
    writer.writerow(["Nodo (Terminal)", "Tensión m:u [p.u.]"])

    for term in terminales:
        try:
            name = term.loc_name
            tension = term.GetAttribute("m:u")
            writer.writerow([name, f"{tension:.4f}"])
        except Exception as e:
            app.PrintPlain(f"⚠️ Terminal {term.loc_name} sin tensión medida: {e}\n")

# ➤ Exportar potencias activas (pgini) de generadores en MW con nodo conectado usando bus1.cterm
pot_path = os.path.join(OUTPUT_DIR, "potencias_activas_generadores.csv")

with open(pot_path, mode="w", newline="") as f_pot:
    writer = csv.writer(f_pot, delimiter=";")
    writer.writerow(["Nombre", "Tipo", "Nodo Conectado", "Potencia Activa pgini [MW]"])

    for gen in generadores:
        name = gen.loc_name
        gen_type = gen.GetClassName()

        # ✅ Alternativa robusta: gen.bus1.cterm
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
            app.PrintPlain(f"⚠️ {name} sin atributo pgini: {e}\n")

# ---------------------------------------------------------
# ➤ Ejecutar cortocircuito trifásico y exportar Ikss y Skss
# ---------------------------------------------------------

app.PrintPlain("⚡ Ejecutando cálculo de cortocircuito trifásico...\n")

# Obtener objeto de cortocircuito
sc = app.GetFromStudyCase("ComShc")
if not sc:
    app.PrintPlain("❌ No se encontró el objeto ComShc en el caso de estudio.")
    raise Exception("No se encontró ComShc.")

# Configurar para trifásico en todos los nodos
sc.iopt_mde = 0     # 0 = simétrico (trifásico)
sc.iopt_allbus = 1  # Calcular en todos los nodos

# Ejecutar cálculo
status = sc.Execute()
if status != 0:
    app.PrintPlain("❌ Error al ejecutar el cálculo de cortocircuito.")
    raise Exception("Error en cortocircuito.")

app.PrintPlain("✅ Cálculo de cortocircuito trifásico ejecutado correctamente.\n")

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
            app.PrintPlain(f"⚠️ Nodo {nodo.loc_name} sin datos: {e}\n")

app.PrintPlain(f"📄 Resultados de cortocircuito exportados en:\n{sc_path}\n")
