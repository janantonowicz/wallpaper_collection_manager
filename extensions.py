from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy() # Tworzymy instancje bazy danych SQLAlchemy.
login_manager = LoginManager() # Inicjalizujemy managera logowania.
login_manager.login_view = 'login'  # Przekierowujemy na stronę logowania jeśli użytkownik nie jest zalogowany.
login_manager.login_message_category = 'info'  # Kategoria wiadomości o konieczności logowania.
