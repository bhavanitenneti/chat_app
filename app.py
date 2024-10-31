from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, send, join_room, leave_room
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:yourpassword@mysql:3306/chat_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ChatRoom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_name = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('chat_room.id', ondelete="CASCADE"), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if username is None or password is None:
        return jsonify({"error": "Username and password required"}), 400
    hashed_password = generate_password_hash(password)
    new_user = User(username=username, password=hashed_password)
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "User registered successfully!"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@app.route('/login', methods=['POST'])
def login_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        session['user_id'] = user.id
        return jsonify({"message": "Logged in successfully!"}), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401

@app.route('/logout', methods=['POST'])
def logout_user():
    session.pop('user_id', None)
    return jsonify({"message": "Logged out successfully!"}), 200


@app.route('/chatrooms', methods=['POST'])
def create_chatroom():
    data = request.get_json()
    room_name = data.get('room_name')
    if room_name is None:
        return jsonify({"error": "Room name required"}), 400
    new_room = ChatRoom(room_name=room_name)
    try:
        db.session.add(new_room)
        db.session.commit()
        return jsonify({"message": "Chat room created successfully!"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@app.route('/chatrooms/<int:room_id>/messages', methods=['POST'])
def send_message(room_id):
    data = request.get_json()
    message_text = data.get('message')
    if not message_text:
        return jsonify({"error": "Message text is required"}), 400
    new_message = Message(user_id=session['user_id'], room_id=room_id, message=message_text)
    try:
        db.session.add(new_message)
        db.session.commit()
        socketio.emit('message', {'message': new_message.message, 'user_id': new_message.user_id, 'room_id': new_message.room_id, 'created_at': new_message.created_at}, room=str(room_id))
        return jsonify({"message": "Message sent!"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@app.route('/chatrooms/<int:room_id>/messages', methods=['GET'])
def get_messages(room_id):
    messages = Message.query.filter_by(room_id=room_id).all()
    return jsonify([{'user_id': msg.user_id, 'message': msg.message, 'created_at': msg.created_at} for msg in messages])


@app.route('/')
def index():
    return "Multi-User Chat Application!"

@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    send(username + ' has entered the room.', to=room)

@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    send(username + ' has left the room.', to=room)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
