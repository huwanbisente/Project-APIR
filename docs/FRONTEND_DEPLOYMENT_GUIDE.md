# Frontend Deployment Guide (Decoupled LXC)

This guide explains how to deploy the **Frontend** (HTML/JS/CSS) of Project APIR to a separate Proxmox LXC container (e.g., using Nginx), while keeping the **Backend** (Python API) on Container 101.

## Prerequisites
1.  **Backend Running**: Ensure your Python API is running on Container 101 and accessible via `https://invoice-api.huwanbisente.online`.
2.  **New LXC Container**: Create a new Lightweight Linux Container (Ubuntu/Debian) in Proxmox for the frontend (e.g., CT 105).

---

## Step 1: Install Nginx on Frontend LXC
Log in to your **new** frontend container (e.g., CT 105) and install the web server.

```bash
apt update && apt upgrade -y
apt install nginx git -y
```

## Step 2: Download the Code
Clone the repository to get the frontend files.

```bash
cd /var/www/html
# Remove default nginx page
rm -rf *
# Clone repo (temporarily into a subfolder)
git clone https://github.com/huwanbisente/Project-APIR.git temp_repo
# Move frontend files to root
mv temp_repo/frontend/* .
# Clean up
rm -rf temp_repo
```

Your `/var/www/html/` folder should now look like this:
```text
css/
js/
Index.html
```

## Step 3: Configure Permissions
Ensure Nginx can read the files.

```bash
chown -R www-data:www-data /var/www/html
chmod -R 755 /var/www/html
```

## Step 4: Verify Nginx Configuration
The default configuration usually works out of the box, but let's double-check.
Edit `/etc/nginx/sites-available/default`:

```nginx
server {
    listen 80 default_server;
    listen [::]:80 default_server;

    root /var/www/html;
    index Index.html;  # Make sure this matches our filename (capital I)

    server_name _;

    location / {
        try_files $uri $uri/ =404;
    }
}
```
*Note: Our file is named `Index.html` (Capital I). Linux is case-sensitive, so ensure the `index` directive matches or rename the file to `index.html`.*

Restart Nginx:
```bash
systemctl restart nginx
```

## Step 5: Expose via Cloudflare Tunnel
You need a public URL for this frontend so you can access it from anywhere.

1.  Go to the **Cloudflare Zero Trust Dashboard**.
2.  Go to **Access** -> **Tunnels**.
3.  Select your existing Main Tunnel (or create a new one).
4.  Click **Configure**.
5.  Go to **Public Hostname** tab -> **Add Public Hostname**.
6.  **Subdomain**: `app` (or whatever you want, e.g., `invoice-hub`).
7.  **Domain**: `huwanbisente.online`.
8.  **Service**: `http://192.168.1.105:80` (Replace with your Frontend Container's IP).
9.  Click **Save Hostname**.

## Step 6: Verify API Connection
1.  Open your browser to `https://app.huwanbisente.online`.
2.  The UI should load.
3.  Try to **Login** (`admin@example.com` / `admin123`).
4.  If it works, the Frontend (CT 105) is successfully talking to the Backend (CT 101) via the public internet!

---

## Troubleshooting

### "Mix Content Error" or CORS Issues
If you see errors in the browser console about CORS or blocked requests:
1.  Ensure `app.js` is point to `https://invoice-api.huwanbisente.online` (HTTPS is required).
2.  Ensure your Backend (Container 101) has CORS enabled (it is enabled by default in our `app.py`).

### "404 Not Found"
*   Check if the file is named `Index.html` or `index.html`. Linux cares about capitalization.
*   Rename it if needed: `mv Index.html index.html`.
