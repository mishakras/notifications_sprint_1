from __future__ import annotations

import logging
import os
from datetime import timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from django.conf import settings
from django.utils import timezone as dj_timezone
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django_apscheduler.util import close_old_connections

from .models import Campaign, ScheduleType
from .tasks import run_campaign_job

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def get_scheduler() -> BackgroundScheduler:
    """
    Инициализирует/кеширует APScheduler.

    Если DISABLE_SCHEDULER=1, не подключаем jobstore и не стартуем фоновые
    задачи — чтобы миграции проходили без ошибок по отсутствующим таблицам.
    """
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    disabled = os.getenv("DISABLE_SCHEDULER")
    scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)

    if disabled:
        logger.info("APScheduler disabled via DISABLE_SCHEDULER=1")
        _scheduler = scheduler
        return scheduler

    scheduler.add_jobstore(DjangoJobStore(), "default")
    scheduler.add_job(
        delete_old_job_executions,
        trigger=CronTrigger(day_of_week="*", hour="3", minute="0"),
        id="clean_old_job_executions",
        max_instances=1,
        replace_existing=True,
    )
    scheduler.start()
    logger.info("APScheduler started with DjangoJobStore")
    _scheduler = scheduler
    return scheduler


def start_scheduler() -> None:
    """Вызывается из AppConfig.ready()."""
    get_scheduler()


def schedule_campaign(campaign_id: int) -> str:
    """
    Ставит кампанию в APScheduler по её типу расписания.
    Возвращает job_id (пустая строка, если планировщик отключён).
    """
    if os.getenv("DISABLE_SCHEDULER"):
        logger.info(
            "Skip scheduling campaign %s because DISABLE_SCHEDULER=1 is set.",
            campaign_id,
        )
        return ""

    scheduler = get_scheduler()
    campaign = Campaign.objects.get(pk=campaign_id)
    job_id = f"campaign_{campaign_id}"

    if campaign.schedule_type == ScheduleType.IMMEDIATE:
        trigger = DateTrigger(run_date=dj_timezone.now())
    elif campaign.schedule_type == ScheduleType.DELAYED:
        run_date = dj_timezone.now() + timedelta(
            seconds=campaign.delay_seconds,
        )
        trigger = DateTrigger(run_date=run_date)
    elif campaign.schedule_type == ScheduleType.CRON:
        if not campaign.cron:
            raise ValueError("Cron expression is empty.")
        parts = campaign.cron.split()
        if len(parts) != 5:
            raise ValueError(
                "Cron expression must have 5 fields: "
                "'minute hour day month day_of_week'.",
            )
        minute, hour, day, month, dow = parts
        trigger = CronTrigger(
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=dow,
            timezone=settings.TIME_ZONE,
        )
    else:
        raise ValueError(f"Unknown schedule_type: {campaign.schedule_type}")

    add_kwargs: dict[str, object] = {
        "id": job_id,
        "args": [campaign_id],
        "max_instances": 1,
        "coalesce": True,
        "replace_existing": True,
        "misfire_grace_time": 60 * 10,
    }
    if any(name == "default" for name in scheduler._jobstores):  # noqa: SLF001
        add_kwargs["jobstore"] = "default"

    scheduler.add_job(
        run_campaign_job,
        trigger=trigger,
        **add_kwargs,
    )
    logger.info(
        "Scheduled campaign %s with job %s using trigger %s",
        campaign_id,
        job_id,
        trigger,
    )
    return job_id


def delete_old_job_executions(max_age: int = 60 * 60 * 24) -> None:
    """Удаляет записи об исполнениях задач старше max_age секунд."""
    close_old_connections()
    DjangoJobExecution.objects.delete_old_job_executions(max_age)
