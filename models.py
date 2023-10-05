from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import validates
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    first_name = db.Column(db.String)
    last_name = db.Column(db.String)
    profile_pic = db.Column(db.String, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    @validates('email')
    def validate_email(self, key, address):
        if '@' not in address:
            raise ValueError("failed simple email validation")
        return address

class BookClub(db.Model):
    __tablename__ = 'bookclubs'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    location = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    creator = db.relationship('User', backref=db.backref('bookclubs', lazy=True))

class ClubMember(db.Model):
    __tablename__ = 'club_members'

    id = db.Column(db.Integer, primary_key=True)
    club_id = db.Column(db.Integer, db.ForeignKey('bookclubs.id'))
    member_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    member = db.relationship('User', backref=db.backref('club_members', lazy=True))
    club = db.relationship('BookClub', backref=db.backref('club_members', lazy=True))

class Book(db.Model):
    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, unique=True, nullable=False)
    author = db.Column(db.String)
    description = db.Column(db.String)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class CurrentBook(db.Model):
    __tablename__ = 'current_books'

    id = db.Column(db.Integer, primary_key=True)
    club_id = db.Column(db.Integer, db.ForeignKey('bookclubs.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'))

    book = db.relationship('Book', backref=db.backref('current_books', lazy=True))
    club = db.relationship('BookClub', backref=db.backref('current_books', lazy=True))

class PrevioislyReadBook(db.Model):
    __tablename__ = 'previously_read_books'

    id = db.Column(db.Integer, primary_key=True)
    club_id = db.Column(db.Integer, db.ForeignKey('bookclubs.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'))

    book = db.relationship('Book', backref=db.backref('previously_read_books', lazy=True))
    club = db.relationship('BookClub', backref=db.backref('previously_read_books', lazy=True))

class BookComment(db.Model):
    __tablename__ = 'book_comments'

    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id')) 
    comment = db.Column(db.String, nullable=False)
    rating = db.Column(db.Integer, nullable=False)

    user = db.relationship('User', backref=db.backref('book_comments', lazy=True)) 
    book = db.relationship('Book', backref=db.backref('book_comments', lazy=True))

    @validates('rating')
    def validate_price(self, key, rating):
        if not (1 <= rating <= 5):
            raise ValueError("Price must be between 1 and 5")
        return rating

class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    club_id = db.Column(db.Integer, db.ForeignKey('bookclubs.id'))
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id')) 
    message = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    sender = db.relationship('User', backref=db.backref('messages', lazy=True)) 
    club = db.relationship('BookClub', backref=db.backref('messages', lazy=True))















