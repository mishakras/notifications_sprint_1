from pydantic import BaseModel


class TitleMixin(BaseModel):
    title: str


class IdMixin(BaseModel):
    id: str


class UUIDMixin(BaseModel):
    uuid: str


class NameMixin(BaseModel):
    name: str


class DescriptionMixin(BaseModel):
    description: str | None


class RatingMixin(BaseModel):
    imdb_rating: float
