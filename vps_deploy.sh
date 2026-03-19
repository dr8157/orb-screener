#!/bin/bash
# ============================================
# ORB Screener Dashboard - VPS Deployment Script
# Run this on your VPS after SSH login
# ============================================

set -e  # Stop on any error

echo "============================================"
echo "  ORB Screener - VPS Deployment"
echo "============================================"

# ----- STEP 1: System Update & Dependencies -----
echo ""
echo "[1/8] Installing system dependencies..."
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv nginx git curl ufw

# Install Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs

echo "Python: $(python3 --version)"
echo "Node: $(node --version)"
echo "npm: $(npm --version)"

# ----- STEP 2: Clone Repository -----
echo ""
echo "[2/8] Cloning repository..."
mkdir -p /var/www
cd /var/www

# Remove old directory if exists
if [ -d "orb-screener" ]; then
    echo "Removing existing directory..."
    rm -rf orb-screener
fi

git clone https://github.com/dr8157/orb-screener.git
cd orb-screener

echo "Repository cloned successfully"

# ----- STEP 3: Setup Python Backend -----
echo ""
echo "[3/8] Setting up Python backend..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "Backend dependencies installed"

# ----- STEP 4: Build Frontend -----
echo ""
echo "[4/8] Building frontend for production..."
cd frontend
npm install
VITE_API_URL="" npm run build
cd ..

echo "Frontend built successfully"

# ----- STEP 5: Create credentials file -----
echo ""
echo "[5/8] Setting up credentials..."

# Create credentials.json (will be filled by user)
if [ ! -f "credentials.json" ]; then
    cat > credentials.json << 'CRED_EOF'
{
    "CLIENT_ID": "REPLACE_WITH_YOUR_CLIENT_ID",
    "PASSWORD": "REPLACE_WITH_YOUR_PASSWORD",
    "AUTH_SECRET": "REPLACE_WITH_YOUR_AUTH_SECRET",
    "API_KEY": "REPLACE_WITH_YOUR_API_KEY",
    "API_SECRET": "REPLACE_WITH_YOUR_API_SECRET"
}
CRED_EOF
    echo "Created credentials.json - YOU MUST EDIT THIS FILE!"
    echo "Run: nano /var/www/orb-screener/credentials.json"
else
    echo "credentials.json already exists"
fi

# Create empty token file
touch token.txt

# ----- STEP 6: Create Systemd Service for Backend -----
echo ""
echo "[6/8] Creating backend systemd service..."

cat > /etc/systemd/system/orb-backend.service << 'SERVICE_EOF'
[Unit]
Description=ORB Screener FastAPI Backend
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/orb-screener
Environment="PATH=/var/www/orb-screener/venv/bin:/usr/bin"
ExecStart=/var/www/orb-screener/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE_EOF

systemctl daemon-reload
systemctl enable orb-backend

echo "Backend service created and enabled"

# ----- STEP 7: Configure Nginx -----
echo ""
echo "[7/8] Configuring Nginx reverse proxy..."

cat > /etc/nginx/sites-available/orb-screener << 'NGINX_EOF'
server {
    listen 80;
    server_name _;

    # Serve React frontend (static build files)
    root /var/www/orb-screener/frontend/dist;
    index index.html;

    # Frontend routes (React SPA)
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to FastAPI backend
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 300;
    }

    # Proxy WebSocket requests to FastAPI backend
    location /ws/ {
        proxy_pass http://127.0.0.1:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400;
    }

    # Health check endpoint
    location = /health {
        proxy_pass http://127.0.0.1:8000/;
    }
}
NGINX_EOF

# Enable site, remove default
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/orb-screener /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
systemctl enable nginx

echo "Nginx configured and running"

# ----- STEP 8: Setup Daily Cron for Market Morning Restart -----
echo ""
echo "[8/8] Setting up daily morning restart cron..."

# IST is UTC+5:30, so 9:10 AM IST = 3:40 AM UTC
# This restarts the backend every morning at 9:10 AM IST (before 9:15 market open)
# It ensures fresh Kite authentication and historical data fetch

(crontab -l 2>/dev/null | grep -v "orb-backend"; echo "40 3 * * 1-5 systemctl restart orb-backend  # 9:10 AM IST Mon-Fri: restart for fresh auth + data") | crontab -

echo "Cron job set: Backend restarts at 9:10 AM IST every weekday"

# ----- STEP 9: Firewall -----
echo ""
echo "Configuring firewall..."
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP (Nginx)
ufw allow 443/tcp   # HTTPS (future)
ufw --force enable

echo ""
echo "============================================"
echo "  DEPLOYMENT COMPLETE!"
echo "============================================"
echo ""
echo "IMPORTANT: Before starting, edit your credentials:"
echo "  nano /var/www/orb-screener/credentials.json"
echo ""
echo "Then start the backend:"
echo "  systemctl start orb-backend"
echo ""
echo "Your dashboard will be at:"
echo "  http://187.127.132.1"
echo ""
echo "Useful commands:"
echo "  systemctl status orb-backend    # Check backend status"
echo "  journalctl -u orb-backend -f    # View live backend logs"
echo "  systemctl restart orb-backend   # Restart backend"
echo "  crontab -l                      # View cron jobs"
echo ""
echo "Daily schedule:"
echo "  9:10 AM IST - Backend auto-restarts (fresh Kite auth)"
echo "  9:15 AM IST - Market opens, ORB candle starts forming"
echo "  9:20 AM IST - ORB candle complete, breakout detection begins"
echo "============================================"
