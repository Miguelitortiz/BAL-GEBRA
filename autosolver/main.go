package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
)

func usage() {
	fmt.Fprintf(os.Stderr, "Uso: go run . \"<ecuacion>\"\n")
	fmt.Fprintf(os.Stderr, "Ejemplo: go run . \"3*(x+2) - 5 = (x-3)/4 + 1/2\"\n")
}

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(1)
	}

	ecuacion := os.Args[1]

	// Construir ruta al script Python (mismo directorio que este binario / módulo).
	_, selfFile, _, _ := runtime.Caller(0)
	scriptDir := filepath.Dir(selfFile)
	scriptPath := filepath.Join(scriptDir, "sympy_engine.py")

	// Para `go run .`, runtime.Caller da la ruta real del .go, así que funciona.
	// Si se compila como binario, usar directorio del ejecutable.
	if _, err := os.Stat(scriptPath); os.IsNotExist(err) {
		exe, _ := os.Executable()
		scriptPath = filepath.Join(filepath.Dir(exe), "sympy_engine.py")
	}

	fmt.Printf("╔══════════════════════════════════════════════════════════╗\n")
	fmt.Printf("║       Solver Simbólico Híbrido  Go + SymPy               ║\n")
	fmt.Printf("╚══════════════════════════════════════════════════════════╝\n")
	fmt.Printf("Ecuación: %s\n\n", ecuacion)

	// Iniciar engine Python.
	engine, err := NewEngine(scriptPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error al iniciar Python: %v\n", err)
		os.Exit(2)
	}
	defer engine.Close()

	// Ejecutar solver.
	solver := NewSolver(engine, ecuacion)
	steps, err := solver.Run()

	// Imprimir traza de pasos.
	fmt.Println("─── Traza de pasos ───────────────────────────────────────")
	for i, step := range steps {
		label := step.Descripcion
		if label == "" {
			label = step.Accion
		}
		fmt.Printf("Paso %d  [%s]\n", i+1, label)
		fmt.Printf("  Antes:   %s\n", step.Estado)
		fmt.Printf("  Después: %s\n\n", step.Resultado)
	}

	if err != nil {
		fmt.Fprintf(os.Stderr, "\n✗ Error: %v\n", err)
		os.Exit(3)
	}

	fmt.Println("─── Resultado ────────────────────────────────────────────")
	fmt.Printf("  ✓ %s\n\n", solver.ecuacionActual)

	// Emitir también JSON estructurado.
	fmt.Println("─── JSON estructurado ────────────────────────────────────")
	out, _ := json.MarshalIndent(steps, "", "  ")
	fmt.Println(string(out))
}
