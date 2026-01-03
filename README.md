# AllDue — Minimal Reminders App

Simple FastAPI app to track reminders and deadlines in a unified view.

Run locally:

1. Create and activate a virtualenv (recommended):

   python -m venv .venv
   .\.venv\Scripts\Activate.ps1  # PowerShell

2. Install deps:

   pip install -r requirements.txt

3. Start the app:

   uvicorn main:app --reload

Open http://127.0.0.1:8000/ and add reminders.

Guiding constraints: manual-first, lightweight, no auth, SQLite storage.

## Deployment (current)

- Repo: https://github.com/88pawankumarjha/alldue
- Deployed to: http://43.204.152.235 (ensure EC2 security group allows inbound HTTP (port 80)).

Basic server steps (already performed):
1. apt update && apt install -y python3-venv python3-pip nginx git
2. git clone https://github.com/88pawankumarjha/alldue.git
3. python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
4. Create systemd unit to run uvicorn and configure Nginx as reverse proxy

Note: For HTTPS, add a domain and run certbot with the nginx plugin.

## Useful commands (non-sensitive)

### Local development
- Create & activate venv (Windows PowerShell):
  - python -m venv .venv
  - .\.venv\Scripts\Activate.ps1
- Install deps: `pip install -r requirements.txt`
- Run locally for development: `uvicorn main:app --reload`

### Server management (example commands—replace placeholders)
- SSH into server: `ssh -i "<your_key.pem>" ubuntu@<server_ip>`
- Start/stop/restart service: `sudo systemctl start|stop|restart alldue`
- Check service status: `sudo systemctl status alldue --no-pager`
- Tail app logs: `sudo journalctl -u alldue -f`
- Tail nginx logs: `sudo journalctl -u nginx -f`

### Deployment (pull & restart)
- On server (pull latest and restart service):
  - `cd /home/ubuntu/alldue && git pull && sudo systemctl restart alldue`

### SQLite
- DB file (server): `/home/ubuntu/alldue/reminders.db`
- Quick inspect: `sqlite3 /home/ubuntu/alldue/reminders.db "SELECT * FROM reminders LIMIT 10;"`

### Nginx checks
- Test nginx config: `sudo nginx -t`
- Restart nginx: `sudo systemctl restart nginx`
- Confirm site (from your laptop): `curl -I http://<server_ip>`

### Firewall (ufw)
- Allow SSH / Nginx Full: `sudo ufw allow OpenSSH && sudo ufw allow 'Nginx Full' && sudo ufw enable`

### HTTPS (Certbot, requires a domain)
- Install certbot: `sudo apt install -y certbot python3-certbot-nginx`
- Obtain/auto-configure cert: `sudo certbot --nginx -d yourdomain.example`

### Notes
- Avoid storing secrets or private keys in this repo or README. Use environment variables or a secure secrets manager for production.
- Consider restricting the EC2 Security Group source to your IP instead of 0.0.0.0/0 for better security.

