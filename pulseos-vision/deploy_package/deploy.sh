#!/bin/bash
set -e

echo "Deploying PulseOS Vision..."

# 1. Frontend Deploy
echo "Deploying frontend to /var/www/html/vision..."
mkdir -p /var/www/html/vision
cp -r frontend_dist/* /var/www/html/vision/
chown -R www-data:www-data /var/www/html/vision

# 2. Backend Deploy
echo "Deploying backend to /opt/pulseos-vision..."
mkdir -p /opt/pulseos-vision
cp -r backend/* /opt/pulseos-vision/
cd /opt/pulseos-vision

# Stop and remove existing container if it exists
docker-compose down || true

# Build and start the container
echo "Building and starting Docker container..."
docker-compose up -d --build

# 3. Nginx Config Reminder
echo "======================================"
echo "Deployment scripts finished!"
echo "Please ensure that your Nginx config for www.ppday.site includes the rules in nginx_snippet.conf."
echo "You can test Nginx with 'nginx -t' and reload with 'systemctl reload nginx'."
echo "======================================"
