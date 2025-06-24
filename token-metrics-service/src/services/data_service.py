import requests
import time
from datetime import datetime, timedelta
from src.models.token import db, Token, TokenMetric
from decimal import Decimal
import os

class DataService:
    def __init__(self):
        self.cmc_api_key = os.getenv('CMC_API_KEY', '818acf4e-ce65-4d5e-8c2d-81135b5572e5')  # Default to sandbox key
        self.cmc_base_url = os.getenv('CMC_BASE_URL', 'https://sandbox-api.coinmarketcap.com/v1')
        self.session = requests.Session()
        self.session.headers.update({
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': self.cmc_api_key,
        })
    
    def update_token_data(self):
        """Fetch latest data from CoinMarketCap and update database"""
        try:
            # Fetch latest cryptocurrency listings
            url = f"{self.cmc_base_url}/cryptocurrency/listings/latest"
            parameters = {
                'start': '1',
                'limit': '100',  # Get top 100 tokens
                'convert': 'USD'
            }
            
            response = self.session.get(url, params=parameters)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status', {}).get('error_code') != 0:
                print(f"CoinMarketCap API error: {data.get('status', {}).get('error_message')}")
                return
            
            # Process each token
            for token_data in data.get('data', []):
                self._process_token_data(token_data)
            
            db.session.commit()
            print(f"Updated data for {len(data.get('data', []))} tokens")
            
        except Exception as e:
            print(f"Error updating token data: {e}")
            db.session.rollback()
    
    def _process_token_data(self, token_data):
        """Process individual token data and update database"""
        try:
            cmc_id = token_data['id']
            
            # Find or create token
            token = Token.query.filter_by(cmc_id=cmc_id).first()
            if not token:
                token = Token(
                    cmc_id=cmc_id,
                    name=token_data['name'],
                    symbol=token_data['symbol'],
                    slug=token_data['slug'],
                    date_added=datetime.fromisoformat(token_data['date_added'].replace('Z', '+00:00')) if token_data.get('date_added') else None
                )
                db.session.add(token)
                try:
                    db.session.flush()  # Get the ID
                except Exception as e:
                    db.session.rollback()
                    # Token might already exist, try to find it again
                    token = Token.query.filter_by(cmc_id=cmc_id).first()
                    if not token:
                        raise e
            else:
                # Update token info
                token.name = token_data['name']
                token.symbol = token_data['symbol']
                token.slug = token_data['slug']
                token.updated_at = datetime.utcnow()
            
            # Extract quote data
            quote_data = token_data.get('quote', {}).get('USD', {})
            
            # Calculate velocity
            market_cap = quote_data.get('market_cap')
            volume_24h = quote_data.get('volume_24h')
            velocity = self._calculate_velocity(volume_24h, market_cap)
            
            # Calculate historical velocities for trend analysis
            velocity_1h = self._calculate_historical_velocity(token.id, hours=1)
            velocity_4h = self._calculate_historical_velocity(token.id, hours=4)
            velocity_12h = self._calculate_historical_velocity(token.id, hours=12)
            velocity_7d = self._calculate_historical_velocity(token.id, days=7)
            
            # Create new metric record
            metric = TokenMetric(
                token_id=token.id,
                timestamp=datetime.utcnow(),
                price_usd=Decimal(str(quote_data.get('price', 0))) if quote_data.get('price') else None,
                market_cap_usd=Decimal(str(market_cap)) if market_cap else None,
                volume_24h_usd=Decimal(str(volume_24h)) if volume_24h else None,
                circulating_supply=Decimal(str(token_data.get('circulating_supply', 0))) if token_data.get('circulating_supply') else None,
                total_supply=Decimal(str(token_data.get('total_supply', 0))) if token_data.get('total_supply') else None,
                max_supply=Decimal(str(token_data.get('max_supply', 0))) if token_data.get('max_supply') else None,
                percent_change_1h=Decimal(str(quote_data.get('percent_change_1h', 0))) if quote_data.get('percent_change_1h') else None,
                percent_change_24h=Decimal(str(quote_data.get('percent_change_24h', 0))) if quote_data.get('percent_change_24h') else None,
                percent_change_7d=Decimal(str(quote_data.get('percent_change_7d', 0))) if quote_data.get('percent_change_7d') else None,
                velocity=Decimal(str(velocity)) if velocity else None,
                velocity_1h=Decimal(str(velocity_1h)) if velocity_1h else None,
                velocity_4h=Decimal(str(velocity_4h)) if velocity_4h else None,
                velocity_12h=Decimal(str(velocity_12h)) if velocity_12h else None,
                velocity_7d=Decimal(str(velocity_7d)) if velocity_7d else None,
                data_quality_score=Decimal('0.95')  # Default quality score
            )
            
            db.session.add(metric)
            
        except Exception as e:
            print(f"Error processing token {token_data.get('symbol', 'Unknown')}: {e}")
            db.session.rollback()
    
    def _calculate_velocity(self, volume_24h, market_cap):
        """Calculate token velocity using the standard formula"""
        if not volume_24h or not market_cap or market_cap <= 0:
            return 0.0
        
        velocity = volume_24h / market_cap
        
        # Apply bounds checking
        if velocity > 100:  # Sanity check for extremely high velocity
            return 100.0
        
        return round(velocity, 8)
    
    def _calculate_historical_velocity(self, token_id, hours=None, days=None):
        """Calculate velocity for a specific historical timeframe"""
        try:
            if hours:
                time_threshold = datetime.utcnow() - timedelta(hours=hours)
            elif days:
                time_threshold = datetime.utcnow() - timedelta(days=days)
            else:
                return None
            
            # Get metrics from the specified timeframe
            metrics = db.session.query(TokenMetric).filter(
                TokenMetric.token_id == token_id,
                TokenMetric.timestamp >= time_threshold
            ).order_by(TokenMetric.timestamp.desc()).all()
            
            if not metrics:
                return None
            
            # Calculate average velocity over the timeframe
            velocities = [float(m.velocity) for m in metrics if m.velocity]
            if not velocities:
                return None
            
            return sum(velocities) / len(velocities)
            
        except Exception as e:
            print(f"Error calculating historical velocity: {e}")
            return None
    
    def calculate_velocity_trend(self, token_id):
        """Determine velocity trend based on recent historical data"""
        try:
            # Get recent metrics (last 24 hours)
            time_threshold = datetime.utcnow() - timedelta(hours=24)
            metrics = db.session.query(TokenMetric).filter(
                TokenMetric.token_id == token_id,
                TokenMetric.timestamp >= time_threshold,
                TokenMetric.velocity.isnot(None)
            ).order_by(TokenMetric.timestamp.desc()).limit(10).all()
            
            if len(metrics) < 3:
                return "insufficient_data"
            
            velocities = [float(m.velocity) for m in metrics]
            
            # Compare recent average with older average
            recent_avg = sum(velocities[:3]) / 3
            older_avg = sum(velocities[3:6]) / 3 if len(velocities) >= 6 else recent_avg
            
            change_threshold = 0.05  # 5% change threshold
            
            if older_avg == 0:
                return "stable"
            
            change_ratio = (recent_avg - older_avg) / older_avg
            
            if change_ratio > change_threshold:
                return "increasing"
            elif change_ratio < -change_threshold:
                return "decreasing"
            else:
                return "stable"
                
        except Exception as e:
            print(f"Error calculating velocity trend: {e}")
            return "unknown"
    
    def get_velocity_metrics(self, token_id, timeframe='24h', include_trend=True):
        """Get detailed velocity metrics for a token"""
        try:
            # Get latest metric
            latest_metric = db.session.query(TokenMetric).filter(
                TokenMetric.token_id == token_id
            ).order_by(TokenMetric.timestamp.desc()).first()
            
            if not latest_metric:
                return None
            
            token = Token.query.get(token_id)
            if not token:
                return None
            
            velocity_data = {
                'token_id': token_id,
                'symbol': token.symbol,
                'velocity_metrics': {
                    'current_velocity': float(latest_metric.velocity) if latest_metric.velocity else None,
                    'velocity_1h': float(latest_metric.velocity_1h) if latest_metric.velocity_1h else None,
                    'velocity_4h': float(latest_metric.velocity_4h) if latest_metric.velocity_4h else None,
                    'velocity_12h': float(latest_metric.velocity_12h) if latest_metric.velocity_12h else None,
                    'velocity_24h': float(latest_metric.velocity) if latest_metric.velocity else None,
                    'velocity_7d': float(latest_metric.velocity_7d) if latest_metric.velocity_7d else None
                },
                'calculation_details': {
                    'volume_24h': float(latest_metric.volume_24h_usd) if latest_metric.volume_24h_usd else None,
                    'market_cap': float(latest_metric.market_cap_usd) if latest_metric.market_cap_usd else None,
                    'calculation_time': latest_metric.timestamp.isoformat(),
                    'data_quality_score': float(latest_metric.data_quality_score) if latest_metric.data_quality_score else None
                }
            }
            
            if include_trend:
                velocity_data['trend_analysis'] = {
                    'trend_24h': self.calculate_velocity_trend(token_id),
                    'volatility_score': 0.15,  # TODO: Calculate actual volatility
                    'momentum_indicator': 'neutral'  # TODO: Calculate momentum
                }
            
            return velocity_data
            
        except Exception as e:
            print(f"Error getting velocity metrics: {e}")
            return None
    
    def get_token_data(self, token_id):
        """Get current token data for WebSocket updates"""
        try:
            # Find token
            token = None
            if str(token_id).isdigit():
                token = Token.query.filter_by(cmc_id=int(token_id)).first()
            if not token:
                token = Token.query.filter_by(symbol=str(token_id).upper()).first()
            if not token:
                token = Token.query.filter_by(slug=str(token_id).lower()).first()
            
            if not token:
                return None
            
            # Get latest metric
            latest_metric = db.session.query(TokenMetric).filter(
                TokenMetric.token_id == token.id
            ).order_by(TokenMetric.timestamp.desc()).first()
            
            if not latest_metric:
                return None
            
            return {
                'token_id': token.id,
                'symbol': token.symbol,
                'timestamp': latest_metric.timestamp.isoformat(),
                'data': {
                    'price': float(latest_metric.price_usd) if latest_metric.price_usd else None,
                    'volume_24h': float(latest_metric.volume_24h_usd) if latest_metric.volume_24h_usd else None,
                    'market_cap': float(latest_metric.market_cap_usd) if latest_metric.market_cap_usd else None,
                    'velocity': float(latest_metric.velocity) if latest_metric.velocity else None,
                    'change_24h': float(latest_metric.percent_change_24h) if latest_metric.percent_change_24h else None
                }
            }
            
        except Exception as e:
            print(f"Error getting token data: {e}")
            return None
    
    def get_market_update(self):
        """Get market-wide update data for WebSocket broadcast"""
        try:
            # Get latest metrics for top tokens
            latest_time = datetime.utcnow() - timedelta(minutes=5)
            
            metrics = db.session.query(TokenMetric, Token).join(
                Token, TokenMetric.token_id == Token.id
            ).filter(
                TokenMetric.timestamp >= latest_time
            ).order_by(TokenMetric.market_cap_usd.desc()).limit(20).all()
            
            tokens_data = []
            for metric, token in metrics:
                tokens_data.append({
                    'id': token.id,
                    'symbol': token.symbol,
                    'price': float(metric.price_usd) if metric.price_usd else None,
                    'velocity': float(metric.velocity) if metric.velocity else None,
                    'change_24h': float(metric.percent_change_24h) if metric.percent_change_24h else None
                })
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'tokens': tokens_data
            }
            
        except Exception as e:
            print(f"Error getting market update: {e}")
            return None
    
    def get_market_overview(self):
        """Get market overview data"""
        try:
            # Calculate market statistics
            latest_time = datetime.utcnow() - timedelta(minutes=5)
            
            total_market_cap = db.session.query(
                db.func.sum(TokenMetric.market_cap_usd)
            ).filter(
                TokenMetric.timestamp >= latest_time
            ).scalar() or 0
            
            total_volume = db.session.query(
                db.func.sum(TokenMetric.volume_24h_usd)
            ).filter(
                TokenMetric.timestamp >= latest_time
            ).scalar() or 0
            
            avg_velocity = db.session.query(
                db.func.avg(TokenMetric.velocity)
            ).filter(
                TokenMetric.timestamp >= latest_time,
                TokenMetric.velocity.isnot(None)
            ).scalar() or 0
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'total_market_cap': float(total_market_cap),
                'total_volume_24h': float(total_volume),
                'average_velocity': float(avg_velocity),
                'active_tokens': Token.query.filter_by(is_active=True).count()
            }
            
        except Exception as e:
            print(f"Error getting market overview: {e}")
            return None

