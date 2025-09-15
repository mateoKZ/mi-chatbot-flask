# app/__init__.py
from flask import Flask
import os
# ¡YA NO NECESITAMOS NullPool!
# from sqlalchemy.pool import NullPool

# Importamos nuestras extensiones
from .extensions import db

def create_app():
    # Creamos la instancia de la aplicación
    app = Flask(__name__)

    # Cargamos la configuración desde variables de entorno
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # --- ELIMINAMOS ESTE BLOQUE ---
    # app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    #     "pool_pre_ping": True,
    #     "pool_recycle": 300,
    #     "poolclass": NullPool
    # }
    # ------------------------------------

    # Inicializamos las extensiones con nuestra app
    db.init_app(app)

    # (El resto del archivo sigue igual...)
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    @app.cli.command("init-db")
    def init_db_command():
        with app.app_context():
            db.create_all()
            print("Base de datos inicializada y tablas creadas.")

    return app