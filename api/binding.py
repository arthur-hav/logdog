from .handler import DomainHandler
from .repository import PostgresRepository


async def handler() -> DomainHandler:
    return DomainHandler(await PostgresRepository.connect())
