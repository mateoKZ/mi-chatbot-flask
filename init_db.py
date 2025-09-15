# init_db.py
from app import create_app, db

print("Iniciando la creación de las tablas en la base de datos...")

# Creamos una instancia de la app para tener el contexto correcto
app = create_app()

with app.app_context():
    db.create_all()

print("¡Tablas creadas exitosamente!")