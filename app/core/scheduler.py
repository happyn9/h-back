"""
Scheduler embarqué dans l'app (APScheduler) — évite d'avoir besoin d'un
service cron externe. Se lance au démarrage de FastAPI (voir main.py).

Installation :  pip install apscheduler
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.services.reminders import send_daily_reminders

logger = logging.getLogger("hlearning.scheduler")

# Fuseau horaire de référence pour le "7h30" : Zambie
scheduler = AsyncIOScheduler(timezone=getattr(settings, "SCHEDULER_TIMEZONE", "Africa/Lusaka"))


def start_scheduler() -> None:
    scheduler.add_job(
        send_daily_reminders,
        trigger=CronTrigger(hour=7, minute=30),
        id="daily_learning_reminder",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.start()
    logger.info("Scheduler démarré : rappel quotidien programmé à 07:30 (%s)", scheduler.timezone)


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)