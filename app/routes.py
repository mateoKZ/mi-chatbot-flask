# app/routes.py
import os
import requests
import google.generativeai as genai
from flask import Blueprint, request
from .models import db, Conversation, Message # Importamos los modelos y la db
from datetime import datetime

# --- CONFIGURACIÓN DE RUTAS Y LÓGICA ---
main = Blueprint('main', __name__)

# Leemos las credenciales (esto se configura en __init__.py)
GEMINI_API_KEY = os.environ.get("GOOGLE_API_KEY")
META_VERIFY_TOKEN = os.environ.get("META_VERIFY_TOKEN")
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")

# Configuración del modelo Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")

# --- LÓGICA DE LA IA ---
def get_response(user_message):
    # (Esta función es la misma de antes)
    try:
        prompt_template = f'Eres "ChatBoty", un asistente virtual amigable... Usuario: "{user_message}" ChatBoty:'
        response = model.generate_content(prompt_template)
        return response.text
    except Exception as e:
        print(f"Error al llamar a la API de Gemini: {e}")
        return "Upa, parece que se me quemaron los cables."

# --- FUNCIÓN PARA ENVIAR MENSAJES ---
def send_whatsapp_message(to_number, message):
    # (Esta función es la misma de antes)
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {META_ACCESS_TOKEN}", "Content-Type": "application/json"}
    data = {"messaging_product": "whatsapp", "to": to_number, "type": "text", "text": {"body": message}}
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar mensaje a WhatsApp: {e}")

# --- WEBHOOK ---
@main.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        if request.args.get("hub.verify_token") == META_VERIFY_TOKEN:
            return request.args.get("hub.challenge"), 200
        else:
            return "Error de verificación", 403

    if request.method == 'POST':
        data = request.get_json()
        try:
            if 'entry' in data and data['entry'][0]['changes'][0]['value']['messages']:
                message_info = data['entry'][0]['changes'][0]['value']['messages'][0]
                from_number = message_info['from']
                msg_body = message_info['text']['body']
                
                # Normalizamos el número
                if from_number.startswith("549") and len(from_number) == 13:
                    from_number = "54" + from_number[3:]

                # Lógica de la base de datos
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

@main.route('/')
def index():
    return "El servidor del chatbot de WhatsApp está funcionando."