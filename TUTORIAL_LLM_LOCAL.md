# Guía de Conexión: Ejecutando el Tutor Neuro-Simbólico Localmente (Mac mini M4)

Para correr la demostración interactiva (`app.py`), necesitas dos componentes corriendo en paralelo en tu máquina: 
1. **Tu LLM local** (el cerebro discursivo).
2. **El Frontend Streamlit** (la pizarra y el orquestador matemático).

Sigue estos pasos. Al tener una **Mac mini M4**, estás corriendo el programa con una ventaja increíble: su arquitectura de Memoria Unificada permite saltarse los cuellos de botella clásicos de PCIe. La RAM funciona directamente como VRAM del procesador gráfico, ¡haciendo que los LLMs sean ultra-rápidos!

---

## 1. Encender el Motor LLM (Ollama)

[Ollama](https://ollama.com/) te permite aprovechar los núcleos del M4 ("Apple Neural Engine") sin configuraciones extrañas.

1. **Instala Ollama:**
   Lo más fácil en Mac es descargar la aplicación [directamente de Ollama.com](https://ollama.com/download/mac). Ábrelo por primera vez y el ícono de la llama se quedará arriba en tu barra de menú superior.
   *(Nota: si prefieres Homebrew, usa `brew install --cask ollama` y arráncalo).*

2. **Descarga un Modelo Inteligente:**
   Abre una terminal nueva ("Terminal.app"). Te sugiero *Llama 3 de Meta*:
   ```bash
   ollama pull llama3
   ```
   *Tu Mac mini M4 se merendará este modelo en ejecución de inferencia ultrarrápida.*

3. **Inicia el Servidor de Ollama (Segundo plano):**
   A veces, abrir la aplicación en tu Mac ya levanta el servicio pero, en caso contrario, bastará con correr:
   ```bash
   ollama serve
   ```
   *Déjalo corriendo en ESA ventana terminal o como proceso de macOS. Escucha nativamente en `http://localhost:11434`.*

---

## 2. Preparar el Ecosistema en macOS

En macOS debes instalar las paqueterías pre-compiladas si deseas usar el motor visual (Manim) además del motor lógico. Para ello [instala Homebrew en tu terminal](https://brew.sh/es/) si no lo tienes.

```bash
# Instala herramientas audiovisuales ultra necesarias para compilar Manim en el Mac
brew install ffmpeg cairo pango pkg-config go

# Ubícate en el directorio de tu proyecto
cd "/Users/TU_NOMBRE_DE_USUARIO/Carpeta/Hacia/El/Proyecto"

# Crea un entorno virtual e instala los binarios de python
python3 -m venv tutor_env
source tutor_env/bin/activate
pip install numpy sympy manim streamlit requests
```

---

## 3. Configurar el Enlace en el Código

Si abres el archivo `app.py` notarás que ya lo he puenteado a la dirección de Ollama por defecto:

```python
# Extracto de app.py
OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3" # <--- Si descargaste otro como "mistral" o "phi3", cámbialo aquí.
```
*Si decidiste decargar un modelo de razonamiento matemático nativo (e.g. `qwen2-math`), simplemente reemplaza donde dice `"llama3"` dentro de `app.py`.*

---

## 4. Lanzar la Aplicación Streamlit

Aún en tu terminal con el `tutor_env` corriendo (y situado en el directorio de `app.py`), lanza la aplicación:

```bash
streamlit run app.py
```

Automáticamente se abrirá una pestaña de Safari o Chrome apuntando a `http://localhost:8501`.

---

## 5. ¡A Probar la Arquitectura Neuro-Simbólica!

Tu MVP web dividirá la pantalla. 
1. Escribe en el chat: **"¿Me ayudas con la resolución?"**. Observarás cómo el LLM lee el diagnóstico del Orquestador SymPy/Go y te responde socráticamente.
2. Atrévete a equivocarte. Ingresa un error intencional matemático en el chat como: `3*x = x + 10`. 
3. Maravíllate viendo cómo Streamlit cruza tus comandos vía Go, Go frena al LLM con el error numérico en fracciones de segundo (usando tu chip M4), y el LLM te manda una pista empática.
