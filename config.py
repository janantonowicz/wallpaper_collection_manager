import os

"""
Config class contains app settings.
SECRET_KEY is used by Flask to secure session data.
sqlalchemy_database_uri is the URL of the database.
    sqlite:///site.db - the file will be created in the current directory
"""
class Config:
    SECRET_KEY = '24fc6d15e6072fd25956da9e5586b54b4c50ca5b722a86bdaa8f051ecf404b13'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False # Turned off tracking of modifications to objects in SQL

    # Upload directory configuration
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    PERMANENT_UPLOAD_DIR = os.path.join(BASE_DIR, 'static', 'uploads', 'permanent')
    TEMPORARY_UPLOAD_DIR = os.path.join(BASE_DIR, 'static', 'uploads', 'temp')