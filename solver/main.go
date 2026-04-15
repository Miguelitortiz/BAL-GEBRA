package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
)

func usage() {
	fmt.Fprintf(os.Stderr, "Uso como API Pedagógica Reactiva:\n")
	fmt.Fprintf(os.Stderr, "  go run . hint \"<ecuacion>\"\n")
	fmt.Fprintf(os.Stderr, "     Devuelve la siguiente heurística sugerida.\n\n")
	fmt.Fprintf(os.Stderr, "  go run . validate \"<ecuacion_vieja>\" \"<ecuacion_nueva>\"\n")
	fmt.Fprintf(os.Stderr, "     Verifica algebraicamente si el paso del usuario es válido.\n")
}

func main() {
	if len(os.Args) < 3 {
		usage()
		os.Exit(1)
	}

	command := os.Args[1]

	// Construir ruta al script Python (mismo directorio que este binario / módulo).
	_, selfFile, _, _ := runtime.Caller(0)
	scriptDir := filepath.Dir(selfFile)
	scriptPath := filepath.Join(scriptDir, "sympy_engine.py")

	if _, err := os.Stat(scriptPath); os.IsNotExist(err) {
		exe, _ := os.Executable()
		scriptPath = filepath.Join(filepath.Dir(exe), "sympy_engine.py")
	}

	// Iniciar engine Python.
	engine, err := NewEngine(scriptPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error al iniciar Python: %v\n", err)
		os.Exit(2)
	}
	defer engine.Close()

	if command == "hint" {
		ecuacion := os.Args[2]
		solver := NewSolver(engine, ecuacion)
		step, err := solver.GetNextHint()

		if err != nil {
			fmt.Fprintf(os.Stderr, "✗ Error o sin sugerencias: %v\n", err)
			os.Exit(3)
		}

		fmt.Printf("Pista Pedagógica: %s\n", step.Descripcion)
		fmt.Printf("Resultado Esperado: %s\n\n", step.Resultado)

		out, _ := json.MarshalIndent(step, "", "  ")
		fmt.Println(string(out))

	} else if command == "validate" {
		if len(os.Args) < 4 {
			usage()
			os.Exit(1)
		}
		ecuacionVieja := os.Args[2]
		ecuacionNueva := os.Args[3]

		solver := NewSolver(engine, ecuacionVieja)
		resp, err := solver.EvaluateStep(ecuacionNueva)
		if err != nil {
			fmt.Fprintf(os.Stderr, "✗ Error interno al validar: %v\n", err)
			os.Exit(3)
		}

		if resp.PasoValido {
			fmt.Println("✅ El paso es matemáticamente VÁLIDO.")
		} else {
			fmt.Println("❌ El paso es matemáticamente INVÁLIDO.")
			if resp.Error != "" {
				fmt.Printf("Detalle: %s\n", resp.Error)
			}
		}

		out, _ := json.MarshalIndent(resp, "", "  ")
		fmt.Println("\n" + string(out))

	} else {
		fmt.Fprintf(os.Stderr, "Comando desconocido: %s\n", command)
		usage()
		os.Exit(1)
	}
}
