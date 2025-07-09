# 🚀 Deployment Guide

## **Option 1: Railway (Recommended - Easy & Free)**

### **Step 1: Prepare Your Repository**
```bash
# Make sure your code is pushed to GitHub
git add .
git commit -m "Prepare for deployment"
git push origin main
```

### **Step 2: Deploy to Railway**
1. Go to [Railway.app](https://railway.app)
2. Sign up with your GitHub account
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository: `Aayushhkher/plumber-booking-system`
5. Railway will automatically detect it's a Python app
6. Click "Deploy Now"

### **Step 3: Configure Environment Variables**
In Railway dashboard:
- Go to your project → Variables
- Add: `FLASK_ENV=production`
- Add: `SECRET_KEY=your-secret-key-here`

### **Step 4: Access Your App**
Railway will provide a URL like: `https://your-app-name.railway.app`

---

## **Option 2: Render (Free Tier Available)**

### **Step 1: Create Render Account**
1. Go to [Render.com](https://render.com)
2. Sign up with GitHub

### **Step 2: Deploy**
1. Click "New" → "Web Service"
2. Connect your GitHub repository
3. Configure:
   - **Name**: `plumber-booking-system`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
   - **Plan**: Free

### **Step 3: Environment Variables**
Add in Render dashboard:
- `FLASK_ENV=production`
- `SECRET_KEY=your-secret-key`

---

## **Option 3: Heroku (Paid)**

### **Step 1: Install Heroku CLI**
```bash
# macOS
brew install heroku/brew/heroku

# Or download from: https://devcenter.heroku.com/articles/heroku-cli
```

### **Step 2: Deploy**
```bash
# Login to Heroku
heroku login

# Create app
heroku create your-plumber-app-name

# Add PostgreSQL (optional)
heroku addons:create heroku-postgresql:mini

# Deploy
git push heroku main

# Open app
heroku open
```

---

## **Option 4: DigitalOcean App Platform**

### **Step 1: Create DigitalOcean Account**
1. Go to [DigitalOcean.com](https://digitalocean.com)
2. Sign up and add payment method

### **Step 2: Deploy**
1. Go to "Apps" in DigitalOcean dashboard
2. Click "Create App"
3. Connect your GitHub repository
4. Configure:
   - **Source**: GitHub
   - **Repository**: `Aayushhkher/plumber-booking-system`
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Run Command**: `python app.py`

---

## **Option 5: VPS Deployment (Advanced)**

### **Step 1: Get a VPS**
- [DigitalOcean Droplet](https://digitalocean.com/products/droplets)
- [Linode](https://linode.com)
- [Vultr](https://vultr.com)

### **Step 2: Server Setup**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python, Git, Nginx
sudo apt install python3 python3-pip git nginx -y

# Clone your repository
git clone https://github.com/Aayushhkher/plumber-booking-system.git
cd plumber-booking-system

# Install dependencies
pip3 install -r requirements.txt

# Install Gunicorn
pip3 install gunicorn
```

### **Step 3: Configure Gunicorn**
Create `/etc/systemd/system/plumber-app.service`:
```ini
[Unit]
Description=Plumber Booking System
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/plumber-booking-system
Environment="PATH=/home/ubuntu/plumber-booking-system/venv/bin"
ExecStart=/home/ubuntu/plumber-booking-system/venv/bin/gunicorn --workers 3 --bind unix:plumber-app.sock -m 007 app:app

[Install]
WantedBy=multi-user.target
```

### **Step 4: Configure Nginx**
Create `/etc/nginx/sites-available/plumber-app`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/ubuntu/plumber-booking-system/plumber-app.sock;
    }
}
```

### **Step 5: Start Services**
```bash
# Enable and start the app
sudo systemctl start plumber-app
sudo systemctl enable plumber-app

# Configure Nginx
sudo ln -s /etc/nginx/sites-available/plumber-app /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

---

## **Environment Variables**

For all deployments, set these environment variables:

```bash
FLASK_ENV=production
SECRET_KEY=your-very-secure-secret-key
DATABASE_URL=your-database-url
```

---

## **Database Setup**

### **For Production Database:**
1. **PostgreSQL** (Recommended)
   ```bash
   # Install PostgreSQL
   sudo apt install postgresql postgresql-contrib
   
   # Create database
   sudo -u postgres createdb plumber_app
   sudo -u postgres createuser plumber_user
   ```

2. **MySQL**
   ```bash
   # Install MySQL
   sudo apt install mysql-server
   
   # Create database
   mysql -u root -p
   CREATE DATABASE plumber_app;
   CREATE USER 'plumber_user'@'localhost' IDENTIFIED BY 'password';
   GRANT ALL PRIVILEGES ON plumber_app.* TO 'plumber_user'@'localhost';
   ```

---

## **SSL/HTTPS Setup**

### **Using Let's Encrypt:**
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

---

## **Monitoring & Maintenance**

### **Logs:**
```bash
# View application logs
sudo journalctl -u plumber-app

# View Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### **Backup Database:**
```bash
# PostgreSQL
pg_dump plumber_app > backup.sql

# MySQL
mysqldump plumber_app > backup.sql
```

---

## **Recommended Deployment Order**

1. **Start with Railway** (easiest, free)
2. **Move to Render** (if you need more features)
3. **Consider VPS** (for full control)

---

## **Troubleshooting**

### **Common Issues:**

1. **Port Issues:**
   ```bash
   # Check what's using port 5001
   lsof -i :5001
   ```

2. **Database Issues:**
   ```bash
   # Reset database
   rm instance/plumber_app.db
   python3 app.py
   ```

3. **Permission Issues:**
   ```bash
   # Fix file permissions
   chmod +x *.sh
   chmod 755 templates/ static/
   ```

---

## **Performance Optimization**

### **For High Traffic:**
1. Use Redis for session storage
2. Implement database connection pooling
3. Add CDN for static files
4. Use load balancer for multiple instances

### **Security:**
1. Enable HTTPS
2. Set secure headers
3. Implement rate limiting
4. Regular security updates

---

**🎉 Your Plumber Booking System is now ready for deployment!**

Choose the option that best fits your needs and budget. Railway is recommended for beginners, while VPS gives you full control. 