from content_service.src.schemas.mixin import IdMixin, NameMixin, UUIDMixin


class Person(IdMixin, NameMixin):
    """Бизнес-модель персонажа."""


class ResponsePersonData(UUIDMixin, NameMixin):
    """API-модель для вывода информации о персонаже."""
