# Table of Contents
1. [Project Structure](#project-structure)
2. [Wyjaśnienie plików oraz spis treści ich omówienia](#file-roles-explanation)
3. [Wyjaśnienie importów](#import-explanation-pl)


# Project Structure
```
user_management_app/
├── app.py
├── config.py
├── extensions.py
├── models.py
├── forms.py
├── admin_routes.py
├── user_routes.py
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── admin_dashboard.html
│   ├── create_user.html
│   ├── reset_password.html
│   ├── user_dashboard.html
```

## File roles explanation
**app.py**: Main application entry point.<br>
**config.py**: Configuration settings.<br>
[**extensions.py**](#extensions): Initioalize extensions like SQLAlchemy and Flask-login.<br>
[**models.py**](#database): Database models.<br>
[**forms.py**](#formularze): WTForms for input validation.<br>
**admin_routes.py**: Routes for admin functionalities.<br>
**user_routes.py**: Routes for user functionalities.<br>
**templates/**: HTML templates.<br>

# Import Explanation (PL)
**import os**<br>
Modół os pozwala na integracje z systemem operacyjnym, np. pobieranie zmiennych środowiskowych.

**SQLAlchemy**
- `from flask_sqlalchemy import SQLAlchemy` Importujemy klasę SQLAlchemy, która ułatwia interakcję z bazą danych w Flasku.

**System logowania**
- `from flask_login import LoginManager` Importujemy LoginManager, który zarządza sesjami użytkowników.
    - [zobacz więcej o flask_login](#flask_login)

**UserMixin**
- `from flask_login import UserMixin` Importujemy UserMixin, który dostarcza standardowe metody potrzebne przez Flask-Login.

## flask_wtf
Integruje bibliotekę WTForms z Flask.<br>
**FlaskForm**
klasa bazowa z której dziedziczą wszystkie formularze tworzone w aplikacji Flask.<br>
Zapewnia integrację formularzy z Flask i obsługę sesji.
## WTForms
- Biblioteka umożliwiająca tworzenie i walidację formularzy w Pythonie.
- Dostarcza zestaw klas, któ©e reprezentują różne elementy formularza HTML.
- Umożliwia walidację danych
### Importowane klasy
- **StringField** - pole tekstowe
- **PasswordField** - maskowane znaki
- **SubmitField** - przycisk przesyłający formularz
- **BooleanField** - Pole wyboru

### WTForms.validators
Sprawdzanie poprawności wprowadzanych danych.
#### Importowane walidatory:
- **DataRequired** - Czy pole nie jest puste.
- **Length** - Czy długość mieści się w przedziale.
- **ValidationError** - klasa wyjątku do sygnalizacji błędu.



# Database
`SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'`<br>
W tym przypadku plik bazy danych zostanie stworzony w bierzoncym katalogu.<br>
SQLALCHEMY_TRACK_MODIFICATIONS = False Wyłączamy śledzenie modyfikacji obiektów przez SQLAlchemy, co pozwala oszczędzić zasoby.

W projekcie modele tabel są stworzone w pliku
[**models.py**](/models.py) ale instancja bazy danych jest inicjalizowana w [**extensions.py**](/extensions.py)

## Tabele
### Users
|Pole|Wyjaśnienie|Inicjacja|
|---|---|---|
|**id**|klucz główny i unikalny identyfikator użytkownika|`db.Integer primary_key=True`|
|**username**|nazwa użytkownika. Unikalne. Nie puste|`db.String(150) unique=True nullable=False`|
|**password**|zahashowane hasła użytkowników|`db.string(150) nullable=False`|
|**is_admin**|czy jest adminem|`db.Boolean default=False`|
|**def __repr__(self):**|Metoda zwracająca reprezentację obiektu użytkownika, przydatna podczas debugowania.|`f"<User('{self.username}', admin={self.is_admin})>"`|

**Czym jest metoda \_\_repr__?**
W Pythonie każda klasa może definiować specjalne metody magiczne (dzięki podwójnym podkreśleniom na początku i końcu nazwy, np. \_\_init__, \_\_str__, \_\_repr__), które pozwalają na określoną interakcję z obiektami tej klasy.

Metoda \_\_repr__:
- ma za zadanie zwócić oficjalną reprezentację obiektu.
- Jednoznaczna reprezentacja obiektu, przejrzystość
- Ułatwienie debugowania i logowania
- Potencjalne umożliwienie odtworzenia obiektu

analogicznie \_\_str__ zwraca przeznaczoną dla użytkowników końcowych czytelną reprezentacje obiektu.

# Extensions
Te rozszerzenia są zapisane w pliku [**extensions.py**](/extensions.py)
## flask_login
Strona internetowa [Flask-Login](https://flask-login.readthedocs.io/en/latest/)
### login_view
The name of the view to redirect to when the user needs to log in. (This can be an absolute URL as well, if your authentication machinery is external to your application.)
### login_message
The message to flash when a user is redirected to the login page.<br>
Login message można zmieniać, więcej na: [Customizing the Login Process](https://flask-login.readthedocs.io/en/latest/#customizing-the-login-process)


# Formularze
Plik: [**forms.py**](/forms.py)<br>
Zależności: [flask_wtf i WTForms](#flask_wtf)

Są tutaj opisane formularze związane z tworzeniem i zarządzaniem użytkownika.

Formularz logowania `class LoginForm` jest wyświetlany kiedy użytkownik nie jest zalogowany.
Użytkownik wpisuje swój login i hasło oraz zatwierdza logowanie.

Formularz tworzenia nowego użytkownika oraz resetowania hasła jest dostępny tylko dla administratora.

# app.py funkcja fabryczna flask
Tutaj jest serce aplikacji. Inicjalizujemy db oraz login_manager.
Importuemy blueprinty odpowiezialne za trasy aplikacji

# Trasy użytkownika
[**user_routes.py**](/user_routes.py)

Tworzymy tutaj blueprint użytkownika:<br>
`user_bp = Blueprint('user', __name__)`<br>
[Więcej o blueprintach](#czym-są-blueprinty)

Funkcje w pliku:
- login
- dashbord (generalnie co widzi user po zalogowaniu)
- logout

# Trasy admina
Analogicznie dla user tworzymy blueprint panelu admina

Funkcje administratora:
- dashboard (wyświetla listę wszystkich użytkowników)
- create_user (pozwala administratorowi na tworzenie nowych użytkowników)
- reset_password (pozwala adminowi resetować hasło użytkownika)
    - `/reset_password/<int:user_id>` przekazujemy tutaj id usera
- logout

# Czym są Blueprinty
Blueprint to sposób na podzielenie aplikacji Flask na mniejsze moduły.

1. Blueprinty są tworzone jako obiekty klasy Blueprint z modułu flask.<br>
`user_bp = Blueprint('user', __name__)`
2. Trasy i widoki są definiowane w obrębie blueprintu.<br>
```
@user_bp.route('/login')
def login():
    ...
```
3. Blueprint rejestrujemy w głównej aplikacji Flask.
```
app.py

app.register_blueprint(user_bp)
```

## Czym się różni import od rejestrowania
**Wyobraź sobie, że budujesz dom:**
- Importowanie blueprintu to jak zamówienie nowego narzędzia:

    - from user_routes import user_bp to jak dostarczenie młotka do Twojego miejsca pracy.

    - Masz dostęp do młotka i możesz go użyć.

- Rejestracja blueprintu to jak użycie tego narzędzia w praktyce:

    - app.register_blueprint(user_bp) to jak faktyczne użycie młotka do wbicia gwoździ w konstrukcję domu.

    - Narzędzie (blueprint) jest teraz aktywnie wykorzystywane w projekcie (aplikacji).

**Kiedy i dlaczego używamy obu tych linii razem:**

Aby poprawnie korzystać z blueprintów w Flasku, należy je zarówno zaimportować, jak i zarejestrować:

- Importowanie:

    -  Konieczne do uzyskania dostępu do obiektu blueprintu.

    - Bez importu nie możesz wywołać app.register_blueprint(user_bp), ponieważ user_bp nie istnieje w bieżącym module.

- Rejestrowanie:

    - Konieczne do zintegrowania blueprintu z aplikacją Flask.

    - Bez rejestracji trasy zdefiniowane w blueprintcie nie będą dostępne w aplikacji.

# Templates (Frontend HTML)
## base.html
Jest to podstawowy szablon który inne szablony będą rozszerzać.