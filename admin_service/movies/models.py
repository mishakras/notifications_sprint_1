import uuid

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class TimeStampedMixin(models.Model):
    class Meta:
        abstract = True

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)


class UUIDMixin(models.Model):
    class Meta:
        abstract = True

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


class Genre(UUIDMixin, TimeStampedMixin):
    class Meta:
        db_table = 'content"."genre'
        verbose_name = _("Genre")
        verbose_name_plural = _("Genres")

    name = models.CharField(_("name"), max_length=255)
    description = models.TextField(_("description"), blank=True)

    def __str__(self):
        return self.name


class Person(UUIDMixin, TimeStampedMixin):
    class Meta:
        db_table = 'content"."person'
        verbose_name = _("person")
        verbose_name_plural = _("persons")

    full_name = models.CharField(_("full_name"), max_length=255)

    def __str__(self):
        return self.full_name


class Filmwork(UUIDMixin, TimeStampedMixin):
    class Meta:
        db_table = 'content"."film_work'
        verbose_name = _("filmwork")
        verbose_name_plural = _("filmworks")

    class FilmworkType(models.TextChoices):
        Movie = _("movie"), _("movie")
        TV_Show = _("tv_show"), _("tv_show")

    title = models.CharField(_("title"), max_length=255, blank=False)
    description = models.TextField(_("description"), blank=True)
    creation_date = models.DateField(_("creation date"), blank=False)
    rating = models.FloatField(
        _("rating"),
        blank=True,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
    )
    type = models.CharField(
        _("type"),
        choices=FilmworkType.choices,
        blank=False,
    )
    genre = models.ManyToManyField(
        Genre,
        through="GenreFilmwork",
        verbose_name=_("genres"),
    )
    person = models.ManyToManyField(Person, through="PersonFilmwork")

    def __str__(self):
        return self.title


class GenreFilmwork(UUIDMixin):
    class Meta:
        db_table = 'content"."genre_film_work'
        verbose_name = _("genre_filmwork")

    created = models.DateTimeField(auto_now_add=True)
    film_work = models.ForeignKey("Filmwork", on_delete=models.CASCADE)
    genre = models.ForeignKey(
        "Genre",
        on_delete=models.CASCADE,
        verbose_name=_("genre"),
    )


class PersonFilmwork(UUIDMixin):
    class Meta:
        db_table = 'content"."person_film_work'
        verbose_name = _("person_filmwork")

    class PersonFilmworkType(models.TextChoices):
        Producer = _("producer"), _("producer")
        Actor = _("actor"), _("actor")
        Director = _("director"), _("director")
        Supply = _("supply"), _("supply")
        BestBoy = _("best boy"), _("best boy")

    created = models.DateTimeField(auto_now_add=True)
    role = models.CharField(
        choices=PersonFilmworkType.choices,
        verbose_name=_("role"),
    )
    film_work = models.ForeignKey("Filmwork", on_delete=models.CASCADE)
    person = models.ForeignKey(
        "Person",
        on_delete=models.CASCADE,
        verbose_name=_("person"),
    )


class MyUserManager(BaseUserManager):
    def create_user(self, email, password=None):
        if not email:
            raise ValueError("Users must have an email address")

        user = self.model(email=self.normalize_email(email))
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None):
        user = self.create_user(email, password=password)
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    email = models.EmailField(
        verbose_name="email address",
        max_length=255,
        unique=True,
    )
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    # строка с именем поля модели,
    # которая используется в качестве уникального идентификатора
    USERNAME_FIELD = "email"

    # менеджер модели
    objects = MyUserManager()

    def __str__(self):
        return f"{self.email} {self.id}"

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True
