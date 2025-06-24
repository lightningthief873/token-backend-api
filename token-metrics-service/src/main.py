import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO
from src.models.token import db
from src.routes.tokens import tokens_bp
from src.routes.websocket import socketio_bp, register_socketio_events
from src.services.data_service import DataService
from dotenv import load_dotenv
import threading
import time
import eventlet

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Enable CORS for all routes
CORS(app, origins="*")

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Register blueprints
app.register_blueprint(tokens_bp, url_prefix='/api/v1')

# Register WebSocket events
register_socketio_events(socketio)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Initialize database
with app.app_context():
    db.create_all()

# Initialize data service
data_service = DataService()

def background_data_updater():
    """Background thread to update token data periodically"""
    while True:
        try:
            with app.app_context():
                data_service.update_token_data()
                # Emit updates to WebSocket clients
                socketio.emit('market_update', data_service.get_market_update(), namespace='/')
        except Exception as e:
            print(f"Error in background data updater: {e}")
        
        # Wait 60 seconds before next update
        time.sleep(60)

# Start background data updater
if os.getenv('FLASK_ENV') != 'testing':
    update_thread = threading.Thread(target=background_data_updater, daemon=True)
    update_thread.start()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)

