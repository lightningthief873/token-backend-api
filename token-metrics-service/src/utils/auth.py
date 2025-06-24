from functools import wraps
from flask import request, jsonify
from src.models.token import ApiKey
import hashlib
from datetime import datetime

def require_api_key(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({
                'status': {
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'error_code': 401,
                    'error_message': 'API key is required. Please include X-API-Key header.',
                    'elapsed': 0,
                    'credit_count': 0
                }
            }), 401
        
        # For demo purposes, accept any non-empty API key
        # In production, validate against database
        if len(api_key) < 8:
            return jsonify({
                'status': {
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'error_code': 401,
                    'error_message': 'Invalid API key format.',
                    'elapsed': 0,
                    'credit_count': 0
                }
            }), 401
        
        # TODO: Implement proper API key validation
        # api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        # key_record = ApiKey.query.filter_by(key_hash=api_key_hash, is_active=True).first()
        # if not key_record:
        #     return jsonify({'error': 'Invalid API key'}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

def validate_api_key(api_key):
    """Validate API key against database"""
    try:
        if not api_key:
            return False
        
        # For demo purposes, accept any API key with minimum length
        return len(api_key) >= 8
        
        # TODO: Implement proper validation
        # api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        # key_record = ApiKey.query.filter_by(key_hash=api_key_hash, is_active=True).first()
        # return key_record is not None
        
    except Exception as e:
        print(f"Error validating API key: {e}")
        return False

