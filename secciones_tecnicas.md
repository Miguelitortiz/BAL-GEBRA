# Análisis Técnico: Arquitectura, Heurísticas e Integración Visual

Este documento detalla los componentes tecnológicos del tutor neuro-simbólico, estructurado para integrarse directamente en las secciones 3, 4 y 5 del artículo académico según las especificaciones de `article_specs.md`.

---

## 3. Arquitectura Neuro-Simbólica Propuesta

La arquitectura del sistema se basa en un paradigma de **Segregación de Responsabilidades Lógicas (SRL)**, donde se desacopla el razonamiento determinista de la interfaz comunicativa. El sistema se compone de cuatro capas fundamentales conectadas mediante un protocolo de intercambio inmutable.

### A. Orquestador de Estado Pedagógico (Go)
El núcleo del sistema es un servidor en Go que actúa como el "Cerebro Lógico". A diferencia de un chatbot convencional, este componente mantiene el grafo de estados de la resolución.
*   **Gestión de Sesiones:** Rastrea la ecuación actual y el historial de pasos.
*   **Ininterrumpibilidad:** Garantiza que el LLM no pueda "alucinar" un resultado, ya que el orquestador valida cada propuesta contra el motor simbólico antes de permitir cualquier respuesta al usuario.

### B. Motor de Transformación Atómica (Python + SymPy)
Para garantizar el rigor matemático, se implementó un motor puente en Python que utiliza la librería `SymPy`. 
*   **Transformaciones No-Evolutivas:** Se utiliza el parámetro `evaluate=False` para preservar la estructura original de la ecuación (ej. no simplifica $1+2$ espontáneamente si el objetivo pedagógico es que el alumno lo haga).
*   **Validación de Equivalencia:** En lugar de comparar strings, el motor calcula la diferencia algebraica entre el estado anterior y el propuesto; si el resultado simplificado de esta diferencia no es cero, el paso es marcado como inválido.

### C. Protocolo de Comunicación Estructurado (JSON)
La comunicación entre procesos sigue un esquema de **Estado-Acción-Resultado**. Cada interacción genera un payload JSON inmutable que previene derivas de contexto:
```json
{
  "estado_actual": "3x - 1 = 8",
  "operacion_detectada": "mover_constante_lhs",
  "descripcion_pedagogica": "Sumar 1 a ambos lados",
  "resultado_previsto": "3x = 9"
}
```

---

## 4. Diseño del Árbol de Heurísticas Pedagógicas

El sistema no utiliza un algoritmo de búsqueda de solución standard (como el Risch algorithm), sino un **Árbol de Prioridad Didáctica** diseñado para imitar la tutoría socrática.

### A. Priorización de Carga Cognitiva
Las heurísticas se ejecutan en un orden secuencial rígido que minimiza la dispersión de atención del alumno:
1.  **Aritmética Constante:** Simplificar términos numéricos en el mismo lado.
2.  **Expansión Distributiva:** Eliminar paréntesis para exponer términos ocultos.
3.  **Eliminación de Denominadores:** Multiplicación por el Mínimo Común Múltiplo (MCM).
4.  **Transposición de Términos:** Movimiento de constantes al RHS y de incógnitas al LHS.
5.  **Aislamiento del Coeficiente:** División final o multiplicación por recíproco.

### B. Clasificación y Diagnóstico de Errores
El sistema no solo rechaza pasos inválidos, sino que los clasifica mediante un **Analizador de Diferencia Simbólica**. Si un usuario comete un error, el árbol compara la entrada fallida con la solución ideal y detecta patrones como:
*   *Error de Signo:* La diferencia entre estados es exactamente el doble del término movido.
*   *Error de Operación Inversa:* El usuario multiplicó cuando el aislamiento requería división.

---

## 5. Integración Visual y Manejo de Latencia

La visualización de las matemáticas es crítica para reducir el "Efecto de Atención Dividida". Se utiliza **Manim (Mathematical Animation Engine)** mediante un sistema de renderizado asíncrono.

### A. Mapeo Simbólico-Visual (Coreografía de Ecuaciones)
Cada transición no es un simple cambio de texto, sino una coreografía de objetos matemáticos basada en la operación detectada por el orquestador:
*   **Anotación Automática:** El sistema dibuja corchetes (`[ ]`) alrededor de la ecuación y anota la operación aplicada (ej. `+1`) en tiempo real.
*   **TransformFromCopy:** Los términos que se conservan en la siguiente línea se desplazan físicamente hacia abajo, mientras que los términos que mutan (como $3x-x \rightarrow 2x$) se transforman usando morfismo de formas (*shape matching*).

### B. Estrategia de Mitigación de Latencia
Dado que Manim requiere compilación (PDFLaTeX/Cairo), se implementó un flujo de ejecución asíncrono:
1.  **Generación Bajo Demanda:** Solo se renderiza el paso actual tras la validación.
2.  **Bucle de Interacción:** El LLM comienza la explicación lingüística de forma inmediata mientras el video se procesa en segundo plano, ocultando así la latencia de renderizado de ~2-3 segundos.
3.  **Persistencia Visual:** El estado final de la animación se convierte en el póster del reproductor para garantizar una transición fluida cuando el video finaliza su carga.

---

Este esquema técnico asegura que el artículo presente una solución **matemáticamente robusta**, **pedagógicamente consciente** y **visualmente coherente**.
