from flask import Flask
from config import Config
from extensions import db, login_manager
from models import User
from flask_login import login_user, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

def create_app():
    app = Flask(__name__)  # inickalizujemy aplikację
    app.config.from_object(Config) # ładujemy zawartośc klasy Config

    # Initialize extensions
    db.init_app(app) # inicjalizujemy db
    login_manager.init_app(app) # inijcalizujemy login_manager

    # wchodzimy do kontekstu aplikacji aby móc pracować z bazą danych
    with app.app_context():
        db.create_all() # tworzymy wszystkie tabele w bazie danych

        # Create default admin if not exists
        if not User.query.filter_by(username='admin').first():
            admin_user = User(
                username='admin',
                password=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()

    # User loader - funkcja która ładuje użytkownika na podstawie jego id
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    """
    Import blueprints odpowiedzialne za trasy aplikacji
    admin_bp z tras admina
    user_bp z tras usera
    """
    from admin_routes import admin_bp
    from user_routes import user_bp

    # Register blueprints - jeśli skrypt jest wywoływany bezpośrednio to uruchamiamy aplikacje 
    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
