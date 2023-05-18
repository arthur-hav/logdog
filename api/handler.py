class DomainHandler:
    def __init__(self, repository) -> None:
        self.repository = repository

    async def get_logs(self, from_time, to_time, jsonfilter):
        return await self.repository.get_logs(from_time, to_time, jsonfilter)
