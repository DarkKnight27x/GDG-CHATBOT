from flask import Flask, request, jsonify
import mysql.connector
import bcrypt
from flask_jwt_extended import create_access_token, jwt_required, JWTManager, get_jwt_identity
import os
from datetime import timedelta
import logging

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Configure JWT
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'default_secret_key')  # Use environment variable for production
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)  # Token expires in 1 hour
jwt = JWTManager(app)

# Database connection (use environment variables for sensitive data)
db = mysql.connector.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    user=os.getenv('DB_USER', 'root'),
    password=os.getenv('DB_PASSWORD', 'Nim@Li20062011'),
    database=os.getenv('DB_NAME', 'chatbot_db')
)
cursor = db.cursor()

# Signup Route
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    
    # Validate input data
    if not all(key in data for key in ['name', 'email', 'username', 'password', 'age']):
        return jsonify({"message": "Missing required fields"}), 400
    
    name, email, username, password, age = data['name'], data['email'], data['username'], data['password'], data['age']
    
    # Enforce strong passwords (example: minimum length)
    if len(password) < 8:
        return jsonify({"message": "Password must be at least 8 characters long"}), 400
    
    # Validate age (must be an integer and above a certain threshold)
    if not isinstance(age, int) or age < 0:
        return jsonify({"message": "Age must be a positive integer"}), 400

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    try:
        cursor.execute("INSERT INTO users (name, email, username, password, age) VALUES (%s, %s, %s, %s, %s)",
                       (name, email, username, hashed_password, age))
        db.commit()
        return jsonify({"message": "User registered successfully"}), 201
    except mysql.connector.IntegrityError:
        return jsonify({"message": "Username or email already exists"}), 400
    except Exception as e:
        logging.error(f"Error during signup: {e}")
        return jsonify({"message": "An error occurred during signup"}), 500

# Login Route (using only username and password)
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    
    # Validate input data
    if not all(key in data for key in ['username', 'password']):
        return jsonify({"message": "Missing required fields"}), 400
    
    username, password = data['username'], data['password']
    
    try:
        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user[4].encode('utf-8')):
            access_token = create_access_token(identity={"username": user[3], "name": user[1], "age": user[5]})  # Include age in token identity
            return jsonify({
                "message": "Login successful",
                "token": access_token,
                "user_details": {
                    "name": user[1],
                    "username": user[3],
                    "age": user[5]
                }
            }), 200
        else:
            return jsonify({"message": "Invalid credentials"}), 401
    except Exception as e:
        logging.error(f"Error during login: {e}")
        return jsonify({"message": "An error occurred during login"}), 500

# Get User Details (Protected)
@app.route('/user', methods=['GET'])
@jwt_required()
def get_user():
    current_user = get_jwt_identity()
    
    try:
        cursor.execute("SELECT name, email, username, age FROM users WHERE username=%s", (current_user['username'],))
        user_info = cursor.fetchone()
        
        if user_info:
            return jsonify({
                "user": {
                    "name": user_info[0],
                    "email": user_info[1],
                    "username": user_info[2],
                    "age": user_info[3]  # Include age in the response
                }
            }), 200
        else:
            return jsonify({"message": "User not found"}), 404
    except Exception as e:
        logging.error(f"Error fetching user details: {e}")
        return jsonify({"message": "An error occurred while fetching user details"}), 500

if __name__ == '__main__':
    app.run(debug=True)
