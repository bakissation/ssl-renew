# SSL Certificate Renewal Documentation for fatoura.app

## Overview

This document outlines the automated SSL certificate renewal process for the domain fatoura.app. The system uses Docker, Nginx, Certbot, and a custom Python script to manage and automate the renewal process.

## System Components

1. **Nginx**: Web server handling HTTP and HTTPS traffic
2. **Certbot**: Tool for obtaining and renewing Let's Encrypt SSL certificates
3. **Docker**: Containerization platform for running services
4. **Python Script**: Custom script (`ssl_renew.py`) for scheduling and managing renewals

## Docker Services

The system consists of four main Docker services:

1. `nginx_http`: Handles HTTP traffic and ACME challenges
2. `certbot`: Obtains and renews SSL certificates
3. `nginx_https`: Serves HTTPS traffic using the obtained certificates
4. `docker_ssl_manager`: Runs the custom Python script for automated renewals

## Configuration Files

1. `compose.yaml`: Docker Compose configuration
2. `nginx.http.conf`: Nginx configuration for HTTP
3. `nginx.https.conf`: Nginx configuration for HTTPS
4. `ssl_renew.py`: Python script for automated renewals
5. `Dockerfile`: For building the docker_ssl_manager service
6. `proxy_params`: Nginx proxy parameters

## Renewal Process

### Initial Certificate Obtainment

1. The `nginx_http` service starts and listens on port 80.
2. The `certbot` service runs and obtains the initial SSL certificate for fatoura.app.
3. The `nginx_https` service starts using the obtained certificates.

### Automated Monthly Renewal

1. The `docker_ssl_manager` service runs the `ssl_renew.py` script.
2. The script is scheduled to run monthly (configurable via environment variables).
3. When executed, the script:
   a. Runs Certbot to renew the certificate
   b. Restarts the `nginx_https` container to use the new certificate

## Detailed Component Breakdown

### Nginx HTTP Configuration (`nginx.http.conf`)

```nginx
server {
    listen 80;
    server_name fatoura.app;

    location /.well-known/acme-challenge {
        allow all;
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}
```

This configuration:
- Listens on port 80
- Serves ACME challenges for certificate validation
- Redirects all other traffic to HTTPS

### Nginx HTTPS Configuration (`nginx.https.conf`)

```nginx
server {
    listen 443 ssl;
    server_name fatoura.app;
    ssl_certificate /etc/letsencrypt/live/fatoura.app/fullchain.pem; 
    ssl_certificate_key /etc/letsencrypt/live/fatoura.app/privkey.pem; 

    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location /socket.io/ {
        include /etc/nginx/proxy_params;
        proxy_pass http://web:5000/socket.io/;
    }

    location / {
        include /etc/nginx/proxy_params;
        proxy_pass http://web:5000;
    }
}
```

This configuration:
- Listens on port 443 with SSL
- Uses the Let's Encrypt certificates
- Includes additional SSL options and parameters
- Proxies requests to a backend service (assumed to be running on web:5000)

### SSL Renewal Script (`ssl_renew.py`)

The Python script performs the following tasks:
1. Schedules the renewal process based on environment variables
2. Executes Certbot to renew the certificate
3. Restarts the Nginx HTTPS container to apply the new certificate

### Docker Compose Configuration (`compose.yaml`)

The Docker Compose file defines four services:
1. `nginx_http`: For HTTP traffic and ACME challenges
2. `certbot`: For obtaining and renewing certificates
3. `nginx_https`: For HTTPS traffic
4. `docker_ssl_manager`: For running the renewal script

## Renewal Schedule

The renewal is scheduled using the following environment variables:
- `RENEW_MINUTE`
- `RENEW_HOUR`
- `RENEW_DAY`
- `RENEW_MONTH`
- `RENEW_DAY_OF_WEEK`

These can be adjusted in the `.env` file to change the renewal schedule.

## Monitoring and Maintenance

1. **Logs**: Check Docker logs for each service to monitor the renewal process:
   ```
   docker-compose logs nginx_http
   docker-compose logs certbot
   docker-compose logs nginx_https
   docker-compose logs docker_ssl_manager
   ```

2. **Manual Renewal**: To manually trigger a renewal:
   ```
   docker-compose run --rm certbot
   docker-compose restart nginx_https
   ```

3. **Certificate Expiry**: Monitor the expiration date of your certificate:
   ```
   echo | openssl s_client -servername fatoura.app -connect fatoura.app:443 2>/dev/null | openssl x509 -noout -dates
   ```

## Troubleshooting

1. If renewals fail, check Certbot logs for error messages.
2. Ensure that port 80 is accessible for ACME challenges.
3. Verify that all environment variables are correctly set in the `.env` file.
4. Check that the domain DNS is correctly pointing to your server's IP address.

By following this documentation, the SSL certificate for fatoura.app should be automatically renewed each month, ensuring continuous HTTPS support for your domain.