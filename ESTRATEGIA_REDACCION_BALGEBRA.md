# Estrategia de Redacción: Proyecto BAL-GEBRA

Este documento consolida las directrices críticas para la construcción del artículo científico "BAL-GEBRA: Tutoría Neuro-Simbólica con Heurísticas Pedagógicas y Visualización Animada".

## 1. Identidad Editorial
- **Formato:** IEEE/ACM, doble columna, 6 páginas máximo.
- **Tono:** Académico aséptico, tercera persona, libre de clichés de IA (prohibidos: "crucial", "panorama", "tapiz", etc.).
- **Enfoque:** Arquitectura técnica y mitigación de alucinaciones, NO bondades genéricas de la IA.

## 2. Estructura de Secciones y Directrices Específicas

| Sección | Extensión | Objetivo Crítico |
| :--- | :--- | :--- |
| **Abstract / Intro** | 0.75 págs | Problematizar la falta de razonamiento lógico en LLMs. Proponer segregación motor-simbólico/generador-natural. |
| **Estado del Arte** | 1.00 pág | Falsar sistemas tradicionales (ITS rígidos) y LLMs puros (inconsistencia matemática). |
| **Arq. Neuro-Simbólica** | 1.50 págs | **Médula Técnica:** SymPy para validación, Protocolo JSON inmutable, LLM restringido a lenguaje natural. |
| **Árbol de Heurísticas** | 1.25 págs | Prioridad didáctica (ej. reducción vs transposición). Manejo de errores y contra-heurísticas. |
| **Integración Visual** | 1.00 pág | Mapeo JSON -> Manim. Estrategias de optimización de latencia de video. |
| **Discusión / Futuro** | 0.50 págs | Honestidad intelectual: escalabilidad y costo computacional. |

## 3. Reglas Innegociables de Redacción (Normativa Interna)
- **Aislamiento Bibliográfico:** Solo citar papers en la carpeta local. Prohibido usar conocimiento general del LLM para citas.
- **Gráficos "Modern Print":** Diagramas Mermaid en escala de grises/blanco sólido. Nada de colores por defecto.
- **Protocolo de Trazabilidad:** Cada sesión de trabajo DEBE registrarse en el `00_Diario_Observacion.md` (Iteración HITL).
- **Control de Alucinaciones:** El sistema no debe proponer matemáticas. El motor simbólico (SymPy) es la única fuente de verdad.

## 4. Instrucciones de Procedimiento (Siguiente Paso)
1. **Fase de Literatura:** Ejecutar `Batch Review Papers` sobre la carpeta de fuentes para extraer "State of the Art".
2. **Fase de Datos:** Proveer métricas de efectividad (Herramienta vs LLM Puro) y tiempos de ejecución para la sección de resultados.
3. **Escritura Modular:** Cargar cada archivo `.md` de la carpeta `manuscrito/` utilizando las Skills especializadas suministradas.

---
> [!IMPORTANT]
> Si no se cuenta con un MVP funcional con métricas, el artículo debe declararse como **Diseño Arquitectónico Teórico** para evitar especulación de rendimiento.
