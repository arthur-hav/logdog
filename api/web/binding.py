from ..domain.handler import DomainHandler
from ..repository.repository import PostgresRepository


async def handler() -> DomainHandler:
    return DomainHandler(await PostgresRepository.connect())
