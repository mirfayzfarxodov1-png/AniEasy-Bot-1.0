from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str | None] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_active: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    favorites = relationship('Favorite', back_populates='user', cascade='all, delete-orphan')

class Anime(Base):
    __tablename__ = 'animes'
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500), index=True)
    alternate_title: Mapped[str | None] = mapped_column(String(500), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    poster: Mapped[str | None] = mapped_column(String(1000))
    genre: Mapped[str | None] = mapped_column(String(500), index=True)
    year: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(50), default='active')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    episodes = relationship('Episode', back_populates='anime', cascade='all, delete-orphan', order_by='Episode.episode_number')

class Episode(Base):
    __tablename__ = 'episodes'
    id: Mapped[int] = mapped_column(primary_key=True)
    anime_id: Mapped[int] = mapped_column(ForeignKey('animes.id', ondelete='CASCADE'), index=True)
    episode_number: Mapped[int] = mapped_column(Integer)
    telegram_file_id: Mapped[str] = mapped_column(String(1000))
    file_unique_id: Mapped[str | None] = mapped_column(String(500), index=True)
    caption: Mapped[str | None] = mapped_column(Text)
    views: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    anime = relationship('Anime', back_populates='episodes')
    __table_args__ = (UniqueConstraint('anime_id', 'episode_number', name='uq_episode_anime_number'), Index('ix_episode_anime_number', 'anime_id', 'episode_number'))

class Favorite(Base):
    __tablename__ = 'favorites'
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    anime_id: Mapped[int] = mapped_column(ForeignKey('animes.id', ondelete='CASCADE'), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user = relationship('User', back_populates='favorites')
    anime = relationship('Anime')

class WatchProgress(Base):
    __tablename__ = 'watch_progress'
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    anime_id: Mapped[int] = mapped_column(ForeignKey('animes.id', ondelete='CASCADE'), primary_key=True)
    episode_number: Mapped[int] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
