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

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///story_circle.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

def is_valid_url(url):
    try:
        response = requests.head(url)
        return response.status_code == 200
    except Exception as e:
        return False

# CORS(app)
# CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})

migrate = Migrate(app, db)
db.init_app(app)
ma = Marshmallow(app)
api = Api(app)
app.config['JWT_SECRET_KEY'] = 'super-secret-key'  # Personal / Owner Key For JWT locked resources
jwt = JWTManager(app)

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
            print(user)

            if user and user.check_password(request.json['password']):
                # Generating a token for the user
                access_token = create_access_token(identity=request.json['username'])

                response = make_response(
                    jsonify({
                        "access_token": access_token, 
                        "message": "Login successful",
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
            print(e)
            response = make_response(
                jsonify({"errors": ["An error occurred"]}),
                500
            )
            response.headers["Content-Type"] = "application/json"

            return response

class Profile(Resource):
    @jwt_required()  
    def get(self, user_id):
        current_user = get_jwt_identity()  # Retrieve the current user's identity from the token
        if current_user['user_id'] == user_id:  # Check if the user is accessing their own profile
            user = User.query.get(user_id)
            if user:
                response_data = {
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "profile_pic":user.profile_pic
                }

                response = make_response(
                    jsonify(response_data),
                    200,
                )
                response.headers["Content-Type"] = "application/json"

                return response
            else:
                response = make_response(jsonify({"message": "User not found"}), 404)
                response.headers["Content-Type"] = "application/json"
                return response
        else:
            response = make_response(jsonify({"message": "Unauthorized"}), 401)
            response.headers["Content-Type"] = "application/json"
            return response

    @jwt_required()
    def patch(self, user_id):
        current_user = get_jwt_identity()
        if current_user['user_id'] == user_id:
            user = User.query.get(user_id)
            if user:

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
                    setattr(user, attr , request.json[attr])

                db.session.add(user)
                db.session.commit()

                response = make_response(
                    jsonify({"message": "Profile updated successfully"}),
                    200,
                )
                response.headers["Content-Type"] = "application/json"

                return response
            else:
                response = make_response(jsonify({"message": "User not found"}), 404)
                response.headers["Content-Type"] = "application/json"
                return response
        else:
            response = make_response(jsonify({"message": "Unauthorized"}), 401)
            response.headers["Content-Type"] = "application/json"
            return response

    @jwt_required()
    def delete(self, user_id):
        current_user = get_jwt_identity()
        if current_user['user_id'] == user_id:
            user = User.query.get(user_id)
            if user:
                db.session.delete(user)
                db.session.commit()

                response = make_response(
                    jsonify({"message": "Profile deleted successfully"}),
                    200,
                )
                response.headers["Content-Type"] = "application/json"

                return response
            else:
                response = make_response(jsonify({"message": "User not found"}), 404)
                response.headers["Content-Type"] = "application/json"
                return response
        else:
            response = make_response(jsonify({"message": "Unauthorized"}), 401)
            response.headers["Content-Type"] = "application/json"
            return response



api.add_resource(Index, '/')
api.add_resource(Register, '/register')
api.add_resource(LogIn, '/login')
api.add_resource(Profile, '/profile/<int:user_id>')

@app.errorhandler(NotFound)
def handle_not_found(e):

    response = make_response(
        jsonify({"Not Found": "The requested resource does not exist."}),
        404
    )
    response.headers["Content-Type"] = "application/json"

    return response

if __name__ == '__main__':
    app.run(port=5555)