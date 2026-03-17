# VPS Deployment Guide

Deploy Signal Tracker alongside your existing admin panel at `http://82.112.236.66/`

---

## Access URLs After Deployment

| App | URL |
|-----|-----|
| ✅ Existing Admin Panel | `http://82.112.236.66/` (unchanged) |
| 🆕 Signal Tracker | `http://82.112.236.66:4000/` |
| 🆕 Backend API Docs | `http://82.112.236.66:8000/docs` |

---

## Step 1: SSH into VPS

```bash
ssh root@82.112.236.66
```

---

## Step 2: Install Required Software

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv nodejs npm -y
npm install -g serve
```

---

## Step 3: Create Project Directory

```bash
mkdir -p /var/www/signal-tracker
```

---

## Step 4: Upload Files from Windows

Open PowerShell on your Windows machine and run:

```powershell
# Upload all project files (excluding node_modules and __pycache__)
scp -r "D:\Signal tracker\*.py" root@82.112.236.66:/var/www/signal-tracker/
scp -r "D:\Signal tracker\*.txt" root@82.112.236.66:/var/www/signal-tracker/
scp -r "D:\Signal tracker\*.json" root@82.112.236.66:/var/www/signal-tracker/
scp -r "D:\Signal tracker\*.html" root@82.112.236.66:/var/www/signal-tracker/
scp -r "D:\Signal tracker\frontend" root@82.112.236.66:/var/www/signal-tracker/
```

Or use **FileZilla/WinSCP**:
1. Connect to `82.112.236.66` via SFTP
2. Upload entire `Signal tracker` folder to `/var/www/signal-tracker/`
3. Skip `node_modules` and `__pycache__` folders

---

## Step 5: Setup Backend (on VPS)

```bash
cd /var/www/signal-tracker

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Step 6: Setup Frontend (on VPS)

```bash
cd /var/www/signal-tracker/frontend

# Remove old node_modules if uploaded
rm -rf node_modules

# Install dependencies
npm install

# Build for production
npm run build
```

---

## Step 7: Create Backend Service

```bash
sudo nano /etc/systemd/system/signal-tracker.service
```

Paste this content:

```ini
[Unit]
Description=Signal Tracker Backend
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/signal-tracker
ExecStart=/var/www/signal-tracker/venv/bin/python run.py
Restart=always
Environment="PATH=/var/www/signal-tracker/venv/bin"

[Install]
WantedBy=multi-user.target
```

Save with `Ctrl+O`, `Enter`, `Ctrl+X`

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable signal-tracker
sudo systemctl start signal-tracker
```

Check status:

```bash
sudo systemctl status signal-tracker
```

---

## Step 8: Create Frontend Service

```bash
sudo nano /etc/systemd/system/signal-frontend.service
```

Paste this content:

```ini
[Unit]
Description=Signal Tracker Frontend
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/signal-tracker/frontend
ExecStart=/usr/bin/serve -s dist -l 4000
Restart=always

[Install]
WantedBy=multi-user.target
```

Save and enable:

```bash
sudo systemctl daemon-reload
sudo systemctl enable signal-frontend
sudo systemctl start signal-frontend
```

---

## Step 9: Open Firewall Ports

```bash
# Open ports for Signal Tracker
sudo ufw allow 4000
sudo ufw allow 8000

# Verify
sudo ufw status
```

---

## ✅ Done!

Your Signal Tracker is now live at: `http://82.112.236.66:4000/`

---

## Useful Commands

| Action | Command |
|--------|---------|
| Restart Backend | `sudo systemctl restart signal-tracker` |
| Restart Frontend | `sudo systemctl restart signal-frontend` |
| View Backend Logs | `sudo journalctl -u signal-tracker -f` |
| View Frontend Logs | `sudo journalctl -u signal-frontend -f` |
| Stop Backend | `sudo systemctl stop signal-tracker` |
| Stop Frontend | `sudo systemctl stop signal-frontend` |

---

## Troubleshooting

### Port already in use?
```bash
# Find what's using the port
sudo lsof -i :4000
sudo lsof -i :8000

# Kill the process
sudo kill -9 <PID>
```

### Service not starting?
```bash
# Check logs
sudo journalctl -u signal-tracker -n 50
sudo journalctl -u signal-frontend -n 50
```

### Need to update code?
1. Upload new files
2. Rebuild frontend: `cd /var/www/signal-tracker/frontend && npm run build`
3. Restart services: `sudo systemctl restart signal-tracker signal-frontend`
