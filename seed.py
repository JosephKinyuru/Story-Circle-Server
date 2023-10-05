#!/usr/bin/env python3

from faker import Faker

from app import app
from models import db, User , BookClub , ClubMember , Book , CurrentBook , PrevioislyReadBook , BookComment , Message

with app.app_context():
    fake = Faker()

    try:
        User.query.delete()
    except Exception as e:
        pass
    users = []
    for i in range(50):
        user = User(
            username=fake.unique.first_name(),
            email= fake.email(),
            password = fake.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True),
            first_name = fake.first_name(),
            last_name = fake.last_name(),
            profile_pic = fake.image_url()
        )
        users.append(user)

    db.session.add_all(users)
    db.session.commit()

    
    
    try:
        BookClub.query.delete()
    except Exception as e:
        pass

    bookclubs = []
    for i in range(25):
        bookclub = BookClub(
            name=fake.company(),
            location = fake.city(),
            description=fake.paragraph(nb_sentences=5),
            creator_id = fake.random_element(elements=users).id, 
        )
        bookclubs.append(bookclub)

    db.session.add_all(bookclubs)
    db.session.commit()

    
    
    
    
    try:
        ClubMember.query.delete()
    except Exception as e:
        pass
    for i in range(100):
        clubmember = ClubMember(
            club_id=fake.random_element(elements=bookclubs).id,
            member_id=fake.random_element(elements=users).id
        )
        db.session.add(clubmember)

    db.session.commit()
    
    
    
    
    
    try:
        Book.query.delete()
    except Exception as e:
        pass
    books = []
    for i in range(50):
        book = Book(
            title=fake.word() + " " + fake.word(),
            author=fake.name(),
            description = fake.paragraph(nb_sentences=5),
        )
        books.append(book)

    db.session.add_all(books)
    db.session.commit()

    
    
    
    
    
    try:
        CurrentBook.query.delete()
    except Exception as e:
        pass
    for i in range(50):
        currentbook = CurrentBook(
            club_id=fake.random_element(elements=bookclubs).id,
            book_id=fake.random_element(elements=books).id
        )
        db.session.add(currentbook)

    db.session.commit()

    
    
    
    
    
    
    try:
        PrevioislyReadBook.query.delete()
    except Exception as e:
        pass
    for i in range(50):
        previousbook = PrevioislyReadBook(
            club_id=fake.random_element(elements=bookclubs).id,
            book_id=fake.random_element(elements=books).id
        )
        db.session.add(previousbook)

    db.session.commit()

    
    
    
    
    
    try:
        BookComment.query.delete()
    except Exception as e:
        pass
    for i in range(200):
        bookcomment = BookComment(
            book_id=fake.random_element(elements=books).id,
            user_id=fake.random_element(elements=users).id,
            rating=fake.random_int(min=1, max=5),
            comment = fake.paragraph(nb_sentences=5),
        )
        db.session.add(bookcomment)

    db.session.commit()

    
    
    
    
    
    
    try:
        Message.query.delete()
    except Exception as e:
        pass
    for i in range(200):
        messageAR = Message(
            club_id=fake.random_element(elements=bookclubs).id,
            sender_id=fake.random_element(elements=users).id,
            message = fake.paragraph(nb_sentences=5),
        )
        db.session.add(messageAR)

    db.session.commit()

