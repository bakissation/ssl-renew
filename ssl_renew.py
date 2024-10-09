import os
import subprocess
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
import docker

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_env_variable(var_name):
    value = os.environ.get(var_name)
    if not value:
        raise ValueError(f"Missing environment variable: {var_name}")
    return value

EMAIL = get_env_variable('EMAIL')
DOMAIN = get_env_variable('DOMAIN')
RENEW_MINUTE = get_env_variable('RENEW_MINUTE')
RENEW_HOUR = get_env_variable('RENEW_HOUR')
RENEW_DAY = get_env_variable('RENEW_DAY')
RENEW_MONTH = get_env_variable('RENEW_MONTH')
RENEW_DAY_OF_WEEK = get_env_variable('RENEW_DAY_OF_WEEK')

def renew_ssl_certificate():
    try:
        command = [
            'certbot', 'certonly', '--reinstall', '--webroot',
            '--webroot-path=/var/www/certbot', '--email', EMAIL, 
            '--agree-tos', '--no-eff-email', '-d', DOMAIN, '--force-renewal',
            '-v'
        ]
        
        logging.info(f"Starting SSL certificate renewal process for domain {DOMAIN}...")
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode == 0:
            logging.info(f"SSL certificate renewal for {DOMAIN} successful:\n{result.stdout}")
        else:
            logging.error(f"SSL certificate renewal for {DOMAIN} failed:\n{result.stderr}")
        
    except subprocess.SubprocessError as e:
        logging.error(f"Subprocess error during certificate renewal: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error during certificate renewal: {str(e)}")

    restart_nginx()

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

def schedule_renewal():
    scheduler = BlockingScheduler()
    scheduler.add_job(
        renew_ssl_certificate,
        'cron',
        minute=RENEW_MINUTE,
        hour=RENEW_HOUR,
        day=RENEW_DAY,
        month=RENEW_MONTH,
        day_of_week=RENEW_DAY_OF_WEEK,
    )
    logging.info("SSL renewal scheduler started. Waiting for next scheduled run.")
    scheduler.start()

if __name__ == '__main__':
    schedule_renewal()