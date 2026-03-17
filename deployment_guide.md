# ORB Screener Production Deployment Guide (VPS Only)

This document provides a complete guide to deploying your ORB Screener completely on a single Virtual Private Server (VPS). Both your React frontend and FastAPI backend will run on the same server, managed by Nginx.

## Architecture Overview
- **Server**: A Linux VPS (Hetzner Cloud or Oracle Cloud).
- **Backend (FastAPI)**: Runs via Python/Uvicorn, controlled by Systemd on port 8000.
- **Frontend (React/Vite)**: Statically built and served directly by Nginx.
- **Reverse Proxy**: Nginx routes `/api` and `/ws` requests to the backend, and everything else to the built frontend files.
- **Domain**: A registered domain name (e.g., `orbscreener.com`) mapped to your VPS to enable secure `https://` and `wss://` connections.

> [!IMPORTANT]
> **Why do we need a Domain and SSL?** 
> To securely serve your data and provide WebSockets without browser security warnings or blockages, the connection must use `https://` and `wss://`.

---

## Step 1: Server Setup (VPS)

### 1. Renting the Server
Rent a basic Linux VPS running **Ubuntu 22.04 or 24.04**. 
- Top pick for reliability/price: **Hetzner Cloud** (ARM64 Ampere instance, CX11 or CAX11, ~$4.20/month).
- Free option: **Oracle Cloud Free Tier** (Always Free ARM instance).

### 2. Point Your Domain
In your domain registrar's DNS settings, create an **A Record** pointing `dashboard.yourdomain.com` to your VPS's public IP address.

### 3. Install Dependencies
SSH into your VPS and run the following commands to install dependencies:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv git nginx curl -y

# Install Node.js mapping (required to build the frontend)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

---

## Step 2: Clone and Configure

### 1. Clone App
```bash
# Clone your repository
git clone https://github.com/your-username/orb-screener.git
cd orb-screener
```

### 2. Prepare the Backend
```bash
# Create virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Build the Frontend
```bash
cd frontend

# Install package dependencies
npm install

# Build the static HTML/JS/CSS files
# Since Nginx will route API calls on the same domain, we set the API URL to be relative.
VITE_API_URL="" npm run build

# Move back to root directory
cd ..
```

---

## Step 3: Run the Backend (Systemd)

To make your backend run continuously and restart on crashes, create a systemd service:

```bash
sudo nano /etc/systemd/system/orbscreener.service
```

Add the following (update the paths `/root/orb-screener` to match your actual clone directory, e.g., `/home/ubuntu/orb-screener`):
```ini
[Unit]
Description=ORB Screener FastAPI Backend
After=network.target

[Service]
User=root
WorkingDirectory=/root/orb-screener
Environment="PATH=/root/orb-screener/venv/bin"
ExecStart=/root/orb-screener/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start it:
```bash
sudo systemctl enable orbscreener
sudo systemctl start orbscreener
```

---

## Step 4: Reverse Proxy & SSL (Nginx)

Now we configure Nginx to serve the frontend files, and pass `/api` and WebSockets to the backend.

```bash
sudo nano /etc/nginx/sites-available/dashboard.yourdomain.com
```

Add this configuration (adjust the `root` path to point to your `frontend/dist` directory):
```nginx
server {
    server_name dashboard.yourdomain.com;

    # Serve the React Frontend
    root /root/orb-screener/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to FastAPI
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Proxy WebSocket requests to FastAPI
    location /ws/ {
        proxy_pass http://127.0.0.1:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400; # Keep WebSockets alive
    }
}
```

Enable it and get a free SSL certificate:
```bash
sudo ln -s /etc/nginx/sites-available/dashboard.yourdomain.com /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo systemctl reload nginx

# Install Certbot and get SSL
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d dashboard.yourdomain.com
```

Your system is now deployed on a single VPS!

---

## Analytics
To add tracking Analytics (like Google Analytics 4):
1. Go to Google Analytics and create a GA4 Web Data Stream.
2. Get the tracking code snippet (starts with `<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXX"></script>`).
3. Paste the code into your frontend's `index.html` file inside the `<head>` tag.
4. Run `npm run build` again and restart Nginx if you ever update the code.
