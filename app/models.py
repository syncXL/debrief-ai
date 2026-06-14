import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Text, DateTime, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship
from app.config import settings

Base = declarative_base()

class Episode(Base):
    __tablename__ = "episode"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String, nullable=False,index=True)
    preference = Column(Text, nullable=True)
    hours = Column(Integer, nullable=True)
    n_story = Column(Integer, nullable=True)
    status = Column(String, default="pending")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    segments = relationship("Segment", back_populates="episode", order_by="Segment.pos")


class Segment(Base):
    __tablename__ = "segment"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    episode_id = Column(UUID(as_uuid=True), ForeignKey("episode.id"), nullable=False)
    pos = Column(Integer, nullable=False)
    type = Column(String, nullable=False)
    show_id = Column(String, nullable=False)
    transcript = Column(Text, nullable=True)
    audio_url = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    episode = relationship("Episode", back_populates="segments")




engine = create_async_engine(settings.database_url, echo=False)
SessionLocal = async_sessionmaker(bind=engine, autocommit=False, autoflush=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)