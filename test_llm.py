import requests
import json
import sys

URL = "http://localhost:11434/api/chat"
MODEL = "llama3"

print("========================================")
print(f"Probando conexión cruda con Ollama ({MODEL})...")
print("========================================\n")

payload = {
    "model": MODEL,
    "messages": [
        {
            "role": "system", 
            "content": "Eres un tutor matemático muy estricto. Responde estrictamente con '¡Conexión exitosa, soy el LLM!' y nada más."
        },
        {
            "role": "user",
            "content": "hola"
        }
    ],
    "stream": False,
    "options": {
        "temperature": 0.1
    }
}

try:
    print("Enviando petición HTTP a Ollama local...")
    response = requests.post(URL, json=payload, timeout=20)
    print("Código de estado HTTP:", response.status_code)
    
    if response.status_code == 200:
        data = response.json()
        print("\n[RESPUESTA CRUDA DEL MODELO]:")
        print(data.get("message", {}).get("content", ">> Vacio <<"))
    else:
        print("\n[ERROR HTTP]:", response.text)
        
except Exception as e:
    print(f"\n[Fallo catastrófico de conexión]: {e}")
    print("Asegúrate de que 'ollama serve' esté corriendo en otra terminal.")
