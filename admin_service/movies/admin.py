from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Filmwork, Genre, GenreFilmwork, Person, PersonFilmwork


class GenreFilmworkInline(admin.TabularInline):
    model = GenreFilmwork
    verbose_name = _("genre_filmwork")
    verbose_name_plural = _("genre_filmworks")


class PersonFilmworkInline(admin.TabularInline):
    model = PersonFilmwork
    verbose_name = _("person_filmwork")
    verbose_name_plural = _("person_filmworks")


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    pass


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    pass


@admin.register(Filmwork)
class FilmworkAdmin(admin.ModelAdmin):
    inlines = (
        GenreFilmworkInline,
        PersonFilmworkInline,
    )

    list_display = (
        "title",
        "type",
        "creation_date",
        "rating",
    )
    list_filter = ("type",)
    search_fields = (
        "title",
        "description",
        "id",
    )
