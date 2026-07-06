from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column

from packages.shared.db.base import GlobalBase


class Tenant(GlobalBase):
    """SQLAlchemy model for global tenants.

    Represents a tenant (institution/organization) in the multi-tenant system.
    This is a global table (no tenant_id foreign key) and is not subject to RLS.
    """

    __tablename__ = "tenants"

    code: Mapped[str] = mapped_column(unique=True, nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    institution_type: Mapped[str] = mapped_column(nullable=False)
    regulatory_body: Mapped[str] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")
    logo_url: Mapped[str | None] = mapped_column(nullable=True)
    primary_color: Mapped[str | None] = mapped_column(nullable=True)
    timezone: Mapped[str] = mapped_column(default="Asia/Kolkata", server_default="'Asia/Kolkata'")
