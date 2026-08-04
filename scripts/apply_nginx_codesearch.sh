#!/bin/bash
set -e

NGINX_CONF="/etc/nginx/sites-available/synology-proxy"
BACKUP_CONF="${NGINX_CONF}.backup_$(date +%F_%H-%M-%S)"

echo "Backing up Nginx configuration to $BACKUP_CONF"
cp "$NGINX_CONF" "$BACKUP_CONF"

echo "Injecting CodeSearch Reverse Proxy configuration into Nginx..."

# We inject the location block right before the main / location block
sed -i '/location \/ {/i \
    location /code-search/ {\n\
        proxy_pass http://127.0.0.1:55010;\n\
        proxy_set_header Host $host;\n\
        proxy_set_header X-Real-IP $remote_addr;\n\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n\
        proxy_set_header X-Forwarded-Proto $scheme;\n\
        \n\
        # WebSocket support for Streamlit notebooks\n\
        proxy_http_version 1.1;\n\
        proxy_set_header Upgrade $http_upgrade;\n\
        proxy_set_header Connection "upgrade";\n\
        \n\
        proxy_read_timeout 86400s;\n\
        proxy_send_timeout 86400s;\n\
    }\n' "$NGINX_CONF"

echo "Restarting Nginx daemon..."
systemctl restart nginx

echo "CodeSearch DMZ Reverse Proxy configured successfully!"
