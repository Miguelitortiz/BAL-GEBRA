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
MANIM_CMD = "../manim_module/generate_video.sh"

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
if "is_solved" not in st.session_state:
    st.session_state.is_solved = False
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

import sys
import re

def extract_equation(text):
    """Filtra la basura conversacional y extrae la pura ecuación matemática"""
    # Busca secuencias con números, la variable x, operadores matemáticos y el igual
    match = re.search(r'([0-9xX\s\+\-\*\/\(\)\^\.]+=[\s0-9xX\+\-\*\/\(\)\^\.]+)', text)
    if match:
        return match.group(1).strip()
    return text

def update_video(old_eq, new_eq, desc):
    """Ejecuta Manim garantizando el PATH del virtual environment local"""
    
    # 1. Logging a Consola
    print("\n\n" + "="*60)
    print("🎬 [MANIM VIDEO DEBUGGER]")
    print(f"🐍 Python VENV Engine: {sys.executable}")
    print(f"📥 Estado Anterior: {old_eq} | 📤 Estado Nuevo: {new_eq}")
    
    # 2. Inyectamos variables de entorno directamente al Subproceso (Simulamos lo que hacía bash)
    env = os.environ.copy()
    env["EQ_OLD"] = old_eq
    env["EQ_NEW"] = new_eq
    env["DESC"] = desc
    
    # 3. Mandamos llamar a Manim forzando estrictamente que use el VENV actual
    cmd = [
        sys.executable, "-m", "manim", "-ql", "--disable_caching", 
        "renderer.py", "EquationTransition"
    ]
    
    try:
        # cwd asegura que opere dentro de manim_module localizando a renderer.py
        result = subprocess.run(cmd, cwd="./manim_module", env=env, capture_output=True, text=True)
        print("\n--- STDOUT de Manim ---")
        print(result.stdout)
        print("\n--- STDERR de Manim ---")
        print(result.stderr)
        print("="*60 + "\n")
    except Exception as e:
        print(f"\n❌ [Excepción Fatal]: No se pudo iniciar el proceso Manim: {e}\n")

    # 4. Resolvemos el archivo de forma absoluta a los ojos de Streamlit (el cual corre en la raíz)
    # Volvemos a la ruta normal que funciona resolutivamente si el script se llama desde el root
    video_file = os.path.abspath("./manim_module/media/videos/renderer/480p15/EquationTransition.mp4")
    
    if os.path.exists(video_file):
        st.session_state.video_path = video_file
        print(f"✅ VIDEO CARGADO EXITOSAMENTE: {video_file}")
    else:
        print(f"⚠️ EL VIDEO FALLÓ EN GENERARSE (File not found en: {video_file})")

# --- UI LAYOUT ---
col1, col2 = st.columns([1.5, 1])

# DERECHA: Pizarra Visual (Manim + Estado Actual)
with col2:
    st.header("Pizarra")
    
    if st.session_state.equation == "":
        st.markdown("### (Pizarra en blanco)")
    else:
        # Aumentamos agresivamente el tamaño de la ecuación en la UI via LaTeX \huge
        st.markdown(f"### Estado Actual:\n$$ \\huge {st.session_state.equation} $$")
    
    if st.session_state.video_path:
        # Reproducir en bucle siempre
        st.video(st.session_state.video_path, loop=True, autoplay=True)
    else:
        st.info("La animación del paso aparecerá aquí.")
        
    if st.session_state.is_solved:
        st.success("¡Ecuación Completada!")
        if st.button("🔄 Comenzar Nueva Ecuación", use_container_width=True):
            st.session_state.equation = ""
            st.session_state.is_solved = False
            st.session_state.video_path = None
            st.session_state.messages = [
                {"role": "assistant", "content": "¡Hola de nuevo! Estoy listo. Escribe la nueva ecuación algebraica que resolveremos."}
            ]
            st.rerun()

# IZQUIERDA: Chat LLM
with col1:
    st.header("Tutor Inteligente")
    
    # Mostrar sólo los últimos 2 mensajes de la conversación, pero Ollama recuerda todos.
    mensajes_visibles = st.session_state.messages[-2:] if len(st.session_state.messages) > 1 else st.session_state.messages
    for msg in mensajes_visibles:
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
                        probe = run_solver("hint", clean_prompt)
                        
                        if "error" in probe and "Error" in str(probe.get("error")):
                            backend_context = f"El usuario intentó proponer la ecuación '{clean_prompt}' pero todavía contiene fallos de formato. Pídele amablemente que la escriba limpiamente sin espacios o letras raras."
                        else:
                            # Interceptamos la ecuación limpia
                            update_video("0 = 0", clean_prompt, "Iniciando la resolución algebraíca")
                            st.session_state.equation = clean_prompt
                            
                            # Validamos inmediamentamente si propuso una ecuación que YA está resuelta
                            probe_next = run_solver("hint", clean_prompt)
                            if "error" in probe_next:
                                st.session_state.is_solved = True
                            
                            backend_context = f"El usuario propuso la ecuación '{clean_prompt}'. Acéptala alegremente y dale una ligerísima pista de cómo empezar."
                    else:
                        # Validar el paso normal
                        validation = run_solver("validate", st.session_state.equation, clean_prompt)
                        
                        if validation.get("paso_valido"):
                            # Animamos el movimiento
                            hint_viejo = run_solver("hint", st.session_state.equation)
                            desc = hint_viejo.get("descripcion", "Operación del alumno")
                            
                            update_video(st.session_state.equation, clean_prompt, desc)
                            st.session_state.equation = clean_prompt
                            
                            # Re-evaluamos el Árbol Heurístico desde la nueva posición del alumno
                            probe_next = run_solver("hint", clean_prompt)
                            if "error" in probe_next:
                                st.session_state.is_solved = True
                                backend_context = f"El alumno resolvió exitosamente la ecuación con el paso VÁLIDO '{clean_prompt}'. Felicítalo efusivamente y menciónale que presione el botón de Reiniciar."
                            else:
                                proximo_paso = probe_next.get("resultado", "")
                                heuristica = probe_next.get("descripcion", "")
                                backend_context = f"El usuario dio un paso VÁLIDO ('{clean_prompt}'). Felicítalo. Además, el NUEVO paso sugerido por el orquestador desde aquí es aplicar: '{heuristica}'. Asígnale sutilmente esta pista para que no se pierda."
                        else:
                            # Si es inválido, el LLM lee el diagnóstico exacto de nuestro árbol de Go
                            error_diagnostico = validation.get("error", "Error matemático desconocido.")
                            backend_context = f"El usuario escribió el paso '{clean_prompt}', el cual es INVÁLIDO. Diagnóstico de Go: '{error_diagnostico}'. Guíalo a que encuentre su error de forma socrática, sin darle la respuesta."
                else:
                    # Si no hay '=', fue conversación normal ("hola", "ayuda", "¿y qué hago?")
                    if st.session_state.equation == "":
                        backend_context = "Todavía no hay ninguna ecuación en la pizarra. Pídele amablemente que escriba la ecuación con la que quiere trabajar hoy."
                    else:
                        hint = run_solver("hint", st.session_state.equation)
                        if "error" in hint:
                            st.session_state.is_solved = True
                            backend_context = f"La ecuación está totalmente resuelta. Felicítalo y dile que presione el botón de nueva ecuación."
                        else:
                            descripcion = hint.get("descripcion")
                            backend_context = f"El paso idóneo sugerido por el Motor lógico ahora mismo es aplicar: '{descripcion}'. Usa esta información para darle una ligera pista conversacional ya que te lo está pidiendo."
                
                # Consumir el LLM local
                llm_response = ask_llm_locally(prompt, backend_context)
                st.markdown(llm_response)
                st.session_state.messages.append({"role": "assistant", "content": llm_response})
                st.rerun()
