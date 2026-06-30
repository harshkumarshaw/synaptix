import uuid

import pytest
from app.schemas.doap import DoapSessionCreate
from app.services.doap_service import DoapService, DoapServiceError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession


class TestDoapNmcCompliance:
    """NMC Regulation compliance tests for DOAP framework (GMER 2019 / CBME 2019)."""

    async def test_doap_nmc_001_stage_progression_enforced(self, test_db_session: AsyncSession):
        """
        Test ID: DOAP-NMC-001
        Verifies: Stage progression D->O->A->P enforced (no skipping).
        """
        tenant_id = uuid.uuid4()
        user_id = uuid.uuid4()
        student_id = uuid.uuid4()
        session_id = uuid.uuid4()
        faculty_id = uuid.uuid4()

        service = DoapService(db=test_db_session)

        # Try O before D certified
        data_o = DoapSessionCreate(
            student_id=student_id,
            session_id=session_id,
            competency_code="AN1.1",
            nmc_level="P",
            is_core=True,
            stage="O",
            rating="M",
            attempt_type="F",
            faculty_decision="C",
            faculty_id=faculty_id,
        )
        with pytest.raises(DoapServiceError) as exc_info:
            await service.submit_doap_session(tenant_id=tenant_id, user_id=user_id, data=data_o)
        assert exc_info.value.code == "DOAP-001"
        assert "D" in exc_info.value.message

        # Certify D
        data_d = DoapSessionCreate(
            student_id=student_id,
            session_id=session_id,
            competency_code="AN1.1",
            nmc_level="P",
            is_core=True,
            stage="D",
            rating="M",
            attempt_type="F",
            faculty_decision="C",
            faculty_id=faculty_id,
        )
        await service.submit_doap_session(tenant_id=tenant_id, user_id=user_id, data=data_d)

        # Now O succeeds
        res_o = await service.submit_doap_session(tenant_id=tenant_id, user_id=user_id, data=data_o)
        assert res_o.stage == "O"

    def test_doap_nmc_002_faculty_decision_required(self):
        """
        Test ID: DOAP-NMC-002
        Verifies: Faculty decision required for every record (cannot be null/missing).
        """
        student_id = uuid.uuid4()
        session_id = uuid.uuid4()
        faculty_id = uuid.uuid4()

        # Try creating without faculty_decision
        with pytest.raises(ValidationError):
            DoapSessionCreate(
                student_id=student_id,
                session_id=session_id,
                competency_code="AN1.1",
                nmc_level="P",
                is_core=True,
                stage="D",
                rating="M",
                attempt_type="F",
                faculty_id=faculty_id,
                # faculty_decision omitted
            )
