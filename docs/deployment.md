# Production Deployment & Security Guide

**Shree Shanishwara Swamy Temple Website**  
**ಶ್ರೀ ಶನೀಶ್ವರಸ್ವಾಮಿ ದೇವಸ್ಥಾನ (ರಿ), ಶ್ರೀ ಕ್ಷೇತ್ರ ಸಿದ್ದಗಿರಿ**

---

## 🛡️ Safe Deployment Architecture

The recommended and safest method to deploy this project is via **Docker & Docker Compose** with **Caddy Reverse Proxy**.

### Key Security Safeguards
1. **Isolated Database**: MongoDB runs in an internal bridge network (`temple-network`) with **no host port exposed**. It is unreachable from the public internet.
2. **Non-Root Execution**: FastAPI runs as a dedicated unprivileged user (`templeuser`) inside the container.
3. **Automated TLS/HTTPS**: Caddy automatically requests, verifies, and renews Let's Encrypt / ZeroSSL TLS certificates with HTTP/3 support and security headers.
4. **Volume Persistence**: Uploads (`temple_uploads_data`) and database documents (`temple_mongodb_data`) persist independently of container updates.
5. **CORS & Documentation Lockdown**: Public OpenAPI documentation (`/docs`, `/redoc`) is disabled in production, and CORS origins are strictly bound to the official temple domain.

---

## 🚀 Option A: Docker & Docker Compose (Recommended)

### 1. Server Prerequisites
- Ubuntu 22.04 / 24.04 LTS (or any Linux VPS)
- Minimum server specs: 1 vCPU, 2 GB RAM, 20 GB SSD
- Ports open in firewall: `80` (HTTP), `443` (HTTPS / QUIC)
- A registered domain name (e.g., `shreeshanitemple.com`) with DNS `A` records pointing to your server's public IP.

### 2. Install Docker on the Server
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Log out and log back in, or run:
newgrp docker
```

### 3. Clone Repository
```bash
git clone <YOUR_REPOSITORY_URL> /opt/temple-website
cd /opt/temple-website
```

### 4. Configure Production Environment Secrets
Copy the production environment template:
```bash
cp .env.production.example .env.production
chmod 600 .env.production
```

Generate secure secrets for `.env.production`:
```bash
# Generate 64-character hex secret for JWT:
openssl rand -hex 32

# Generate 32-character base64 password for MongoDB:
openssl rand -base64 24
```

Edit `.env.production` using your favorite editor (`nano` or `vim`):
```bash
nano .env.production
```

Ensure you configure:
- `DOMAIN`: Your real domain (e.g. `shreeshanitemple.com`)
- `MONGO_ROOT_PASSWORD`: The generated MongoDB password
- `JWT_SECRET_KEY`: The generated JWT secret
- `ADMIN_EMAIL` & `ADMIN_PASSWORD`: Super-admin credentials
- `RAZORPAY_KEY_ID` & `RAZORPAY_KEY_SECRET`: Live Razorpay API credentials
- `ALLOWED_ORIGINS`: Comma-separated domain list (`https://shreeshanitemple.com,https://www.shreeshanitemple.com`)

### 5. Launch the Application
Run the automated deployment script:
```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

Or execute directly with Docker Compose:
```bash
docker compose up -d --build
```

### 6. Verify Health & Logs
```bash
# Check status of all containers
docker compose ps

# Follow live backend and reverse proxy logs
docker compose logs -f
```

---

## 🔒 Server Firewall & OS Hardening Checklist

Run the following commands on your Ubuntu server to secure the host:

```bash
# 1. Update system packages
sudo apt update && sudo apt upgrade -y

# 2. Configure UFW Firewall (Allow SSH, HTTP, HTTPS only)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP (Let's Encrypt challenge & redirect)
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 443/udp   # HTTP/3 (QUIC)
sudo ufw enable
sudo ufw status verbose

# 3. Enable automatic security updates
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

---

## 💾 Database Backup & Recovery

### Automated Backup Script
Create `/opt/backup_temple_db.sh`:
```bash
#!/usr/bin/env bash
BACKUP_DIR="/opt/backups/mongodb"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
mkdir -p "$BACKUP_DIR"

# Source environment variables for credentials
source /opt/temple-website/.env.production

# Run mongodump inside the container
docker compose -f /opt/temple-website/docker-compose.yml exec -T mongodb \
  mongodump -u "$MONGO_ROOT_USER" -p "$MONGO_ROOT_PASSWORD" --authenticationDatabase admin \
  --db "$DB_NAME" --archive --gzip > "$BACKUP_DIR/temple_backup_${TIMESTAMP}.gz"

# Retain backups for 30 days
find "$BACKUP_DIR" -type f -name "*.gz" -mtime +30 -delete
```

Make executable and add to crontab:
```bash
chmod +x /opt/backup_temple_db.sh
# Run every day at 3:00 AM:
(crontab -l 2>/dev/null; echo "0 3 * * * /opt/backup_temple_db.sh") | crontab -
```

---

## 🔄 Option B: Traditional Linux VPS (Systemd + Nginx)

If deploying directly without Docker:

1. **Systemd Service (`/etc/systemd/system/temple-backend.service`)**:
```ini
[Unit]
Description=Shree Shanishwara Swamy Temple FastAPI Backend
After=network.target mongod.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/temple-website/backend
EnvironmentFile=/var/www/temple-website/backend/.env
ExecStart=/var/www/temple-website/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

2. **Nginx Reverse Proxy (`/etc/nginx/sites-available/shreeshanitemple.com`)**:
```nginx
server {
    listen 80;
    server_name shreeshanitemple.com www.shreeshanitemple.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name shreeshanitemple.com www.shreeshanitemple.com;

    ssl_certificate /etc/letsencrypt/live/shreeshanitemple.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/shreeshanitemple.com/privkey.pem;

    client_max_body_size 20M;

    location /static/ {
        alias /var/www/temple-website/frontend/;
        expires 7d;
        add_header Cache-Control "public, no-transform";
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
