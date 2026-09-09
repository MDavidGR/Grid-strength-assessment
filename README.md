# Estructura del repositorio

El repositorio se organiza en multiples directorios de acuerdo con la función que desempeñan dentro de la metodología. Esta estructura permite separar los **archivos de entrada**, los **códigos de procesamiento**, los **modelos de DIgSILENT PowerFactory** y los **resultados generados**, facilitando la ejecución y reproducción de los resultados.

La estructura principal del repositorio es la siguiente:

```text
Grid-strength-assessment/
│
├── data/
│   ├── example/
│   │   ├── IEEE9/
│   │   └── IEEE39/
│   │
│   ├── scenarios/
│   │   ├── IEEE9/
│   │   │   ├── CAP/
│   │   │   └── IND/
│   │   └── IEEE39/
│   │       ├── CAP/
│   │       └── IND/
│   │
│   └── results/
│       ├── IEEE9/
│       └── IEEE39/
│
├── powerfactory/
│
├── python/
│   ├── preprocessing/
│   ├── analysis/
│   ├── indicators/
│   └── visualization/
│
├── results/
│   ├── IEEE9/
│   │   ├── CAP/
│   │   └── IND/
│   └── IEEE39/
│       ├── CAP/
│       └── IND/
│
└── README.md
```

## Descripción de los directorios

### `data/`

Contiene los datos utilizados durante las diferentes etapas de la metodología, incluyendo los archivos de entrada, la definición de escenarios y los resultados intermedios generados durante los cálculos.

#### `data/example/`

Contiene los archivos de entrada asociados a los sistemas de prueba **IEEE de 9 y 39 nodos**. Estos archivos constituyen la información de partida necesaria para ejecutar los diferentes procesos de análisis.

```text
data/example/
├── IEEE9/
└── IEEE39/
```

#### `data/scenarios/`

Contiene la definición de los escenarios utilizados para evaluar la fortaleza de red. Los escenarios se organizan según el sistema de prueba y el tipo de factor de potencia considerado:

* `CAP/`: escenarios con comportamiento **capacitivo**.
* `IND/`: escenarios con comportamiento **inductivo**.

Cada uno de estos directorios contiene los escenarios de prueba correspondientes (`Escenario_1` a `Escenario_6`).

```text
data/scenarios/
├── IEEE9/
│   ├── CAP/
│   └── IND/
└── IEEE39/
    ├── CAP/
    └── IND/
```

#### `data/results/`

Contiene los **resultados intermedios y datos generados durante el primer procesamiento** de los escenarios. Estos archivos incluyen, entre otros, información utilizada para el cálculo de los diferentes indicadores de fortaleza de red, exportaciones de impedancias y resultados asociados a los análisis realizados en Python.

Los resultados se organizan por sistema de prueba, resultados de barrido de potencia por tipo de generación y el resultado de la extracción de información basica para los indicadores por escenario planteado.

```text
data/results/
├── IEEE9/
│   ├── CAP/
│   ├── IND/
│   ├── IEEE9C/
│   └── IEEE9I/
└── IEEE39/
    ├── CAP/
    ├── IND/
    ├── IEEE39C/
    └── IEEE39I/
```

Dentro de los directorios de cada escenario se encuentran subdirectorios específicos para los distintos tipos de información generada, tales como:

* `Datos GSIM/`: datos utilizados para el cálculo del **Grid Strength Impedance Metric (GSIM)**.
* `ExportZ_Python/`: archivos asociados a la informacion de cargas e impedancias de los generadores.
* `Informacion SCR/`: información utilizada para el cálculo de indicadores basados en **Short Circuit Ratio (SCR)**.
* `Positive/`: resultados correspondientes a la informacion base de la red (generadores, nodos, transformadores, corrientes de cortocircuito, Ybus, etc.).
* `SDSCR INFO/`: información utilizada en el cálculo del **SDSCR**.

### `powerfactory/`

Contiene los archivos asociados a **DIgSILENT PowerFactory** utilizados en el desarrollo de la metodología. En este directorio se incluyen los scripts y archivos necesarios para realizar la ejecucion de análisis de la red y exportar la información requerida por los scripts de Python.

### `python/`

Contiene los scripts desarrollados en **Python**. Los códigos se encuentran organizados de acuerdo con la etapa del procesamiento en la que son utilizados:

| Directorio       | Función                                                                                       |
| ---------------- | --------------------------------------------------------------------------------------------- |
| `preprocessing/` | Preparación, organización y procesamiento inicial de los datos de entrada.                    |
| `indicators/`    | Cálculo de los indicadores utilizados para evaluar la fortaleza de red.                       |
| `visualization/` | Generación de gráficos y representaciones utilizadas para analizar y comparar los resultados. |

Esta separación permite mantener independientes las diferentes etapas del flujo de procesamiento y facilita la reutilización de los scripts.

### `results/`

Contiene los **resultados finales y figuras generadas para el análisis de los sistemas de prueba**. A diferencia de `data/results/`, este directorio está orientado principalmente a los resultados finales utilizados para la presentación, comparación y análisis de los indicadores.

Los resultados se organizan por sistema de prueba y tipo de escenario:

```text
results/
├── IEEE9/
│   ├── CAP/
│   └── IND/
└── IEEE39/
    ├── CAP/
    └── IND/
```

Dentro de cada directorio por tipo de generación se almacenan las gráficas y resultados finales correspondientes. Adicionalmente, se incluyen directorios destinados a diferentes tipos de visualización, como:

* `Graficas_SCR/`: gráficos relacionados con la evaluación de los indicadores por escenario.
* `Matriz_Graficas_Derecha/`: matriz de gráficos correspondientes a los resultados comparativos para los indicadores basados en tensión.
* `Matriz_Graficas_Izquierda/`: matrices de gráficos correspondientes a los resultados comparativos para los indicadores basados en corrientes de cortocircuito.
* `Normalized graphs/`: gráficos comparativos de indicadores normalizados.

Finalmente, `README.md` contiene la documentación general del repositorio, incluyendo la descripción de la metodología, los requisitos, la estructura de archivos y las instrucciones necesarias para reproducir los análisis.