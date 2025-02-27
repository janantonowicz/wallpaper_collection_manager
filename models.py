from extensions import db # importujemy instancje db
from flask_login import UserMixin # dostarcza standardowe metody potrzebne dla Flask-Login


"""
Klasa User reprezentuje tabelę użytkowników w bazie danych.
"""
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Pole id jest unikalnym głównym kluczem tabeli
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<User('{self.username}', admin={self.is_admin})>"
    
    """
    metoda __repr_(self) zwraca informacje o User
    przykład:
    ```
    user = User(username='janek', is_admin=False)
    print(user)
    Wyświetla: <User('janek', admin=False)>
    ```
    """