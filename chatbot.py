import os
import requests
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# --- CONFIGURACIÓN ---
GEMINI_API_KEY = os.environ.get("GOOGLE_API_KEY")
META_VERIFY_TOKEN = os.environ.get("META_VERIFY_TOKEN")
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
DATABASE_URL = os.environ.get("DATABASE_URL")

# --- INICIALIZACIÓN DE APP Y DB ---
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Recomendado para optimizar
db = SQLAlchemy(app)

# --- MODELOS DE LA BASE DE DATOS ---
# Tabla para guardar las conversaciones
class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_phone = db.Column(db.String(30), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    messages = db.relationship('Message', backref='conversation', lazy=True)

# Tabla para guardar cada mensaje
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    sender = db.Column(db.String(10), nullable=False) # 'user' o 'bot'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Tabla para guardar los turnos
class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_phone = db.Column(db.String(30), nullable=False)
    appointment_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending') # pending, confirmed, cancelled

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

# --- WEBHOOK MODIFICADO PARA USAR LA DB ---
@app.route('/webhook', methods=['POST'])
def webhook():
    # ... (el código para procesar la data de Meta es el mismo)
    
    # Extraemos el número y el mensaje del usuario
    from_number = ...
    msg_body = ...

    # 1. Busca o crea una conversación para este usuario
    conversation = Conversation.query.filter_by(user_phone=from_number).first()
    if not conversation:
        conversation = Conversation(user_phone=from_number)
        db.session.add(conversation)
        db.session.commit() # Guardamos para obtener un ID

    # 2. Guarda el mensaje del usuario
    user_msg_db = Message(conversation_id=conversation.id, sender='user', content=msg_body)
    db.session.add(user_msg_db)
    
    # 3. Lógica para agendar turnos vs. chat normal
    if "turno" in msg_body.lower() or "agendar" in msg_body.lower():
        # Lógica especial para turnos... por ahora un mensaje simple
        bot_reply = "¡Claro! Veo que quieres agendar un turno. Por favor, decime para qué día y hora te gustaría."
        # Aquí podrías añadir la lógica para crear un objeto Appointment
    else:
        # Lógica de chat normal con IA
        bot_reply = get_response(msg_body)

    # 4. Guarda la respuesta del bot
    bot_msg_db = Message(conversation_id=conversation.id, sender='bot', content=bot_reply)
    db.session.add(bot_msg_db)

    # 5. Guarda todos los cambios en la base de datos
    db.session.commit()
    
    # 6. Envía la respuesta a WhatsApp
    send_whatsapp_message(from_number, bot_reply)
    
    return "EVENT_RECEIVED", 200

# Con este comando creamos las tablas en la base de datos la primera vez
with app.app_context():
    db.create_all()

# La página web ya no es necesaria para este flujo, pero la dejamos
@app.route('/')
def index():
    return "El servidor del chatbot de WhatsApp está funcionando."

if __name__ == '__main__':
    app.run(debug=True, port=5001)