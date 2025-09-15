# app/__init__.py
from flask import Flask
import os
from sqlalchemy.pool import NullPool # ¡NUEVA IMPORTACIÓN!

# Importamos nuestras extensiones
from .extensions import db

def create_app():
    # Creamos la instancia de la aplicación
    app = Flask(__name__)

    # Cargamos la configuración desde variables de entorno
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # --- ¡LA NUEVA MAGIA ESTÁ AQUÍ! ---
    # Opciones avanzadas para el motor de la base de datos
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_pre_ping": True, # Verifica la conexión antes de cada uso
        "pool_recycle": 300,   # Recicla conexiones cada 5 minutos
        "poolclass": NullPool  # ¡LA CLAVE! Desactiva el pool de SQLAlchemy
    }
    # ------------------------------------

    # Inicializamos las extensiones con nuestra app
    db.init_app(app)

    # Importamos y registramos nuestras rutas (el Blueprint)
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    # (El comando init-db no cambia)
    @app.cli.command("init-db")
    def init_db_command():
        """Limpia los datos existentes y crea las tablas nuevas."""
        with app.app_context():
            db.create_all()
            print("Base de datos inicializada y tablas creadas.")

    return app