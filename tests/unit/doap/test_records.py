import uuid

from app.models.logbook_phase2 import DoapSessionRecord, LogbookEntry
from app.schemas.doap import DoapSessionCreate
from app.services.doap_service import DoapService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class TestDoapRecords:
    """Tests for DOAP session record creation and retrieval."""

    async def test_doap_001_d_stage_creates_record_and_logbook(self, test_db_session: AsyncSession):
        """
        Test ID: DOAP-001
        Verifies: Record D stage with C decision creates record and logbook entry.
        """
        tenant_id = uuid.uuid4()
        user_id = uuid.uuid4()
        student_id = uuid.uuid4()
        session_id = uuid.uuid4()
        faculty_id = uuid.uuid4()

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
            notes="Excellent demonstration",
        )

        service = DoapService(db=test_db_session)
        result = await service.submit_doap_session(
            tenant_id=tenant_id,
            user_id=user_id,
            data=data,
        )

        # Assert returned schema matches
        assert result.stage == "D"
        assert result.rating == "M"
        assert result.faculty_decision == "C"
        assert result.notes == "Excellent demonstration"
        assert result.student_id == student_id

        # Verify DOAP record was inserted in DB
        db_records_res = await test_db_session.execute(
            select(DoapSessionRecord).where(DoapSessionRecord.id == result.id)
        )
        db_record = db_records_res.scalar_one_or_none()
        assert db_record is not None
        assert db_record.competency_code == "AN1.1"

        # Verify LogbookEntry was auto-created in DB
        db_entries_res = await test_db_session.execute(
            select(LogbookEntry).where(
                LogbookEntry.student_id == student_id,
                LogbookEntry.competency_code == "AN1.1",
            )
        )
        db_entry = db_entries_res.scalar_one_or_none()
        assert db_entry is not None
        assert db_entry.subject_code == "ANAT"
        assert db_entry.rating == "M"
        assert db_entry.faculty_decision == "C"
        assert db_entry.status == "approved"

    async def test_doap_005_re_attempt_after_r_decision(self, test_db_session: AsyncSession):
        """
        Test ID: DOAP-005
        Verifies: Re-attempt after R decision (attempt_type=R, same stage).
        """
        tenant_id = uuid.uuid4()
        user_id = uuid.uuid4()
        student_id = uuid.uuid4()
        session_id = uuid.uuid4()
        faculty_id = uuid.uuid4()

        service = DoapService(db=test_db_session)

        # First attempt: Rating B, Decision R (repeat required)
        data1 = DoapSessionCreate(
            student_id=student_id,
            session_id=session_id,
            competency_code="AN1.1",
            nmc_level="P",
            is_core=True,
            stage="D",
            rating="B",
            attempt_type="F",
            faculty_decision="R",
            faculty_id=faculty_id,
        )
        res1 = await service.submit_doap_session(tenant_id=tenant_id, user_id=user_id, data=data1)
        assert res1.faculty_decision == "R"

        # Second attempt: same stage D, attempt_type R (repeat), decision C (certified!)
        data2 = DoapSessionCreate(
            student_id=student_id,
            session_id=session_id,
            competency_code="AN1.1",
            nmc_level="P",
            is_core=True,
            stage="D",
            rating="M",
            attempt_type="R",
            faculty_decision="C",
            faculty_id=faculty_id,
        )
        res2 = await service.submit_doap_session(tenant_id=tenant_id, user_id=user_id, data=data2)
        assert res2.faculty_decision == "C"

        # Verify both records exist in DB
        db_records_res = await test_db_session.execute(
            select(DoapSessionRecord).where(
                DoapSessionRecord.student_id == student_id,
                DoapSessionRecord.competency_code == "AN1.1",
            )
        )
        db_records = db_records_res.scalars().all()
        assert len(db_records) == 2
