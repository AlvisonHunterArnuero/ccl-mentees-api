from flask import Flask, request, jsonify, redirect, url_for
from flask import flash
from flask import render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy import Enum
import enum
from dotenv import dotenv_values
from typing import Optional, Dict, Any

# Initialize Flask application
app = Flask(__name__)
app.app_context().push()

# Load configuration from .env file
config = dotenv_values(".env")

# MySQL Database configuration using Aiven free resource
SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}:18978/{databasename}?ssl_disabled=False".format(
    username=config["username"],
    password=config["password"],
    hostname=config["hostname"],
    databasename=config["databasename"],
)
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SECRET_KEY'] = config["secret_key"]  # Needed for session management

# Initialize SQLAlchemy
db = SQLAlchemy(app)


# Enums for user roles
class UserRole(enum.Enum):
    """Enumeration for user roles."""
    admin = "admin"
    guest = "guest"


class User(UserMixin, db.Model):
    """User model for the application."""
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False)


class Mentee(db.Model):
    """Mentee model for the application."""
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    english_level = db.Column(db.String(50))
    python_level = db.Column(db.String(50))
    javascript_level = db.Column(db.String(50))
    seniority = db.Column(db.String(50))
    linkedin_profile = db.Column(db.String(100))
    github_profile = db.Column(db.String(100))
    website = db.Column(db.String(100))
    final_grade = db.Column(db.Float)


# Create tables in the aiven MySQL database
with app.app_context():
    try:
        db.create_all()
        print("Database connected successfully and tables created.")
    except Exception as e:
        print(f"Error connecting to the database: {e}")

# Initialize Flask-Login
login_manager = LoginManager(app)

# Route to redirect if not logged in
login_manager.login_view = 'login'


# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id: int) -> Optional[User]:
    """Load user by ID for Flask-Login."""
    flash("User ID", str(user_id))
    return User.query.get(int(user_id))


# Login route
@app.route('/login', methods=['POST'])
def login() -> Any:
    """Login route for the application."""
    data = request.json
    user = User.query.filter_by(name=data['name']).first()
    if user and user.password == data['password']:
        login_user(user)
        return jsonify({'message': 'Logged in successfully'}), 200
    return jsonify({'message': 'Invalid credentials'}), 401


# Logout route
@app.route('/logout', methods=['GET'])
@login_required
def logout() -> Any:
    """Logout route for the application."""
    logout_user()
    return jsonify({'message': 'Logged out successfully'}), 200


# The rest of the routes
@app.route('/')
def hello() -> str:
    """Route to render the home page."""
    return render_template('home.html')


# Docs Routes
@app.route('/login_docs')
def login_docs() -> str:
    """Route to render the login documentation page."""
    return render_template('login_docs.html')


@app.route('/mentees_docs')
def mentees_docs() -> str:
    """Route to render the mentees documentation page."""
    return render_template('mentees_docs.html')


@app.route('/users_docs')
def users_docs() -> str:
    """Route to render the users documentation page."""
    return render_template('users_docs.html')


# ------- CRUD operations for User -----------

@app.route('/users', methods=['POST'])
@login_required
def create_user() -> Any:
    """Route to create a new user."""
    data = request.json
    new_user = User(
        name=data['name'],
        password=data['password'],
        role=UserRole[data['role']]
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User created successfully'}), 201


@app.route('/users', methods=['GET'])
@login_required
def get_users() -> Any:
    """Route to get all users."""
    users = User.query.all()
    return jsonify([{
        'id': user.id,
        'name': user.name,
        'password': user.password,
        'role': user.role.value
    } for user in users]), 200


@app.route('/users/<int:usr_id>', methods=['GET'])
@login_required
def get_user(usr_id: int) -> Any:
    """Route to get a user by ID."""
    user = User.query.get_or_404(usr_id)
    return jsonify({
        'id': user.id,
        'name': user.name,
        'role': user.role.value
    }), 200


@app.route('/users/<int:usr_id>', methods=['PUT'])
@login_required
def update_user(usr_id: int) -> Any:
    """Route to update a user by ID."""
    data = request.json
    user = User.query.get_or_404(usr_id)
    user.name = data['name']
    user.password = data['password']
    user.role = UserRole[data['role']]
    db.session.commit()
    return jsonify({'message': 'User updated successfully'}), 200


@app.route('/users/<int:usr_id>', methods=['DELETE'])
@login_required
def delete_user(usr_id: int) -> Any:
    """Route to delete a user by ID."""
    user = User.query.get_or_404(usr_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully'}), 200


# ------- CRUD operations for Mentee -------

@app.route('/mentees', methods=['POST'])
@login_required
def create_mentee() -> Any:
    """Route to create a new mentee."""
    data = request.json
    new_mentee = Mentee(
        name=data['name'],
        last_name=data['last_name'],
        email=data['email'],
        phone=data.get('phone'),
        english_level=data.get('english_level'),
        python_level=data.get('python_level'),
        javascript_level=data.get('javascript_level'),
        seniority=data.get('seniority'),
        linkedin_profile=data.get('linkedin_profile'),
        github_profile=data.get('github_profile'),
        website=data.get('website'),
        final_grade=data.get('final_grade')
    )
    db.session.add(new_mentee)
    db.session.commit()
    return jsonify({'message': 'Mentee created successfully'}), 201


@app.route('/mentees', methods=['GET'])
@login_required
def get_mentees() -> Any:
    """Route to get all mentees."""
    mentees = Mentee.query.all()
    return jsonify([{
        'id': mentee.id,
        'name': mentee.name,
        'last_name': mentee.last_name,
        'email': mentee.email,
        'phone': mentee.phone,
        'english_level': mentee.english_level,
        'python_level': mentee.python_level,
        'javascript_level': mentee.javascript_level,
        'seniority': mentee.seniority,
        'linkedin_profile': mentee.linkedin_profile,
        'github_profile': mentee.github_profile,
        'website': mentee.website,
        'final_grade': mentee.final_grade
    } for mentee in mentees]), 200


@app.route('/mentees/<int:id>', methods=['GET'])
@login_required
def get_mentee(id: int) -> Any:
    """Route to get a mentee by ID."""
    mentee = Mentee.query.get_or_404(id)
    return jsonify({
        'id': mentee.id,
        'name': mentee.name,
        'last_name': mentee.last_name,
        'email': mentee.email,
        'phone': mentee.phone,
        'english_level': mentee.english_level,
        'python_level': mentee.python_level,
        'javascript_level': mentee.javascript_level,
        'seniority': mentee.seniority,
        'linkedin_profile': mentee.linkedin_profile,
        'github_profile': mentee.github_profile,
        'website': mentee.website,
        'final_grade': mentee.final_grade
    }), 200


@app.route('/mentees/<int:id>', methods=['PUT'])
@login_required
def update_mentee(id: int) -> Any:
    """Route to update a mentee by ID."""
    data = request.json
    mentee = Mentee.query.get_or_404(id)
    mentee.name = data['name']
    mentee.last_name = data['last_name']
    mentee.email = data['email']
    mentee.phone = data.get('phone')
    mentee.english_level = data.get('english_level')
    mentee.python_level = data.get('python_level')
    mentee.javascript_level = data.get('javascript_level')
    mentee.seniority = data.get('seniority')
    mentee.linkedin_profile = data.get('linkedin_profile')
    mentee.github_profile = data.get('github_profile')
    mentee.website = data.get('website')
    mentee.final_grade = data.get('final_grade')
    db.session.commit()
    return jsonify({'message': 'Mentee updated successfully'}), 200


@app.route('/mentees/<int:id>', methods=['DELETE'])
@login_required
def delete_mentee(id: int) -> Any:
    """Route to delete a mentee by ID."""
    mentee = Mentee.query.get_or_404(id)
    db.session.delete(mentee)
    db.session.commit()
    return jsonify({'message': 'Mentee deleted successfully'}), 200


if __name__ == '__main__':
    app.run(debug=False)
