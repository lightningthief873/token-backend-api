from flask import Blueprint, request, jsonify
from src.models.token import db, Token, TokenMetric
from src.services.data_service import DataService
from src.utils.auth import require_api_key
from src.utils.pagination import paginate_query
from datetime import datetime, timedelta
import json

tokens_bp = Blueprint('tokens', __name__)
data_service = DataService()

@tokens_bp.route('/tokens', methods=['GET'])
@require_api_key
def get_tokens():
    """Get paginated list of all tracked tokens with their current metrics"""
    try:
        # Parse query parameters
        limit = min(int(request.args.get('limit', 100)), 1000)
        start = int(request.args.get('start', 1))
        sort_field = request.args.get('sort', 'market_cap')
        sort_dir = request.args.get('sort_dir', 'desc')
        convert = request.args.get('convert', 'USD')
        min_market_cap = request.args.get('min_market_cap', type=float)
        max_market_cap = request.args.get('max_market_cap', type=float)
        
        # Build query
        query = db.session.query(Token).filter(Token.is_active == True)
        
        # Apply market cap filters if provided
        if min_market_cap or max_market_cap:
            # Join with latest metrics to filter by market cap
            latest_metrics_subquery = db.session.query(
                TokenMetric.token_id,
                db.func.max(TokenMetric.timestamp).label('latest_timestamp')
            ).group_by(TokenMetric.token_id).subquery()
            
            query = query.join(
                TokenMetric, Token.id == TokenMetric.token_id
            ).join(
                latest_metrics_subquery,
                db.and_(
                    TokenMetric.token_id == latest_metrics_subquery.c.token_id,
                    TokenMetric.timestamp == latest_metrics_subquery.c.latest_timestamp
                )
            )
            
            if min_market_cap:
                query = query.filter(TokenMetric.market_cap_usd >= min_market_cap)
            if max_market_cap:
                query = query.filter(TokenMetric.market_cap_usd <= max_market_cap)
        
        # Apply sorting
        if sort_field in ['market_cap', 'volume_24h', 'velocity', 'price']:
            # For metric-based sorting, we need to join with latest metrics
            if 'TokenMetric' not in str(query):
                latest_metrics_subquery = db.session.query(
                    TokenMetric.token_id,
                    db.func.max(TokenMetric.timestamp).label('latest_timestamp')
                ).group_by(TokenMetric.token_id).subquery()
                
                query = query.join(
                    TokenMetric, Token.id == TokenMetric.token_id
                ).join(
                    latest_metrics_subquery,
                    db.and_(
                        TokenMetric.token_id == latest_metrics_subquery.c.token_id,
                        TokenMetric.timestamp == latest_metrics_subquery.c.latest_timestamp
                    )
                )
            
            sort_column = getattr(TokenMetric, f"{sort_field}_usd" if sort_field in ['market_cap', 'volume_24h'] else sort_field)
            if sort_field == 'price':
                sort_column = TokenMetric.price_usd
        else:
            sort_column = getattr(Token, sort_field, Token.id)
        
        if sort_dir == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Apply pagination
        offset = start - 1
        total_count = query.count()
        tokens = query.offset(offset).limit(limit).all()
        
        # Get latest metrics for each token
        token_data = []
        for token in tokens:
            latest_metric = db.session.query(TokenMetric).filter(
                TokenMetric.token_id == token.id
            ).order_by(TokenMetric.timestamp.desc()).first()
            
            token_dict = token.to_dict()
            if latest_metric:
                token_dict['quote'] = {
                    convert: {
                        'price': float(latest_metric.price_usd) if latest_metric.price_usd else None,
                        'volume_24h': float(latest_metric.volume_24h_usd) if latest_metric.volume_24h_usd else None,
                        'market_cap': float(latest_metric.market_cap_usd) if latest_metric.market_cap_usd else None,
                        'percent_change_1h': float(latest_metric.percent_change_1h) if latest_metric.percent_change_1h else None,
                        'percent_change_24h': float(latest_metric.percent_change_24h) if latest_metric.percent_change_24h else None,
                        'percent_change_7d': float(latest_metric.percent_change_7d) if latest_metric.percent_change_7d else None,
                        'velocity': float(latest_metric.velocity) if latest_metric.velocity else None,
                        'velocity_trend': data_service.calculate_velocity_trend(token.id)
                    }
                }
                token_dict['last_updated'] = latest_metric.timestamp.isoformat()
            else:
                token_dict['quote'] = {convert: {}}
                token_dict['last_updated'] = None
            
            token_data.append(token_dict)
        
        # Calculate pagination info
        total_pages = (total_count + limit - 1) // limit
        current_page = (start + limit - 1) // limit
        
        response = {
            'status': {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'error_code': 0,
                'error_message': None,
                'elapsed': 0,
                'credit_count': 1
            },
            'data': token_data,
            'pagination': {
                'total_count': total_count,
                'page': current_page,
                'per_page': limit,
                'total_pages': total_pages
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'status': {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'error_code': 500,
                'error_message': str(e),
                'elapsed': 0,
                'credit_count': 0
            }
        }), 500

@tokens_bp.route('/tokens/<token_id>', methods=['GET'])
@require_api_key
def get_token_details(token_id):
    """Get detailed information about a specific token"""
    try:
        convert = request.args.get('convert', 'USD')
        include_history = request.args.get('include_history', 'false').lower() == 'true'
        
        # Find token by ID, symbol, or slug
        token = None
        if token_id.isdigit():
            token = Token.query.filter_by(cmc_id=int(token_id)).first()
        if not token:
            token = Token.query.filter_by(symbol=token_id.upper()).first()
        if not token:
            token = Token.query.filter_by(slug=token_id.lower()).first()
        
        if not token:
            return jsonify({
                'status': {
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'error_code': 404,
                    'error_message': 'Token not found',
                    'elapsed': 0,
                    'credit_count': 0
                }
            }), 404
        
        # Get latest metrics
        latest_metric = db.session.query(TokenMetric).filter(
            TokenMetric.token_id == token.id
        ).order_by(TokenMetric.timestamp.desc()).first()
        
        token_dict = token.to_dict()
        if latest_metric:
            token_dict['quote'] = {
                convert: {
                    'price': float(latest_metric.price_usd) if latest_metric.price_usd else None,
                    'volume_24h': float(latest_metric.volume_24h_usd) if latest_metric.volume_24h_usd else None,
                    'market_cap': float(latest_metric.market_cap_usd) if latest_metric.market_cap_usd else None,
                    'circulating_supply': float(latest_metric.circulating_supply) if latest_metric.circulating_supply else None,
                    'total_supply': float(latest_metric.total_supply) if latest_metric.total_supply else None,
                    'max_supply': float(latest_metric.max_supply) if latest_metric.max_supply else None,
                    'percent_change_1h': float(latest_metric.percent_change_1h) if latest_metric.percent_change_1h else None,
                    'percent_change_24h': float(latest_metric.percent_change_24h) if latest_metric.percent_change_24h else None,
                    'percent_change_7d': float(latest_metric.percent_change_7d) if latest_metric.percent_change_7d else None,
                    'velocity': float(latest_metric.velocity) if latest_metric.velocity else None,
                    'velocity_trend': data_service.calculate_velocity_trend(token.id),
                    'velocity_1h': float(latest_metric.velocity_1h) if latest_metric.velocity_1h else None,
                    'velocity_4h': float(latest_metric.velocity_4h) if latest_metric.velocity_4h else None,
                    'velocity_12h': float(latest_metric.velocity_12h) if latest_metric.velocity_12h else None,
                    'velocity_7d': float(latest_metric.velocity_7d) if latest_metric.velocity_7d else None
                }
            }
            token_dict['last_updated'] = latest_metric.timestamp.isoformat()
        else:
            token_dict['quote'] = {convert: {}}
            token_dict['last_updated'] = None
        
        response = {
            'status': {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'error_code': 0,
                'error_message': None,
                'elapsed': 0,
                'credit_count': 1
            },
            'data': token_dict
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'status': {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'error_code': 500,
                'error_message': str(e),
                'elapsed': 0,
                'credit_count': 0
            }
        }), 500

@tokens_bp.route('/tokens/<token_id>/velocity', methods=['GET'])
@require_api_key
def get_token_velocity(token_id):
    """Get detailed velocity metrics for a specific token"""
    try:
        timeframe = request.args.get('timeframe', '24h')
        include_trend = request.args.get('include_trend', 'true').lower() == 'true'
        
        # Find token
        token = None
        if token_id.isdigit():
            token = Token.query.filter_by(cmc_id=int(token_id)).first()
        if not token:
            token = Token.query.filter_by(symbol=token_id.upper()).first()
        if not token:
            token = Token.query.filter_by(slug=token_id.lower()).first()
        
        if not token:
            return jsonify({
                'status': {
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'error_code': 404,
                    'error_message': 'Token not found',
                    'elapsed': 0,
                    'credit_count': 0
                }
            }), 404
        
        # Get velocity metrics
        velocity_data = data_service.get_velocity_metrics(token.id, timeframe, include_trend)
        
        response = {
            'status': {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'error_code': 0,
                'error_message': None,
                'elapsed': 0,
                'credit_count': 1
            },
            'data': velocity_data
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'status': {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'error_code': 500,
                'error_message': str(e),
                'elapsed': 0,
                'credit_count': 0
            }
        }), 500

@tokens_bp.route('/tokens/search', methods=['GET'])
@require_api_key
def search_tokens():
    """Search for tokens by name or symbol"""
    try:
        query_param = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 10)), 100)
        
        if not query_param:
            return jsonify({
                'status': {
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'error_code': 400,
                    'error_message': 'Query parameter "q" is required',
                    'elapsed': 0,
                    'credit_count': 0
                }
            }), 400
        
        # Search tokens by name or symbol
        tokens = Token.query.filter(
            db.and_(
                Token.is_active == True,
                db.or_(
                    Token.name.ilike(f'%{query_param}%'),
                    Token.symbol.ilike(f'%{query_param}%'),
                    Token.slug.ilike(f'%{query_param}%')
                )
            )
        ).limit(limit).all()
        
        token_data = []
        for token in tokens:
            latest_metric = db.session.query(TokenMetric).filter(
                TokenMetric.token_id == token.id
            ).order_by(TokenMetric.timestamp.desc()).first()
            
            token_dict = token.to_dict()
            if latest_metric:
                token_dict['quote'] = {
                    'USD': {
                        'price': float(latest_metric.price_usd) if latest_metric.price_usd else None,
                        'market_cap': float(latest_metric.market_cap_usd) if latest_metric.market_cap_usd else None,
                        'velocity': float(latest_metric.velocity) if latest_metric.velocity else None
                    }
                }
            else:
                token_dict['quote'] = {'USD': {}}
            
            token_data.append(token_dict)
        
        response = {
            'status': {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'error_code': 0,
                'error_message': None,
                'elapsed': 0,
                'credit_count': 1
            },
            'data': token_data
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'status': {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'error_code': 500,
                'error_message': str(e),
                'elapsed': 0,
                'credit_count': 0
            }
        }), 500

