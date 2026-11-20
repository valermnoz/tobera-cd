# TOBERA-CD

Herramienta para el diseño y análisis de toberas convergente–divergentes,
desarrollada como proyecto final de Mecánica de Fluidos
(Ingeniería Aeroespacial, ENES Juriquilla, UNAM).

A partir de las condiciones de cámara, el gas, la presión ambiente y el
empuje requerido, la herramienta:

1. dimensiona la tobera (garganta y salida) con expansión ideal;
2. calcula las presiones críticas que separan los regímenes de operación;
3. clasifica el régimen y localiza el choque normal para cualquier presión exterior;
4. calcula el empuje y el coeficiente de empuje.

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

Los resultados se guardan en `salidas/<nombre del caso>/`.

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
| `main.py` | Corre un caso completo y guarda resultados |
| `casos/` | Archivos de entrada |
| `tests/` | Pruebas automáticas |

## Equipo

Aldo Sánchez · Andrés Bernal · Ezequiel Trejo · Mateo de Lafuente · Valeria Rodríguez
