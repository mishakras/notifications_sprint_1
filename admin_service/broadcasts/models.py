from __future__ import annotations

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

class DeliveryMethod(models.TextChoices):
    EMAIL = "email", _("Email")
    SMS = "sms", _("SMS")
    PUSH = "push", _("Push")
    WS = "websocket", _("WebSocket")


class ScheduleType(models.TextChoices):
    IMMEDIATE = "immediate", _("Сразу")
    DELAYED = "delayed", _("Отложенная")
    CRON = "cron", _("Повторяющаяся (cron)")


class Template(models.Model):
    name = models.CharField(_("Название"), max_length=128, unique=True)
    subject = models.CharField(_("Тема"), max_length=255, blank=True)
    body = models.TextField(_("Текст"))
    delivery_method = models.CharField(
        _("Канал доставки"),
        max_length=16,
        choices=DeliveryMethod.choices,
        default=DeliveryMethod.EMAIL,
    )
    created_at = models.DateTimeField(_("Создано"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлено"), auto_now=True)

    class Meta:
        verbose_name = _("Шаблон")
        verbose_name_plural = _("Шаблоны")
        ordering = ("-updated_at",)

    def __str__(self) -> str:
        return self.name


class CampaignStatus(models.TextChoices):
    DRAFT = "draft", _("Черновик")
    SCHEDULED = "scheduled", _("Запланирована")
    RUNNING = "running", _("Выполняется")
    FINISHED = "finished", _("Завершена")
    CANCELED = "canceled", _("Отменена")
    FAILED = "failed", _("Ошибка")


class Campaign(models.Model):
    name = models.CharField(_("Название"), max_length=128, unique=True)
    template = models.ForeignKey(
        Template,
        on_delete=models.PROTECT,
        verbose_name=_("Шаблон"),
        related_name="campaigns",
    )
    delivery_method = models.CharField(
        _("Канал доставки"),
        max_length=16,
        choices=DeliveryMethod.choices,
        help_text=_(
            "На этапе админки просто прокидываем канал; "
            "персонализация на стороне воркера."
        ),
    )
    audience = models.CharField(
        _("Аудитория"),
        max_length=255,
        default="all",
        help_text=_(
            "Напр.: "
            "'all', 'segment:premium', 'user_ids:1,2,3'"
        ),
    )

    schedule_type = models.CharField(
        _("Тип расписания"),
        max_length=16,
        choices=ScheduleType.choices,
        default=ScheduleType.IMMEDIATE,
    )
    delay_seconds = models.PositiveIntegerField(
        _("Задержка, сек."),
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text=_("Только для отложенных задач."),
    )
    cron = models.CharField(
        _("Cron-выражение"),
        max_length=128,
        null=True,
        blank=True,
        help_text=_(
            "Только для повторяющихся задач. "
            "Пример: '0 12 * * FRI'"
        ),
    )

    status = models.CharField(
        _("Статус"),
        max_length=16,
        choices=CampaignStatus.choices,
        default=CampaignStatus.DRAFT,
        db_index=True,
    )
    created_at = models.DateTimeField(_("Создано"),
                                      auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлено"),
                                      auto_now=True)

    class Meta:
        verbose_name = _("Кампания")
        verbose_name_plural = _("Кампании")
        ordering = ("-updated_at",)

    def __str__(self) -> str:
        return self.name

    def clean(self) -> None:


        if (self.schedule_type == ScheduleType.DELAYED
                and not self.delay_seconds):
            raise ValidationError(
                _(
                    "Для отложенной кампании укажите 'delay_seconds'."
                )
            )
        if self.schedule_type == ScheduleType.CRON and not self.cron:
            raise ValidationError(
                _(
                    "Для повторяющейся кампании укажите 'cron'."
                )
            )
