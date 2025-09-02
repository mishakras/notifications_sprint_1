from .base import BaseTimestamp, MixinFilmID, MixinID, MixinUserID


class FilmMark(BaseTimestamp, MixinUserID, MixinFilmID):
    pass


class FilmMarkCreate(FilmMark):
    pass


class FilmMarkUpdate(FilmMark):
    pass


class FilmMarkReturn(FilmMark, MixinID):
    pass
