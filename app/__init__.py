# app/__init__.py
from flask import Flask
import os

# Importamos nuestras extensiones
from .extensions import db

def create_app():
    # Creamos la instancia de la aplicación
    app = Flask(__name__)

    # Cargamos la configuración desde variables de entorno
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializamos las extensiones con nuestra app
    db.init_app(app)

    # Importamos y registramos nuestras rutas (el Blueprint)
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app