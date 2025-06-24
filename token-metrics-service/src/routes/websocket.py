from flask import Blueprint
from flask_socketio import emit, join_room, leave_room, disconnect
from src.services.data_service import DataService
import json

socketio_bp = Blueprint('websocket', __name__)
data_service = DataService()

# Store active subscriptions
active_subscriptions = {}

@socketio_bp.route('/socket.io/')
def handle_connect(auth):
    """Handle WebSocket connection"""
    try:
        # Validate API key from connection auth
        api_key = auth.get('api_key') if auth else None
        if not api_key:
            disconnect()
            return False
        
        # TODO: Validate API key against database
        print(f"WebSocket client connected with API key: {api_key[:8]}...")
        emit('connected', {'status': 'Connected to Token Metrics Service'})
        return True
        
    except Exception as e:
        print(f"WebSocket connection error: {e}")
        disconnect()
        return False

def handle_disconnect():
    """Handle WebSocket disconnection"""
    try:
        # Clean up subscriptions for this client
        # TODO: Implement subscription cleanup
        print("WebSocket client disconnected")
    except Exception as e:
        print(f"WebSocket disconnection error: {e}")

def handle_subscribe_token(data):
    """Handle token subscription request"""
    try:
        token_id = data.get('token_id')
        metrics = data.get('metrics', ['price', 'volume', 'velocity'])
        
        if not token_id:
            emit('error', {'message': 'token_id is required'})
            return
        
        # Join room for this token
        room_name = f"token_{token_id}"
        join_room(room_name)
        
        # Store subscription info
        # TODO: Implement subscription storage
        
        emit('subscribed', {
            'token_id': token_id,
            'metrics': metrics,
            'status': 'Successfully subscribed to token updates'
        })
        
        # Send initial data
        token_data = data_service.get_token_data(token_id)
        if token_data:
            emit('token_update', token_data)
        
    except Exception as e:
        emit('error', {'message': f'Subscription error: {str(e)}'})

def handle_unsubscribe_token(data):
    """Handle token unsubscription request"""
    try:
        token_id = data.get('token_id')
        
        if not token_id:
            emit('error', {'message': 'token_id is required'})
            return
        
        # Leave room for this token
        room_name = f"token_{token_id}"
        leave_room(room_name)
        
        # Remove subscription info
        # TODO: Implement subscription removal
        
        emit('unsubscribed', {
            'token_id': token_id,
            'status': 'Successfully unsubscribed from token updates'
        })
        
    except Exception as e:
        emit('error', {'message': f'Unsubscription error: {str(e)}'})

def handle_subscribe_market(data):
    """Handle market-wide subscription request"""
    try:
        # Join market updates room
        join_room('market_updates')
        
        emit('market_subscribed', {
            'status': 'Successfully subscribed to market updates'
        })
        
        # Send initial market data
        market_data = data_service.get_market_overview()
        if market_data:
            emit('market_update', market_data)
        
    except Exception as e:
        emit('error', {'message': f'Market subscription error: {str(e)}'})

def handle_unsubscribe_market():
    """Handle market unsubscription request"""
    try:
        # Leave market updates room
        leave_room('market_updates')
        
        emit('market_unsubscribed', {
            'status': 'Successfully unsubscribed from market updates'
        })
        
    except Exception as e:
        emit('error', {'message': f'Market unsubscription error: {str(e)}'})

# Register event handlers
def register_socketio_events(socketio):
    """Register all WebSocket event handlers"""
    socketio.on_event('connect', handle_connect)
    socketio.on_event('disconnect', handle_disconnect)
    socketio.on_event('subscribe_token', handle_subscribe_token)
    socketio.on_event('unsubscribe_token', handle_unsubscribe_token)
    socketio.on_event('subscribe_market', handle_subscribe_market)
    socketio.on_event('unsubscribe_market', handle_unsubscribe_market)

