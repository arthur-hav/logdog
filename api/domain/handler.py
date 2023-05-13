class DomainHandler:
    def __init__(self, repository) -> None:
        self.repository = repository

    async def get_logs(self, key, value, group_id, group_value, page):
        return await self.repository.get_logs(key, value, group_id, group_value, page)

    async def make_log(self, post_data):
        return await self.repository.make_log(post_data)

    async def get_keys(self):
        return await self.repository.get_keys()

    async def get_values(self, key):
        return await self.repository.get_values(key)

    async def get_metrics(self, key):
        return await self.repository.get_metrics(key)
