# Cloudflare Tunnel Setup Guide for Project APIR

This guide explains how to replace Ngrok with Cloudflare Tunnel on your Proxmox server.
**Target Domain**: `api.huwanbisente.online`
**Local Service**: `http://localhost:5000`

## Prerequisites
- SSH access to your Proxmox container (`ssh root@192.168.1.101`)
- A Cloudflare account with your domain `huwanbisente.online` active.

---

## 1. Install `cloudflared` on Proxmox
Run these commands in your SSH session:

```bash
# Download the latest Debian package
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb

# Install the package
dpkg -i cloudflared.deb

# Verify installation
cloudflared --version
```

## 2. Authenticate the Tunnel
This step links the server to your Cloudflare account.

```bash
cloudflared tunnel login
```
1. It will output a URL (e.g., `https://discord.cloudflare.com/checkout...`).
2. Copy this URL and open it in your web browser **on your Windows PC**.
3. Select your domain (`huwanbisente.online`) and authorize.
4. Once done, the terminal on Proxmox will confirm success.

## 3. Create the Tunnel
Create a named tunnel (e.g., `apir-tunnel`).

```bash
cloudflared tunnel create apir-tunnel
```
*Note: Save the **Tunnel ID** shown in the output (a long UUID).*

## 4. Configure DNS Routing
Map the tunnel to your desired subdomain.

```bash
# Syntax: cloudflared tunnel route dns <tunnel-name> <public-hostname>
cloudflared tunnel route dns apir-tunnel api.huwanbisente.online
```

## 5. Create Configuration File
Create the configuration directory and file:

```bash
mkdir -p /etc/cloudflared
nano /etc/cloudflared/config.yml
```

Paste the following content into `config.yml`:

```yaml
tunnel: <Your-Tunnel-UUID>
credentials-file: /root/.cloudflared/<Your-Tunnel-UUID>.json

ingress:
  - hostname: api.huwanbisente.online
    service: http://localhost:5000
  - service: http_status:404
```
**Important:**
1. Replace `<Your-Tunnel-UUID>` with the actual ID from step 3.
2. Ensure the `credentials-file` path matches where the JSON key file was created (usually `/root/.cloudflared/`). You can verify by running `ls /root/.cloudflared/`.

## 6. Run as a Service
Install `cloudflared` as a system service so it starts automatically.

```bash
cloudflared service install /etc/cloudflared/config.yml
systemctl start cloudflared
systemctl enable cloudflared
```

## 7. Disable Old Ngrok Service (Optional)
If you are replacing the Ngrok tunnel:

```bash
systemctl stop project_tunnel
systemctl disable project_tunnel
```

## 8. Connectivity Test
On your Windows PC, visit: `https://api.huwanbisente.online`
You should see your API Flask app response.
