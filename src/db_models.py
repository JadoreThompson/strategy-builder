from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import (
    UUID,
    DateTime,
    Float,
    String,
    ForeignKey,
    Integer,
    Enum as SQLAlchemyEnum,
)
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship

from utils import get_datetime
from core.enums import TaskStatus


class Base(DeclarativeBase): ...


class Users(Base):
    __tablename__ = "users"

    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)

    strategies: Mapped[list["Strategies"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    positions: Mapped[list["Positions"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Ticks(Base):
    __tablename__ = "ticks"

    tick_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    instrument: Mapped[str] = mapped_column(String, nullable=False)
    last_price: Mapped[Decimal] = mapped_column(Float, nullable=False)
    bid_price: Mapped[Decimal] = mapped_column(Float, nullable=False)
    ask_price: Mapped[Decimal] = mapped_column(Float, nullable=False)
    time: Mapped[int] = mapped_column(Integer, nullable=False)  # Unix Epoch seconds


class Strategies(Base):
    __tablename__ = "strategies"

    strategy_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=get_datetime
    )

    # Relationships
    user: Mapped["Users"] = relationship(back_populates="strategies")
    versions: Mapped[list["StrategyVersions"]] = relationship(
        back_populates="strategy", cascade="all, delete-orphan"
    )


class StrategyVersions(Base):
    __tablename__ = "strategy_versions"

    version_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    strategy_id: Mapped[UUID] = mapped_column(
        ForeignKey("strategies.strategy_id"), nullable=False
    )
    code: Mapped[str] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(
        String, nullable=False, default=TaskStatus.PENDING.value
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=get_datetime
    )

    # Relationship
    strategy: Mapped["Strategies"] = relationship(back_populates="versions")
    positions: Mapped[list["Positions"]] = relationship(
        back_populates="strategy_version", cascade="all, delete-orphan"
    )
    backtests: Mapped[list["Backtests"]] = relationship(
        back_populates="strategy_version", cascade="all, delete-orphan"
    )


class Positions(Base):
    __tablename__ = "positions"

    position_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    version_id: Mapped[UUID] = mapped_column(
        ForeignKey("strategy_versions.version_id"), nullable=False
    )
    size: Mapped[Decimal] = mapped_column(Float, nullable=False)
    entry_price: Mapped[Decimal] = mapped_column(Float, nullable=False)
    timestamp: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # Unix Epoch seconds

    # Relationships
    user: Mapped["Users"] = relationship(back_populates="positions")
    strategy_version: Mapped["StrategyVersions"] = relationship(
        back_populates="positions"
    )


class Backtests(Base):
    __tablename__ = "backtests"

    backtest_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    version_id: Mapped[UUID] = mapped_column(
        ForeignKey("strategy_versions.version_id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=get_datetime
    )
    status: Mapped[str] = mapped_column(
        String, nullable=False, default=TaskStatus.PENDING.value
    )
    # Result fields
    total_pnl: Mapped[Decimal] = mapped_column(Float, nullable=True)
    starting_balance: Mapped[Decimal] = mapped_column(Float, nullable=True)
    end_balance: Mapped[Decimal] = mapped_column(Float, nullable=True)
    total_trades: Mapped[int] = mapped_column(Integer, nullable=True)
    win_rate: Mapped[float] = mapped_column(Float, nullable=True)

    # Relationship
    strategy_version: Mapped["StrategyVersions"] = relationship(
        back_populates="backtests"
    )
