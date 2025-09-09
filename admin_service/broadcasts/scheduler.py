# broadcasts/scheduler.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from django.conf import settings
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django_apscheduler.util import close_old_connections

from apscheduler.schedulers.background import BackgroundScheduler

from .tasks import run_campaign_job  # см. ниже


_scheduler: Optional[BackgroundScheduler] = None


def get_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler:
        return _scheduler

    scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)
    scheduler.add_jobstore(DjangoJobStore(), "default")

    # Рекомендовано чистить старые записи об исполнениях
    scheduler.add_job(
        delete_old_job_executions,
        trigger=CronTrigger(day_of_week="*", hour="3", minute="0"),
        id="clean_old_job_executions",
        max_instances=1,
        replace_existing=True,
    )
    scheduler.start()
    _scheduler = scheduler
    return scheduler


def schedule_campaign(campaign) -> str:
    """
    Ставит кампанию в APScheduler по её типу доставки.
    Возвращает job_id.
    """
    scheduler = get_scheduler()
    job_id = f"campaign_{campaign.id}"

    if campaign.delivery_type == "immediate":
        trigger = DateTrigger(run_date=datetime.now(tz=timezone.utc))
    elif campaign.delivery_type == "scheduled":
        trigger = DateTrigger(run_date=campaign.run_at)  # run_at с tz
    elif campaign.delivery_type == "cron":
        # cron_expr формата "m h dom mon dow"
        minute, hour, day, month, dow = campaign.cron_expr.split()
        trigger = CronTrigger(
            minute=minute, hour=hour, day=day, month=month, day_of_week=dow,
            timezone=settings.TIME_ZONE,
        )
    else:
        raise ValueError(f"Unknown delivery_type: {campaign.delivery_type}")

    scheduler.add_job(
        run_campaign_job,
        trigger=trigger,
        id=job_id,
        args=[campaign.id],
        max_instances=1,
        coalesce=True,
        replace_existing=True,
        misfire_grace_time=60 * 10,  # 10 минут
        jobstore="default",
    )
    return job_id


def delete_old_job_executions(max_age: int = 60 * 60 * 24) -> None:
    """Чистим старые записи об исполнениях задач (по умолчанию — старше суток)."""
    close_old_connections()
    DjangoJobExecution.objects.delete_old_job_executions(max_age)
