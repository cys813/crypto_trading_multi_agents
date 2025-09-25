# Development Commands - Crypto Trading Agents

## Quick Start Commands

### Web Application
```bash
# Start the web interface
python start_web.py

# Alternative direct start
python crypto_trading_agents/web/app.py
```

### Environment Setup
```bash
# Install main dependencies
pip install -r requirements.txt

# Install web dependencies
pip install -r requirements_web.txt

# Install clean dependencies (minimal) - now main requirements
pip install -r requirements.txt

# Install full dependencies (if needed)
pip install -r requirements_full.txt
```

## Development Workflow Commands

### Code Quality
```bash
# Format code with black
black .

# Lint code with flake8
flake8 .

# Type checking with mypy
mypy .

# Sort imports with isort
isort .
```

### Testing
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_specific_file.py

# Run async tests
pytest -m asyncio
```

### Development Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install development dependencies
pip install -e .
```

## Docker Commands

### Development
```bash
# Build and run with Docker Compose
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production
```bash
# Build production image
docker build -t crypto-trading-agents .

# Run production container
docker run -p 8501:8501 crypto-trading-agents
```

## Database Commands

### MongoDB (if enabled)
```bash
# Start MongoDB
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Connect to MongoDB
mongo mongodb://localhost:27017/crypto_trading_agents
```

### Redis (if enabled)
```bash
# Start Redis
docker run -d -p 6379:6379 --name redis redis:latest

# Connect to Redis
redis-cli
```

## Configuration Commands

### Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env  # or your preferred editor
```

### Configuration Validation
```bash
# Check API keys configuration
python -c "from crypto_trading_agents.config import validate_config; print(validate_config())"
```

## Monitoring and Debugging

### Log Management
```bash
# View application logs
tail -f logs/app.log

# View error logs
tail -f logs/error.log

# Clear logs
rm -rf logs/*.log
```

### Performance Monitoring
```bash
# Monitor memory usage
python -c "import psutil; print(f'Memory: {psutil.virtual_memory().percent}%')"

# Monitor disk usage
df -h
```

### Debug Mode
```bash
# Run with debug logging
export DEBUG=true
export LOG_LEVEL=DEBUG
python start_web.py
```

## Data Management

### Cache Management
```bash
# Clear cache
rm -rf ~/.crypto_trading_agents/cache/*

# Clear session data
rm -rf ~/.crypto_trading_agents/sessions/*

# Clear progress data
rm -rf ~/.crypto_trading_agents/progress/*
```

### Database Cleanup
```bash
# Clean old analysis results (older than 48 hours)
find ~/.crypto_trading_agents/data/analysis -name "*.json" -mtime +2 -delete

# Clean old session data
find ~/.crypto_trading_agents/data/sessions -name "*.json" -mtime +2 -delete
```

## API Testing

### Health Check
```bash
# Check if web interface is running
curl http://localhost:8501

# Check API endpoints (if available)
curl http://localhost:8501/api/health
```

### API Key Testing
```bash
# Test OpenAI API
python -c "import openai; print('OpenAI API works')"

# Test CoinGecko API
python -c "import pycoingecko; print('CoinGecko API works')"
```

## Git Commands

### Standard Workflow
```bash
# Add changes
git add .

# Commit changes
git commit -m "Description of changes"

# Push changes
git push origin main

# Pull latest changes
git pull origin main
```

### Branch Management
```bash
# Create new branch
git checkout -b feature/new-feature

# Switch branches
git checkout main

# Delete branch
git branch -d feature/new-feature
```

## Deployment Commands

### Production Deployment
```bash
# Build for production
docker build -t crypto-trading-agents:latest .

# Tag version
docker tag crypto-trading-agents:latest crypto-trading-agents:v0.1.0

# Push to registry
docker push crypto-trading-agents:v0.1.0
```

### Systemd Service (Linux)
```bash
# Create service file
sudo nano /etc/systemd/system/crypto-trading-agents.service

# Enable service
sudo systemctl enable crypto-trading-agents

# Start service
sudo systemctl start crypto-trading-agents

# Check status
sudo systemctl status crypto-trading-agents
```

## Security Commands

### API Key Management
```bash
# Generate secure API key
openssl rand -hex 32

# Check environment variables
env | grep API

# Secure environment file
chmod 600 .env
```

### SSL/TLS Setup
```bash
# Generate SSL certificate
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Test HTTPS connection
curl -k https://localhost:8501
```

## Troubleshooting Commands

### Port Conflicts
```bash
# Check port usage
lsof -i :8501

# Kill process on port
kill -9 <PID>

# Find available ports
netstat -tuln
```

### Dependency Issues
```bash
# Check installed packages
pip list

# Check package conflicts
pip check

# Upgrade packages
pip install --upgrade -r requirements.txt
```

### Memory Issues
```bash
# Check memory usage
free -h

# Check process memory
ps aux | grep python

# Clear Python cache
find . -name "*.pyc" -delete
find . -name "__pycache__" -delete
```

## Performance Commands

### Load Testing
```bash
# Install load testing tools
pip install locust

# Run load test
locust -f locustfile.py --host=http://localhost:8501
```

### Benchmarking
```bash
# Time analysis execution
time python -c "from crypto_trading_agents.agents.technical_analyst import TechnicalAnalyst; print('Benchmark')"

# Profile memory usage
python -m memory_profiler script_to_profile.py
```

## Backup Commands

### Configuration Backup
```bash
# Backup configuration files
tar -czf config_backup.tar.gz .env config/ *.toml *.yaml

# Backup user data
tar -czf user_data_backup.tar.gz ~/.crypto_trading_agents/
```

### Database Backup
```bash
# Backup MongoDB
mongodump --db crypto_trading_agents --out backup/

# Backup Redis
redis-cli SAVE
cp /var/lib/redis/dump.rdb redis_backup.rdb
```