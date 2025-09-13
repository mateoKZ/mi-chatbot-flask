import os
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# --- CONFIGURACIÓN DE IA ---
# Lee la clave de API desde las variables de entorno
api_key = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

# Configuración del modelo Gemini
generation_config = {
  "temperature": 0.9,
  "top_p": 1,
  "top_k": 1,
  "max_output_tokens": 2048,
}
safety_settings = [
  { "category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE" },
  { "category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE" },
  { "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE" },
  { "category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE" },
]
model = genai.GenerativeModel(model_name="gemini-pro",
                              generation_config=generation_config,
                              safety_settings=safety_settings)
# -------------------------


# --- APLICACIÓN FLASK (esto casi no cambia) ---
app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

# ¡AQUÍ ESTÁ LA NUEVA MAGIA!
def get_response(user_message):
    """
    Genera una respuesta usando la IA de Gemini.
    """
    try:
        # Esto se llama "Prompt Engineering". Le damos contexto a la IA.
        # ¡Puedes cambiar esta personalidad como quieras!
        prompt_template = f"""
        Eres "ChatBoty", un asistente virtual amigable, un poco sarcástico y muy útil que vive en Argentina.
        Tu objetivo es responder las preguntas del usuario de forma concisa y con un toque de humor porteño.
        No respondas preguntas sobre política o temas ofensivos.

        Usuario: "{user_message}"
        ChatBoty:
        """
        
        # Llama a la API de Gemini
        response = model.generate_content(prompt_template)
        
        # Devuelve solo el texto de la respuesta
        return response.text

    except Exception as e:
        print(f"Error al llamar a la API de Gemini: {e}")
        return "Upa, parece que se me quemaron los cables. Intenta de nuevo en un ratito."


@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    user_message = data.get('message')
    if not user_message:
        return jsonify({'error': 'No se recibió ningún mensaje'}), 400
    
    # ¡Ahora llamamos a nuestra nueva función inteligente!
    bot_reply = get_response(user_message)
    
    return jsonify({'response': bot_reply})


if __name__ == '__main__':
    app.run(debug=True, port=5001)