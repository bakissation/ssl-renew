import os
import subprocess
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
import docker
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_env_variable(var_name):
    value = os.environ.get(var_name)
    if not value:
        raise ValueError(f"Missing environment variable: {var_name}")
    return value

EMAIL = get_env_variable('EMAIL')
DOMAINS = get_env_variable('DOMAINS').split(',')

def renew_ssl_certificate(domain):
    try:
        command = [
            'certbot', 'certonly', '--reinstall', '--webroot',
            '--webroot-path=/var/www/certbot', '--email', EMAIL, 
            '--agree-tos', '--no-eff-email', '-d', domain, '--force-renewal',
            '-v'
        ]
        
        logging.info(f"Starting SSL certificate renewal process for domain {domain}...")
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode == 0:
            logging.info(f"SSL certificate renewal for {domain} successful:\n{result.stdout}")
            return True
        else:
            logging.error(f"SSL certificate renewal for {domain} failed:\n{result.stderr}")
            return False
        
    except subprocess.SubprocessError as e:
        logging.error(f"Subprocess error during certificate renewal for {domain}: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error during certificate renewal for {domain}: {str(e)}")
    
    return False

def restart_nginx():
    client = docker.from_env()
    try:
        container_name = 'nginx_https'
        container = client.containers.get(container_name)
        container.restart()
        logging.info(f"{container_name} container restarted successfully")
    except docker.errors.NotFound:
        logging.error(f"Nginx container '{container_name}' not found")
    except docker.errors.APIError as e:
        logging.error(f"Docker API error while restarting Nginx: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error while restarting Nginx: {str(e)}")

def check_and_renew_certificate(domain):
    if should_renew(domain):
        if renew_ssl_certificate(domain):
            restart_nginx()

def should_renew(domain):
    try:
        cert_path = f"/etc/letsencrypt/live/{domain}/cert.pem"
        result = subprocess.run(['openssl', 'x509', '-noout', '-dates', '-in', cert_path], 
                                capture_output=True, text=True)
        if result.returncode != 0:
            logging.error(f"Error checking certificate for {domain}: {result.stderr}")
            return True  # to renew if we can't check the expiration (just in case)

        for line in result.stdout.split('\n'):
            if line.startswith('notAfter='):
                expiry_date = datetime.strptime(line.split('=')[1], '%b %d %H:%M:%S %Y %Z')
                if expiry_date - datetime.now() < timedelta(days=30):
                    logging.info(f"Certificate for {domain} is due for renewal")
                    return True
        
        logging.info(f"Certificate for {domain} does not need renewal yet")
        return False
    except Exception as e:
        logging.error(f"Error checking renewal for {domain}: {str(e)}")
        return True  # to renew if there's an error checking

def schedule_renewals():
    scheduler = BlockingScheduler()
    
    for domain in DOMAINS:
        domain_prefix = domain.split('.')[0].upper()
        minute = get_env_variable(f'{domain_prefix}_RENEW_MINUTE')
        hour = get_env_variable(f'{domain_prefix}_RENEW_HOUR')
        day = get_env_variable(f'{domain_prefix}_RENEW_DAY')
        month = get_env_variable(f'{domain_prefix}_RENEW_MONTH')
        day_of_week = get_env_variable(f'{domain_prefix}_RENEW_DAY_OF_WEEK')
        
        scheduler.add_job(
            check_and_renew_certificate,
            'cron',
            args=[domain],
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
        )
        logging.info(f"Scheduled renewal for {domain}: {minute} {hour} {day} {month} {day_of_week}")
    
    logging.info("SSL renewal scheduler started. Waiting for scheduled runs.")
    scheduler.start()

if __name__ == '__main__':
    schedule_renewals()