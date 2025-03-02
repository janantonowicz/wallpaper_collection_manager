import os

"""
Klasa Config zawiera ustawienia konfiguracyjne aplikacji.
Secret key jest używany przez flask do zabezpieczenia danych sesji.
SQLAlchemy database URL - URL bazy danych SQLite
    sqlite:///site.db - plik zostanie utworzony w bieżoncym katalogu
"""
class Config:
    SECRET_KEY = '24fc6d15e6072fd25956da9e5586b54b4c50ca5b722a86bdaa8f051ecf404b13'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False # Wyłączone śledzenie modyfikacji obiektów SQL

    # Upload directory
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    PERMANENT_UPLOAD_DIR = os.path.join(BASE_DIR, 'static', 'uploads', 'permanent')
    TEMPORARY_UPLOAD_DIR = os.path.join(BASE_DIR, 'static', 'uploads', 'temp')