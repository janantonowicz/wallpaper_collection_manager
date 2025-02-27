"""
Importujemy klasy do tworzenia formularzy z flask_wtf oraz wtforms
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, ValidationError
from models import User

"""
Formularz logowania z polami:
username
password
przycisk submit
"""
class LoginForm(FlaskForm):
    username = StringField('Login', validators=[DataRequired(), Length(min=2, max=150)])
    password = PasswordField('Hasło', validators=[DataRequired()])
    submit = SubmitField('Zaloguj się')

"""
Formularz tworzenia nowego użytkownika:
Metoda validate_username sprawdza czy nazwa nie jest już zajęta.
Dostępny tylko dla administratora.
"""
class CreateUserForm(FlaskForm):
    username = StringField('Login', validators=[DataRequired(), Length(min=2, max=150)])
    password = PasswordField('Hasło', validators=[DataRequired()])
    is_admin = BooleanField('Czy administrator?')
    submit = SubmitField('Utwórz użytkownika')

    """
    Metoda validate_username jest wywoływana automatycznie poprzed WTForms przy walidacji pola username
    """
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Ten login jest już zajęty.')

"""
Formulaż umożliwiający resetowanie hasła użytkownika.
Dostępny tylko dla administratora.
"""
class ResetPasswordForm(FlaskForm):
    password = PasswordField('Nowe hasło', validators=[DataRequired()])
    submit = SubmitField('Zresetuj hasło')
