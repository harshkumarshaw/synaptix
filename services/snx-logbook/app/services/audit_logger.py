import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from packages.shared.logging import get_logger

logger = get_logger(__name__)


async def write_audit_log(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    actor_user_id: uuid.UUID | None,
    action: str,
    resource_type: str,
    resource_id: uuid.UUID,
    old_values: dict[str, Any] | None = None,
    new_values: dict[str, Any] | None = None,
    metadata_attrs: dict[str, Any] | None = None,
) -> None:
    import json

    stmt = text("""
        INSERT INTO audit_log (
            tenant_id, actor_user_id, action, resource_type, resource_id,
            old_values, new_values, metadata
        ) VALUES (
            :tenant_id, :actor_user_id, :action, :resource_type, :resource_id,
            :old_values, :new_values, :metadata
        )
        """)

    try:
        await db.execute(
            stmt,
            {
                "tenant_id": tenant_id,
                "actor_user_id": actor_user_id,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "old_values": json.dumps(old_values) if old_values else None,
                "new_values": json.dumps(new_values) if new_values else None,
                "metadata": json.dumps(metadata_attrs) if metadata_attrs else "{}",
            },
        )
    except Exception as e:
        logger.error(
            "Failed to write to audit_log table",
            extra={"action": action, "resource_id": str(resource_id), "error": str(e)},
        )
