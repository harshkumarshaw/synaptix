"""Manually trace ADR-034 worked example against current implementation."""
import asyncio
import os
import uuid
import datetime
from datetime import timezone
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool

# Import the service and models
from app.services.elective_service import ElectiveService
from app.schemas.electives import AllocationRunRequest
from app.models.electives import Elective, StudentElectivePreference, ElectiveAllocation, ElectiveAllocationRun

# Tenant and curriculum IDs
TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
CURRICULUM_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")

async def main():
    database_url = os.environ.get(
        "SNX_DATABASE_URL",
        "postgresql+asyncpg://snx_test:snx_test_pass@localhost:5436/synaptix_test"
    )
    engine = create_async_engine(database_url, poolclass=NullPool)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # Disable foreign key triggers for seeding (single transaction)
        await session.execute(text("SET session_replication_role = 'replica'"))
        
        # Step 1: Clean up electives tables
        await session.execute(text("TRUNCATE TABLE student_elective_preferences, elective_allocations, electives, elective_allocation_runs CASCADE"))

        # Step 2: Seed Electives (A, B, C) with capacity 4 each
        sa_id_a = uuid.UUID("a0000000-0000-0000-0000-000000000000")
        sa_id_b = uuid.UUID("b0000000-0000-0000-0000-000000000000")
        sa_id_c = uuid.UUID("c0000000-0000-0000-0000-000000000000")

        elective_a = Elective(
            id=sa_id_a,
            tenant_id=TENANT_ID,
            curriculum_id=CURRICULUM_ID,
            code="ELEC-A",
            title="Elective A",
            block="Block 1",
            elective_type="clinical",
            capacity=4,
        )
        elective_b = Elective(
            id=sa_id_b,
            tenant_id=TENANT_ID,
            curriculum_id=CURRICULUM_ID,
            code="ELEC-B",
            title="Elective B",
            block="Block 1",
            elective_type="clinical",
            capacity=4,
        )
        elective_c = Elective(
            id=sa_id_c,
            tenant_id=TENANT_ID,
            curriculum_id=CURRICULUM_ID,
            code="ELEC-C",
            title="Elective C",
            block="Block 1",
            elective_type="clinical",
            capacity=4,
        )
        session.add_all([elective_a, elective_b, elective_c])

        # Seed students with preferences per ADR-034
        students = {
            f"S{i}": uuid.UUID(f"{i:08x}-0000-0000-0000-000000000000")
            for i in range(1, 11)
        }

        # Submission times
        base_time = datetime.datetime(2026, 6, 30, 9, 0, 0, tzinfo=timezone.utc)
        sub_times = {
            "S1": base_time,
            "S2": base_time + datetime.timedelta(seconds=30),
            "S3": base_time + datetime.timedelta(seconds=60),
            "S4": base_time + datetime.timedelta(seconds=90),
            "S5": base_time + datetime.timedelta(hours=1, seconds=1),
            "S6": base_time + datetime.timedelta(minutes=55),
            "S7": base_time + datetime.timedelta(minutes=56),
            "S8": base_time + datetime.timedelta(minutes=57),
            "S9": base_time + datetime.timedelta(minutes=58),
            "S10": base_time + datetime.timedelta(minutes=59),
        }

        # Preferences
        prefs_data = {
            "S1": [("ELEC-A", 1), ("ELEC-B", 2)],
            "S2": [("ELEC-A", 1), ("ELEC-B", 2)],
            "S3": [("ELEC-A", 1), ("ELEC-C", 2)],
            "S4": [("ELEC-A", 1), ("ELEC-C", 2)],
            "S5": [("ELEC-A", 1), ("ELEC-B", 2)],
            "S6": [("ELEC-B", 1), ("ELEC-A", 2)],
            "S7": [("ELEC-B", 1), ("ELEC-A", 2)],
            "S8": [("ELEC-B", 1), ("ELEC-C", 2)],
            "S9": [("ELEC-C", 1), ("ELEC-A", 2)],
            "S10": [("ELEC-C", 1), ("ELEC-B", 2)],
        }

        elective_map = {"ELEC-A": sa_id_a, "ELEC-B": sa_id_b, "ELEC-C": sa_id_c}

        for sname, s_uuid in students.items():
            for el_code, rank in prefs_data[sname]:
                pref = StudentElectivePreference(
                    id=uuid.uuid4(),
                    tenant_id=TENANT_ID,
                    student_id=s_uuid,
                    elective_id=elective_map[el_code],
                    block="Block 1",
                    rank_position=rank,
                    submitted_at=sub_times[sname]
                )
                session.add(pref)
        await session.flush()
        # Step 3: Run Ranked Allocation (dry_run=False so we can query allocations table)
        service = ElectiveService(db=session)
        payload = AllocationRunRequest(
            curriculum_id=CURRICULUM_ID,
            block="Block 1",
            algorithm="ranked",
            dry_run=False,
            force_reallocate=None,
        )

        try:
            result = await service.run_allocation(
                tenant_id=TENANT_ID,
                request=payload,
                actor_id=uuid.uuid4(),
            )
        except Exception as e:
            print("ERROR OCCURRED:", e)
            import traceback
            traceback.print_exc()
            return

        # Query the newly created allocations
        alloc_result = await session.execute(
            select(ElectiveAllocation, Elective.code)
            .join(Elective, Elective.id == ElectiveAllocation.elective_id)
            .where(ElectiveAllocation.tenant_id == TENANT_ID)
        )
        allocations_list = alloc_result.all()

        # Build reverse student lookup mapping
        student_id_to_name = {v: k for k, v in students.items()}

        actual = {}
        for alloc, el_code in allocations_list:
            s_name = student_id_to_name.get(alloc.student_id, str(alloc.student_id))
            el_letter = el_code.split("-")[-1]  # 'ELEC-A' -> 'A'
            actual.setdefault(el_letter, set()).add(s_name)

        # Expected allocations per ADR-034
        expected = {
            "A": {"S1", "S2", "S3", "S4"},
            "B": {"S5", "S6", "S7", "S8"},
            "C": {"S9", "S10"},
        }

        print("# ADR-034 Worked Example Trace Results")
        print("\n## Verification Status")
        
        all_passed = True
        for code in ["A", "B", "C"]:
            match = actual.get(code, set()) == expected[code]
            status = "PASS" if match else "FAIL"
            if not match:
                all_passed = False
            print(f"- **Elective {code}**: expected {sorted(list(expected[code]))}, got {sorted(list(actual.get(code, set())))} -> **{status}**")

        print(f"\n- **Total allocated**: {result.total_allocated} (expected 10)")
        print(f"- **Unallocated pending review**: {result.total_unallocated_pending_review} (expected 0)")
        print(f"- **Allocations by rank**: {result.allocations_by_rank}")
        print(f"- **Overall status**: **{'PASS' if all_passed else 'FAIL'}**")

        # Cleanup table after verification
        await session.execute(text("TRUNCATE TABLE student_elective_preferences, elective_allocations, electives, elective_allocation_runs CASCADE"))
        await session.commit()

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
