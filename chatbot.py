import os
import requests
import google.generativeai as genai
from flask import Flask, request, jsonify

# --- CONFIGURACIÓN (Leemos todo desde variables de entorno) ---
# Clave de API de Gemini (ya la tenías)
GEMINI_API_KEY = os.environ.get("GOOGLE_API_KEY")

# ¡NUEVO! Credenciales de Meta
META_VERIFY_TOKEN = os.environ.get("META_VERIFY_TOKEN") # El que inventaste (ej: MI_CHATBOT_ES_GENIAL_123)
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN") # El token que aparece en tu captura de pantalla
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID") # El "Identificador de número de teléfono" de tu captura

# Configuración del modelo Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name="gemini-2.5-flash")

# --- APLICACIÓN FLASK ---
app = Flask(__name__)

# --- LÓGICA DE LA IA (no cambia) ---
def get_response(user_message):
    # (El código de esta función es exactamente el mismo que ya tenías)
    try:
        prompt_template = f"""
        Eres "ChatBoty", un asistente virtual amigable, un poco sarcástico y muy útil que vive en Argentina.
        Tu objetivo es responder las preguntas del usuario de forma concisa y con un toque de humor porteño.

        Usuario: "{user_message}"
        ChatBoty:
        """
        response = model.generate_content(prompt_template)
        return response.text
    except Exception as e:
        print(f"Error al llamar a la API de Gemini: {e}")
        return "Upa, parece que se me quemaron los cables. Intenta de nuevo en un ratito."

# --- ¡NUEVA FUNCIÓN PARA ENVIAR MENSAJES CON MÁS LOGS! ---
def send_whatsapp_message(to_number, message):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": { "body": message }
    }

    # --- LOGS DE DEPURACIÓN (ESTO ES LO IMPORTANTE) ---
    print("--- Intentando enviar mensaje a WhatsApp ---")
    print(f"URL: {url}")
    # Ocultamos la mayor parte del token en el log por seguridad
    print(f"Headers: {{'Authorization': 'Bearer EAA...{META_ACCESS_TOKEN[-5:]}', 'Content-Type': 'application/json'}}")
    print(f"Data (payload): {data}")
    print("-----------------------------------------")

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        print(f"Mensaje enviado a {to_number}: {response.json()}")
    except requests.exceptions.RequestException as e:
        # Imprimimos el contenido del error si está disponible
        error_details = e.response.json() if e.response else str(e)
        print(f"Error al enviar mensaje a WhatsApp: {e} - Detalles: {error_details}")

# --- WEBHOOK ADAPTADO PARA META ---
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        # Esta parte es solo para la verificación inicial de Meta
        if request.args.get("hub.verify_token") == META_VERIFY_TOKEN:
            return request.args.get("hub.challenge"), 200
        else:
            return "Error de verificación", 403

    if request.method == 'POST':
        # Esta parte procesa los mensajes entrantes
        data = request.get_json()
        print(f"Data recibida de Meta: {data}") # Muy útil para depurar

        try:
            # Extraemos la información relevante del complejo JSON de Meta
            if 'entry' in data and data['entry']:
                changes = data['entry'][0]['changes']
                if changes and 'value' in changes[0] and 'messages' in changes[0]['value']:
                    message_info = changes[0]['value']['messages'][0]
                    from_number = message_info['from']
                    msg_body = message_info['text']['body']
                    
                    print(f"Mensaje de {from_number}: {msg_body}")
                    
                    # Obtenemos la respuesta de la IA
                    bot_reply = get_response(msg_body)
                    
                    # Enviamos la respuesta usando la nueva función
                    send_whatsapp_message(from_number, bot_reply)

        except KeyError as e:
            print(f"Error al procesar el JSON: no se encontró la clave {e}")
        except Exception as e:
            print(f"Error inesperado: {e}")

        # Le respondemos a Meta inmediatamente que recibimos el evento
        return "EVENT_RECEIVED", 200

# La página web ya no es necesaria para este flujo, pero la dejamos
@app.route('/')
def index():
    return "El servidor del chatbot de WhatsApp está funcionando."

if __name__ == '__main__':
    app.run(debug=True, port=5001)