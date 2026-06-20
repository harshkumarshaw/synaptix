from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column
from packages.shared.db.base import GlobalBase


class Tenant(GlobalBase):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(nullable=False)
    code: Mapped[str] = mapped_column(nullable=False)
    institution_type: Mapped[str] = mapped_column(nullable=False)
    regulatory_body: Mapped[str] = mapped_column(nullable=False)
