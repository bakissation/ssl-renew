import os
import subprocess
import logging

from apscheduler.schedulers.blocking import BlockingScheduler
import docker

logging.basicConfig(
    level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s'
)

EMAIL = os.environ.get('EMAIL')
DOMAIN = os.environ.get('DOMAIN')

RENEW_MINUTE = os.environ.get('RENEW_MINUTE')
RENEW_SECOND = os.environ.get('RENEW_SECOND')
RENEW_HOUR = os.environ.get('RENEW_HOUR')
RENEW_DAY = os.environ.get('RENEW_DAY')
RENEW_DAY_OF_WEEK = os.environ.get('RENEW_DAY_OF_WEEK')
RENEW_MONTH = os.environ.get('RENEW_MONTH')

def renew_ssl_certificate():
    try:
        command = [
            'certbot', 'certonly', '--reinstall', '--webroot',
            '--webroot-path=/var/www/certbot', '--email', EMAIL, 
            '--agree-tos', '--no-eff-email', '-d', DOMAIN, '--force-renewal',
            '-v'
        ]
        
        logging.info(
            f"Starting SSL certificate renewal process for domain {DOMAIN}..."
        )
        result = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        if result.returncode == 0:
            logging.info(
                f"SSL certificate renewal for {DOMAIN} successful:\n"
                f"{result.stdout}"
            )
        else:
            logging.error(
                f"SSL certificate renewal for {DOMAIN} failed:\n"
                f"{result.stderr}"
            )
        
    except Exception as e:
        logging.error(
            f"An error occurred during certificate renewal for {DOMAIN}: "
            f"{str(e)}"
        )

    client = docker.from_env()
    try:
        container_name = 'nginx_https'
        container = client.containers.get(container_name)
        container.restart()
        logging.info(f"{container_name} container restarted successfully")
    except docker.errors.NotFound as e:
        logging.error(f"Nginx container not found: {str(e)}")
    except Exception as e:
        logging.error(
            f"An error occurred while restarting Nginx containers: {str(e)}"
        )

def schedule_renewal():
    scheduler = BlockingScheduler()
    scheduler.add_job(
        renew_ssl_certificate,
        'cron',
        second=RENEW_SECOND,
        minute=RENEW_MINUTE,
        hour=RENEW_HOUR,
        day=RENEW_DAY,
        day_of_week=RENEW_DAY_OF_WEEK,
        month=RENEW_MONTH,
    )
    scheduler.start()

if __name__ == '__main__':
    schedule_renewal()