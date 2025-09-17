# app/routes.py
import os
import requests
import google.generativeai as genai
from flask import Blueprint, request, render_template
from .models import db, Conversation, Message
from datetime import datetime
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
model = genai.GenerativeModel(model_name="gemini-2.5-flash")

# --- ¡LA NUEVA LÓGICA DE IA CON MEMORIA! ---
def get_response(user_phone, user_message):
    try:
        # 1. Buscar la conversación en la base de datos
        conversation = Conversation.query.filter_by(user_phone=user_phone).first()
        
        rebuilt_history = []
        if conversation:
            # 2. Si existe, reconstruir el historial
            print(f"Historial encontrado para el usuario {user_phone}. Reconstruyendo...")
            # Buscamos los últimos 10 mensajes para no exceder el límite de tokens
            recent_messages = Message.query.filter_by(conversation_id=conversation.id).order_by(Message.timestamp.desc()).limit(10).all()
            recent_messages.reverse() # Los ponemos en orden cronológico

            for msg in recent_messages:
                # El rol de la IA se llama 'model', no 'bot'
                role = 'user' if msg.sender == 'user' else 'model'
                rebuilt_history.append({'role': role, 'parts': [{'text': msg.content}]})

        # 3. Iniciar el chat con el historial reconstruido
        chat = model.start_chat(history=rebuilt_history)
        
        # Le damos el prompt/personalidad del bot como primera instrucción en el nuevo mensaje si la historia está vacía
        prompt_template = f"""
        (Contexto: Eres "ChatBoty", un asistente virtual amigable, un poco sarcástico y muy útil que vive en Argentina.)
        
        Usuario: "{user_message}"
        ChatBoty:
        """
        
        # Usamos el prompt solo si es el inicio de la conversación para no repetirlo
        message_to_send = prompt_template if not rebuilt_history else user_message

        # 4. Enviar el nuevo mensaje a la sesión de chat
        response = chat.send_message(message_to_send)
        
        return response.text

    except Exception as e:
        print(f"Error en get_response con memoria: {e}")
        return "Uff, tuve un problema intentando recordar nuestra charla. ¿Podés repetirme?"


# --- FUNCIÓN PARA ENVIAR MENSAJES (Ahora devuelve el ID del mensaje) ---
def send_whatsapp_message(to_number, message):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {META_ACCESS_TOKEN}", "Content-Type": "application/json"}
    data = {"messaging_product": "whatsapp", "to": to_number, "type": "text", "text": {"body": message}}
    
    meta_msg_id = None # Variable para guardar el ID
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        # ¡NUEVO! Extraemos el ID del mensaje de la respuesta de Meta
        response_data = response.json()
        meta_msg_id = response_data['messages'][0]['id']
        print(f"Mensaje enviado con ID: {meta_msg_id}")
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar mensaje a WhatsApp: {e}")
    
    return meta_msg_id # Devolvemos el ID

# --- WEBHOOK UNIVERSAL Y COMPLETO ---
@main.route('/webhook', methods=['GET', 'POST'])
def webhook():
    # --- Parte 1: Manejo de la Verificación de Meta (Método GET) ---
    if request.method == 'GET':
        # Este bloque es SOLO para la verificación inicial de Meta.
        if request.args.get("hub.verify_token") == META_VERIFY_TOKEN:
            return request.args.get("hub.challenge"), 200
        else:
            return "Error de verificación", 403

    # --- Parte 2: Manejo de Notificaciones Entrantes (Método POST) ---
    if request.method == 'POST':
        data = request.get_json()
        
        # Diferenciamos si la petición viene de Meta (WhatsApp) o de nuestro frontend web
        if 'entry' in data and data.get('object') == 'whatsapp_business_account':
            # --- Lógica para WhatsApp ---
            try:
                value = data['entry'][0]['changes'][0]['value']
                
                if 'messages' in value:
                    # (Toda tu lógica para procesar mensajes de WhatsApp va aquí)
                    message_info = value['messages'][0]
                    if 'text' in message_info:
                        from_number = message_info['from']
                        msg_body = message_info['text']['body']
                        
                        if from_number.startswith("549"): from_number = "54" + from_number[3:]

                        bot_reply = get_response(from_number, msg_body)
                        
                        conversation = Conversation.query.filter_by(user_phone=from_number).first()
                        if not conversation:
                            conversation = Conversation(user_phone=from_number, origin='whatsapp')
                            db.session.add(conversation)
                            db.session.commit()
                        
                        db.session.add(Message(conversation_id=conversation.id, sender='user', content=msg_body, status='received'))
                        meta_id = send_whatsapp_message(from_number, bot_reply)
                        if meta_id:
                            db.session.add(Message(conversation_id=conversation.id, sender='bot', content=bot_reply, meta_message_id=meta_id, status='sent'))
                        db.session.commit()

                elif 'statuses' in value:
                    # (Toda tu lógica para procesar estados de WhatsApp va aquí)
                    status_info = value['statuses'][0]
                    message_id = status_info['id']
                    new_status = status_info['status']
                    message_to_update = Message.query.filter_by(meta_message_id=message_id).first()
                    if message_to_update:
                        message_to_update.status = new_status
                        db.session.commit()

            except Exception as e:
                print(f"Error procesando payload de Meta: {e}")
            
            return "EVENT_RECEIVED", 200

        else:
            # --- Lógica para el Frontend Web ---
            try:
                user_phone = data['user_phone']
                user_message = data['message']
                origin = data.get('origin', 'web') # Usamos .get para seguridad
                
                bot_reply = get_response(user_phone, user_message)
                
                conversation = Conversation.query.filter_by(user_phone=user_phone).first()
                if not conversation:
                    conversation = Conversation(user_phone=user_phone, origin=origin)
                    db.session.add(conversation)
                    db.session.commit()

                db.session.add(Message(conversation_id=conversation.id, sender='user', content=user_message, status='received'))
                db.session.add(Message(conversation_id=conversation.id, sender='bot', content=bot_reply, status='delivered'))
                db.session.commit()
                
                return jsonify({'response': bot_reply})
                
            except Exception as e:
                print(f"Error procesando payload de la web: {e}")
                return jsonify({'error': 'Error interno del servidor'}), 500

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

@main.route('/home')
def home(): 
    return render_template('index.html')