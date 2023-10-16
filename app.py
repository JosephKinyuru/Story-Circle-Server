import os
from datetime import timedelta
from flask import Flask, jsonify, request, make_response
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_restful import Api, Resource
from werkzeug.exceptions import NotFound
import requests
from flask_cors import CORS
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, create_access_token

from models import db , User , BookClub , ClubMember , Book , CurrentBook , PrevioislyReadBook , BookComment , Message

# These Configerations are for when  running the server locally for deployment configerations look at create_app function
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///story_circle.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

CORS(app)
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})

migrate = Migrate(app, db)
db.init_app(app)
ma = Marshmallow(app)
api = Api(app)
app.config['JWT_SECRET_KEY'] = '$2a$10$Xs1h0711a6I8n4c9179t0u.h773sj7/Xc2.0737j5r6v996349/Hm0j6z3yM'  # Personal / Owner Key For JWT locked resources
jwt = JWTManager(app)

def is_valid_url(url):
    try:
        response = requests.head(url)
        return response.status_code == 200
    except Exception as e:
        return False

class BookSchema(ma.SQLAlchemyAutoSchema):

    class Meta:
        model = Book
        load_instance = True

book_schema = BookSchema()
books_schema = BookSchema(many=True)

class BookClubSchema(ma.SQLAlchemyAutoSchema):

    class Meta:
        model = BookClub
        load_instance = True

bookClub_schema = BookClubSchema()
bookClubs_schema = BookClubSchema(many=True)

class Index(Resource):
    def get(self):

        response_dict = {
            "index": "Welcome to the Story Circle RESTful API",
        }

        response = make_response(
            jsonify(response_dict),
            200,
        )
        response.headers["Content-Type"] = "application/json"

        return response

class Register(Resource):
    def post(self):
        try: 
            new_user = User(
                username=request.json['username'],
                email=request.json['email'],
                first_name=request.json['first_name'],
                last_name=request.json['last_name'],
                profile_pic=request.json['profile_pic']
            )
            new_user.set_password(request.json['password'])  

            db.session.add(new_user)
            db.session.commit()

            response = make_response(
                jsonify({ "message": "User created successfully"}),
                201,
            )
            response.headers["Content-Type"] = "application/json"

            return response
        
        except IntegrityError as e:
            db.session.rollback()

            response = make_response(
                jsonify({"errors": ["Username or email already exists"]}),
                400
            )
            response.headers["Content-Type"] = "application/json"

            return response

        except Exception as e:
            db.session.rollback()
                
            response = make_response(
                jsonify({"errors": ["validation errors"]}),
                400
            )
            response.headers["Content-Type"] = "application/json"

            return response

class LogIn(Resource):
    def post(self):
        try:
            user = User.query.filter_by(username=request.json['username']).first()

            if user and user.check_password(request.json['password']):
                # Generating a token for the user
                access_token = create_access_token(identity=request.json['username'], expires_delta=timedelta(days=30))

                response = make_response(
                    jsonify({
                        "access_token": access_token, 
                        "message": "Login successful",
                        "user_id": user.id , 
                        }),
                    200,
                )
            else:
                # Password is incorrect or user doesn't exist
                response = make_response(
                    jsonify({"errors": ["Invalid email or password"]}),
                    401
                )

            response.headers["Content-Type"] = "application/json"

            return response
    
        except Exception as e:
            response = make_response(
                jsonify({"errors": ["An error occurred"]}),
                500
            )
            response.headers["Content-Type"] = "application/json"

            return response

class Profile(Resource):
    @jwt_required()
    def get(self, username):
        current_username = get_jwt_identity()  # Retrieve the current user's identity from the token

        if current_username != username:
            response = make_response(jsonify({"message": "Unauthorized"}), 401)
            response.headers["Content-Type"] = "application/json"
            return response

        user = User.query.filter_by(username=username).first()

        if user:
            response_data = {
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "profile_pic": user.profile_pic
            }

            response = make_response(
                jsonify(response_data),
                200,
            )
            response.headers["Content-Type"] = "application/json"

            return response

        response = make_response(jsonify({"message": "User not found"}), 404)
        response.headers["Content-Type"] = "application/json"
        return response

    @jwt_required()
    def patch(self, username):
        current_username = get_jwt_identity()

        if current_username != username:
            response = make_response(jsonify({"message": "Unauthorized"}), 401)
            response.headers["Content-Type"] = "application/json"
            return response

        user = User.query.filter_by(username=username).first()

        if not user:
            response = make_response(jsonify({"message": "User not found"}), 404)
            response.headers["Content-Type"] = "application/json"
            return response

        if 'profile_pic' in request.json:
            profile_pic_url = request.json['profile_pic']
            if not is_valid_url(profile_pic_url):
                response = make_response(
                    jsonify({"errors": ["Invalid profile picture URL"]}),
                    400
                )
                response.headers["Content-Type"] = "application/json"
                return response

        for attr in request.json:
            setattr(user, attr, request.json[attr])

        db.session.add(user)
        db.session.commit()

        response = make_response(
            jsonify({"message": "Profile updated successfully"}),
            200,
        )
        response.headers["Content-Type"] = "application/json"

        return response

    @jwt_required()
    def delete(self, username):
        current_username = get_jwt_identity()

        if current_username != username:
            response = make_response(jsonify({"message": "Unauthorized"}), 401)
            response.headers["Content-Type"] = "application/json"
            return response

        user = User.query.filter_by(username=username).first()

        if not user:
            response = make_response(jsonify({"message": "User not found"}), 404)
            response.headers["Content-Type"] = "application/json"
            return response

        db.session.delete(user)
        db.session.commit()

        response = make_response(
            jsonify({"message": "Profile deleted successfully"}),
            200,
        )
        response.headers["Content-Type"] = "application/json"

        return response

class BookClubRes(Resource):
    @jwt_required()
    def post(self):
        try: 
            new_club = BookClub(
                name=request.json['name'],
                location=request.json['location'],
                description=request.json['description'],
                creator_id=request.json['creator_id'],
            )  

            db.session.add(new_club)
            db.session.commit()

            response = make_response(
                jsonify({ "message": "Book Club created successfully"}),
                201,
            )
            response.headers["Content-Type"] = "application/json"

            return response
        
        except IntegrityError as e:
            db.session.rollback()

            response = make_response(
                jsonify({"errors": ["Name already exists"]}),
                400
            )
            response.headers["Content-Type"] = "application/json"

            return response

        except Exception as e:
            db.session.rollback()
                
            response = make_response(
                jsonify({"errors": ["validation errors"]}),
                400
            )
            response.headers["Content-Type"] = "application/json"

            return response

    def get(self):
        try:
            bookclubs = BookClub.query.all()

            if bookclubs:
                response = make_response(
                    bookClubs_schema.dump(bookclubs),
                    200,
                )
                response.headers["Content-Type"] = "application/json"
                return response
            else:
                response = make_response(
                    jsonify({"error": "Book Clubs are not currently in database"}),
                    404
                )
                response.headers["Content-Type"] = "application/json"
                return response
        except Exception as e:
            # Handle unexpected server errors
            response = make_response(
                jsonify({"error": "An unexpected error occurred on the server"}),
                500
            )
            response.headers["Content-Type"] = "application/json"
            return response

class BookClubByID(Resource):

    def get(self, id):
        bookclub = BookClub.query.filter_by(id=id).first()

        if bookclub:

            # Get creator
            creator = User.query.filter_by(id=bookclub.creator_id).first()

            creator_data = {
                "id": creator.id if creator else None,
                "username": creator.username if creator else None,
                "first_name": creator.first_name if creator else None,
                "last_name": creator.last_name if creator else None
            }


            # Get club members
            members = [member.member for member in bookclub.club_members]

            # Get current book
            current_book = CurrentBook.query.filter_by(club_id=id).first()

            # Get previous books and their comments
            previous_books = PrevioislyReadBook.query.filter_by(club_id=id).all()

        previous_books_data = []

        for prev_book in previous_books:
            book_comments = BookComment.query.filter_by(book_id=prev_book.book_id).all()
            comment_data = []

            for comment in book_comments:
                comment_data.append({
                    "id": comment.id,
                    "comment": comment.comment,
                    "rating": comment.rating,
                    "username": comment.user.username
                })

            previous_books_data.append({
                "book": {
                    "id": prev_book.book.id,
                    "title": prev_book.book.title,
                    "author": prev_book.book.author,
                    "description": prev_book.book.description
            } if prev_book.book else None,  # Check if prev_book has an associated book
            "comments": comment_data
             })

            # Get messages
            messages = Message.query.filter_by(club_id=id).all()

            message_data = []
            for message in messages:
                message_data.append({
                    "id": message.id,
                    "sender": message.sender.username,
                    "message": message.message,
                    "created_at": message.created_at
                })

            response_data = {
                "id": bookclub.id,
                "name": bookclub.name,
                "location": bookclub.location,
                "description": bookclub.description,
                "creator": creator_data,
                "members": [{
                    "id": member.id,
                    "username": member.username
                } for member in members],
                "current_book": {
                    "id": current_book.book.id,
                    "title": current_book.book.title,
                    "author": current_book.book.author,
                    "description": current_book.book.description
                } if current_book else None,
                "previous_books": previous_books_data,
                "messages": message_data
            }

            response = make_response(
                jsonify(response_data),
                200,
            )
            response.headers["Content-Type"] = "application/json"

            return response

        else:
            response = make_response(
                jsonify({"error": "Book Club not found"}),
                404
            )
            response.headers["Content-Type"] = "application/json"

            return response

    @jwt_required()
    def patch(self, id):
        bookclub = BookClub.query.filter_by(id=id).first()

        if bookclub :
            for attr in request.json:
                setattr(bookclub, attr, request.json[attr])

            db.session.add(bookclub)
            db.session.commit()

            response = make_response(
                jsonify({{"message": "Book Club updated successfully"}}),
                200
            )
            response.headers["Content-Type"] = "application/json"

            return response

        
        else :
            response = make_response(
                jsonify({"error": "BookClub not found"}),
                404
            )
            response.headers["Content-Type"] = "application/json"

            return response
        
    @jwt_required()
    def delete(self, id):
        current_user_username = get_jwt_identity()  # Retrieve the current user's username from the token

        # Query the User table to get the user object based on the username
        current_user = User.query.filter_by(username=current_user_username).first()

        if current_user:
            # Check if the book club exists and if the current user is its creator
            bookclub = BookClub.query.filter_by(id=id, creator_id=current_user.id).first()

            if bookclub:
                db.session.delete(bookclub)
                db.session.commit()

                response = make_response(
                    jsonify({"message": "Book Club successfully deleted"}),
                    200
                )
            else:
                response = make_response(
                    jsonify({"error": "Book Club not found or you are not the creator"}),
                    404
                )
        else:
            response = make_response(
                jsonify({"error": "Current user not found"}),
                404
            )

        response.headers["Content-Type"] = "application/json"
        return response

class JoinClub(Resource):
    @jwt_required()
    def post(self):
        try: 
            current_user = get_jwt_identity()

            new_member = ClubMember(
                club_id = request.json['club_id'],
                member_id = request.json['user_id'],
            )

            db.session.add(new_member)
            db.session.commit()

            response = make_response(
                jsonify({ "message": "Member joined successfully"}),
                201,
            )
            response.headers["Content-Type"] = "application/json"

            return response
        
        except IntegrityError as e:
            db.session.rollback()

            response = make_response(
                jsonify({"errors": ["User or club does not exists"]}),
                400
            )
            response.headers["Content-Type"] = "application/json"

            return response

        except Exception as e:
            db.session.rollback()
                
            response = make_response(
                jsonify({"errors": ["validation errors"]}),
                400
            )
            response.headers["Content-Type"] = "application/json"

            return response

class Books(Resource):

    def get(self):
        books = Book.query.all()

        if books :
            response = make_response(
                books_schema.dump(books),
                200,
            )
            response.headers["Content-Type"] = "application/json"

            return response
        
        else :
            response = make_response(
                jsonify({"error":" Books are not currently in database"}),
                  404
                )
            response.headers["Content-Type"] = "application/json"

            return response
        
    @jwt_required()
    def post(self):
        try:
            new_book = Book(
                title=request.json['title'],
                author=request.json['author'],
                description=request.json['description'],
            )

            db.session.add(new_book)
            db.session.commit()

            response = make_response(
                book_schema.dump(new_book),
                201,
            )
            response.headers["Content-Type"] = "application/json"

            return response
        
        except IntegrityError as e:
            db.session.rollback()

            response = make_response(
                jsonify({"errors": ["Book title already exists"]}),
                400
            )
            response.headers["Content-Type"] = "application/json"

            return response

        except Exception as e:
            db.session.rollback()
                
            response = make_response(
                jsonify({"errors": ["validation errors"]}),
                400
            )
            response.headers["Content-Type"] = "application/json"

            return response

class BooksByID(Resource):

    def get(self, id):
        book = Book.query.filter_by(id=id).first()

        if book :
            book_comments = BookComment.query.filter_by(book_id=id).all()
            comment_data = []

            for comment in book_comments:
                    comment_data.append({
                        "id": comment.id,
                        "comment": comment.comment,
                        "rating": comment.rating,
                        "username":comment.user.username,
                        "user_profile_pic":comment.user.profile_pic,
                    })

            response_data = {
                "id": book.id,
                "title": book.title,
                "author": book.author,
                "description": book.description,
                "comments": comment_data,
            }

            response = make_response(
                jsonify(response_data),
                200,
            )
            response.headers["Content-Type"] = "application/json"

            return response
        
        else :
            response = make_response(
                jsonify({"error":" Restaurant not found"}),
                  404
                )
            response.headers["Content-Type"] = "application/json"

            return response

    @jwt_required()
    def patch(self, id):
        book = Book.query.filter_by(id=id).first()

        if book :
            for attr in request.json:
                setattr(book, attr, request.json[attr])

            db.session.add(book)
            db.session.commit()

            response = make_response(
                book_schema.dump(book),
                200
            )
            response.headers["Content-Type"] = "application/json"

            return response

        
        else :
            response = make_response(
                jsonify({"error": "Restaurant not found"}),
                404
            )
            response.headers["Content-Type"] = "application/json"

            return response

    @jwt_required()
    def delete(self, id):
        book = Book.query.filter_by(id=id).first()

        if book :
            db.session.delete(book)
            db.session.commit()

            response = make_response(
                jsonify({"message": "Book successfully deleted"}),
                200
            )
            response.headers["Content-Type"] = "application/json"

            return response
        else :
            response = make_response(
                jsonify({"error": "Restaurant not found"}),
                404
                )
            response.headers["Content-Type"] = "application/json"

            return response

class AddCurrentBook(Resource):
    @jwt_required()
    def post(self):
        try: 
            new_current_book = CurrentBook(
                club_id=request.json['club_id'],
                book_id=request.json['book_id'],
            )

            db.session.add(new_current_book)
            db.session.commit()

            response = make_response(
                jsonify({ "message": "Current created successfully"}),
                201,
            )
            response.headers["Content-Type"] = "application/json"

            return response

        except Exception as e:
            db.session.rollback()
                
            response = make_response(
                jsonify({"errors": ["validation errors"]}),
                400
            )
            response.headers["Content-Type"] = "application/json"

            return response

class DelCurrentBook(Resource):
    @jwt_required()
    def delete(self, id):
        currentBook = CurrentBook.query.filter_by(club_id=id).first()

        if currentBook :
            db.session.delete(currentBook)        
            db.session.commit()

            response = make_response(
                jsonify({"message": "Current Book successfully deleted"}),
                200
            )
            response.headers["Content-Type"] = "application/json"

            return response
        else :
            response = make_response(
                jsonify({"error": "Current Book not found"}),
                404
                )
            response.headers["Content-Type"] = "application/json"

            return response

class AddPreviousBook(Resource):
    @jwt_required()
    def post(self):
        try: 
            new_previous_book = PrevioislyReadBook(
                club_id=request.json['club_id'],
                book_id=request.json['book_id'],
            )

            db.session.add(new_previous_book)
            db.session.commit()

            response = make_response(
                jsonify({ "message": "Previously  Read Book created successfully"}),
                201,
            )
            response.headers["Content-Type"] = "application/json"

            return response

        except Exception as e:
            db.session.rollback()
                
            response = make_response(
                jsonify({"errors": ["validation errors"]}),
                400
            )
            response.headers["Content-Type"] = "application/json"

            return response

class DelPreviousBook(Resource):
    @jwt_required()
    def delete(self, id):
        previousBook = PrevioislyReadBook.query.filter_by(club_id=id).first()

        if previousBook :
            db.session.delete(previousBook)        
            db.session.commit()

            response = make_response(
                jsonify({"message": "Previous Book successfully deleted"}),
                200
            )
            response.headers["Content-Type"] = "application/json"

            return response
        else :
            response = make_response(
                jsonify({"error": "Previous Book not found"}),
                404
                )
            response.headers["Content-Type"] = "application/json"

            return response

class AddBookComment(Resource):
    @jwt_required()
    def post(self):
        try:

            new_comment = BookComment(
                user_id=request.json['user_id'],
                book_id=request.json['book_id'],
                comment=request.json['comment'],
                rating=request.json['rating'],
            )

            db.session.add(new_comment)
            db.session.commit()

            response = make_response(
                jsonify({"message": "Comment created successfully"}),
                201,
            )
            response.headers["Content-Type"] = "application/json"

            return response

        except Exception as e:
            db.session.rollback()

            response = make_response(
                jsonify({"errors": ["validation errors"]}),
                400
            )
            response.headers["Content-Type"] = "application/json"

            return response

class AddMessage(Resource):
    @jwt_required()
    def post(self):
        try:

            new_message = Message(
                sender_id=request.json['sender_id'],
                club_id=request.json['club_id'],
                message=request.json['message'],
            )

            db.session.add(new_message)
            db.session.commit()

            response = make_response(
                jsonify({"message": "Message created successfully"}),
                201,
            )
            response.headers["Content-Type"] = "application/json"

            return response

        except Exception as e:
            db.session.rollback()

            response = make_response(
                jsonify({"errors": ["validation errors"]}),
                400
            )
            response.headers["Content-Type"] = "application/json"

            return response


api.add_resource(Index, '/')
api.add_resource(Register, '/register')
api.add_resource(LogIn, '/login')
api.add_resource(Profile, '/profile/<string:username>')
api.add_resource(BookClubRes, '/clubs')
api.add_resource(BookClubByID, '/clubs/<int:id>')
api.add_resource(JoinClub, '/joinclub')
api.add_resource(Books, '/books')
api.add_resource(BooksByID, '/books/<int:id>')
api.add_resource(AddCurrentBook, '/currentbook')
api.add_resource(DelCurrentBook, '/currentbook/<int:id>')  # The id is the club ID
api.add_resource(AddPreviousBook, '/previousbooks')
api.add_resource(DelPreviousBook, '/previousbooks/<int:id>')  # The id is the club ID
api.add_resource(AddBookComment, '/bookcomments')
api.add_resource(AddMessage, '/messages')




@app.errorhandler(NotFound)
def handle_not_found(e):

    response = make_response(
        jsonify({"error": "The requested resource does not exist."}),
        404
    )
    response.headers["Content-Type"] = "application/json"

    return response


def create_app():

    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = '$2a$10$Xs1h0711a6I8n4c9179t0u.h773sj7/Xc2.0737j5r6v996349/Hm0j6z3yM'
    CORS(app)
    CORS(app, resources={r"/*": {"origins": "https://magical-dolphin-be64a8.netlify.app/"}})
    api = Api(app)
    db.init_app(app)
        
    api.add_resource(Index, '/')
    api.add_resource(Register, '/register')
    api.add_resource(LogIn, '/login')
    api.add_resource(Profile, '/profile/<string:username>')
    api.add_resource(BookClubRes, '/clubs')
    api.add_resource(BookClubByID, '/clubs/<int:id>')
    api.add_resource(JoinClub, '/joinclub')
    api.add_resource(Books, '/books')
    api.add_resource(BooksByID, '/books/<int:id>')
    api.add_resource(AddCurrentBook, '/currentbook')
    api.add_resource(DelCurrentBook, '/currentbook/<int:id>')
    api.add_resource(AddPreviousBook, '/previousbooks')
    api.add_resource(DelPreviousBook, '/previousbooks/<int:id>')
    api.add_resource(AddBookComment, '/bookcomments')
    api.add_resource(AddMessage, '/messages')


    @app.errorhandler(NotFound)
    def handle_not_found(e):
        response = make_response(
            jsonify({"error": "The requested resource does not exist."}),
            404
        )
        response.headers["Content-Type"] = "application/json"
        return response

    return app


if __name__ == '__main__':
    app.run(port=5555)