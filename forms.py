"""
Imoporting classes for creating forms from flask_wtf and wtforms
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, FileField, SelectField
from wtforms.validators import DataRequired, Length, ValidationError
from models import User

"""
Login form with fields:
username
password
submit button
"""
class LoginForm(FlaskForm):
    username = StringField('Login', validators=[DataRequired(), Length(min=2, max=150)])
    password = PasswordField('Hasło', validators=[DataRequired()])
    submit = SubmitField('Zaloguj się')

"""
Create new user form:
validate_username method checks if the username is not already taken.
Available only for the administrator.
"""
class CreateUserForm(FlaskForm):
    username = StringField('Login', validators=[DataRequired(), Length(min=2, max=150)])
    password = PasswordField('Hasło', validators=[DataRequired()])
    is_admin = BooleanField('Czy administrator?')
    submit = SubmitField('Utwórz użytkownika')

    """
    validate_username method is called automatically by WTForms when validating the username field
    checks if the username is not already taken.
    """
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Ten login jest już zajęty.')

"""
Reset user password form:
Available only for the administrator.
"""
class ResetPasswordForm(FlaskForm):
    password = PasswordField('Nowe hasło', validators=[DataRequired()])
    submit = SubmitField('Zresetuj hasło')


# Forms for adding wallpapers, collections, tags, etc.
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
