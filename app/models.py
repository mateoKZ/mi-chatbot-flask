# app/models.py
from .extensions import db
from datetime import datetime

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