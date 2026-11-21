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

Modo interactivo (pregunta los datos y guarda el caso en `casos/`):

```
python main.py
```

Con un caso guardado:

```
python main.py casos/caso_preliminar.json
```

Interfaz gráfica (se abre en el navegador):

```
streamlit run app.py
```

La interfaz abre con una pantalla de inicio (botón *Iniciar sesión de diseño*).
El programa tiene seis pestañas:

1. **Caso**: abrir un `.json` de `casos/` o subir uno, editarlo en el
   formulario (o empezar uno nuevo), guardarlo y simularlo. El perfil de la
   tobera se actualiza al editar.
2. **Resultados** (después de simular): resumen del caso con el régimen de
   cada presión exterior, presión estática (con p1, p2 y p3 marcadas) y Mach a
   lo largo de la tobera, campo de Mach o presión pintado sobre la tobera (vista
   tipo CFD), mapa de regímenes (empuje contra presión exterior) y
   descarga de `contorno.dxf` y demás archivos.
3. **Explorador de choque**: la presión exterior se mueve con un deslizador y la
   solución (régimen, choque, empuje, campo de Mach) se recalcula al instante;
   incluye una animación del choque recorriendo la divergente y avisos de
   desprendimiento (criterio de Summerfield).
4. **Análisis dimensional** (objetivo 5): C_F = f(γ, Ae/A*, pb/p0) por el
   teorema Π, curvas de C_F, prueba de semejanza con toberas de distinto
   tamaño, T0 y p0, número de Reynolds en la garganta y efecto de γ.
5. **Comparar casos**: dos casos lado a lado (hoja de datos, perfiles, Mach y C_F).
6. **Validación SolidWorks** (después de simular): se modela `contorno.dxf` en
   SolidWorks, se corre Flow Simulation y se sube el `.csv` para compararlo. El
   error se muestra de cuatro formas: empalme animado de las dos curvas (el área
   entre ellas es el error y un cursor recorre la tobera), mapa de error sobre la
   tobera, gráfica de paridad con franja de ±5 % y error contra x. También se
   pueden capturar los goals de Flow Simulation (ṁ, Me, pe, F) para comparar las
   magnitudes globales. Con *Probar con datos de ejemplo* se ve la presentación
   antes de tener el CFD (son datos sintéticos, no de SolidWorks).

En Resultados, el botón *Reporte PDF* genera un reporte técnico del caso con la
hoja de datos y las figuras.

Al guardar, el caso se escribe en `casos/<nombre>.json`. Si ya existe otro
caso con ese nombre (distinto del que se abrió), la interfaz pide confirmación
antes de reemplazarlo.

La interfaz usa un tema grafito con azul profundo y la tipografía IBM Plex (`.streamlit/config.toml`); la paleta está en
`graficas_gui.py` y el CSS adicional en `estilo.py`. Los PNG de `graficas.py`
se quedan con fondo blanco para el reporte. Cada gráfica de la interfaz se
puede descargar como PNG en alta resolución con el ícono de cámara.

Los resultados se guardan en `salidas/<nombre del caso>/`:

| Archivo | Contenido |
|---|---|
| `resumen.txt` | Resumen legible de todo el caso |
| `resultados.json` | Todos los resultados numéricos |
| `distribucion.csv` | M, p y T sección por sección para cada presión exterior (se abre en Excel) |
| `contorno.png` | Media sección de la tobera con sus cotas |
| `presiones.png` | p/p0 a lo largo de la tobera para cada presión exterior |
| `mach.png` | Número de Mach a lo largo de la tobera |
| `contorno.dxf` | Perfil cerrado de media tobera (líneas y arcos exactos, en mm) y eje de revolución |
| `contorno_xyz.txt` | Coordenadas X Y Z del contorno interior, en mm |
| `dimensiones.txt` | Variables globales para las Ecuaciones de SolidWorks |

## Geometría

Tobera cónica con transiciones tangentes: tramo recto de entrada, arco de
entrada, convergente cónico, garganta redondeada (dos arcos) y divergente
cónico. La garganta está en x = 0. Los ángulos, la relación de contracción,
los radios de los arcos y el espesor de pared se editan en la sección
`geometria` del caso.

La pared exterior puede ser de espesor constante (`"tipo_pared": "constante"`,
forma de tobera de cohete) o un tubo recto (`"cilindrica"`). En ambos casos los
extremos quedan planos, listos para crear las tapas en Flow Simulation.

El cálculo de M(x), p(x) y T(x) usa el área real de este contorno, así que la
posición del choque que reporta el programa (en mm desde la garganta) es
directamente comparable con la simulación.

## Modelado en SolidWorks

Opción recomendada, con el DXF:

1. Abrir `contorno.dxf` (Archivo → Abrir, tipo DXF) e importarlo como croquis
   en el plano Alzado, con unidades en milímetros.
2. Convertir la línea de la capa EJE en geometría constructiva.
3. Operación **Revolución** del perfil cerrado alrededor de esa línea, 360°.

Alternativas:

- **Curva por puntos XYZ** (Insertar → Curva → Curva por puntos XYZ) con
  `contorno_xyz.txt`, y después cerrar el perfil en un croquis.
- **Croquis acotado** vinculado a `dimensiones.txt` desde Herramientas →
  Ecuaciones → Vincular a archivo externo.

Para un caso nuevo se puede usar el modo interactivo o copiar
`casos/caso_preliminar.json` y cambiar los valores:

- En `ambiente` se da `altitud_m` (atmósfera estándar) o `pa_Pa` directamente.
- `presiones_exteriores_Pa` es una lista en Pa o `"auto"` (una presión por régimen).
  La presión ambiente de diseño siempre se analiza.
- La sección `geometria` es opcional; lo que falte toma los valores por defecto.

## Validación con Flow Simulation

En la pestaña *Validación SolidWorks* se sube el `.csv` con los resultados
CFD sobre una línea en el eje (XY Plot o Point Parameters). Se aceptan
separador `,`, `;` o tabulador, coma decimal y líneas de título antes del
encabezado. Las columnas de posición, presión estática y Mach se detectan por
nombre (`X [m]`, `Pressure [Pa]`, `Mach Number`, también en español) y se
pueden corregir a mano junto con sus unidades.

La coordenada del CSV se lleva al eje del modelo (garganta en x = 0) según
dónde esté su origen: en la garganta (modelo hecho con `contorno.dxf`), en la
entrada, en la salida o en el primer punto del CSV; también se puede invertir
el sentido y sumar un desplazamiento. Los valores de SolidWorks se interpolan
linealmente en los nodos del modelo que caen dentro del tramo del CSV, y se
grafican superpuestos junto con la diferencia (código − SolidWorks) y el error
relativo a SolidWorks en %. La tabla alineada se puede descargar en `.csv`.

## Pruebas

```
pytest
```

Las pruebas comparan contra valores tabulados de flujo isentrópico y choque
normal (gamma = 1.4) y contra el caso preliminar resuelto a mano; también
cubren la geometría, las exportaciones, la lectura de CSV de SolidWorks, la
comparación, los casos de la interfaz y que la interfaz cargue sin errores.

Las pruebas usan su propia copia del caso en `tests/datos/caso_prueba.json`,
así que editar o guardar casos desde la interfaz no las afecta.

## Estructura

| Archivo | Contenido |
|---|---|
| `flujo.py` | Relaciones isentrópicas, área–Mach, gasto estrangulado y choque normal |
| `tobera.py` | Dimensionamiento, presiones críticas, régimen, posición del choque, empuje y distribución a lo largo de la tobera |
| `geometria.py` | Contorno de la tobera, pared exterior y exportación a DXF, coordenadas XYZ y dimensiones |
| `graficas.py` | Gráficas de contorno, presión y Mach |
| `interactivo.py` | Modo interactivo en la terminal |
| `main.py` | Corre un caso completo y guarda resultados |
| `app.py` | Interfaz gráfica (Streamlit); solo maneja la interfaz |
| `configuracion.py` | Leer, armar, guardar, previsualizar y ejecutar casos para la interfaz |
| `resumen_txt.py` | Lectura de `resumen.txt` como datos estructurados |
| `comparacion.py` | Lectura del CSV de SolidWorks, alineación, interpolación y error |
| `graficas_gui.py` | Gráficas interactivas (Plotly) de la interfaz |
| `estilo.py` | CSS de la interfaz (bordes, fuentes monoespaciadas en valores numéricos, fotos) |
| `.streamlit/config.toml` | Tema claro de Streamlit (azul ingeniería, gris frío) |
| `assets/` | Fotografías del encabezado de la interfaz (dominio público, NASA); créditos en `assets/CREDITOS.md` |
| `casos/` | Archivos de entrada |
| `tests/` | Pruebas automáticas |

## Equipo

Aldo Sánchez · Andrés Bernal · Ezequiel Trejo · Mateo de Lafuente · Valeria Rodríguez
