from content_service.src.schemas.mixin import IdMixin, NameMixin, UUIDMixin


class Genre(IdMixin, NameMixin):
    """Бизнес-модель жанра."""


class ResponseGenreData(UUIDMixin, NameMixin):
    """API-модель для вывода информации о жанре."""
