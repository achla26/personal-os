from datetime import datetime
from typing import Any

from sqlalchemy.orm import Mapped, mapped_column
import uuid
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, Uuid, func

from app.infra.models import Base
 

class RefreshToken(Base):
    __tablename__ ="refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid7)

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
   
    token_hash: Mapped[str] = mapped_column(String, nullable=False)

    revoked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    created_at: Mapped[datetime|None] = mapped_column(
            DateTime(timezone=True),
            server_default=func.now()
    )

    