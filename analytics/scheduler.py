import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from analytics.tasks import delete_analytics_reports_in_media

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def start():
    scheduler = BackgroundScheduler()
    trigger = CronTrigger(hour=0, minute=0)  # Midnight
    scheduler.add_job(delete_analytics_reports_in_media, trigger, name="Delete PDFs and Excels at Midnight", replace_existing=True)
    scheduler.start()
    message = "APScheduler started: Midnight delete job registered."
    print(message)
    logger.info(message)
