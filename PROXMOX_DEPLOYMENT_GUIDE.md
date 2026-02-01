# Proxmox Deployment & Maintenance Guide

## Server Information
- **LXC IP**: `192.168.1.101`
- **Project Path**: `/root/Project-APIR`
- **Python venv**: `/root/Project-APIR/.venv`

---

## 🚀 Initial Setup (One-Time)

### 1. SSH into Proxmox LXC
```bash
ssh root@192.168.1.101
```

### 2. Clone Repository
```bash
cd /root
git clone https://github.com/huwanbisente/Project-APIR
cd Project-APIR
```

### 3. Create Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Configure Environment Variables
```bash
nano .env
```
Add:
```
OPENAI_API_KEY=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
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=google/gemini-2.0-flash-001
```

### 5. Create Systemd Services

#### App Service
```bash
cat <<EOF > /etc/systemd/system/project_apir.service
[Unit]
Description=Invoice API Flask App
After=network.target

[Service]
User=root
WorkingDirectory=/root/Project-APIR
ExecStart=/root/Project-APIR/.venv/bin/gunicorn -w 1 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF
```

#### Tunnel Service (Ngrok)
```bash
cat <<EOF > /etc/systemd/system/project_tunnel.service
[Unit]
Description=Ngrok Tunnel for Invoice API
After=project_apir.service

[Service]
User=root
WorkingDirectory=/root/Project-APIR
ExecStart=/root/Project-APIR/.venv/bin/python tests/start_tunnel_ngrok.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

### 6. Enable and Start Services
```bash
systemctl daemon-reload
systemctl enable project_apir project_tunnel
systemctl start project_apir project_tunnel
```

---

## 🔄 Deploying Updates from GitHub

### Step 1: Pull Latest Code
```bash
cd /root/Project-APIR
git pull origin fix/gemini-migration
```

### Step 2: Update Dependencies (if requirements.txt changed)
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Restart Services
```bash
systemctl restart project_apir
systemctl restart project_tunnel
```

### Step 4: Verify Services are Running
```bash
systemctl status project_apir
systemctl status project_tunnel
```

---

## 🛠️ Common Maintenance Commands

### Check Service Status
```bash
# Check both services
systemctl status project_apir project_tunnel

# Check individual service
systemctl status project_apir
systemctl status project_tunnel
```

### View Service Logs
```bash
# Real-time logs (press Ctrl+C to exit)
journalctl -u project_apir -f
journalctl -u project_tunnel -f

# Last 50 lines
journalctl -u project_apir -n 50
journalctl -u project_tunnel -n 50
```

### Restart Services
```bash
# Restart both
systemctl restart project_apir project_tunnel

# Restart individual
systemctl restart project_apir
systemctl restart project_tunnel
```

### Stop Services
```bash
systemctl stop project_apir project_tunnel
```

### Start Services
```bash
systemctl start project_apir project_tunnel
```

### Kill Process on Port (if port 5000 is stuck)
```bash
fuser -k 5000/tcp
```

---

## 📝 Editing Configuration Files

### Edit .env File
```bash
cd /root/Project-APIR
nano .env
```
After editing, restart the app:
```bash
systemctl restart project_apir
```

### Edit Service Files
```bash
# Edit app service
nano /etc/systemd/system/project_apir.service

# Edit tunnel service
nano /etc/systemd/system/project_tunnel.service

# After editing, reload and restart
systemctl daemon-reload
systemctl restart project_apir project_tunnel
```

---

## 🔍 Troubleshooting

### Service Won't Start
```bash
# Check detailed error logs
journalctl -u project_apir -n 100 --no-pager
journalctl -u project_tunnel -n 100 --no-pager

# Check if port is in use
lsof -i :5000
netstat -tulpn | grep 5000
```

### App Returns 500 Error
```bash
# Check app logs
journalctl -u project_apir -f

# Test manually
cd /root/Project-APIR
source .venv/bin/activate
python -m flask run --host=0.0.0.0 --port=5000
```

### Tunnel Not Working
```bash
# Check tunnel logs
journalctl -u project_tunnel -f

# Test manually
cd /root/Project-APIR
source .venv/bin/activate
python tests/start_tunnel_ngrok.py
```

---

## 🌐 Public URLs

### Ngrok Static Domain
- **URL**: `https://osvaldo-nonenervating-jama.ngrok-free.dev`
- **Update in Google Apps Script**: `Project_APIR_GAS/Code.gs` → `FLASK_API_URL`

### Cloudflare (Future)
- **Domain**: `huwanbisente.online`
- **Planned URL**: `https://api.huwanbisente.online`

---

## 📦 Git Workflow (Local → Proxmox)

### On Your Windows PC
```powershell
# Make changes to code
# Test locally

# Commit and push
git add .
git commit -m "Your commit message"
git push origin fix/gemini-migration
```

### On Proxmox LXC
```bash
# Pull updates
cd /root/Project-APIR
git pull origin fix/gemini-migration

# Restart services
systemctl restart project_apir project_tunnel
```

---

## 🔐 Security Notes

- `.env` file is gitignored (never commit API keys!)
- `input_data/` and `output_data/` are gitignored (local data only)
- Always use `https://` URLs for production

---

## 📊 System Resources

### Check Disk Usage
```bash
df -h
```

### Check Memory Usage
```bash
free -h
```

### Check Running Processes
```bash
ps aux | grep python
ps aux | grep gunicorn
```

---

## 🆘 Emergency Commands

### Complete Service Reset
```bash
systemctl stop project_apir project_tunnel
fuser -k 5000/tcp
systemctl start project_apir project_tunnel
systemctl status project_apir project_tunnel
```

### Reboot LXC Container
```bash
reboot
```
(Services will auto-start on boot because of `systemctl enable`)

---

## 📞 Quick Reference

| Task | Command |
|------|---------|
| SSH to server | `ssh root@192.168.1.101` |
| Pull updates | `cd /root/Project-APIR && git pull origin fix/gemini-migration` |
| Restart everything | `systemctl restart project_apir project_tunnel` |
| Check status | `systemctl status project_apir project_tunnel` |
| View logs | `journalctl -u project_apir -f` |
| Edit .env | `nano /root/Project-APIR/.env` |

---

**Last Updated**: 2026-02-01
