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
Creating user blueprint for user routes.
Blueprint is a way to organize a group of related views and other code.
"""
user_bp = Blueprint('user', __name__)


@user_bp.route('/', methods=['GET', 'POST'])
@user_bp.route('/login', methods=['GET', 'POST']) # Login route for users
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

# TUser main page route (admin dashboard and user dashboard) - displays user collections
@user_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin.admin_dashboard'))
    # Get user collections
    user_collections = get_user_collections(current_user.id)
    # Get other users' collections
    other_collections = Collection.query.filter(Collection.user_id != current_user.id).all()

    # Fetch up to three wallpapers for each collection (for preview collage)
    for collection in user_collections + other_collections:
        collection.preview_wallpapers = collection.wallpapers.limit(3).all()

    return render_template('user_dashboard.html', username=current_user.username,
                           user_collections=user_collections, other_collections=other_collections)


# logout route for users
@user_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('user.login'))

# Wallpapers methods


# Import wallpaper from file provided by user
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





# downloading wallpapers
@user_bp.route('/download_wallpaper/<int:wallpaper_id>')
@login_required
def download_wallpaper(wallpaper_id):
    wallpaper = get_wallpaper(wallpaper_id)
    directory = os.path.dirname(wallpaper.path)
    filename = os.path.basename(wallpaper.path)
    return send_from_directory(directory, filename, as_attachment=True)


# Creating collections
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


# Add wallpaper to collection
@user_bp.route('/add_to_collection/<int:wallpaper_id>', methods=['GET', 'POST'])
@login_required
def add_to_collection(wallpaper_id):
    wallpaper = get_wallpaper(wallpaper_id)
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

# Load wallpaper modal (AJAX)
@user_bp.route('/load_wallpaper_modal', methods=['GET'])
@login_required
def load_wallpaper_modal():
    wallpaper_id = request.args.get('wallpaper_id', type=int)
    wallpaper = get_wallpaper(wallpaper_id)
    return render_template('wallpaper_modal_content.html', wallpaper=wallpaper)


# Query suggesions (on wallpaper view user can search for wallpapers, tags and colors)
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

# Edit wallpaper
@user_bp.route('/edit_wallpaper/<int:wallpaper_id>', methods=['GET', 'POST'])
@login_required
def edit_wallpaper(wallpaper_id):
    # Get the wallpaper from the database
    wallpaper = get_wallpaper(wallpaper_id)

    # Check if current user is the owner of the wallpaper
    if wallpaper.user_id != current_user.id:
        flash('Nie masz uprawnień do edycji tej tapety.', 'danger')
        return redirect(url_for('user.dashboard'))

    # Create form and fill it with current wallpaper details (since user edits existing wallpaper)
    form = UploadWallpaperForm(obj=wallpaper)
    form.device.choices = [(device.id, device.name) for device in Device.query.all()]

    # Set the form fields with current wallpaper tags and colors
    form.colors.data = ', '.join([color.name for color in wallpaper.colors])
    form.tags.data = ', '.join([tag.name for tag in wallpaper.tags])

    # Update wallpaper details
    if form.validate_on_submit():
        wallpaper.name = form.name.data
        wallpaper.device_id = form.device.data

        # Colors update
        wallpaper.colors.clear()
        color_names = [name.strip() for name in form.colors.data.split(',') if name.strip()]
        for color_name in color_names:
            color = Color.query.filter_by(name=color_name).first()
            if not color:
                color = Color(name=color_name)
                db.session.add(color)
            wallpaper.colors.append(color)

        # Tags Update
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

# Deleting wallpaper
@user_bp.route('/delete_wallpaper/<int:wallpaper_id>', methods=['POST'])
@login_required
def delete_wallpaper(wallpaper_id):
    # Fetch the wallpaper from the database with user and collections
    wallpaper = Wallpaper.query.options(
        joinedload(Wallpaper.collections).joinedload(Collection.user)
    ).get_or_404(wallpaper_id)

    # Check if the current user is the owner of the wallpaper
    if wallpaper.user_id != current_user.id:
        flash('Nie masz uprawnień do usunięcia tej tapety.', 'danger')
        return redirect(url_for('user.dashboard'))

    # Find collections of other users that contain this wallpaper
    other_users_collections = [
        collection for collection in wallpaper.collections
        if collection.user_id != current_user.id
    ]

    if other_users_collections:
        # If wallpaper is in collections of other users, we want only to remove the wallpaper from the current user's collections
        # Other users may want to still use the wallpaper

        # Removing wallpaper from all collections of the current user
        owner_collections = [
            collection for collection in wallpaper.collections
            if collection.user_id == current_user.id
        ]
        for collection in owner_collections:
            collection.wallpapers.remove(wallpaper)

        db.session.commit()
        flash('Tapeta została usunięta z Twoich kolekcji, ale pozostaje dostępna dla innych użytkowników.', 'success')
    else:
        # If wallpaper is not in collections of other users, we can safely delete it from the system

        # Remove wallpaper files from the filesystem
        filepath = os.path.join(current_app.root_path, wallpaper.path)
        if os.path.exists(filepath):
            os.remove(filepath)

        # Remove wallpaper from the database
        db.session.delete(wallpaper)
        db.session.commit()
        flash('Tapeta została usunięta!', 'success')

    return redirect(url_for('user.dashboard'))


# Removing wallpaper from collection
@user_bp.route('/select_collection_to_remove/<int:wallpaper_id>', methods=['GET', 'POST'])
@login_required
def select_collection_to_remove(wallpaper_id):
    wallpaper = get_wallpaper(wallpaper_id)
    
    # Get user collections that contain the wallpaper
    collections = [collection for collection in current_user.collections if wallpaper in collection.wallpapers]
    
    if not collections:
        flash("Ta tapeta nie znajduje się w żadnej z Twoich kolekcji.", 'info')
        return redirect(url_for('user.dashboard'))  # Send user back to main page
    
    if request.method == 'POST':
        collection_id = request.form.get('collection_id', type=int)
        collection = Collection.query.filter_by(id=collection_id, user_id=current_user.id).first_or_404()
        
        if wallpaper in collection.wallpapers:
            collection.wallpapers.remove(wallpaper)
            db.session.commit()
            flash(f"Tapeta została usunięta z kolekcji '{collection.name}'.", 'success')
        else:
            flash("Ta tapeta nie znajduje się w wybranej kolekcji.", 'warning')
        
        return redirect(url_for('user.dashboard'))  # Send user back to main page
    
    return render_template('select_collection_to_remove.html', wallpaper=wallpaper, collections=collections)


# Deleting collection
@user_bp.route('/delete_collection/<int:collection_id>', methods=['POST'])
@login_required
def delete_collection(collection_id):
    collection = Collection.query.get_or_404(collection_id)

    # Che` ck if the current user is the owner of the collection`
    if collection.user_id != current_user.id:
        flash("Nie masz uprawnień do usunięcia tej kolekcji.", 'danger')
        return redirect(url_for('user.dashboard'))

    try:
        # Remove relationships between the collection and wallpapers
        collection.wallpapers.clear()
        db.session.delete(collection)
        db.session.commit()
        flash(f"Kolekcja została usunięta.", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Wystąpił błąd podczas usuwania kolekcji: {e}", 'danger')

    return redirect(url_for('user.dashboard'))

# Get user collections helper func
def get_user_collections(user_id):
    return Collection.query.filter_by(user_id=user_id).all()

# Get wallpaper by ID helper func
def get_wallpaper(wallpaper_id):
    return Wallpaper.query.get_or_404(wallpaper_id)
