from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory, jsonify, session, current_app
from forms import LoginForm, UploadWallpaperForm, CreateCollectionForm
from models import User, Device, Wallpaper, Color, Tag, Collection
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash
from flask_login import login_user, current_user, logout_user, login_required
from flask_paginate import Pagination, get_page_args
import os
from PIL import Image, UnidentifiedImageError
import uuid
from extensions import db
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

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

    # Fetch up to three wallpapers for each collection
    for collection in user_collections + other_collections:
        collection.preview_wallpapers = collection.wallpapers.limit(3).all()

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
    # Populate device choices
    form.device.choices = [(device.id, device.name) for device in Device.query.all()]

    if form.validate_on_submit():
        file = form.file.data
        if file:
            filename = secure_filename(file.filename)
            unique_filename = str(uuid.uuid4()) + os.path.splitext(filename)[1]
            permanent_dir = current_app.config['PERMANENT_UPLOAD_DIR']
            os.makedirs(permanent_dir, exist_ok=True)
            permanent_filepath = os.path.join(permanent_dir, unique_filename)
            file.save(permanent_filepath)  # Save directly to permanent directory

            # Verify the image file
            try:
                with Image.open(permanent_filepath) as img:
                    img.verify()
            except (IOError, SyntaxError, UnidentifiedImageError) as e:
                flash('Plik nie jest prawidłowym obrazem. Proszę przesłać prawidłowy plik graficzny.', 'danger')
                os.remove(permanent_filepath)
                return redirect(url_for('user.upload_wallpaper'))

            # Get image resolution
            with Image.open(permanent_filepath) as image:
                width, height = image.size
            resolution = f"{width}x{height}"

            # Get the user's selected device
            selected_device_id = form.device.data
            selected_device = Device.query.get(selected_device_id)
            if not selected_device:
                flash('Wybrane urządzenie nie zostało znalezione.', 'danger')
                os.remove(permanent_filepath)  # Remove the uploaded file
                return redirect(url_for('user.upload_wallpaper'))

            # Optionally, provide feedback if dimensions don't match device type
            if selected_device.name.lower() == "desktop" and width < height:
                flash('Uwaga: Przesłany obraz jest w orientacji pionowej, a wybrano urządzenie "Desktop".', 'warning')
            elif selected_device.name.lower() == "mobile" and width > height:
                flash('Uwaga: Przesłany obraz jest w orientacji poziomej, a wybrano urządzenie "Mobile".', 'warning')

            relative_path = permanent_filepath[len(current_app.root_path):].lstrip('/')

            # Create Wallpaper object
            new_wallpaper = Wallpaper(
                name=form.name.data,
                resolution=resolution,
                path=relative_path,  # Store relative path
                user_id=current_user.id,
                device_id=selected_device_id
            )
            db.session.add(new_wallpaper)

            # Process colors
            color_names = [name.strip() for name in form.colors.data.split(',') if name.strip()]
            for color_name in color_names:
                color = Color.query.filter_by(name=color_name).first()
                if not color:
                    color = Color(name=color_name)
                    db.session.add(color)
                new_wallpaper.colors.append(color)

            # Process tags
            tag_names = [name.strip() for name in form.tags.data.split(',') if name.strip()]
            for tag_name in tag_names:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                new_wallpaper.tags.append(tag)

            db.session.commit()
            flash('Tapeta została dodana!', 'success')
            return redirect(url_for('user.dashboard'))
        else:
            flash('Nie wybrano pliku.', 'danger')
    return render_template('upload_wallpaper.html', form=form)





# Filter wallpapers helper func
def get_filtered_wallpapers(query, search_query, selected_device_id, page, per_page):
    # Filter by device if selected
    if selected_device_id:
        query = query.filter(Wallpaper.device_id == selected_device_id)

    # Filter by search query if not empty
    if search_query:
        # Split the search terms by commas and strip whitespace
        search_terms = [term.strip() for term in search_query.split(',') if term.strip()]
        # Build the filter conditions
        conditions = []
        for term in search_terms:
            # Use '%' wildcards for partial matches
            pattern = f"%{term}%"
            conditions.append(Wallpaper.name.ilike(pattern))
            conditions.append(Wallpaper.tags.any(Tag.name.ilike(pattern)))
            conditions.append(Wallpaper.colors.any(Color.name.ilike(pattern)))
        # Combine conditions using OR
        query = query.filter(or_(*conditions))

    total = query.count()
    offset = (page - 1) * per_page
    wallpapers = query.options(
        joinedload(Wallpaper.tags),
        joinedload(Wallpaper.device)
    ).offset(offset).limit(per_page).all()

    return wallpapers, total


# Display wallpapers with filter option
@user_bp.route('/wallpapers')
@login_required
def wallpapers():
    # Retrieve search and filter parameters
    search_query = request.args.get('search', '')
    selected_device_id = request.args.get('device', type=int)

    # Pagination parameters
    page, per_page, _ = get_page_args()
    per_page = 12

    # Base query
    query = Wallpaper.query.order_by(Wallpaper.id.desc())

    # Use the helper function
    wallpapers, total = get_filtered_wallpapers(query, search_query, selected_device_id, page, per_page)

    # Fetch devices
    devices = Device.query.all()

    # Preserve query parameters
    args = request.args.copy()
    args.pop('page', None)
    pagination = Pagination(
        page=page,
        total=total,
        per_page=per_page,
        css_framework='bootstrap4',
        args=args
    )

    return render_template(
        'wallpapers.html',
        wallpapers=wallpapers,
        devices=devices,
        selected_device_id=selected_device_id,
        pagination=pagination
    )





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
    if form.validate_on_submit():
        new_collection = Collection(
            name=form.name.data,
            user_id=current_user.id
        )
        db.session.add(new_collection)
        db.session.commit()
        flash('Kolekcja została utworzona!', 'success')
        return redirect(url_for('user.dashboard'))
    return render_template('create_collection.html', form=form)


# Display collection with filters
@user_bp.route('/collection/<int:collection_id>')
@login_required
def view_collection(collection_id):
    collection = Collection.query.get_or_404(collection_id)
    search_query = request.args.get('search', '')
    selected_device_id = request.args.get('device', type=int)

    # Pagination parameters
    page, per_page, _ = get_page_args()
    per_page = 12

    # Base query
    query = collection.wallpapers.order_by(Wallpaper.id.desc())

    # Use the helper function
    wallpapers, total = get_filtered_wallpapers(query, search_query, selected_device_id, page, per_page)

    # Fetch devices
    devices = Device.query.all()

    # Preserve query parameters
    args = request.args.copy()
    args.pop('page', None)
    pagination = Pagination(
        page=page,
        total=total,
        per_page=per_page,
        css_framework='bootstrap4',
        args=args
    )

    return render_template(
        'view_collection.html',
        wallpapers=wallpapers,
        devices=devices,
        selected_device_id=selected_device_id,
        pagination=pagination,
        collection=collection
    )


# Filter wallpapers by device
@user_bp.route('/device/<int:device_id>/wallpapers')
@login_required
def wallpapers_by_device(device_id):
    device = Device.query.get_or_404(device_id)
    wallpapers = Wallpaper.query.filter_by(device_id=device.id, wallpapers=wallpapers)


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

# Obsługa żądania AJAX
@user_bp.route('/load_wallpaper_modal', methods=['GET'])
@login_required
def load_wallpaper_modal():
    wallpaper_id = request.args.get('wallpaper_id', type=int)
    wallpaper = Wallpaper.query.get_or_404(wallpaper_id)
    return render_template('wallpaper_modal_content.html', wallpaper=wallpaper)


# Query suggesions
@user_bp.route('/suggestions')
@login_required
def suggestions():
    term = request.args.get('term', '')
    suggestions = []

    if term:
        pattern = f"%{term}%"
        # Fetch matching wallpaper names
        names = Wallpaper.query.filter(Wallpaper.name.ilike(pattern)).with_entities(Wallpaper.name).all()
        suggestions.extend([name[0] for name in names])

        # Fetch matching tag names
        tags = Tag.query.filter(Tag.name.ilike(pattern)).with_entities(Tag.name).all()
        suggestions.extend([tag[0] for tag in tags])

        # Fetch matching color names
        colors = Color.query.filter(Color.name.ilike(pattern)).with_entities(Color.name).all()
        suggestions.extend([color[0] for color in colors])

    # Remove duplicates
    suggestions = list(set(suggestions))

    return jsonify(suggestions)


@user_bp.route('/edit_wallpaper/<int:wallpaper_id>', methods=['GET', 'POST'])
@login_required
def edit_wallpaper(wallpaper_id):
    # Pobierz tapetę z bazy danych
    wallpaper = Wallpaper.query.get_or_404(wallpaper_id)

    # Sprawdź, czy aktualny użytkownik jest właścicielem tapety
    if wallpaper.user_id != current_user.id:
        flash('Nie masz uprawnień do edycji tej tapety.', 'danger')
        return redirect(url_for('user.dashboard'))

    # Stwórz formularz i wypełnij go aktualnymi danymi tapety
    form = UploadWallpaperForm(obj=wallpaper)
    form.device.choices = [(device.id, device.name) for device in Device.query.all()]

    # Ustawienie początkowych wartości dla pól colors i tags
    form.colors.data = ', '.join([color.name for color in wallpaper.colors])
    form.tags.data = ', '.join([tag.name for tag in wallpaper.tags])

    if form.validate_on_submit():
        # Aktualizuj dane tapety
        wallpaper.name = form.name.data
        wallpaper.device_id = form.device.data

        # Aktualizuj kolory
        wallpaper.colors.clear()
        color_names = [name.strip() for name in form.colors.data.split(',') if name.strip()]
        for color_name in color_names:
            color = Color.query.filter_by(name=color_name).first()
            if not color:
                color = Color(name=color_name)
                db.session.add(color)
            wallpaper.colors.append(color)

        # Aktualizuj tagi
        wallpaper.tags.clear()
        tag_names = [name.strip() for name in form.tags.data.split(',') if name.strip()]
        for tag_name in tag_names:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
            wallpaper.tags.append(tag)

        db.session.commit()
        flash('Tapeta została zaktualizowana!', 'success')
        return redirect(url_for('user.dashboard'))

    return render_template('edit_wallpaper.html', form=form, wallpaper=wallpaper)


@user_bp.route('/delete_wallpaper/<int:wallpaper_id>', methods=['POST'])
@login_required
def delete_wallpaper(wallpaper_id):
    # Pobierz tapetę z bazy danych wraz z relacjami do kolekcji
    wallpaper = Wallpaper.query.options(
        joinedload(Wallpaper.collections).joinedload(Collection.user)
    ).get_or_404(wallpaper_id)

    # Sprawdź, czy aktualny użytkownik jest właścicielem tapety
    if wallpaper.user_id != current_user.id:
        flash('Nie masz uprawnień do usunięcia tej tapety.', 'danger')
        return redirect(url_for('user.dashboard'))

    # Znajdź kolekcje innych użytkowników, które zawierają tę tapetę
    other_users_collections = [
        collection for collection in wallpaper.collections
        if collection.user_id != current_user.id
    ]

    if other_users_collections:
        # Tapeta jest w kolekcjach innych użytkowników

        # Usuwamy tapetę z kolekcji właściciela
        owner_collections = [
            collection for collection in wallpaper.collections
            if collection.user_id == current_user.id
        ]
        for collection in owner_collections:
            collection.wallpapers.remove(wallpaper)

        db.session.commit()
        flash('Tapeta została usunięta z Twoich kolekcji, ale pozostaje dostępna dla innych użytkowników.', 'success')
    else:
        # Tapeta nie jest w kolekcjach innych użytkowników

        # Usuń plik z systemu plików
        filepath = os.path.join(current_app.root_path, wallpaper.path)
        if os.path.exists(filepath):
            os.remove(filepath)

        # Usuń tapetę z bazy danych
        db.session.delete(wallpaper)
        db.session.commit()
        flash('Tapeta została usunięta!', 'success')

    return redirect(url_for('user.dashboard'))

@user_bp.route('/remove_wallpaper_from_collection/<int:collection_id>/<int:wallpaper_id>', methods=['POST'])
@login_required
def remove_wallpaper_from_collection(collection_id, wallpaper_id):
    collection = Collection.query.filter_by(id=collection_id, user_id=current_user.id).first_or_404()
    wallpaper = Wallpaper.query.get_or_404(wallpaper_id)

    if wallpaper in collection.wallpapers:
        collection.wallpapers.remove(wallpaper)
        db.session.commit()
        flash('Tapeta została usunięta z kolekcji.', 'success')
    else:
        flash('Ta tapeta nie znajduje się w wybranej kolekcji.', 'warning')

    return redirect(url_for('user.dashboard'))

