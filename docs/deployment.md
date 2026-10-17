# Production Deployment Guide

**Shree Shanishwara Swamy Temple Website**  
**ಶ್ರೀ ಶನೀಶ್ವರಸ್ವಾಮಿ ದೇವಸ್ಥಾನ (ರಿ), ಶ್ರೀ ಕ್ಷೇತ್ರ ಸಿದ್ದಗಿರಿ**

---

## 1. Prerequisites

- Python 3.10+ (Python 3.11 or 3.12 recommended)
- MongoDB 6.0+ (Local Community Edition or MongoDB Atlas M0/M10 cluster)
- Reverse Proxy: Nginx or Caddy
- SSL Certificate: Let's Encrypt Certbot
- Process Manager: Systemd (Linux) or NSSM / Windows Service

---

## 2. Environment Preparation

1. **Clone repository to target server:**
   ```bash
   git clone <REPO_URL> /var/www/temple-website
   cd /var/www/temple-website
   ```

2. **Configure Environment:**
   Copy `.env.example` to `backend/.env` and configure production secrets:
   ```bash
   cp .env.example backend/.env
   chmod 600 backend/.env
   ```
   Generate a secure JWT secret:
   ```bash
   openssl rand -hex 32
   ```

3. **Install Dependencies:**
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

---

## 3. Systemd Service Setup (Linux)

Create `/etc/systemd/system/temple-backend.service`:

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

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable temple-backend
sudo systemctl start temple-backend
sudo systemctl status temple-backend
```

---

## 4. Nginx Reverse Proxy Configuration

Create `/etc/nginx/sites-available/shreeshanitemple.com`:

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

    # Static assets caching
    location /static/ {
        alias /var/www/temple-website/frontend/;
        expires 7d;
        add_header Cache-Control "public, no-transform";
    }

    # API & Frontend route proxy
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
