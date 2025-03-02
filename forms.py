"""
Importujemy klasy do tworzenia formularzy z flask_wtf oraz wtforms
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, FileField, SelectField
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


# Formularze do obsługi dodawania tapet, kolekcji, tagów itp.
class UploadWallpaperForm(FlaskForm):
    name = StringField('Nazwa tapety', validators=[DataRequired(), Length(max=100)])
    file = FileField('Plik tapety', validators=[DataRequired(), FileAllowed(['jpg', 'png', 'jpeg'], 'Tylko obrazy JPG i PNG!')])
    device = SelectField('Urządzenie', coerce=int, validators=[DataRequired()])
    colors = StringField('Kolory (oddzielone przecinkami)', validators=[DataRequired()])
    tags = StringField('Tagi (oddzielone przecinkami)', validators=[DataRequired()])
    submit = SubmitField('Prześlij')

class CreateCollectionForm(FlaskForm):
    name = StringField('Nazwa kolekcji', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Utwórz kolekcję')
