from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# 1. CREACIÓN DE LA APLICACIÓN FLASK
app = Flask(__name__)
# ¡NUEVO! Habilita CORS para permitir que tu frontend hable con este backend
CORS(app)

# ¡NUEVO! Esta ruta servirá nuestra página web (el archivo index.html)
@app.route('/')
def index():
    return render_template('index.html')

# Esta es la misma función que ya tenías
def get_response(message):
    message = message.lower()
    if "hola" in message or "hi" in message:
        return "¡Hola! ¿Cómo puedo ayudarte hoy?"
    elif "horario" in message:
        return "Nuestro horario de atención es de 9 AM a 5 PM, de lunes a viernes."
    elif "adiós" in message or "chau" in message:
        return "¡Adiós! Que tengas un excelente día."
    else:
        return "Lo siento, no entiendo esa pregunta. Por favor, pregunta por nuestro 'horario' o saluda."

# El endpoint para el webhook sigue igual
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    user_message = data.get('message')
    if not user_message:
        return jsonify({'error': 'No se recibió ningún mensaje'}), 400
    bot_reply = get_response(user_message)
    return jsonify({'response': bot_reply})

# El inicio del servidor sigue igual
if __name__ == '__main__':
    app.run(debug=True, port=5001)