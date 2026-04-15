# Neuro-Symbolic Pedagogical API (Solver)

Este proyecto implementa una **API Pedagógica Reactiva** (`Single-Step State Machine`) diseñada para operar como el "cerebro lógico" de un Sistema de Tutoría Inteligente basado en LLMs. 

A diferencia de un *solver* tradicional que escupe la respuesta de principio a fin, este sistema ha sido estructurado meticulosamente bajo el paradigma Neuro-Simbólico: **El Orquestador (Go) es el maestro que rige las prioridades cognitivas del alumno, y el Motor (SymPy) es el músculo que asegura que no haya alucinaciones matemáticas.**

## 🧠 Filosofía de Diseño

Para mitigar la carga cognitiva y evitar el sobre-procesamiento, el sistema adhiere a reglas restrictivas:
1. **Paso por Paso (Atómico):** El orquestador obliga al LLM a ir a un paso a la vez, garantizando un JSON inmutable con transformaciones lógicas precisas (evita "spoilers" y saltos ilegales).
2. **Determinismo Heurístico:** Existe una jerarquía estricta que dictamina **enseñar primero lo óptimo**. Ejemplo: Siempre exigirá recolectar términos semejantes antes de multiplicar lados de una ecuación.
3. **No-Agrupación Prematura (`evaluate=False`):** El sistema fue recableado en Python para NO simplificar internamente las operaciones. Ecuaciones como `2*(3x+5)/8` se mantienen intactas hasta que le toque su turno en la heurística distributiva.

---

## 🛠 Instalación y Configuración

El proyecto requiere Go y Python.

```bash
# 1. Asegúrate de tener Python y SymPy
pip install sympy

# 2. Compilar el ejecutable de Go (Opcional, directo a usar 'go run .')
go build -o solver .
```

---

## 🚀 Uso de la API (CLI Interface)

Este solver se comporta como una caja negra reactiva para el LLM. Sólo expone dos *endpoints* ejecutables:

### 1. Sugerencia del Siguiente Mejor Paso (`hint`)
Si el estudiante no sabe qué hacer y el LLM le exige al motor la siguiente acción óptima, usamos `hint`.

**Comando:**
```bash
./solver hint "6*x = -26"
```

**Respuesta JSON:**
```json
{
  "estado": "6*x = -26",
  "accion": "dividir_coeficiente",
  "descripcion": "Dividir ambos lados entre 6 para aislar x",
  "resultado": "x = -26/6"
}
```
*Nota:* El LLM debe leer el campo `descripcion` para empatizar con el usuario o trasladar a animaciones el `resultado`.

### 2. Validación de Acciones de Usuario (`validate`)
Cuando el estudiante somete un paso por su propia intuición, el sistema lo califica.

**Comando:**
```bash
./solver validate "3*x - 2 = x + 4" "3*x = x + 6"
```

**Respuesta JSON:**
```json
{
  "paso_valido": true
}
```
*Si se ingresa un salto matemáticamente falso (e.g. `3x = x + 10`), el sistema devolverá `false` previniendo que el LLM sufra una alucinación por arrastre de error.*

---

## 📁 Arquitectura Interna del Ecosistema

El proyecto se divide en 3 módulos principales que conforman la Arquitectura Neuro-Simbólica final:

### 1. El Cerebro Lógico (`/solver`)
- `main.go` 👉 Router principal que canaliza el CLI hacia `validate` o `hint`.
- `heuristics.go` 👉 La regla de vida del sistema. Un arreglo estrictamente priorizado de heurísticas de mitigación cognitiva (Árbol de Decisión Didáctico).
- `sympy_engine.py` 👉 Músculo simbólico estricto evaluado en aislamiento termodinámico. Evalúa y comprueba congruencia vía árboles y clasifica errores heurísticamente (ej. suma errónea de constantes vs división invertida).

### 2. El Renderizador Visual (`/manim_module`)
- `renderer.py` 👉 Guion en Python utilizando la librería *Manim*. Extrae el estado dinámico y anima la transición matemática mediante `TransformMatchingShapes` para preservar la estructura visual (interpolación sin cortes).
- `generate_video.sh` 👉 Script bash acoplador. Se ejecuta con banderas de mitigación de latencia de Manim (`-ql` para calidad rápida) optimizando la generación al vuelo.

### 3. El MVP Interactivo (`app.py`)
- Ubicado en la raíz del proyecto.
- Construido en **Streamlit**.
- Emula un Tutor Inteligente completo con 2 paneles:
  - **Izquierda:** El Chat del Tutor. Se alimenta cruzando el llm local (vía Ollama u otro) pero atado contextualmente a los veredictos inmutables de Go.
  - **Derecha:** La Pizarra Interactiva. Muestra el estado simbólico vivo de la ecuación y reproduce los videos de `.mp4` compilados asíncronamente por Manim.

Para ejecutar toda la simulación:
```bash
pip install streamlit requests manim sympy
streamlit run app.py
```
