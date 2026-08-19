from datetime import datetime
from typing import Any

from sqlalchemy.orm import Mapped, mapped_column
import uuid
from sqlalchemy import DateTime, String,Uuid,  func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict

from app.infra.models import Base


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

