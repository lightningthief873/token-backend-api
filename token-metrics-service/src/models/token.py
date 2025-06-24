from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Token(db.Model):
    __tablename__ = 'tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    cmc_id = db.Column(db.Integer, unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    symbol = db.Column(db.String(50), nullable=False)
    slug = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    logo_url = db.Column(db.String(500))
    website_url = db.Column(db.String(500))
    twitter_handle = db.Column(db.String(100))
    reddit_url = db.Column(db.String(500))
    github_url = db.Column(db.String(500))
    whitepaper_url = db.Column(db.String(500))
    date_added = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to metrics
    metrics = db.relationship('TokenMetric', backref='token', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'cmc_id': self.cmc_id,
            'name': self.name,
            'symbol': self.symbol,
            'slug': self.slug,
            'description': self.description,
            'logo_url': self.logo_url,
            'website_url': self.website_url,
            'twitter_handle': self.twitter_handle,
            'reddit_url': self.reddit_url,
            'github_url': self.github_url,
            'whitepaper_url': self.whitepaper_url,
            'date_added': self.date_added.isoformat() if self.date_added else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class TokenMetric(db.Model):
    __tablename__ = 'token_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    token_id = db.Column(db.Integer, db.ForeignKey('tokens.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    price_usd = db.Column(db.Numeric(20, 8))
    market_cap_usd = db.Column(db.Numeric(20, 2))
    volume_24h_usd = db.Column(db.Numeric(20, 2))
    circulating_supply = db.Column(db.Numeric(20, 8))
    total_supply = db.Column(db.Numeric(20, 8))
    max_supply = db.Column(db.Numeric(20, 8))
    percent_change_1h = db.Column(db.Numeric(10, 4))
    percent_change_24h = db.Column(db.Numeric(10, 4))
    percent_change_7d = db.Column(db.Numeric(10, 4))
    velocity = db.Column(db.Numeric(10, 8))
    velocity_1h = db.Column(db.Numeric(10, 8))
    velocity_4h = db.Column(db.Numeric(10, 8))
    velocity_12h = db.Column(db.Numeric(10, 8))
    velocity_7d = db.Column(db.Numeric(10, 8))
    data_quality_score = db.Column(db.Numeric(3, 2))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'token_id': self.token_id,
            'timestamp': self.timestamp.isoformat(),
            'price_usd': float(self.price_usd) if self.price_usd else None,
            'market_cap_usd': float(self.market_cap_usd) if self.market_cap_usd else None,
            'volume_24h_usd': float(self.volume_24h_usd) if self.volume_24h_usd else None,
            'circulating_supply': float(self.circulating_supply) if self.circulating_supply else None,
            'total_supply': float(self.total_supply) if self.total_supply else None,
            'max_supply': float(self.max_supply) if self.max_supply else None,
            'percent_change_1h': float(self.percent_change_1h) if self.percent_change_1h else None,
            'percent_change_24h': float(self.percent_change_24h) if self.percent_change_24h else None,
            'percent_change_7d': float(self.percent_change_7d) if self.percent_change_7d else None,
            'velocity': float(self.velocity) if self.velocity else None,
            'velocity_1h': float(self.velocity_1h) if self.velocity_1h else None,
            'velocity_4h': float(self.velocity_4h) if self.velocity_4h else None,
            'velocity_12h': float(self.velocity_12h) if self.velocity_12h else None,
            'velocity_7d': float(self.velocity_7d) if self.velocity_7d else None,
            'data_quality_score': float(self.data_quality_score) if self.data_quality_score else None,
            'created_at': self.created_at.isoformat()
        }

class ApiKey(db.Model):
    __tablename__ = 'api_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    key_hash = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255))
    tier = db.Column(db.String(50), default='basic')
    rate_limit_per_minute = db.Column(db.Integer, default=60)
    rate_limit_per_month = db.Column(db.Integer, default=1000)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used_at = db.Column(db.DateTime)
    usage_count = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'tier': self.tier,
            'rate_limit_per_minute': self.rate_limit_per_minute,
            'rate_limit_per_month': self.rate_limit_per_month,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'usage_count': self.usage_count
        }

