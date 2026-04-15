package main

import (
	"fmt"
	"strings"
)

// HeuristicName identifica una acción simbólica atómica.
type HeuristicName = string

const (
	HConstantes   HeuristicName = "simplificar_constantes"
	HDistributiva HeuristicName = "aplicar_distributiva"
	HDenominador  HeuristicName = "eliminar_denominador"
	HDenomSim     HeuristicName = "eliminar_denominador_simbolico"
	HSemejantes   HeuristicName = "reducir_semejantes"
	HVoltear      HeuristicName = "voltear_ecuacion"
	HFraccion     HeuristicName = "simplificar_fraccion"
	HConstanteLHS HeuristicName = "mover_constante_lhs"
	HVariableRHS  HeuristicName = "mover_variable_rhs"
	HDividirCoef  HeuristicName = "dividir_coeficiente"
)

// orderedHeuristics define el orden de prioridad de aplicación.
// El loop reinicia desde aquí después de cada paso exitoso.
var orderedHeuristics = []HeuristicName{
	HConstantes,   // 0. Evaluar aritmética constante
	HDistributiva, // 1. Expandir paréntesis
	HSemejantes,   // 2. Reducir términos semejantes ANTES de eliminar denominadores
	HFraccion,     // 2.5 Simplificar fracciones si las hay
	HDenominador,  // 3. Eliminar fracciones numéricas
	HDenomSim,     // 4. Eliminar denominadores simbólicos (×x)
	HVoltear,      // 5. Voltear si x está solo en el RHS
	HConstanteLHS, // 6. Pasar constantes del LHS al RHS
	HVariableRHS,  // 7. Pasar términos con x del RHS al LHS
	HDividirCoef,  // 8. Dividir entre coeficiente de x
}

const maxIterations = 40

// Solver encapsula el estado y el árbol de heurísticas.
type Solver struct {
	engine         *Engine
	ecuacionActual string
	steps          []Step
}

// NewSolver crea un Solver con la ecuación inicial.
func NewSolver(engine *Engine, ecuacion string) *Solver {
	return &Solver{engine: engine, ecuacionActual: ecuacion}
}

// isSolved reporta si la ecuación tiene forma "x = <expr>" sin x en el RHS.
func isSolved(ecuacion string) bool {
	parts := strings.SplitN(ecuacion, "=", 2)
	if len(parts) != 2 {
		return false
	}
	lhs := strings.TrimSpace(parts[0])
	rhs := strings.TrimSpace(parts[1])
	return lhs == "x" && !strings.Contains(rhs, "x")
}

// normalize limpia espacios para comparación de no-op.
func normalize(s string) string {
	return strings.ReplaceAll(strings.TrimSpace(s), " ", "")
}

// isNoOp detecta que un paso no cambió la ecuación.
func isNoOp(before, after string) bool {
	return normalize(before) == normalize(after)
}

// Run ejecuta el árbol de heurísticas paso a paso.
// Después de cada paso exitoso reinicia desde la heurística #1,
// garantizando prioridad correcta en todo momento.
func (s *Solver) Run() ([]Step, error) {
	for iter := 0; iter < maxIterations; iter++ {
		if isSolved(s.ecuacionActual) {
			break
		}

		progress := false

		for _, heuristica := range orderedHeuristics {
			req := SymPyRequest{
				Accion:   heuristica,
				Ecuacion: s.ecuacionActual,
			}

			resp, err := s.engine.Call(req)
			if err != nil {
				return s.steps, fmt.Errorf("error en '%s': %w", heuristica, err)
			}

			// Si no cambió nada o no fue válido, intentar siguiente heurística.
			if !resp.Valido || isNoOp(s.ecuacionActual, resp.Resultado) {
				continue
			}

			// Paso exitoso: registrar y reiniciar desde heurística #1.
			s.steps = append(s.steps, Step{
				Estado:      s.ecuacionActual,
				Accion:      heuristica,
				Descripcion: resp.Descripcion,
				Resultado:   resp.Resultado,
			})
			s.ecuacionActual = resp.Resultado
			progress = true
			break // ← reinicia el for de heurísticas
		}

		if !progress {
			return s.steps, fmt.Errorf(
				"no se puede continuar: estado = %s", s.ecuacionActual,
			)
		}
	}

	if !isSolved(s.ecuacionActual) {
		return s.steps, fmt.Errorf(
			"no se pudo resolver: estado final = %s", s.ecuacionActual,
		)
	}

	// Post-procesamiento: si la ecuación resuelta es una fracción reducible (ej. x = -26/6),
	// apply simplificar_fraccion one last time.
	req := SymPyRequest{
		Accion:   HFraccion,
		Ecuacion: s.ecuacionActual,
	}
	if resp, err := s.engine.Call(req); err == nil && resp.Valido && !isNoOp(s.ecuacionActual, resp.Resultado) {
		s.steps = append(s.steps, Step{
			Estado:      s.ecuacionActual,
			Accion:      HFraccion,
			Descripcion: resp.Descripcion,
			Resultado:   resp.Resultado,
		})
		s.ecuacionActual = resp.Resultado
	}

	return s.steps, nil
}
