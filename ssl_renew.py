import os
import subprocess
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
import docker
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

EMAIL = os.environ.get('EMAIL')
DOMAINS = os.environ.get('DOMAINS').split(',')

if not EMAIL or not DOMAINS:
    raise ValueError("Missing required environment variables: EMAIL and DOMAINS")

def schedule_renewals():
    scheduler = BlockingScheduler()
    
    for domain in DOMAINS:
        domain_prefix = domain.split('.')[0].upper()
        minute = os.environ.get(f'{domain_prefix}_RENEW_MINUTE')
        hour = os.environ.get(f'{domain_prefix}_RENEW_HOUR')
        day = os.environ.get(f'{domain_prefix}_RENEW_DAY')
        month = os.environ.get(f'{domain_prefix}_RENEW_MONTH')
        day_of_week = os.environ.get(f'{domain_prefix}_RENEW_DAY_OF_WEEK')

        scheduler.add_job(
            lambda: renew_ssl(domain), 'cron',
            minute=minute, hour=hour, day=day, month=month, day_of_week=day_of_week
        )
        logging.info(f"Scheduled renewal for {domain}: {minute} {hour} {day} {month} {day_of_week}")
    
    logging.info("SSL renewal scheduler started. Waiting for scheduled runs.")
    scheduler.start()

def renew_ssl(domain):
    try:
        cert_path = f"/etc/letsencrypt/live/{domain}/cert.pem"
        result = subprocess.run(['openssl', 'x509', '-noout', '-dates', '-in', cert_path], 
                                capture_output=True, text=True)

        if result.returncode != 0:
            logging.error(f"Error checking certificate for {domain}: {result.stderr}")
            needs_renewal = True 
        else:
            for line in result.stdout.split('\n'):
                if line.startswith('notAfter='):
                    expiry_date = datetime.strptime(line.split('=')[1], '%b %d %H:%M:%S %Y %Z')
                    needs_renewal = (expiry_date - datetime.now() < timedelta(days=30))

        if not needs_renewal:
            logging.info(f"Certificate for {domain} does not need renewal yet.")
            return

        logging.info(f"Starting SSL certificate renewal process for domain {domain}...")
        command = [
            'certbot', 'certonly', '--reinstall', '--webroot',
            '--webroot-path=/var/www/certbot', '--email', EMAIL, 
            '--agree-tos', '--no-eff-email', '-d', domain, '--force-renewal', '-v'
        ]
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode == 0:
            logging.info(f"SSL certificate renewal for {domain} successful:\n{result.stdout}")
            restart_nginx()
        else:
            logging.error(f"SSL certificate renewal for {domain} failed:\n{result.stderr}")

    except Exception as e:
        logging.error(f"Error renewing SSL certificate for {domain}: {str(e)}")

def restart_nginx():
    try:
        client = docker.from_env()
        container = client.containers.get('nginx')
        container.restart()
        logging.info(f"Nginx container restarted successfully")
    except docker.errors.NotFound:
        logging.error("Nginx container 'nginx' not found")
    except docker.errors.APIError as e:
        logging.error(f"Docker API error while restarting Nginx: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error while restarting Nginx: {str(e)}")

if __name__ == '__main__':
    schedule_renewals()