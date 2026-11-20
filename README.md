# TOBERA-CD

Herramienta para el diseño y análisis de toberas convergente–divergentes,
desarrollada como proyecto final de Mecánica de Fluidos
(Ingeniería Aeroespacial, ENES Juriquilla, UNAM).

A partir de las condiciones de cámara, el gas, la presión ambiente y el
empuje requerido, la herramienta:

1. dimensiona la tobera (garganta y salida) con expansión ideal;
2. calcula las presiones críticas que separan los regímenes de operación;
3. clasifica el régimen y localiza el choque normal para cualquier presión exterior;
4. calcula el empuje y el coeficiente de empuje;
5. genera el contorno de la tobera y los archivos para modelarla en SolidWorks.

Modelo: flujo cuasi-unidimensional, permanente y adiabático de un gas ideal
calóricamente perfecto, isentrópico salvo a través de las ondas de choque.

## Instalación (PyCharm)

1. Abrir la carpeta del repositorio como proyecto.
2. Crear un intérprete con entorno virtual (*Settings → Python Interpreter → Add → Virtualenv*).
3. Instalar dependencias: `pip install -r requirements.txt`.

## Uso

```
python main.py casos/caso_preliminar.json
```

Los resultados se guardan en `salidas/<nombre del caso>/`:

| Archivo | Contenido |
|---|---|
| `resumen.txt` | Resumen legible de todo el caso |
| `resultados.json` | Todos los resultados numéricos |
| `contorno.dxf` | Perfil cerrado de media tobera (líneas y arcos exactos, en mm) y eje de revolución |
| `contorno_xyz.txt` | Coordenadas X Y Z del contorno interior, en mm |
| `dimensiones.txt` | Variables globales para las Ecuaciones de SolidWorks |

## Geometría

Tobera cónica con transiciones tangentes: tramo recto de entrada, arco de
entrada, convergente cónico, garganta redondeada (dos arcos) y divergente
cónico. La garganta está en x = 0. Los ángulos, la relación de contracción,
los radios de los arcos y el espesor de pared se editan en la sección
`geometria` del caso.

## Modelado en SolidWorks

Opción recomendada, con el DXF:

1. Abrir `contorno.dxf` (Archivo → Abrir, tipo DXF) e importarlo como croquis
   en el plano Alzado, con unidades en milímetros.
2. Operación **Revolución** del perfil cerrado alrededor de la línea de la capa EJE.

Alternativas:

- **Curva por puntos XYZ** (Insertar → Curva → Curva por puntos XYZ) con
  `contorno_xyz.txt`, y después cerrar el perfil en un croquis.
- **Croquis acotado** vinculado a `dimensiones.txt` desde Herramientas →
  Ecuaciones → Vincular a archivo externo.

Para un caso nuevo, copiar `casos/caso_preliminar.json` y cambiar los valores.
En `ambiente` se puede dar `altitud_m` (atmósfera estándar) o `pa_Pa` directamente.

## Pruebas

```
pytest
```

Las pruebas comparan contra valores tabulados de flujo isentrópico y choque
normal (gamma = 1.4) y contra el caso preliminar resuelto a mano.

## Estructura

| Archivo | Contenido |
|---|---|
| `flujo.py` | Relaciones isentrópicas, área–Mach, gasto estrangulado y choque normal |
| `tobera.py` | Dimensionamiento, presiones críticas, régimen, posición del choque, empuje y distribución a lo largo de la tobera |
| `geometria.py` | Contorno de la tobera y exportación a DXF, coordenadas XYZ y dimensiones |
| `main.py` | Corre un caso completo y guarda resultados |
| `casos/` | Archivos de entrada |
| `tests/` | Pruebas automáticas |

## Equipo

Aldo Sánchez · Andrés Bernal · Ezequiel Trejo · Mateo de Lafuente · Valeria Rodríguez
