from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory
from forms import LoginForm, UploadWallpaperForm, CreateCollectionForm
from models import User, Device, Wallpaper, Color, Tag, Collection
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash
from flask_login import login_user, current_user, logout_user, login_required
import os
from PIL import Image
import uuid
from extensions import db

"""
Tworzymy blueprint dla tras użytkownika.
"""
user_bp = Blueprint('user', __name__)


@user_bp.route('/', methods=['GET', 'POST'])
@user_bp.route('/login', methods=['GET', 'POST']) # Trasa logowania
def login():
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('user.dashboard'))
        else:
            flash('Błędny login lub hasło.', 'danger')
    return render_template('login.html', form=form)

# Trasa pulpitu użytkownika (admin dashboard oraz user dashboard)
@user_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin.admin_dashboard'))
    # Pobierz kolekcje użytkownika
    user_collections = Collection.query.filter_by(user_id=current_user.id).all()
    # Pobierz kolekcje innych użytkowników
    other_collections = Collection.query.filter(Collection.user_id != current_user.id).all()
    return render_template('user_dashboard.html', username=current_user.username,
                           user_collections=user_collections, other_collections=other_collections)


# Trasa wylogowania
@user_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('user.login'))

# Funkcje dla tapet

# Import tapety
@user_bp.route('/upload_wallpaper', methods=['GET', 'POST'])
@login_required
def upload_wallpaper():
    form = UploadWallpaperForm()
    if form.validate_on_submit():
        file = form.file.data
        filename = secure_filename(file.filename)
        # Generujemy unikalną nazwę pliku
        unique_filename = str(uuid.uuid4()) + os.path.splitext(filename)[1]
        filepath = os.path.join('static/uploads/', unique_filename)
        file.save(filepath)

        # Pobranie rozdzielczości obrazu
        image = Image.open(filepath)
        resolution = f"{image.width}x{image.height}"

        # Tworzenie obiektu Wallpaper
        new_wallpaper = Wallpaper(
            name=form.name.data,
            resolution=resolution,
            path=filepath,
            user_id=current_user.id
        )

        # Przetwarzanie kolorów
        color_names = [name.strip() for name in form.colors.data.split(',')]
        for color_name in color_names:
            color = Color.query.filter_by(name=color_name).first()
            if not color:
                color = Color(name=color_name)
                db.session.add(color)
            new_wallpaper.colors.append(color)

        # Przetwarzanie tagów
        tag_names = [name.strip() for name in form.tags.data.split(',')]
        for tag_name in tag_names:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
            new_wallpaper.tags.append(tag)

        db.session.add(new_wallpaper)
        db.session.commit()
        flash('Tapeta została dodana!', 'success')
        return redirect(url_for('user.dashboard'))
    return render_template('upload_wallpaper.html', form=form)

# Wyświetlanie tapet
@user_bp.route('/wallpapers')
@login_required
def wallpapers():
    wallpapers = Wallpaper.query.all()
    return render_template('wallpapers.html', wallpapers=wallpapers)

#pobieranie tapet
@user_bp.route('/download_wallpaper/<int:wallpaper_id>')
@login_required
def download_wallpaper(wallpaper_id):
    wallpaper = Wallpaper.query.get_or_404(wallpaper_id)
    directory = os.path.dirname(wallpaper.path)
    filename = os.path.basename(wallpaper.path)
    return send_from_directory(directory, filename, as_attachment=True)


# Tworzenie kolekcji
@user_bp.route('/create_collection', methods=['GET', 'POST'])
@login_required
def create_collection():
    form = CreateCollectionForm()
    form.device.choices = [(device.id, device.name) for device in Device.query.all()]
    if form.validate_on_submit():
        new_collection = Collection(
            name=form.name.data,
            user_id=current_user.id,
            device_id=form.device.data
        )
        db.session.add(new_collection)
        db.session.commit()
        flash('Kolekcja została utworzona!', 'success')
        return redirect(url_for('user.dashboard'))
    return render_template('create_collection.html', form=form)


# Wyświetlanie kolekcji
@user_bp.route('/collection/<int:collection_id>')
@login_required
def view_collection(collection_id):
    collection = Collection.query.get_or_404(collection_id)
    wallpapers = collection.wallpapers
    return render_template('view_collection.html', collection=collection, wallpapers=wallpapers)


# Dodanie tapety do kolekcji
@user_bp.route('/add_to_collection/<int:wallpaper_id>', methods=['GET', 'POST'])
@login_required
def add_to_collection(wallpaper_id):
    wallpaper = Wallpaper.query.get_or_404(wallpaper_id)
    collections = Collection.query.filter_by(user_id=current_user.id).all()
    if not collections:
        flash('Nie masz żadnych kolekcji. Utwórz najpierw kolekcję.', 'warning')
        return redirect(url_for('user.create_collection'))
    if request.method == 'POST':
        collection_id = request.form.get('collection_id')
        collection = Collection.query.get_or_404(collection_id)
        if collection.user_id != current_user.id:
            flash('Nie możesz dodawać tapet do kolekcji innych użytkowników.', 'danger')
            return redirect(url_for('user.dashboard'))
        if wallpaper in collection.wallpapers:
            flash('Ta tapeta już znajduje się w wybranej kolekcji.', 'info')
        else:
            collection.wallpapers.append(wallpaper)
            db.session.commit()
            flash('Tapeta została dodana do kolekcji!', 'success')
        return redirect(url_for('user.view_collection', collection_id=collection.id))
    return render_template('add_to_collection.html', wallpaper=wallpaper, collections=collections)
