import streamlit as st
import subprocess
import json
import requests
import os

# --- ARCHITECTURE CONFIGURATION ---
st.set_page_config(page_title="Neuro-Symbolic LLM Tutor", layout="wide")

# Rutas absolutas a nuestros módulos (Go y Bash/Manim)
SOLVER_CMD = "./solver/solver"  # Asumiendo que se ejecuta desde la raíz del proyecto
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
    st.session_state.equation = "3*x - 2 = x + 4"
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "¡Hola! Estoy aquí para ayudarte a resolver ecuaciones. Observa la ecuación en la pantalla. ¿Qué paso te gustaría hacer primero?"}
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

def ask_llm_locally(prompt_text):
    """Hace ping a Ollama pasándole nuestro mensaje inyectado con los metadatos de SymPy"""
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt_text}
        ],
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=10)
        return response.json().get("message", {}).get("content", "Error al leer del LLM.")
    except Exception:
         return "(El LLM local no está respondiendo. Verifica que Ollama esté encendido en el puerto 11434). \n\n**JSON Simbólico Interno:**\n" + prompt_text

def update_video(old_eq, new_eq, desc):
    """Ejecuta Manim de forma asíncrona para mitigar latencia y actualiza la UI cuando acaba"""
    subprocess.run([MANIM_CMD, old_eq, new_eq, desc], cwd="./manim_module", capture_output=True)
    video_file = "./manim_module/media/videos/renderer/480p15/EquationTransition.mp4"
    if os.path.exists(video_file):
        st.session_state.video_path = video_file

# --- UI LAYOUT ---
col1, col2 = st.columns([1.5, 1])

# DERECHA: Pizarra Visual (Manim + Estado Actual)
with col2:
    st.header("Pizarra")
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
        # Mostrar lo que el usuario escribió
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Motor Simbólico + LLM pensando..."):
                # Si el input tiene "=", presumimos que intentó un paso matemático
                if "=" in prompt:
                    # Validar el paso
                    validation = run_solver("validate", st.session_state.equation, prompt)
                    
                    if validation.get("paso_valido"):
                        # Si es válido, animamos!
                        # Primero le preguntamos sutilmente al solver cómo se llamó ese paso algebraico
                        hint = run_solver("hint", st.session_state.equation)
                        desc = hint.get("descripcion", "Operación del alumno")
                        
                        update_video(st.session_state.equation, prompt, desc)
                        st.session_state.equation = prompt
                        
                        llm_prompt = f"El alumno ingresó el paso correcto '{prompt}'. Felicítalo brevemente."
                    else:
                        # Si es inválido, el LLM lee el diagnóstico exacto de nuestro árbol de Go
                        error_diagnostico = validation.get("error", "Error matemático desconocido.")
                        llm_prompt = f"El alumno ingresó '{prompt}' pero es incorrecto matemáticamente. El clasificador heurístico dictamina: '{error_diagnostico}'. Guía al alumno para que entienda el error, no le des la respuesta directa."
                else:
                    # Si sólo pide ayuda o hace una pregunta verbal, forzamos un HINT
                    hint = run_solver("hint", st.session_state.equation)
                    if "error" in hint:
                        llm_prompt = f"El alumno pidió ayuda. Dile que la ecuación '{st.session_state.equation}' ya está completamente resuelta."
                    else:
                        siguiente_paso = hint.get("resultado")
                        descripcion = hint.get("descripcion")
                        llm_prompt = f"El alumno pide ayuda. El siguiente paso heurístico correcto para la ecuación '{st.session_state.equation}' es llegar a '{siguiente_paso}' usando '{descripcion}'. Dale una ligera pista empática sin darle el resultado explícitamente."
                
                # Consumir el LLM local
                llm_response = ask_llm_locally(llm_prompt)
                st.markdown(llm_response)
                st.session_state.messages.append({"role": "assistant", "content": llm_response})
                st.rerun()
