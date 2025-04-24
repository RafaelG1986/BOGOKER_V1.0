from flask import Flask
from flask_login import LoginManager
import os
import sys

# Añadir el directorio raíz al path para poder importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'bogoker_secret_key'  # Cambia esto por una clave segura
    
    # Inicializar Login Manager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    
    from .models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.get(user_id)
    
    # Registrar blueprints
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)
    
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    return app