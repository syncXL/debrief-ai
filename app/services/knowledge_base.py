import abc
from neo4j import AsyncGraphDatabase


class KnowledgeBase(abc.ABC):
    @abc.abstractmethod
    async def execute_query(self, query: str) -> str:
        raise NotImplementedError
    
    @abc.abstractmethod
    async def get_labels(self) -> list:
        raise NotImplementedError
    


class Neo4jKnowledgeBase(KnowledgeBase):
    def __init__(self, uri: str, user: str, password: str):
        self._driver = AsyncGraphDatabase.driver(uri, auth=(user, password))

    async def execute_query(self, query: str) -> list:
        async with self._driver.session() as session:
            result = await session.run(query)
            return await result.data()

    async def get_labels(self) -> list:
        async with self._driver.session() as session:
            result = await session.run("CALL db.labels()")
            records = await result.data()
            return [r["label"] for r in records]

    async def close(self):
        await self._driver.close()