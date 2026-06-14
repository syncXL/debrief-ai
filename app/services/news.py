import abc
import asyncio
from newspaper import Article
import logging

logger = logging.getLogger(__name__)

class ArticleParser(abc.ABC):

    @abc.abstractmethod
    async def get_story(self, link: str) -> str:
        raise NotImplementedError


class News4k(ArticleParser):

    async def get_story(self, link: str) -> str:
        return await asyncio.to_thread(self._parse, link)

    def _parse(self, link: str) -> str:
        try:
            article = Article(link)
            article.download()
            article.parse()
            return article.text
        except Exception as e:
            logger.warning("Failed to parse article %s: %s", link, e)
            return ""  # return empty string, let the caller decide what to do