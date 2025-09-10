from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from django.template import Context, Template
from django.utils.safestring import mark_safe


@dataclass(frozen=True)
class RenderedMessage:
    subject: str
    body: str


def render_template(
    subject_tpl: str,
    body_tpl: str,
    context: Mapping[str, Any],
) -> RenderedMessage:
    """
    Рендерит subject/body c плейсхолдерами {{ first_name }} и т.п.

    :param subject_tpl: строка-шаблон темы письма
    :param body_tpl: строка-шаблон тела
    :param context: словарь данных пользователя/события
    :return: RenderedMessage(subject, body)
    """
    subject = Template(subject_tpl).render(Context(context))
    body = Template(body_tpl).render(Context(context))
    # Если дальше отдаёшь в email/sms — оставь как есть.
    # Для HTML допускается mark_safe.
    return RenderedMessage(subject=subject.strip(), body=mark_safe(body))
