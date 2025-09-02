from .base import BaseTimestamp, MixinFilmID, MixinID, MixinUserID


class FilmScore(BaseTimestamp, MixinUserID, MixinFilmID):
    score: int


class FilmScoreCreate(FilmScore):
    pass


class FilmScoreUpdate(FilmScore):
    pass


class FilmScoreReturn(FilmScore, MixinID):
    pass
