# Data Storage and Caching Strategy

## Database Schema Design

### Primary Tables

#### tokens
```sql
CREATE TABLE tokens (
    id INTEGER PRIMARY KEY,
    cmc_id INTEGER UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    slug VARCHAR(255) NOT NULL,
    description TEXT,
    logo_url VARCHAR(500),
    website_url VARCHAR(500),
    twitter_handle VARCHAR(100),
    reddit_url VARCHAR(500),
    github_url VARCHAR(500),
    whitepaper_url VARCHAR(500),
    date_added TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tokens_symbol ON tokens(symbol);
CREATE INDEX idx_tokens_cmc_id ON tokens(cmc_id);
CREATE INDEX idx_tokens_slug ON tokens(slug);
```

#### token_metrics
```sql
CREATE TABLE token_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_id INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    price_usd DECIMAL(20, 8),
    market_cap_usd DECIMAL(20, 2),
    volume_24h_usd DECIMAL(20, 2),
    circulating_supply DECIMAL(20, 8),
    total_supply DECIMAL(20, 8),
    max_supply DECIMAL(20, 8),
    percent_change_1h DECIMAL(10, 4),
    percent_change_24h DECIMAL(10, 4),
    percent_change_7d DECIMAL(10, 4),
    velocity DECIMAL(10, 8),
    velocity_1h DECIMAL(10, 8),
    velocity_4h DECIMAL(10, 8),
    velocity_12h DECIMAL(10, 8),
    velocity_7d DECIMAL(10, 8),
    data_quality_score DECIMAL(3, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (token_id) REFERENCES tokens(id)
);

CREATE INDEX idx_token_metrics_token_timestamp ON token_metrics(token_id, timestamp);
CREATE INDEX idx_token_metrics_timestamp ON token_metrics(timestamp);
CREATE INDEX idx_token_metrics_velocity ON token_metrics(velocity);
```

#### api_keys
```sql
CREATE TABLE api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    tier VARCHAR(50) DEFAULT 'basic',
    rate_limit_per_minute INTEGER DEFAULT 60,
    rate_limit_per_month INTEGER DEFAULT 1000,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP,
    usage_count INTEGER DEFAULT 0
);

CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_active ON api_keys(is_active);
```

#### rate_limiting
```sql
CREATE TABLE rate_limiting (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_key_id INTEGER NOT NULL,
    window_start TIMESTAMP NOT NULL,
    request_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (api_key_id) REFERENCES api_keys(id)
);

CREATE INDEX idx_rate_limiting_key_window ON rate_limiting(api_key_id, window_start);
```

## Caching Architecture

### Redis Cache Structure

#### Token Data Cache
```
Key Pattern: token:{token_id}
TTL: 60 seconds
Structure: JSON object with current token metrics
Example:
{
  "id": 1,
  "symbol": "BTC",
  "price": 45000.50,
  "market_cap": 850000000000,
  "volume_24h": 25000000000,
  "velocity": 0.029,
  "last_updated": "2025-06-19T17:40:00Z"
}
```

#### Token List Cache
```
Key Pattern: tokens:list:{sort}:{limit}:{offset}
TTL: 300 seconds (5 minutes)
Structure: JSON array of token summaries
```

#### Velocity Calculations Cache
```
Key Pattern: velocity:{token_id}:{timeframe}
TTL: 300 seconds
Structure: JSON object with velocity metrics
Example:
{
  "velocity_1h": 0.031,
  "velocity_4h": 0.028,
  "velocity_24h": 0.029,
  "velocity_7d": 0.025,
  "trend": "stable",
  "calculated_at": "2025-06-19T17:40:00Z"
}
```

#### Rate Limiting Cache
```
Key Pattern: rate_limit:{api_key_hash}:{window}
TTL: 3600 seconds (1 hour)
Structure: Integer counter
```

#### WebSocket Subscriptions
```
Key Pattern: ws_subs:{token_id}
TTL: No expiration (managed by connection lifecycle)
Structure: Set of WebSocket connection IDs
```

### Cache Invalidation Strategy

#### Time-Based Invalidation
- Token metrics: 60 seconds
- Token lists: 5 minutes
- Velocity calculations: 5 minutes
- Historical data: 1 hour

#### Event-Based Invalidation
- New data from CoinMarketCap API triggers cache refresh
- WebSocket disconnections remove subscription entries
- API key changes invalidate rate limiting caches

#### Cache Warming
- Pre-populate top 100 tokens on startup
- Background jobs refresh popular token data
- Predictive caching based on usage patterns

## Data Processing Pipeline

### Data Ingestion Flow
1. **Scheduled Polling**: CoinMarketCap API polled every 60 seconds
2. **Data Validation**: Incoming data validated for completeness and accuracy
3. **Velocity Calculation**: Token velocity computed using current and historical data
4. **Database Storage**: Validated data stored in token_metrics table
5. **Cache Update**: Redis cache updated with new data
6. **WebSocket Broadcast**: Real-time updates sent to subscribed clients

### Velocity Calculation Algorithm
```python
def calculate_velocity(volume_24h_usd, market_cap_usd):
    """
    Calculate token velocity using the standard formula:
    Velocity = 24h Trading Volume (USD) / Market Cap (USD)
    """
    if market_cap_usd <= 0:
        return 0.0
    
    velocity = volume_24h_usd / market_cap_usd
    
    # Apply bounds checking
    if velocity > 100:  # Sanity check for extremely high velocity
        return 100.0
    
    return round(velocity, 8)

def calculate_velocity_trend(current_velocity, historical_velocities):
    """
    Determine velocity trend based on recent historical data
    """
    if len(historical_velocities) < 3:
        return "insufficient_data"
    
    recent_avg = sum(historical_velocities[-3:]) / 3
    older_avg = sum(historical_velocities[-6:-3]) / 3
    
    change_threshold = 0.05  # 5% change threshold
    
    if (current_velocity - recent_avg) / recent_avg > change_threshold:
        return "increasing"
    elif (recent_avg - current_velocity) / recent_avg > change_threshold:
        return "decreasing"
    else:
        return "stable"
```

### Data Quality Assurance
- **Outlier Detection**: Statistical analysis to identify anomalous data points
- **Cross-Validation**: Compare data across multiple timeframes for consistency
- **Missing Data Handling**: Interpolation and estimation for missing data points
- **Data Freshness Monitoring**: Track data age and alert on stale data

## Performance Optimization

### Database Optimization
- **Indexing Strategy**: Optimized indexes for common query patterns
- **Partitioning**: Time-based partitioning for historical data tables
- **Query Optimization**: Prepared statements and query plan analysis
- **Connection Pooling**: Efficient database connection management

### Cache Optimization
- **Memory Management**: Redis memory optimization and eviction policies
- **Cache Hit Rate Monitoring**: Track and optimize cache effectiveness
- **Compression**: Data compression for large cached objects
- **Cache Clustering**: Redis clustering for high-availability deployments

### Background Processing
- **Async Processing**: Non-blocking data processing using async/await
- **Queue Management**: Task queues for data processing and API calls
- **Batch Operations**: Bulk database operations for efficiency
- **Error Recovery**: Retry mechanisms and error handling for failed operations

## Backup and Recovery

### Database Backup Strategy
- **Automated Backups**: Daily full backups and hourly incremental backups
- **Backup Retention**: 30-day retention for daily backups, 7-day for incremental
- **Backup Verification**: Automated backup integrity checks
- **Cross-Region Replication**: Backup storage in multiple geographic locations

### Cache Recovery
- **Cache Warming**: Automated cache population after Redis restarts
- **Persistent Storage**: Redis persistence configuration for critical data
- **Failover Handling**: Graceful degradation when cache is unavailable
- **Cache Synchronization**: Multi-instance cache synchronization strategies

### Disaster Recovery
- **Recovery Time Objective (RTO)**: 15 minutes for service restoration
- **Recovery Point Objective (RPO)**: 5 minutes maximum data loss
- **Failover Procedures**: Automated failover to backup systems
- **Data Consistency**: Ensure data consistency across recovery operations

