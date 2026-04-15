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

// GetNextHint evalúa la ecuación paso a paso y devuelve únicamente la primer sugerencia útil.
// Si la ecuación ya está resuelta o no aplican heurísticas, devuelve un Step vacío y un error.
func (s *Solver) GetNextHint() (Step, error) {
	if isSolved(s.ecuacionActual) {
		// Verify if there's a reducible fraction left over
		req := SymPyRequest{
			Accion:   HFraccion,
			Ecuacion: s.ecuacionActual,
		}
		if resp, err := s.engine.Call(req); err == nil && resp.Valido && !isNoOp(s.ecuacionActual, resp.Resultado) {
			return Step{
				Estado:      s.ecuacionActual,
				Accion:      HFraccion,
				Descripcion: resp.Descripcion,
				Resultado:   resp.Resultado,
			}, nil
		}
		return Step{}, fmt.Errorf("la ecuación ya está resuelta")
	}

	for _, heuristica := range orderedHeuristics {
		req := SymPyRequest{
			Accion:   heuristica,
			Ecuacion: s.ecuacionActual,
		}

		resp, err := s.engine.Call(req)
		if err != nil {
			return Step{}, fmt.Errorf("error en '%s': %w", heuristica, err)
		}

		if !resp.Valido || isNoOp(s.ecuacionActual, resp.Resultado) {
			continue
		}

		// Encontramos la primera heurística útil. La devolvemos inmediatamente sin loopear.
		return Step{
			Estado:      s.ecuacionActual,
			Accion:      heuristica,
			Descripcion: resp.Descripcion,
			Resultado:   resp.Resultado,
		}, nil
	}

	return Step{}, fmt.Errorf("no se encontró ningún paso aplicable para: %s", s.ecuacionActual)
}

// EvaluateStep valida si el paso dado por el usuario es equivalente algebraicamente.
func (s *Solver) EvaluateStep(ecuacionUsuario string) (ValidationResponse, error) {
	req := SymPyRequest{
		Accion:           "validar",
		Ecuacion:         ecuacionUsuario,
		EcuacionOriginal: s.ecuacionActual,
	}

	resp, err := s.engine.Call(req)
	if err != nil {
		return ValidationResponse{PasoValido: false, Error: err.Error()}, err
	}

	return ValidationResponse{
		PasoValido: resp.Valido,
		Error:      resp.Error,
	}, nil
}
