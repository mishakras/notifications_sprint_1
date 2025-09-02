import uuid

import pytest
from pydantic import ValidationError

from content_service.src.schemas.movies.persons import (
    Person,
    ResponsePersonData,
)


def test_create_person():
    person_uuid = str(uuid.uuid4())
    person = Person(id=person_uuid, name="Mark Hamill")

    assert person.id == person_uuid
    assert person.name == "Mark Hamill"


def test_create_response_person_data():
    person_uuid = str(uuid.uuid4())
    response_person = ResponsePersonData(uuid=person_uuid, name="Mark Hamill")

    assert response_person.uuid == person_uuid
    assert response_person.name == "Mark Hamill"


def test_person_validation_error():
    with pytest.raises(ValidationError):
        Person(name="Mark Hamill")


def test_response_person_validation_error():
    with pytest.raises(ValidationError):
        ResponsePersonData(name="Mark Hamill")


def test_person_id_validation_error():
    with pytest.raises(ValidationError):
        Person(id="")


def test_response_person_uuid_validation_error():
    with pytest.raises(ValidationError):
        ResponsePersonData(uuid="")


@pytest.mark.parametrize(
    "input_data",
    [
        {"id": 123, "name": "Mark Hamill"},
        {"id": 123.45, "name": "Mark Hamill"},
        {"id": 123, "name": 456},
        {"id": 123, "name": ["foo", "bar"]},
    ],
)
def test_invalid_types(input_data):
    with pytest.raises(ValidationError):
        Person(id=input_data["id"], name=input_data["name"])

    with pytest.raises(ValidationError):
        ResponsePersonData(uuid=input_data["id"], name=input_data["name"])
