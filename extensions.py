from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy() # Create an instance of the SQLAlchemy database.
login_manager = LoginManager() # Initialize the login manager.
login_manager.login_view = 'login'  # Redirect to the login page if the user is not logged in.
login_manager.login_message_category = 'info'  # Category of the message to display when the user is not logged in.
