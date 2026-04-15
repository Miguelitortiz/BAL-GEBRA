package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"io"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
)

// Engine gestiona la comunicación con el proceso Python/SymPy.
type Engine struct {
	cmd    *exec.Cmd
	stdin  io.WriteCloser
	reader *bufio.Reader
}

// NewEngine inicia el proceso Python y devuelve el engine conectado.
func NewEngine(scriptPath string) (*Engine, error) {
	python := "python3"
	if runtime.GOOS == "windows" {
		python = "python"
	}
	abs, err := filepath.Abs(scriptPath)
	if err != nil {
		return nil, fmt.Errorf("ruta absoluta de script: %w", err)
	}

	cmd := exec.Command(python, abs)
	stdin, err := cmd.StdinPipe()
	if err != nil {
		return nil, fmt.Errorf("stdin pipe: %w", err)
	}
	stdout, err := cmd.StdoutPipe()
	if err != nil {
		return nil, fmt.Errorf("stdout pipe: %w", err)
	}
	cmd.Stderr = nil // silence stderr so it doesn't pollute output

	if err := cmd.Start(); err != nil {
		return nil, fmt.Errorf("iniciar Python: %w", err)
	}

	return &Engine{
		cmd:    cmd,
		stdin:  stdin,
		reader: bufio.NewReader(stdout),
	}, nil
}

// Call envía una solicitud al engine Python y devuelve la respuesta.
func (e *Engine) Call(req SymPyRequest) (SymPyResponse, error) {
	data, err := json.Marshal(req)
	if err != nil {
		return SymPyResponse{}, fmt.Errorf("marshal request: %w", err)
	}

	if _, err := fmt.Fprintf(e.stdin, "%s\n", data); err != nil {
		return SymPyResponse{}, fmt.Errorf("write to Python: %w", err)
	}

	line, err := e.reader.ReadString('\n')
	if err != nil {
		return SymPyResponse{}, fmt.Errorf("read from Python: %w", err)
	}

	var resp SymPyResponse
	if err := json.Unmarshal([]byte(strings.TrimSpace(line)), &resp); err != nil {
		return SymPyResponse{}, fmt.Errorf("unmarshal response: %w", err)
	}
	return resp, nil
}

// Close cierra el engine Python.
func (e *Engine) Close() {
	e.stdin.Close()
	e.cmd.Wait()
}
