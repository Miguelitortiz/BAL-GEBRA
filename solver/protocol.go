package main

// SymPyRequest es la estructura que se serializa a JSON y se envía a Python.
type SymPyRequest struct {
	Accion           string `json:"accion"`
	Ecuacion         string `json:"ecuacion"`
	EcuacionOriginal string `json:"ecuacion_original,omitempty"` // sólo para "validar"
}

// SymPyResponse es la respuesta deserializada que devuelve Python.
type SymPyResponse struct {
	Valido      bool   `json:"valido"`
	Resultado   string `json:"resultado"`
	Descripcion string `json:"descripcion,omitempty"`
	Error       string `json:"error,omitempty"`
}

// Step representa un paso (hint) en la traza.
type Step struct {
	Estado      string `json:"estado"`
	Accion      string `json:"accion"`
	Descripcion string `json:"descripcion"`
	Resultado   string `json:"resultado"`
}

// ValidationResponse representa el resultado de la validación matemática.
type ValidationResponse struct {
	PasoValido bool   `json:"paso_valido"`
	Error      string `json:"error,omitempty"`
}
