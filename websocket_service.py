from flask_socketio import SocketIO, emit, send
from datetime import datetime
import json


def init_socketio(app):
    """Initialize Flask-SocketIO"""
    socketio = SocketIO(app, cors_allowed_origins="*")

    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        print(f"📡 Client connected: {datetime.utcnow()}")
        emit('status', {'message': 'Connected to Flask-SocketIO server', 'timestamp': datetime.utcnow().isoformat()})

    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        print(f"🔚 Client disconnected: {datetime.utcnow()}")

    @socketio.on('message')
    def handle_message(data):
        """Handle incoming messages"""
        print(f"📨 Received message: {data}")

        response = {
            'type': 'echo',
            'original_message': data,
            'timestamp': datetime.utcnow().isoformat(),
            'server': 'Flask-SocketIO'
        }

        emit('message_response', response)

    @socketio.on('chat_message')
    def handle_chat_message(data):
        """Handle chat messages"""
        print(f"💬 Chat message: {data}")

        # Send to all connected clients
        response = {
            'type': 'chat',
            'username': data.get('username', 'Anonymous'),
            'message': data.get('message', ''),
            'timestamp': datetime.utcnow().isoformat()
        }

        emit('chat_response', response, broadcast=True)

    @socketio.on('test_data')
    def handle_test_data(data):
        """Handle test data processing"""
        print(f"🧪 Test data: {data}")

        # Process data
        processed_data = {
            'original': data,
            'processed_at': datetime.utcnow().isoformat(),
            'char_count': len(str(data)),
            'word_count': len(str(data).split()) if isinstance(data, str) else 0,
            'data_type': type(data).__name__
        }

        emit('test_response', processed_data)

    @socketio.on('ping')
    def handle_ping():
        """Handle ping requests"""
        emit('pong', {'timestamp': datetime.utcnow().isoformat()})

    return socketio