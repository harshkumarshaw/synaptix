"""MDM Configuration Service — reads tenant-scoped config from mdm_configs table."""

from decimal import Decimal
from typing import Any, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class MdmConfigService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, tenant_id: UUID, key: str, default: Any = None) -> Any:
        """Get a config value by key. Returns default if not found."""
        from packages.shared.db.models import MdmConfig  # avoid circular

        result = await self.session.scalar(
            select(MdmConfig).where(
                MdmConfig.tenant_id == tenant_id,
                MdmConfig.config_key == key,
            )
        )
        if result and result.config_value is not None:
            return result.config_value
        return default

    async def get_subject_code_mapping(self, tenant_id: UUID) -> dict[str, str]:
        """
        Get competency prefix → subject_code mapping.
        Replaces hardcoded D7 mapping in DoapService.
        """
        mapping = await self.get(
            tenant_id,
            "competency.prefix_to_subject_code",
            default=self._default_subject_mapping(),
        )
        return mapping

    async def get_ia_config(
        self, tenant_id: UUID, subject_code: str, professional_phase: str
    ) -> tuple[Decimal, Decimal]:
        """
        Get IA weight percentage and subject IA max marks.
        Replaces hardcoded D8 fallbacks in LogbookService.
        """
        config = await self.get(
            tenant_id,
            f"ia_config.{subject_code}.{professional_phase}",
            default=None,
        )
        if config:
            return (
                Decimal(str(config.get("ia_weight_pct", 10.0))),
                Decimal(str(config.get("subject_ia_max", 40.0))),
            )

        # Try subject-level default (without phase)
        config = await self.get(
            tenant_id,
            f"ia_config.{subject_code}",
            default=None,
        )
        if config:
            return (
                Decimal(str(config.get("ia_weight_pct", 10.0))),
                Decimal(str(config.get("subject_ia_max", 40.0))),
            )

        # Global default
        return Decimal("10.0"), Decimal("40.0")

    async def get_attendance_thresholds(self, tenant_id: UUID, attendance_category: str) -> Decimal:
        """Get attendance threshold for a category."""
        defaults = {
            "theory": Decimal("75.00"),
            "practical": Decimal("80.00"),
            "clinical": Decimal("80.00"),
            "doap": Decimal("80.00"),
            "ece": Decimal("80.00"),
            "aetcom": Decimal("75.00"),
            "foundation_course": Decimal("75.00"),
            "elective": Decimal("75.00"),
        }
        config = await self.get(
            tenant_id,
            f"attendance.threshold.{attendance_category}",
            default=None,
        )
        if config:
            return Decimal(str(config))
        return defaults.get(attendance_category, Decimal("75.00"))

    @staticmethod
    def _default_subject_mapping() -> dict[str, str]:
        """NMC CBME 2019 standard prefix mapping."""
        return {
            "AN": "ANAT",
            "PY": "PHYS",
            "BI": "BIOC",
            "MI": "MICR",
            "PA": "PATH",
            "PH": "PHAR",
            "FM": "FMED",
            "CM": "CMED",
            "GM": "GMED",
            "GS": "GSUR",
            "OG": "OBGY",
            "PE": "PEDI",
            "OR": "ORTH",
            "OP": "OPHT",
            "EN": "ENT",
            "DE": "DERM",
            "PS": "PSYC",
            "RD": "RADI",
            "AS": "ANES",
        }
