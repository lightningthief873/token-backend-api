# REST API Endpoint Specifications

## Base URL and Versioning
- Base URL: `https://api.tokenmetrics.service/v1`
- API Version: v1
- Content-Type: `application/json`
- Authentication: API Key via `X-API-Key` header

## Authentication
All endpoints require authentication via API key:
```
X-API-Key: your_api_key_here
```

## Core Endpoints

### 1. Get All Tokens
**Endpoint:** `GET /api/v1/tokens`

**Description:** Retrieve a paginated list of all tracked tokens with their current metrics.

**Query Parameters:**
- `limit` (integer, optional): Number of results to return (default: 100, max: 1000)
- `start` (integer, optional): Starting position for pagination (default: 1)
- `sort` (string, optional): Sort field - `market_cap`, `volume_24h`, `velocity`, `price` (default: `market_cap`)
- `sort_dir` (string, optional): Sort direction - `asc`, `desc` (default: `desc`)
- `convert` (string, optional): Currency for price conversion (default: `USD`)
- `min_market_cap` (number, optional): Minimum market cap filter
- `max_market_cap` (number, optional): Maximum market cap filter

**Response Example:**
```json
{
  "status": {
    "timestamp": "2025-06-19T17:40:00Z",
    "error_code": 0,
    "error_message": null,
    "elapsed": 15,
    "credit_count": 1
  },
  "data": [
    {
      "id": 1,
      "name": "Bitcoin",
      "symbol": "BTC",
      "slug": "bitcoin",
      "cmc_rank": 1,
      "last_updated": "2025-06-19T17:39:45Z",
      "quote": {
        "USD": {
          "price": 45000.50,
          "volume_24h": 25000000000,
          "market_cap": 850000000000,
          "percent_change_1h": 0.5,
          "percent_change_24h": 2.1,
          "percent_change_7d": -1.2,
          "velocity": 0.029,
          "velocity_trend": "stable"
        }
      }
    }
  ],
  "pagination": {
    "total_count": 5000,
    "page": 1,
    "per_page": 100,
    "total_pages": 50
  }
}
```

### 2. Get Token Details
**Endpoint:** `GET /api/v1/tokens/{token_id}`

**Description:** Retrieve detailed information about a specific token.

**Path Parameters:**
- `token_id` (string): Token identifier (CoinMarketCap ID, symbol, or slug)

**Query Parameters:**
- `convert` (string, optional): Currency for price conversion (default: `USD`)
- `include_history` (boolean, optional): Include historical data summary (default: false)

**Response Example:**
```json
{
  "status": {
    "timestamp": "2025-06-19T17:40:00Z",
    "error_code": 0,
    "error_message": null,
    "elapsed": 12,
    "credit_count": 1
  },
  "data": {
    "id": 1,
    "name": "Bitcoin",
    "symbol": "BTC",
    "slug": "bitcoin",
    "description": "Bitcoin is a decentralized cryptocurrency...",
    "logo": "https://s2.coinmarketcap.com/static/img/coins/64x64/1.png",
    "website": ["https://bitcoin.org/"],
    "technical_doc": ["https://bitcoin.org/bitcoin.pdf"],
    "twitter": "bitcoin",
    "reddit": "r/Bitcoin",
    "message_board": ["https://bitcointalk.org"],
    "chat": [],
    "explorer": ["https://blockchain.info/"],
    "source_code": ["https://github.com/bitcoin/bitcoin"],
    "tags": ["mineable", "pow", "sha-256"],
    "platform": null,
    "date_added": "2013-04-28T00:00:00.000Z",
    "quote": {
      "USD": {
        "price": 45000.50,
        "volume_24h": 25000000000,
        "market_cap": 850000000000,
        "circulating_supply": 18900000,
        "total_supply": 18900000,
        "max_supply": 21000000,
        "percent_change_1h": 0.5,
        "percent_change_24h": 2.1,
        "percent_change_7d": -1.2,
        "velocity": 0.029,
        "velocity_trend": "stable",
        "velocity_1h": 0.031,
        "velocity_4h": 0.028,
        "velocity_12h": 0.030,
        "velocity_7d": 0.025
      }
    }
  }
}
```

### 3. Get Token Velocity Metrics
**Endpoint:** `GET /api/v1/tokens/{token_id}/velocity`

**Description:** Retrieve detailed velocity metrics and analysis for a specific token.

**Path Parameters:**
- `token_id` (string): Token identifier

**Query Parameters:**
- `timeframe` (string, optional): Analysis timeframe - `1h`, `4h`, `12h`, `24h`, `7d` (default: `24h`)
- `include_trend` (boolean, optional): Include trend analysis (default: true)

**Response Example:**
```json
{
  "status": {
    "timestamp": "2025-06-19T17:40:00Z",
    "error_code": 0,
    "error_message": null,
    "elapsed": 8,
    "credit_count": 1
  },
  "data": {
    "token_id": 1,
    "symbol": "BTC",
    "velocity_metrics": {
      "current_velocity": 0.029,
      "velocity_1h": 0.031,
      "velocity_4h": 0.028,
      "velocity_12h": 0.030,
      "velocity_24h": 0.029,
      "velocity_7d": 0.025,
      "velocity_30d": 0.032
    },
    "trend_analysis": {
      "trend_1h": "increasing",
      "trend_4h": "decreasing",
      "trend_24h": "stable",
      "trend_7d": "increasing",
      "volatility_score": 0.15,
      "momentum_indicator": "neutral"
    },
    "calculation_details": {
      "volume_24h": 25000000000,
      "market_cap": 850000000000,
      "calculation_time": "2025-06-19T17:39:45Z",
      "data_quality_score": 0.98
    }
  }
}
```

### 4. Get Token Historical Data
**Endpoint:** `GET /api/v1/tokens/{token_id}/history`

**Description:** Retrieve historical data for a specific token.

**Path Parameters:**
- `token_id` (string): Token identifier

**Query Parameters:**
- `time_start` (string, optional): Start date (ISO 8601 format)
- `time_end` (string, optional): End date (ISO 8601 format)
- `interval` (string, optional): Data interval - `1h`, `4h`, `12h`, `1d`, `7d` (default: `1d`)
- `convert` (string, optional): Currency for price conversion (default: `USD`)

### 5. Get Market Overview
**Endpoint:** `GET /api/v1/market/overview`

**Description:** Get overall market statistics and top performers.

**Query Parameters:**
- `convert` (string, optional): Currency for conversion (default: `USD`)

### 6. Search Tokens
**Endpoint:** `GET /api/v1/tokens/search`

**Description:** Search for tokens by name or symbol.

**Query Parameters:**
- `q` (string, required): Search query
- `limit` (integer, optional): Number of results (default: 10, max: 100)

## WebSocket Events Specification

### Connection
**Endpoint:** `/socket.io/`
**Authentication:** API key in connection query: `?api_key=your_api_key`

### Events

#### 1. Subscribe to Token Updates
**Event:** `subscribe_token`
**Payload:**
```json
{
  "token_id": "1",
  "metrics": ["price", "volume", "velocity"]
}
```

#### 2. Unsubscribe from Token Updates
**Event:** `unsubscribe_token`
**Payload:**
```json
{
  "token_id": "1"
}
```

#### 3. Token Update Event
**Event:** `token_update`
**Payload:**
```json
{
  "token_id": 1,
  "symbol": "BTC",
  "timestamp": "2025-06-19T17:40:00Z",
  "data": {
    "price": 45000.50,
    "volume_24h": 25000000000,
    "market_cap": 850000000000,
    "velocity": 0.029,
    "change_24h": 2.1
  }
}
```

#### 4. Bulk Market Update
**Event:** `market_update`
**Payload:**
```json
{
  "timestamp": "2025-06-19T17:40:00Z",
  "tokens": [
    {
      "id": 1,
      "symbol": "BTC",
      "price": 45000.50,
      "velocity": 0.029,
      "change_24h": 2.1
    }
  ]
}
```

## Error Responses

### Standard Error Format
```json
{
  "status": {
    "timestamp": "2025-06-19T17:40:00Z",
    "error_code": 400,
    "error_message": "Invalid parameter: limit must be between 1 and 1000",
    "elapsed": 5,
    "credit_count": 0
  }
}
```

### Common Error Codes
- `400` - Bad Request (invalid parameters)
- `401` - Unauthorized (invalid API key)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found (token not found)
- `429` - Too Many Requests (rate limit exceeded)
- `500` - Internal Server Error
- `503` - Service Unavailable (maintenance mode)

## Rate Limiting

### Rate Limit Headers
All responses include rate limiting information:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1624123200
```

### Rate Limit Tiers
- **Basic**: 1,000 requests/month
- **Hobbyist**: 10,000 requests/month  
- **Startup**: 100,000 requests/month
- **Standard**: 1,000,000 requests/month
- **Professional**: 10,000,000 requests/month
- **Enterprise**: Custom limits

