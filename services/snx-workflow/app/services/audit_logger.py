import uuid
from typing import Any, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from packages.shared.logging import get_logger

logger = get_logger(__name__)


async def write_audit_log(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    actor_user_id: Optional[uuid.UUID],
    action: str,
    resource_type: str,
    resource_id: uuid.UUID,
    old_values: Optional[dict[str, Any]] = None,
    new_values: Optional[dict[str, Any]] = None,
    metadata_attrs: Optional[dict[str, Any]] = None,
) -> None:
    # Use raw SQL insert because audit_log model is not declared in ORM, 
    # and it is partitioned which raw insert handles perfectly.
    import json
    
    stmt = text(
        """
        INSERT INTO audit_log (
            tenant_id, actor_user_id, action, resource_type, resource_id, 
            old_values, new_values, metadata
        ) VALUES (
            :tenant_id, :actor_user_id, :action, :resource_type, :resource_id,
            :old_values, :new_values, :metadata
        )
        """
    )
    
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
        # Never fail main operations if audit log fails, but log it.
