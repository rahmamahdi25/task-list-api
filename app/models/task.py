
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import db


class Task(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(),
        nullable=True,
        default=None
    )
    goal_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("goal.id"), nullable=True
    )
    goal: Mapped[Optional["Goal"]] = relationship(back_populates="tasks")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "goal_id": self.goal_id,
            "title": self.title,
            "description": self.description,
            "is_complete": self.completed_at is not None
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            title=data["title"],
            description=data["description"],
            completed_at=None
        )

