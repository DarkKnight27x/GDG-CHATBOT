from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import mysql.connector  
from datetime import datetime, timezone

app = Flask(__name__)
CORS(app)

# MySQL database configuration
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "Nim@Li0611",
    "database": "chatbot"
}

RASA_SERVER_URL = "http://localhost:5005/webhooks/rest/webhook"

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    print(f"Received data: {data}")
    user_message = data.get('message')
    user_id = data.get('user_id')
    conversation_id = data.get('conversation_id')

    if not user_message or not user_id or not conversation_id:
        return jsonify({"error": "No message, user_id, or conversation_id provided"}), 400

    print(f"Recieved message from user {user_id} in conversation {conversation_id}: {user_message}")

    #send message to rasa
    response = requests.post(RASA_SERVER_URL, json={"sender": user_id, "message": user_message})

    if response.status_code != 200:
        print(f"Failed to send message to Rasa: {response.status_code}")
        return jsonify({"error": "Failed to send message to Rasa"}), 500
    
    rasa_response = response.json()
    print(f"Recieved response from Rasa: {rasa_response}")

    #Save user message and rasa response in database
    save_chat_to_db(user_id, conversation_id, user_message, rasa_response[0]['text'])

    return jsonify(rasa_response)

def save_chat_to_db(user_id, conversation_id, user_message, rasa_response):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_history (conversation_id, user_message, rasa_response, timestamp) VALUES (%s, %s, %s, %s)", (conversation_id, user_message, rasa_response, datetime.now(timezone.utc)))
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Saved chat to DB: user_id={user_id}, conversation_id={conversation_id}, user_message={user_message}, rasa_response={rasa_response}")

def get_chat_history(user_id, conversation_id):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT user_message, rasa_response FROM chat_history WHERE conversation_id = %s ORDER BY timestamp ASC", (conversation_id))
    history = cursor.fetchall()
    cursor.close()
    conn.close()
    print(f"Retrieved chat history from DB: user_id={user_id}, conversation_id={conversation_id}, history={history}")
    return history

@app.route('/history', methods=['GET'])
def get_history():
    user_id = request.args.get('user_id')
    conversation_id = request.args.get('conversation_id')

    if not user_id or not conversation_id:
        return jsonify({"error": "No user_id or conversation_id provided"}), 400

    history = get_chat_history(user_id, conversation_id)
    return jsonify(history)

@app.route('/new_conversation', methods=['POST'])
def new_conversation():
    data = request.json
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({"error": "No user_id provided"}), 400

    conversation_id = str(datetime.now(timezone.utc).timestamp())

    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    cursor.execute("INSERT INTO conversations (user_id, conversation_id,timestamp) VALUES (%s, %s,%s)", (user_id, conversation_id, datetime.now(timezone.utc)))
    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({"conversation_id": conversation_id})

@app.route('/conversations', methods=['GET'])
def get_conversations():
    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({"error": "No user_id provided"}), 400

    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT conversation_id FROM conversations WHERE user_id = %s", (user_id,))
    conversations = cursor.fetchall()
    cursor.close()
    connection.close()

    return jsonify(conversations)

@app.route('/conversation', methods=['DELETE'])
def delete_conversation():
    data = request.json
    user_id = data.get('user_id')
    conversation_id = data.get('conversation_id')

    if not user_id or not conversation_id:
        return jsonify({"error": "No user_id or conversation_id provided"}), 400

    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    cursor.execute("DELETE FROM chat_history WHERE conversation_id = %s", (conversation_id))
    cursor.execute("DELETE FROM conversations WHERE conversation_id = %s", (conversation_id))
    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({"message": "Conversation deleted successfully"})

    if __name__ == '__main__':
        app.run(host='0.0.0.0', port=5001, debug=True)

    
