import streamlit as st
import subprocess
import json
import requests
import os

# --- ARCHITECTURE CONFIGURATION ---
st.set_page_config(page_title="Neuro-Symbolic LLM Tutor", layout="wide")

# Rutas absolutas a nuestros módulos (Go y Bash/Manim)
# Revertido al target dinámico para que use tu compilación nativa en la Mac
SOLVER_CMD = "./solver/solver"  
MANIM_CMD = "./manim_module/generate_video.sh"

# Configuración del LLM Local (Ollama por defecto)
OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3"  # Modificar al modelo descargado localmente (ej. mistral, phi3)

# Prompt del Sistema: Evita alucinaciones matemáticas obligando al LLM a seguir el JSON
SYSTEM_PROMPT = """Eres un tutor socrático de álgebra estricto. DEBES cumplir las siguientes reglas al pie de la letra:
1. IDIOMA: Responde ÚNICA Y EXCLUSIVAMENTE en Español neutro. Prohibido usar inglés u otros idiomas, incluso si el usuario lo hace.
2. BREVEDAD: Responde en máximo 1 o 2 oraciones breves y empáticas.
3. CERO ALUCINACIONES: Tú NO sabes resolver ecuaciones. Tu único conocimiento real viene del JSON que se te inyecta en el prompt. 
4. REGLA DE NO-SPOILER: NUNCA le digas al estudiante la respuesta final ni le des el paso resuelto. Si el JSON recomienda sumar X, dile: "¿Qué pasaría si sumamos X en ambos lados?"
5. EN CASO DE ERROR: Si el JSON indica que el alumno cometió un error numérico o de signo, explícaselo basándote estrictamente en la razón técnica que te dice el JSON. No inventes posibles errores."""

# --- SESSION STATE ---
if "equation" not in st.session_state:
    st.session_state.equation = ""
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "¡Hola! Estoy aquí para acompañarte a practicar. Escribe la ecuación algebraica con la que quieres empezar en el chat."}
    ]
if "video_path" not in st.session_state:
    st.session_state.video_path = None

# --- HELPER FUNCTIONS ---
def run_solver(*args):
    """Ejecuta el Go Orchestrator de manera atómica"""
    cmd = [SOLVER_CMD] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Extraemos el bloque JSON escupido al final del comando de Go
    output = result.stdout.strip()
    try:
        # El JSON empieza en el último corchete o llave
        json_start = output.rfind('{')
        if json_start != -1:
            return json.loads(output[json_start:])
    except Exception:
        pass
    return {"error": result.stderr}

def ask_llm_locally(user_prompt, backend_context):
    """Hace ping a Ollama pasándole nuestro historial, el mensaje y el contexto oculto de SymPy"""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Agregar todo el historial previo
    for msg in st.session_state.messages[:-1]:
        messages.append({"role": msg["role"], "content": msg["content"]})
        
    # Colocar primero lo que dijo el usuario, y al final una instrucción estricta de sistema reducida
    combined_prompt = f"{user_prompt}\n\n[INFO INTERNA (NO MENCIONAR)]: {backend_context}"
    
    messages.append({"role": "user", "content": combined_prompt})

    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.2  # Endurece el modelo para evitar alucinaciones
        }
    }
    
    # --- DIAGNÓSTICO (IMPRESIÓN A LA CONSOLA DONDE CORRE STREAMLIT) ---
    print("\n\n" + "="*60)
    print("🚀 [LLM PAYLOAD DEBUGGER] - ENVIANDO A OLLAMA LOCAL")
    print("="*60)
    print(json.dumps(payload["messages"], indent=2, ensure_ascii=False))
    print("="*60 + "\n\n")
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=10)
        return response.json().get("message", {}).get("content", "Error al leer del LLM.")
    except Exception:
         return "(El LLM local no está respondiendo. Verifica que Ollama esté encendido). \n\n**JSON Simbólico Interno:**\n" + backend_context

import re

def extract_equation(text):
    """Filtra la basura conversacional y extrae la pura ecuación matemática"""
    # Busca secuencias con números, la variable x, operadores matemáticos y el igual
    match = re.search(r'([0-9xX\s\+\-\*\/\(\)\^\.]+=[\s0-9xX\+\-\*\/\(\)\^\.]+)', text)
    if match:
        return match.group(1).strip()
    return text

def update_video(old_eq, new_eq, desc):
    """Ejecuta Manim de forma asíncrona para mitigar latencia y actualiza la UI cuando acaba"""
    subprocess.run([MANIM_CMD, old_eq, new_eq, desc], cwd="./manim_module", capture_output=True)
    video_file = "../manim_module/media/videos/renderer/480p15/EquationTransition.mp4"
    if os.path.exists(video_file):
        st.session_state.video_path = video_file

# --- UI LAYOUT ---
col1, col2 = st.columns([1.5, 1])

# DERECHA: Pizarra Visual (Manim + Estado Actual)
with col2:
    st.header("Pizarra")
    
    if st.session_state.equation == "":
        st.markdown("### (Pizarra en blanco)")
    else:
        st.markdown(f"### Estado Actual:\n$${st.session_state.equation}$$")
    
    if st.session_state.video_path:
        st.video(st.session_state.video_path)
    else:
        st.info("La animación del paso aparecerá aquí.")

# IZQUIERDA: Chat LLM
with col1:
    st.header("Tutor Inteligente")
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Escribe tu paso algebraico (ej. 3*x = x + 6) o pide una pista..."):
        # Mostrar lo que el usuario escribió textualmente en el chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Motor Simbólico + LLM pensando..."):
                
                # Extraer la ecuación si el usuario escribió texto mixto
                clean_prompt = extract_equation(prompt)
                
                # Si el input resultante tiene "=", presumimos que intentó un paso matemático
                if "=" in clean_prompt:
                    if st.session_state.equation == "":
                        # Verificamos furtivamente si la ecuación inicial tiene formato matemático limpio
                        # usando el motor para atrapar basurilla (ej. "quiero resolver 3x=9")
                        probe = run_solver("hint", clean_prompt)
                        
                        if "error" in probe and "Error" in str(probe.get("error")):
                            backend_context = f"El usuario intentó proponer la ecuación '{clean_prompt}' pero todavía contiene fallos de formato. Pídele amablemente que la escriba limpiamente (ej. '3*x - 1 = 9')."
                        else:
                            # Si es la primera vez y el parseo sobrevivió, interceptamos la ecuación limpia
                            update_video("0 = 0", clean_prompt, "Iniciando la resolución algebraíca")
                            st.session_state.equation = clean_prompt
                            backend_context = f"El usuario te trajo esta ecuación con lenguaje natural: '{prompt}'. El sistema extrajo matemáticamente '{clean_prompt}'. Acéptala alegremente y dile que empiecen."
                    else:
                        # Validar el paso normal
                        validation = run_solver("validate", st.session_state.equation, clean_prompt)
                        
                        if validation.get("paso_valido"):
                            # Si es válido, animamos!
                            hint = run_solver("hint", st.session_state.equation)
                            desc = hint.get("descripcion", "Operación del alumno")
                            
                            update_video(st.session_state.equation, clean_prompt, desc)
                            st.session_state.equation = clean_prompt
                            
                            backend_context = f"El usuario escribió: '{prompt}'. Su paso matemático extraído '{clean_prompt}' es VÁLIDO matemática y lógicamente. Felicítalo empáticamente."
                        else:
                            # Si es inválido, el LLM lee el diagnóstico exacto de nuestro árbol de Go
                            error_diagnostico = validation.get("error", "Error matemático desconocido.")
                            backend_context = f"El usuario escribió: '{prompt}'. Su paso '{clean_prompt}' es INVÁLIDO. Diagnóstico de Go: '{error_diagnostico}'. Guíalo a que encuentre su error sin regalarle respuestas."
                else:
                    # Si no hay '=', fue conversación normal ("hola", "ayuda", "¿y qué hago?")
                    if st.session_state.equation == "":
                        backend_context = "Todavía no hay ninguna ecuación en la pizarra. Pídele amablemente que escriba la ecuación con la que quiere trabajar hoy."
                    else:
                        hint = run_solver("hint", st.session_state.equation)
                        if "error" in hint:
                            backend_context = f"La ecuación está totalmente resuelta. Felicítalo y dile que ya acabaron."
                        else:
                            siguiente_paso = hint.get("resultado")
                            descripcion = hint.get("descripcion")
                            backend_context = f"El paso idóneo sugerido por el Motor ahora mismo es aplicar: '{descripcion}'. Usa esta información para darle una ligera pista conversacional."
                
                # Consumir el LLM local
                llm_response = ask_llm_locally(prompt, backend_context)
                st.markdown(llm_response)
                st.session_state.messages.append({"role": "assistant", "content": llm_response})
                st.rerun()
