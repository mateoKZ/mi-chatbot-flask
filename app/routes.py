# app/routes.py
import os
import requests
import google.generativeai as genai
from flask import Blueprint, request
from .models import db, Conversation, Message
from datetime import datetime
import re # Importamos la librería de expresiones regulares para sanitizar
import socket # Importamos la librería de sockets para la prueba de red

# --- CONFIGURACIÓN DE RUTAS Y LÓGICA ---
main = Blueprint('main', __name__)

# Leemos las credenciales
GEMINI_API_KEY = os.environ.get("GOOGLE_API_KEY")
META_VERIFY_TOKEN = os.environ.get("META_VERIFY_TOKEN")
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")

# Configuración del modelo Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")

# (Aquí van las funciones get_response y send_whatsapp_message, no cambian)
def get_response(user_message):
    # ... (código igual que antes)
    try:
        prompt_template = f'Eres "ChatBoty", un asistente virtual amigable... Usuario: "{user_message}" ChatBoty:'
        response = model.generate_content(prompt_template)
        return response.text
    except Exception as e:
        print(f"Error al llamar a la API de Gemini: {e}")
        return "Upa, parece que se me quemaron los cables."

def send_whatsapp_message(to_number, message):
    # ... (código igual que antes)
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {META_ACCESS_TOKEN}", "Content-Type": "application/json"}
    data = {"messaging_product": "whatsapp", "to": to_number, "type": "text", "text": {"body": message}}
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar mensaje a WhatsApp: {e}")

# --- WEBHOOK CON LOGS DE DEPURACIÓN ADICIONALES ---
@main.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        if request.args.get("hub.verify_token") == META_VERIFY_TOKEN:
            return request.args.get("hub.challenge"), 200
        else:
            return "Error de verificación", 403

    if request.method == 'POST':
        # --- ¡NUEVO! PRUEBA 1: Imprimir la URL de la DB que la app está viendo ---
        database_url_runtime = os.environ.get("DATABASE_URL")
        print("--- VERIFICANDO URL DE DB EN RUNTIME ---")
        if database_url_runtime:
            # Sanitizamos la URL para no mostrar la contraseña en los logs
            sanitized_url = re.sub(r':(.[^@]*?)@', ':*****@', database_url_runtime)
            print(f"La app está usando esta URL (sanitizada): {sanitized_url}")
        else:
            print("¡ERROR! La variable de entorno DATABASE_URL no fue encontrada en runtime.")
        print("------------------------------------")
        
        # El resto del código del webhook
        data = request.get_json()
        try:
            if 'entry' in data and data['entry'][0]['changes'][0]['value']['messages']:
                message_info = data['entry'][0]['changes'][0]['value']['messages'][0]
                from_number = message_info['from']
                msg_body = message_info['text']['body']
                
                if from_number.startswith("549") and len(from_number) == 13:
                    from_number = "54" + from_number[3:]

                conversation = Conversation.query.filter_by(user_phone=from_number).first()
                if not conversation:
                    conversation = Conversation(user_phone=from_number)
                    db.session.add(conversation)
                    db.session.commit()
                
                db.session.add(Message(conversation_id=conversation.id, sender='user', content=msg_body))
                bot_reply = get_response(msg_body)
                db.session.add(Message(conversation_id=conversation.id, sender='bot', content=bot_reply))
                db.session.commit()
                send_whatsapp_message(from_number, bot_reply)
        except Exception as e:
            print(f"Error procesando el webhook: {e}")
        
        return "EVENT_RECEIVED", 200

# --- ¡NUEVO! PRUEBA 2: Ruta para probar la conectividad de red ---
@main.route('/test-connection')
def test_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        return "Error: DATABASE_URL no está configurada.", 500
    
    try:
        # Extraemos el host y el puerto de la URL
        # postgresql://user:pass@HOST:PORT/db
        host = db_url.split('@')[1].split(':')[0]
        port = int(db_url.split(':')[-1].split('/')[0])

        print(f"Intentando conectar a Host: {host}, Puerto: {port}")
        
        # Intentamos abrir una conexión de socket
        socket.create_connection((host, port), timeout=10)
        
        return f"¡ÉXITO! La conexión al host {host} en el puerto {port} fue exitosa.", 200
    except Exception as e:
        return f"¡FALLO! No se pudo conectar al host y puerto. Error: {e}", 500

@main.route('/')
def index():
    return "El servidor del chatbot de WhatsApp está funcionando."