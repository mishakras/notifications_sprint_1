from abc import ABC, abstractmethod


class AbstractRepository(ABC):
    @abstractmethod
    async def create(self, **kwargs):
        raise NotImplementedError

    @abstractmethod
    async def update(self, **kwargs):
        raise NotImplementedError

    @abstractmethod
    async def delete(self, **kwargs):
        raise NotImplementedError

    @abstractmethod
    async def read(self, **kwargs):
        raise NotImplementedError

    @abstractmethod
    async def read_list(self, **kwargs):
        raise NotImplementedError

    @abstractmethod
    async def read_list_by_filter(self, **kwargs):
        raise NotImplementedError
