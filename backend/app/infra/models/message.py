from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
import uuid
from sqlalchemy import DateTime, ForeignKey,  String, Text, Uuid, func
 

from app.infra.models import Base
 

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, 
        default=uuid.uuid7
    )

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    role: Mapped[str] = mapped_column(String, nullable=False)

    content: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime|None] = mapped_column(
            DateTime(timezone=True),
            server_default=func.now()
    )
