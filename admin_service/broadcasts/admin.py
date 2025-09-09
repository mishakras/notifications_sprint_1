# admin_service/broadcasts/admin.py
from django.contrib import admin
from django.utils.html import format_html

from .models import Campaign, Template, CampaignStatus, ScheduleType
from .scheduler import schedule_campaign


@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "delivery_method", "updated_at")
    search_fields = ("name", "subject")
    list_filter = ("delivery_method",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "delivery_method",
        "schedule_type",
        "status",
        "updated_at",
        "run_now_button",
    )
    list_filter = ("delivery_method", "schedule_type", "status")
    search_fields = ("name", "audience")
    readonly_fields = ("created_at", "updated_at", "status")
    actions = ("run_now", "plan_selected")

    fieldsets = (
        (None, {"fields": ("name", "template", "delivery_method", "audience")}),
        ("Расписание", {"fields": ("schedule_type", "delay_seconds", "cron")}),
        ("Служебные", {"fields": ("status",)}),
    )

    def save_model(self, request, obj, form, change) -> None:
        super().save_model(request, obj, form, change)
        # После сохранения — поставить в планировщик/запустить
        schedule_campaign(obj.id)

    @admin.action(description="Запустить сейчас")
    def run_now(self, request, queryset) -> None:
        for campaign in queryset:
            campaign.schedule_type = ScheduleType.IMMEDIATE
            campaign.save(update_fields=["schedule_type"])
            schedule_campaign(campaign.id)

    @admin.action(description="Поставить по расписанию")
    def plan_selected(self, request, queryset) -> None:
        for campaign in queryset:
            schedule_campaign(campaign.id)

    def run_now_button(self, obj) -> str:
        return format_html(
            '<a class="button" href="{}">Запустить</a>',
            f"./{obj.id}/change/",  # менеджер нажимает, сохраняет — автозапуск
        )

    run_now_button.short_description = "Действие"
