from extensions import db # importujemy instancje db
from flask_login import UserMixin # dostarcza standardowe metody potrzebne dla Flask-Login


"""
Klasa User reprezentuje tabelę użytkowników w bazie danych.
"""
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)  # Pole id jest unikalnym głównym kluczem tabeli
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    email = db.Column(db.String(150), nullable=True)


    # relacje
    wallpapers = db.relationship('Wallpaper', backref='owner', lazy=True)
    collections = db.relationship('Collection', backref='user', lazy=True)

    def __repr__(self):
        return f"<User('{self.username}', admin={self.is_admin})>"
    
    """
    metoda __repr_(self) zwraca informacje o User
    przykład:
    ```
    user = User(username='janek', is_admin=False)
    print(user)
    Wyświetla: <User('janek', admin=False)>
    ```
    """

# Modele tapet
"""
Device: mobile lub desktop
kolekcje są konkretnego typu
"""
class Device(db.Model):
    __tablename__ = 'device'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"<Device('{self.name}')>"

class Collection(db.Model):
    __tablename__ = 'collection'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    wallpapers = db.relationship(
        'Wallpaper', 
        secondary='wallpaper_collection', 
        backref='collections',
          lazy='dynamic'
    )

    def __repr__(self):
        return f"<Collection('{self.name}', user_id={self.user_id})>"

class Wallpaper(db.Model):
    __tablename__ = 'wallpaper'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    resolution = db.Column(db.String(20), nullable=False)
    path = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey('device.id'), nullable=False)

    colors = db.relationship('Color', secondary='wallpaper_color', backref='wallpapers')
    tags = db.relationship('Tag', secondary='wallpaper_tag', backref='wallpapers')
    device = db.relationship('Device', backref='wallpapers')

    def __repr__(self):
        return f"<Wallpaper('{self.name}', resolution={self.resolution}, device_id={self.device_id})>"

class Color(db.Model):
    __tablename__ = 'color'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"<Color('{self.name}')>"

class Tag(db.Model):
    __tablename__ = 'tag'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"<Tag('{self.name}')>"

# Tabele pośredniczące
wallpaper_collection = db.Table('wallpaper_collection',
    db.Column('wallpaper_id', db.Integer, db.ForeignKey('wallpaper.id'), primary_key=True),
    db.Column('collection_id', db.Integer, db.ForeignKey('collection.id'), primary_key=True)
)

wallpaper_color = db.Table('wallpaper_color',
    db.Column('wallpaper_id', db.Integer, db.ForeignKey('wallpaper.id'), primary_key=True),
    db.Column('color_id', db.Integer, db.ForeignKey('color.id'), primary_key=True)
)

wallpaper_tag = db.Table('wallpaper_tag',
    db.Column('wallpaper_id', db.Integer, db.ForeignKey('wallpaper.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)
