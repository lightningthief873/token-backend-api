# Token Metrics Service

A real-time backend service that tracks live cryptocurrency token metrics (market cap, velocity), exposes data via REST API and WebSocket, and includes a basic dashboard/UI. The service is containerized using Docker for easy deployment.

## Features

### Backend Service

- **REST API** for token metrics with comprehensive endpoints
- **WebSocket support** for real-time data streaming
- **Token velocity calculation** using market cap and volume data
- **CoinMarketCap API integration** for live cryptocurrency data
- **SQLite database** for data persistence and historical tracking
- **API authentication** with key-based access control
- **Rate limiting** and error handling
- **Docker containerization** for easy deployment

### Frontend Dashboard

- **Real-time visualization** of token metrics and velocity
- **Interactive charts** showing velocity trends and volume correlation
- **Live WebSocket updates** with connection status indicators
- **Responsive design** optimized for desktop and mobile
- **Token search and filtering** capabilities
- **Market overview** with aggregate statistics
- **Modern UI** built with React and Tailwind CSS

### Key Metrics Tracked

- **Market Capitalization**: Real-time market cap data
- **Token Velocity**: Calculated as volume/market_cap ratio
- **24h Volume**: Trading volume over 24 hours
- **Price Changes**: 1h, 24h, and 7d percentage changes
- **Velocity Trends**: Historical velocity analysis and trend detection

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd token-metrics-service

# Start all services
docker compose up -d

# Access the application
# Frontend: http://localhost:80
# Backend API: http://localhost:5000
```

### Manual Setup

#### Backend

```bash
cd token-metrics-service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python src/main.py
```

#### Frontend

```bash
cd token-metrics-dashboard
pnpm install
pnpm run dev
```

## API Usage

### Authentication

Include API key in request headers:

```bash
curl -H "X-API-Key: demo-api-key-12345678" \
     http://localhost:5000/api/v1/tokens?limit=10
```

### WebSocket Connection

```javascript
const socket = io("http://localhost:5000", {
  auth: { api_key: "demo-api-key-12345678" },
});

socket.emit("subscribe_token", {
  token_id: 1,
  metrics: ["price", "volume", "velocity"],
});
```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   External      │
│   (React)       │◄──►│   (Flask)       │◄──►│   APIs          │
│   Port: 80      │    │   Port: 5000    │    │   (CoinMarketCap)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │
         │              ┌─────────────────┐
         │              │   Database      │
         └──────────────►│   (SQLite)      │
                        │   + Redis Cache │
                        └─────────────────┘
```

## Technology Stack

### Backend

- **Python 3.11** with Flask framework
- **Flask-SocketIO** for WebSocket support
- **SQLAlchemy** for database ORM
- **Redis** for caching (optional)
- **Requests** for external API integration

### Frontend

- **React 19** with modern hooks
- **Vite** for fast development and building
- **Tailwind CSS** for styling
- **shadcn/ui** for UI components
- **Recharts** for data visualization
- **Socket.IO Client** for real-time updates

### Infrastructure

- **Docker** and Docker Compose for containerization
- **Nginx** for frontend serving in production
- **SQLite** for development, PostgreSQL recommended for production

## Token Velocity Calculation

Token velocity is calculated using the formula:

```
Velocity = 24h Trading Volume / Market Capitalization
```

This metric indicates how frequently tokens change hands relative to their total market value. Higher velocity suggests more active trading and liquidity.

### Velocity Trends

- **Increasing**: Rising trading activity relative to market cap
- **Decreasing**: Declining trading activity or growing market cap
- **Stable**: Consistent velocity over time

## Deployment

### Production Deployment

1. **Configure environment variables** for API keys and secrets
2. **Use Docker Compose** for multi-container deployment
3. **Set up reverse proxy** (nginx) for SSL termination
4. **Configure monitoring** and logging
5. **Implement backup strategy** for database

### Cloud Platforms

- **AWS**: ECS/Fargate with ALB
- **Google Cloud**: Cloud Run with Cloud SQL
- **Azure**: Container Instances with Azure Database
- **DigitalOcean**: App Platform or Droplets

## Security

- **API Key Authentication**: All endpoints require valid API keys
- **CORS Configuration**: Properly configured for cross-origin requests
- **Rate Limiting**: Prevents API abuse and ensures fair usage
- **Environment Variables**: Sensitive data stored securely
- **Input Validation**: All user inputs are validated and sanitized

## Monitoring

### Health Checks

- Backend: `GET /api/v1/tokens?limit=1`
- Frontend: HTTP 200 response from root
- Database: Connection and query performance
- External APIs: CoinMarketCap API status and rate limits

### Metrics to Monitor

- API response times and error rates
- WebSocket connection counts
- Database query performance
- External API usage and costs
- System resource utilization

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:

- Check the [Deployment Guide](DEPLOYMENT_GUIDE.md) for detailed setup instructions
- Review the API documentation in the deployment guide
- Open an issue for bugs or feature requests

## Roadmap

### Planned Features

- **Additional Metrics**: RSI, MACD, Bollinger Bands
- **Historical Data**: Extended historical analysis
- **Alerts System**: Price and velocity alerts
- **Portfolio Tracking**: Multi-token portfolio analysis
- **Advanced Charts**: Candlestick and technical indicators
- **Mobile App**: Native mobile application
- **API Webhooks**: Push notifications for events
