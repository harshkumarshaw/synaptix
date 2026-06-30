import uuid

from app.models.logbook_phase2 import DoapSessionRecord, LogbookEntry
from app.models.stubs import WorkflowInstance
from app.schemas.doap import DoapSessionCreate
from app.services.doap_service import DoapService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class TestDoapWorkflows:
    """Integration tests for DOAP cross-module workflows (logbook, remediation, assets)."""

    async def test_doap_006_remediation_workflow_created(self, test_db_session: AsyncSession):
        """
        Test ID: DOAP-006
        Verifies: Remediation workflow auto-created on Re decision.
        """
        tenant_id = uuid.uuid4()
        user_id = uuid.uuid4()
        student_id = uuid.uuid4()
        session_id = uuid.uuid4()
        faculty_id = uuid.uuid4()

        service = DoapService(db=test_db_session)

        data = DoapSessionCreate(
            student_id=student_id,
            session_id=session_id,
            competency_code="AN1.1",
            nmc_level="P",
            is_core=True,
            stage="D",
            rating="B",
            attempt_type="F",
            faculty_decision="Re",  # Remediate decision!
            faculty_id=faculty_id,
        )

        result = await service.submit_doap_session(
            tenant_id=tenant_id,
            user_id=user_id,
            data=data,
        )

        # Assert workflow was created in DB
        workflows_res = await test_db_session.execute(
            select(WorkflowInstance).where(
                WorkflowInstance.entity_type == "doap_session_record",
                WorkflowInstance.entity_id == result.id,
            )
        )
        workflow = workflows_res.scalar_one_or_none()
        assert workflow is not None
        assert workflow.workflow_definition_code == "doap_remediation"
        assert workflow.status == "initiated"

    async def test_doap_007_evidence_asset_ids_linked(self, test_db_session: AsyncSession):
        """
        Test ID: DOAP-007
        Verifies: Evidence asset IDs are linked correctly.
        """
        tenant_id = uuid.uuid4()
        user_id = uuid.uuid4()
        student_id = uuid.uuid4()
        session_id = uuid.uuid4()
        faculty_id = uuid.uuid4()
        asset_ids = [uuid.uuid4(), uuid.uuid4()]

        service = DoapService(db=test_db_session)

        data = DoapSessionCreate(
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
            evidence_asset_ids=asset_ids,
        )

        result = await service.submit_doap_session(
            tenant_id=tenant_id,
            user_id=user_id,
            data=data,
        )

        # Fetch and verify
        db_records_res = await test_db_session.execute(
            select(DoapSessionRecord).where(DoapSessionRecord.id == result.id)
        )
        db_record = db_records_res.scalar_one_or_none()
        assert db_record is not None
        assert [uuid.UUID(uid) for uid in db_record.evidence_asset_ids] == asset_ids

    async def test_doap_008_auto_creation_of_logbook_entry(self, test_db_session: AsyncSession):
        """
        Test ID: DOAP-008
        Verifies: Auto-creation of logbook_entries on every DOAP record.
        """
        tenant_id = uuid.uuid4()
        user_id = uuid.uuid4()
        student_id = uuid.uuid4()
        session_id = uuid.uuid4()
        faculty_id = uuid.uuid4()

        service = DoapService(db=test_db_session)

        data = DoapSessionCreate(
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

        await service.submit_doap_session(
            tenant_id=tenant_id,
            user_id=user_id,
            data=data,
        )

        # Assert LogbookEntry was created
        db_entries_res = await test_db_session.execute(
            select(LogbookEntry).where(
                LogbookEntry.student_id == student_id,
                LogbookEntry.competency_code == "AN1.1",
            )
        )
        db_entry = db_entries_res.scalar_one_or_none()
        assert db_entry is not None
        assert db_entry.faculty_decision == "C"

    async def test_doap_e002_re_decision_with_no_active_remediation(
        self, test_db_session: AsyncSession
    ):
        """
        Test ID: DOAP-E002
        Verifies: Faculty decision Re with no active remediation programme is handled gracefully.
        """
        tenant_id = uuid.uuid4()
        user_id = uuid.uuid4()
        student_id = uuid.uuid4()
        session_id = uuid.uuid4()
        faculty_id = uuid.uuid4()

        service = DoapService(db=test_db_session)

        data = DoapSessionCreate(
            student_id=student_id,
            session_id=session_id,
            competency_code="AN1.1",
            nmc_level="P",
            is_core=True,
            stage="D",
            rating="B",
            attempt_type="F",
            faculty_decision="Re",  # Remediate decision
            faculty_id=faculty_id,
        )

        # Should succeed without failing on remediation workflow initiation
        result = await service.submit_doap_session(
            tenant_id=tenant_id,
            user_id=user_id,
            data=data,
        )
        assert result.faculty_decision == "Re"
