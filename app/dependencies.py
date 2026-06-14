from functools import lru_cache
from email.utils import parsedate_to_datetime
from pathlib import Path
import pandas as pd
from app.config import settings
from app.services.llm import AzureOpenAIProvider 
from app.services import news, tts, audio_storage
from app.services import knowledge_base

import asyncio
import yaml
from datetime import datetime, timedelta, timezone
import aiohttp
import feedparser

@lru_cache
def get_heavy_llm() -> AzureOpenAIProvider:
    resource_endpoint = settings.azure_resource_endpoint + ".services.ai.azure.com/openai/v1"
    return AzureOpenAIProvider(settings.azure_openai_api_key, resource_endpoint, "gpt-4.1", temperature=0)

@lru_cache
def get_max_llm() -> AzureOpenAIProvider:
    resource_endpoint = settings.azure_resource_endpoint + ".services.ai.azure.com/openai/v1"
    return AzureOpenAIProvider(settings.azure_openai_api_key, resource_endpoint, "gpt-5.1", reasoning_effort="medium")

@lru_cache
def get_kb_client():
    return knowledge_base.Neo4jKnowledgeBase(
        uri=settings.kb_uri,
        user=settings.kb_username,
        password=settings.kb_password
    )

@lru_cache
def get_storage() -> audio_storage.CloudinaryStorage:
    return audio_storage.CloudinaryStorage(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
    )


def get_tts():
    endpoint  =settings.azure_resource_endpoint + ".cognitiveservices.azure.com/"
    return tts.AzureTTSProvider(api_key=settings.azure_openai_api_key,
                                endpoint=endpoint)

def load_instruction(path: str, **kwargs) -> str:
    """Read a prompt template from a file and format it with provided keyword arguments."""
    template = Path(path).read_text()
    if len(kwargs) > 0:
        return template.format(**kwargs)
    else:
        return template
    
def load_config(path: str) -> dict:
    """Read a YAML file from the given path and return the parsed content."""
    with open(path, 'r') as file:
        return yaml.safe_load(file)


@lru_cache
def get_rss_data() -> pd.DataFrame:
    return pd.read_csv("data/rss_feeds.csv")


def parse_date(date_str: str) -> datetime:
    """Parse both RFC 2822 and ISO 8601 date formats."""
    try:
        # RFC 2822: "Thu, 09 May 2026 18:47:00 +0000"
        dt = parsedate_to_datetime(date_str)
    except (ValueError, TypeError):
        # ISO 8601: "2026-05-09T18:47:00Z" or "2026-05-09T18:47:00+00:00"
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    
    # Ensure timezone aware
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt



async def fetch_recent_news(
    feed_url: str,
    hours: int = 24,
    timeout: int = 10,
) -> tuple[list | str, bool]:

    headers = {"User-Agent": "Mozilla/5.0 (compatible; TheDebrief/1.0)"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                feed_url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as response:
                response.raise_for_status()
                content = await response.read()
    except (asyncio.TimeoutError, TimeoutError) as exc:
        return f"[WARN] Timed out fetching feed {feed_url}: {exc}, try another feed", False
    except aiohttp.ClientError as exc:
        return f"[WARN] Failed to fetch feed {feed_url}: {exc}, try another feed", False

    feed = await asyncio.get_event_loop().run_in_executor(
        None, feedparser.parse, content
    )

    if feed.bozo and not feed.entries:
        return f"[WARN] Feed parse issue for {feed_url}: {feed.bozo_exception}, try another feed", False

    if len(feed.entries) == 0:
        return f"No article found for {feed_url}: {feed.bozo_exception}, try another feed", False
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    recent = []

    for entry in feed.entries:
        try:
            date_str = entry.get("published") or entry.get("updated")
            pub_date = None

            if date_str:
                pub_date = parse_date(date_str)
            else:
                parsed = entry.get("published_parsed") or entry.get("updated_parsed")
                if parsed:
                    pub_date = datetime(*parsed[:6], tzinfo=timezone.utc)

            if pub_date is None or pub_date < cutoff:
                continue

            recent.append(
                {
                    "title": entry.get("title", "No title"),
                    "summary": entry.get("summary", ""),
                    "link": entry.get("link", ""),
                    "published": pub_date.isoformat(),
                }
            )
        except Exception:
            continue

    return recent, True

@lru_cache
def get_article_parser():
    return news.News4k()
