from datetime import datetime
from typing import Any

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import uuid
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, Uuid, desc, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ ="users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid7)

    name: Mapped[str] = mapped_column(String(50))

    email: Mapped[str] = mapped_column(String(100), unique=True)

    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),    # Database create time 
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),    
        onupdate=func.now(),          # On update automatically change
    )


class Item(Base):
    __tablename__ = "items"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, 
        default=uuid.uuid7
    )

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    item_type: Mapped[str] = mapped_column(String, nullable=False)

    title: Mapped[str] = mapped_column(String, nullable=False)

    body: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[str] = mapped_column(String, nullable=False, default="open")

    completed_at: Mapped[datetime] = mapped_column(
            DateTime(timezone=True),
            nullable=True
    )

    nag_policy: Mapped[str] = mapped_column(String, nullable=False, default="off")

    next_nag_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    nag_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    source: Mapped[str] = mapped_column(Text, nullable=False, default="chat")


    meta: Mapped[dict[str, Any]] = mapped_column(MutableDict.as_mutable(JSONB),nullable=False, default=dict, server_default=text("'{}'::jsonb"),)

    created_at: Mapped[datetime|None] = mapped_column(
            DateTime(timezone=True),
            server_default=func.now()
    )
    
    updated_at: Mapped[datetime| None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),    
        onupdate=func.now() 
    )


    __table_args__ = (
        Index(
            "ix_items_user_status_created_at",
            "user_id",
            "status",
            desc("created_at"),
        ),
        Index(
            "ix_items_user_type_created_at",
            "user_id",
            "item_type",
            desc("created_at"),
        ),
        Index(
            "ix_items_next_nag_open",
            "next_nag_at",
            postgresql_where=text("status = 'open' AND next_nag_at IS NOT NULL"),
        ),
    )
   