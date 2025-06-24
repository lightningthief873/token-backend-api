# Token Metrics Service - Deployment Guide

## Overview

This is a real-time backend service that tracks live cryptocurrency token metrics (market cap, velocity), exposes data via REST API and WebSocket, and includes a basic dashboard/UI. The service is containerized using Docker for easy deployment.

## Architecture

### Backend Service (Flask)

- **Port**: 5000
- **Features**:
  - REST API endpoints for token metrics
  - WebSocket support for real-time updates
  - Token velocity calculation
  - CoinMarketCap API integration
  - SQLite database for data storage

### Frontend Dashboard (React)

- **Port**: 80 (when containerized) or 5173 (development)
- **Features**:
  - Real-time token metrics visualization
  - Interactive charts and tables
  - WebSocket integration for live updates
  - Responsive design

### Additional Services

- **Redis**: Optional caching layer (port 6379)

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Git (for cloning the repository)

### Using Docker Compose (Recommended)

1. **Clone and navigate to the project directory**:

   ```bash
   cd /path/to/token-metrics-service
   ```

2. **Start all services**:

   ```bash
   docker compose up -d
   ```

3. **Access the application**:
   - Frontend Dashboard: http://localhost
   - Backend API: http://localhost:5000
   - API Documentation: http://localhost:5000/api/v1/tokens

### Manual Setup (Development)

#### Backend Setup

1. **Navigate to backend directory**:

   ```bash
   cd token-metrics-service
   ```

2. **Create virtual environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables**:

   ```bash
   export CMC_API_KEY=your-coinmarketcap-api-key
   export SECRET_KEY=your-secret-key
   ```

5. **Run the backend**:
   ```bash
   python src/main.py
   ```

#### Frontend Setup

1. **Navigate to frontend directory**:

   ```bash
   cd token-metrics-dashboard
   ```

2. **Install dependencies**:

   ```bash
   pnpm install
   ```

3. **Start development server**:

   ```bash
   pnpm run dev
   ```

4. **Build for production**:
   ```bash
   pnpm run build
   ```

## API Documentation

### Authentication

All API requests require an API key in the header:

```
X-API-Key: demo-api-key-12345678
```

### REST API Endpoints

#### Get All Tokens

```
GET /api/v1/tokens?limit=20&start=1&sort=market_cap&sort_dir=desc
```

**Response**:

```json
{
  "status": {
    "timestamp": "2025-06-19T18:00:00Z",
    "error_code": 0,
    "error_message": null,
    "elapsed": 0,
    "credit_count": 1
  },
  "data": [
    {
      "id": 1,
      "symbol": "BTC",
      "name": "Bitcoin",
      "quote": {
        "USD": {
          "price": 45000.0,
          "market_cap": 850000000000,
          "volume_24h": 25000000000,
          "velocity": 0.029,
          "percent_change_24h": 2.5
        }
      }
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total_count": 100,
    "total_pages": 5
  }
}
```

#### Get Token Details

```
GET /api/v1/tokens/{token_id}
```

#### Get Token Velocity Metrics

```
GET /api/v1/tokens/{token_id}/velocity?timeframe=24h&include_trend=true
```

#### Search Tokens

```
GET /api/v1/tokens/search?q=bitcoin&limit=10
```

### WebSocket Events

#### Connect

```javascript
const socket = io("http://localhost:5000", {
  auth: {
    api_key: "demo-api-key-12345678",
  },
});
```

#### Subscribe to Token Updates

```javascript
socket.emit("subscribe_token", {
  token_id: 1,
  metrics: ["price", "volume", "velocity"],
});
```

#### Receive Updates

```javascript
socket.on("token_update", (data) => {
  console.log("Token update:", data);
});

socket.on("market_update", (data) => {
  console.log("Market update:", data);
});
```

## Configuration

### Environment Variables

#### Backend (.env)

```bash
# Flask Configuration
SECRET_KEY=your-secret-key-change-this-in-production
FLASK_ENV=production

# CoinMarketCap API Configuration
CMC_API_KEY=your-coinmarketcap-api-key
CMC_BASE_URL=https://pro-api.coinmarketcap.com/v1

# Redis Configuration (optional)
REDIS_URL=redis://localhost:6379/0

# Database Configuration
DATABASE_URL=sqlite:///database/app.db

# API Configuration
DEFAULT_API_KEY=demo-api-key-12345678
```

#### Frontend (.env.production)

```bash
VITE_API_BASE_URL=http://localhost:5000/api/v1
VITE_WEBSOCKET_URL=http://localhost:5000
```

## Deployment Options

### Docker Compose (Production)

1. **Update environment variables** in `docker-compose.yml`
2. **Build and start services**:
   ```bash
   docker compose up -d --build
   ```

### Cloud Deployment

#### AWS ECS/Fargate

1. Push images to ECR
2. Create ECS task definitions
3. Deploy using ECS service

#### Google Cloud Run

1. Build and push to Google Container Registry
2. Deploy using Cloud Run

#### Azure Container Instances

1. Push to Azure Container Registry
2. Deploy using Container Instances

### Traditional Server Deployment

1. **Install dependencies** on target server
2. **Configure reverse proxy** (nginx/Apache)
3. **Set up process manager** (PM2/systemd)
4. **Configure SSL certificates**

## Monitoring and Maintenance

### Health Checks

- Backend: `GET /api/v1/tokens?limit=1` with API key
- Frontend: HTTP 200 response from root path

### Logs

- Backend logs: Application logs via Flask
- Frontend logs: Browser console and server access logs

### Database Maintenance

- Regular backups of SQLite database
- Monitor database size and performance
- Clean up old metric records if needed

### API Rate Limits

- CoinMarketCap API has rate limits based on plan
- Monitor API usage and upgrade plan if needed

## Troubleshooting

### Common Issues

1. **API Key Invalid**:

   - Verify CoinMarketCap API key is correct
   - Check API key permissions and rate limits

2. **WebSocket Connection Failed**:

   - Ensure backend is running and accessible
   - Check CORS configuration
   - Verify API key in WebSocket auth

3. **Database Errors**:

   - Check database file permissions
   - Ensure database directory exists
   - Verify SQLite installation

4. **Frontend Build Errors**:
   - Clear node_modules and reinstall dependencies
   - Check Node.js version compatibility
   - Verify environment variables

### Performance Optimization

1. **Backend**:

   - Implement Redis caching
   - Optimize database queries
   - Use connection pooling

2. **Frontend**:
   - Enable gzip compression
   - Implement code splitting
   - Optimize bundle size

## Security Considerations

1. **API Keys**:

   - Use environment variables for sensitive data
   - Rotate API keys regularly
   - Implement proper API key validation

2. **CORS**:

   - Configure appropriate CORS policies
   - Restrict origins in production

3. **Rate Limiting**:

   - Implement rate limiting on API endpoints
   - Monitor for abuse patterns

4. **SSL/TLS**:
   - Use HTTPS in production
   - Configure proper SSL certificates

## Support and Maintenance

### Regular Tasks

- Monitor API usage and costs
- Update dependencies regularly
- Review and rotate API keys
- Monitor system performance
- Backup database regularly

### Scaling Considerations

- Horizontal scaling with load balancers
- Database migration to PostgreSQL for larger datasets
- Implement caching strategies
- Consider microservices architecture for larger deployments
