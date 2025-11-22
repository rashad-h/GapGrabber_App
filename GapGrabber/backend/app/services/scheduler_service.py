from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
import logging

logger = logging.getLogger(__name__)

# Create scheduler
scheduler = AsyncIOScheduler(
    jobstores={'default': MemoryJobStore()},
    executors={'default': AsyncIOExecutor()},
    job_defaults={'coalesce': False, 'max_instances': 3}
)


def start_scheduler():
    """Start the scheduler"""
    scheduler.start()
    logger.info("APScheduler started")


def shutdown_scheduler():
    """Shutdown the scheduler"""
    scheduler.shutdown()
    logger.info("APScheduler shut down")

