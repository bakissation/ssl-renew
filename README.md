# Automated SSL Certificate Renewal

## Overview

This project provides an automated SSL certificate renewal system for a domain. It uses Docker, Nginx, Certbot, and a custom Python script to manage and automate the SSL certificate renewal process.

## System Components

1. Nginx: Web server handling HTTP and HTTPS traffic
2. Certbot: Tool for obtaining and renewing Let's Encrypt SSL certificates
3. Docker: Containerization platform for running services
4. Python Script: Custom script (ssl_renew.py) for scheduling and managing renewals

## Prerequisites

- Docker and Docker Compose installed on your system
- A registered domain name
- Port 80 and 443 open on your server

## Initial Setup

1. Clone this repository:

```bash
git clone https://github.com/yourusername/ssl-renewal.git
cd ssl-renewal
```

1. Copy the example environment file and edit it with your specific details:

```bash
cp .env.example .env
nano .env
```

Fill in your email address, domain names, and adjust the renewal schedules if needed.

3. Build and start the Docker containers:

```bash
docker-compose up -d
```

4. Verify that all containers are running:

```bash
docker-compose ps
```

## System Architecture

The system consists of four main Docker services:

1. `nginx_http`: Handles HTTP traffic and ACME challenges
2. `certbot`: Obtains and renews SSL certificates
3. `nginx_https`: Serves HTTPS traffic using the obtained certificates
4. `docker_ssl_manager`: Runs the custom Python script for automated renewals

## Configuration Files

- `compose.yaml`: Docker Compose configuration
- `nginx/nginx.http.conf`: Nginx configuration for HTTP
- `nginx/nginx.https.conf`: Nginx configuration for HTTPS
- `ssl_renew.py`: Python script for automated renewals
- `Dockerfile`: For building the docker_ssl_manager service
- `nginx/proxy_params`: Nginx proxy parameters

## SSL Renewal Process

### Initial Certificate Obtainment

1. The `nginx_http` service starts and listens on port 80.
2. The `certbot` service runs and obtains the initial SSL certificate for domain.
3. The `nginx_https` service starts using the obtained certificates.

### Automated Renewal

1. The `docker_ssl_manager` service runs the `ssl_renew.py` script.
2. The script is scheduled to run based on the cron-like schedule defined in the .env file.
3. When executed, the script:
a. Runs Certbot to renew the certificate
b. Restarts the `nginx_https` container to use the new certificate

## Manual Certificate Renewal

To manually trigger a certificate renewal:

1. Run the certbot container:

```bash

docker-compose run --rm certbot
```

2. Restart the nginx_https container:

```bash
docker-compose restart nginx_https
```

## Monitoring and Maintenance

1. Check Docker logs for each service:

```bash

docker-compose logs nginx_http
docker-compose logs certbot
docker-compose logs nginx_https
docker-compose logs docker_ssl_manager
```

2. Monitor the expiration date of your certificate:

```bash
echo | openssl s_client -servername {domain} -connect {domain}:443 2>/dev/null | openssl x509 -noout -dates
```

## Troubleshooting

1. If renewals fail, check Certbot logs for error messages:


docker-compose logs certbot

2. Ensure that port 80 is accessible for ACME challenges.
3. Verify that all environment variables are correctly set in the `.env` file.
4. Check that the domain DNS is correctly pointing to your server's IP address.
5. If the `docker_ssl_manager` service is failing, check its logs:


docker-compose logs docker_ssl_manager


## Security Considerations

- The system uses named volumes for persistent data storage.
- A custom Docker network isolates the services.
- The Nginx configurations use environment variables to avoid hardcoding sensitive information.
- The SSL renewal script runs as a non-root user for improved security.

## Customization

- To change the renewal schedule, edit the cron-like parameters in the `.env` file.
- To add or modify Nginx server blocks, edit the `nginx/nginx.http.conf` and `nginx/nginx.https.conf` files.

## Contributing

Contributions to improve the system are welcome. Please submit a pull request or open an issue to discuss proposed changes.

## License