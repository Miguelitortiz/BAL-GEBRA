Actúa como un ingeniero senior especializado en sistemas simbólicos híbridos (Go + Python). Diseña e implementa un sistema que resuelva ecuaciones algebraicas paso a paso desde CLI, usando Go como orquestador y SymPy como motor simbólico.

## Objetivo

Construir un sistema determinista que NO resuelva ecuaciones directamente, sino que genere una secuencia de transformaciones algebraicas válidas y verificables.

Ejemplo de input:

"3*(x+2) - 5 = (x-3)/4 + 1/2"

---

## Arquitectura obligatoria

### Go (orquestador principal)

Responsabilidades:

* Parsear input
* Mantener estado de la ecuación
* Implementar árbol de heurísticas (decidir siguiente paso)
* Construir salida estructurada
* Llamar a Python/SymPy para ejecutar transformaciones

---

### Python + SymPy (motor simbólico)

Responsabilidades:

* Aplicar transformaciones específicas solicitadas por Go
* Validar equivalencia algebraica entre estados
* Devolver resultado normalizado

IMPORTANTE:

* NO usar `solve()` directamente
* NO tomar decisiones heurísticas
* SOLO ejecutar acciones explícitas

---

## Comunicación entre Go y Python

Define un protocolo JSON estricto:

Input a SymPy:

{
"accion": "expandir",
"ecuacion": "3*(x+2) - 5 = (x-3)/4 + 1/2"
}

Output:

{
"valido": true,
"resultado": "3x + 6 - 5 = (x-3)/4 + 1/2"
}

---

## Heurísticas (implementadas en Go)

Orden obligatorio:

1. Expandir paréntesis
2. Eliminar fracciones (multiplicar por mcm)
3. Reducir términos semejantes
4. Agrupar variables en un lado
5. Aislar variable

Cada paso debe ser explícito y controlado.

---

## Validación (CRÍTICO)

Después de cada transformación:

* SymPy debe verificar:
  simplify(lhs_original - rhs_original) == simplify(lhs_nuevo - rhs_nuevo)

Si no se cumple:
→ rechazar paso

---

## Output final

Lista de pasos:

{
"estado": "...",
"accion": "...",
"resultado": "..."
}

---

## CLI

go run main.go "ecuacion"

---

## Entregables

1. Explicación de arquitectura
2. Código Go (orquestador)
3. Script Python con SymPy
4. Ejemplo de ejecución
5. Casos donde falla el sistema

---

## Restricción clave

El sistema debe demostrar que:

* Las decisiones son externas a SymPy
* SymPy solo ejecuta y valida
* Cada paso es trazable

Este diseño debe ser adecuado para un paper académico sobre sistemas neuro-simbólicos.
