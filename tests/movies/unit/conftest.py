import json
import os
from unittest.mock import AsyncMock

import pytest

from tests.movies.functional.settings import test_settings


def read_json_file(file_path):
    with open(file_path) as json_file:
        json_data = json.load(json_file)
    return json_data


@pytest.fixture
def movies_data() -> list[dict]:
    """
    Create movies data from testdata JSON
    """

    data_path = os.path.join(
        test_settings.testdata_dir,
        f"{test_settings.es_movies_index}.json",
    )
    data = read_json_file(data_path)

    return data


@pytest.fixture
def persons_data() -> list[dict]:
    """
    Create persons data from testdata JSON
    """

    data_path = os.path.join(
        test_settings.testdata_dir,
        f"{test_settings.es_persons_index}.json",
    )
    data = read_json_file(data_path)

    return data


@pytest.fixture
def genres_data() -> list[dict]:
    """
    Create genres data from testdata JSON
    """

    data_path = os.path.join(
        test_settings.testdata_dir,
        f"{test_settings.es_genres_index}.json",
    )
    data = read_json_file(data_path)

    return data


@pytest.fixture
def mock_redis():
    """
    Create Redis mock
    """

    return AsyncMock()


@pytest.fixture
def mock_elastic():
    """
    Create Elastic mock
    """

    return AsyncMock()
