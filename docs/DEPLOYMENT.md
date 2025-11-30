# Deployment Guide

This guide covers deploying Vibe Agent to production environments.

## 🚀 Deployment Options

### Option 1: Local/Self-Hosted (Recommended)

**Advantages:**
- Complete data privacy
- No API costs (except Gemini)
- Full control
- Best for sensitive codebases

**Requirements:**
- Linux/Mac server or Windows with WSL
- 4GB+ RAM (8GB+ recommended)
- 10GB+ disk space
- Docker (optional but recommended)

### Option 2: Cloud VPS

**Providers:**
- DigitalOcean, Linode, AWS EC2, Google Cloud Compute

**Recommended Specs:**
- 2+ vCPUs
- 8GB RAM
- 25GB SSD

### Option 3: Docker Containers

**Best for:**
- Easy deployment
- Consistent environments
- Scaling

## 🐳 Docker Deployment

### Create Dockerfiles

**Backend Dockerfile:**
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend/src ./src
COPY models ./models

# Download BGE-M3 model
RUN python models/download_bge_m3.py

EXPOSE 8000

CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Frontend Dockerfile:**
```dockerfile
FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY frontend/package*.json ./
RUN npm ci

# Copy application
COPY frontend .

# Build
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - NEO4J_URL=bolt://neo4j:7687
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./data:/app/data
    depends_on:
      - neo4j
      - redis

  frontend:
    build:
      context: .
      dockerfile: frontend/Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - backend

  neo4j:
    image: neo4j:5
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/your_password
    volumes:
      - neo4j_data:/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  neo4j_data:
  redis_data:
```

### Deploy with Docker

```bash
# Set environment variables
export GEMINI_API_KEY=your_key_here

# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## 🔧 Manual Deployment

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.10+
sudo apt install python3.10 python3.10-venv python3-pip

# Install Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs

# Install Neo4j
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list
sudo apt update
sudo apt install neo4j

# Install Redis
sudo apt install redis-server
```

###2. Application Setup

```bash
# Clone repository
git clone <your-repo> /opt/vibe-agent
cd /opt/vibe-agent

# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python ../models/download_bge_m3.py

# Frontend
cd ../frontend
npm install
npm run build
```

### 3. Configure Services

**Create systemd service for backend:**
```ini
# /etc/systemd/system/vibe-backend.service
[Unit]
Description=Vibe Agent Backend
After=network.target neo4j.service redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/vibe-agent/backend
Environment="PATH=/opt/vibe-agent/backend/venv/bin"
ExecStart=/opt/vibe-agent/backend/venv/bin/uvicorn src.app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

**Create systemd service for frontend:**
```ini
# /etc/systemd/system/vibe-frontend.service
[Unit]
Description=Vibe Agent Frontend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/vibe-agent/frontend
ExecStart=/usr/bin/npm start
Restart=always

[Install]
WantedBy=multi-user.target
```

### 4. Start Services

```bash
sudo systemctl daemon-reload
sudo systemctl enable vibe-backend vibe-frontend
sudo systemctl start vibe-backend vibe-frontend

# Check status
sudo systemctl status vibe-backend
sudo systemctl status vibe-frontend
```

## 🔒 Security Considerations

### 1. Environment Variables
```bash
# Never commit .env file
# Use secure secrets management

# /opt/vibe-agent/.env
GEMINI_API_KEY=your_secret_key
NEO4J_PASSWORD=strong_password
```

### 2. Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/vibe-agent
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. SSL with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 4. Firewall

```bash
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

## 📊 Monitoring

### Health Checks
```bash
# Backend health
curl http://localhost:8000/health

# Neo4j
systemctl status neo4j

# Redis
systemctl status redis
```

### Logs
```bash
# Application logs
journalctl -u vibe-backend -f
journalctl -u vibe-frontend -f

# Neo4j logs
sudo journalctl -u neo4j -f
```

## 🔄 Updates

```bash
cd /opt/vibe-agent
git pull

# Backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart vibe-backend

# Frontend
cd ../frontend
npm install
npm run build
sudo systemctl restart vibe-frontend
```

## 📦 Backup

```bash
# Create backup script
#!/bin/bash
BACKUP_DIR=/backups/vibe-agent
DATE=$(date +%Y%m%d)

# Backup Neo4j
neo4j-admin database dump neo4j --to=$BACKUP_DIR/neo4j-$DATE.dump

# Backup data
tar -czf $BACKUP_DIR/data-$DATE.tar.gz /opt/vibe-agent/data

# Rotate old backups (keep 7 days)
find $BACKUP_DIR -name "*.dump" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

## ⚡ Performance Tuning

### Neo4j
```conf
# /etc/neo4j/neo4j.conf
dbms.memory.heap.initial_size=2g
dbms.memory.heap.max_size=4g
dbms.memory.pagecache.size=2g
```

### Redis
```conf
# /etc/redis/redis.conf
maxmemory 512mb
maxmemory-policy allkeys-lru
```

## 🆘 Troubleshooting

**Backend won't start:**
- Check logs: `journalctl -u vibe-backend -n 50`
- Verify .env file exists
- Check Neo4j/Redis are running

**Out of memory:**
- Reduce chunk size in settings
- Increase server RAM
- Enable swap memory

**Slow indexing:**
- Use SSD storage
- Increase worker threads
- Index in batches

---

For questions or issues, please open a GitHub issue.
