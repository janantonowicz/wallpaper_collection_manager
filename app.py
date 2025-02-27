from flask import Flask
from config import Config
from extensions import db, login_manager
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash
import sqlalchemy.exc  # Importing exceptions from SQLAlchemy

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate = Migrate(app, db)

    # Import and register blueprints
    from user_routes import user_bp
    from admin_routes import admin_bp
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        # Import models inside the app context to avoid circular imports
        from models import User, Device

        db.create_all()  # Create all tables in the database

        # Initialize devices if they don't exist
        if not Device.query.first():
            devices = [Device(name='mobile'), Device(name='desktop')]
            db.session.bulk_save_objects(devices)
            db.session.commit()
            print("Devices initialized.")

        # Check if the 'user' table exists
        inspector = db.inspect(db.engine)
        if 'user' in inspector.get_table_names():
            try:
                # Create default admin user if not exists
                if not User.query.filter_by(username='admin').first():
                    admin_user = User(
                        username='admin',
                        password=generate_password_hash('admin123'),
                        is_admin=True
                    )
                    db.session.add(admin_user)
                    db.session.commit()
                    print("Default admin user created.")
            except sqlalchemy.exc.OperationalError:
                # The table exists but the structure is incompatible
                pass

    # Define user_loader callback for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from models import User  # Import inside the function to avoid circular imports
        return User.query.get(int(user_id))

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)

