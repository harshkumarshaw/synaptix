import asyncio
import datetime
import os
import uuid
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

# Import the models from logbook service
from app.models.electives import (
    Elective,
    StudentElectivePreference,
)

TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
CURRICULUM_ID = uuid.UUID("9f9d5554-7909-4bdf-bb7e-0789dc5706e5")  # NMC CBME 2023

async def main():
    database_url = os.environ.get(
        "SNX_DATABASE_URL",
        "postgresql+asyncpg://snx:snx_dev_pass@localhost:5435/synaptix_dev",
    )
    print(f"Connecting to database: {database_url}")
    engine = create_async_engine(database_url, poolclass=NullPool)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # Disable foreign key triggers for seeding (single transaction)
        await session.execute(text("SET session_replication_role = 'replica'"))

        # Step 1: Clean up electives tables
        await session.execute(
            text(
                "TRUNCATE TABLE student_elective_preferences, elective_allocations, electives, elective_allocation_runs CASCADE"
            )
        )

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

        # Step 3: Seed preferences for the 3 students in the database
        student_uuids = [
            uuid.UUID("30000000-0000-0000-0000-000000000011"),
            uuid.UUID("30000000-0000-0000-0000-000000000012"),
            uuid.UUID("ef200d03-5bee-4541-be02-9a15dbbb0bc8"),
        ]

        base_time = datetime.datetime(2026, 6, 30, 9, 0, 0, tzinfo=datetime.UTC)
        elective_map = {"ELEC-A": sa_id_a, "ELEC-B": sa_id_b, "ELEC-C": sa_id_c}

        prefs_data = [
            [("ELEC-A", 1), ("ELEC-B", 2)],
            [("ELEC-B", 1), ("ELEC-C", 2)],
            [("ELEC-C", 1), ("ELEC-A", 2)],
        ]

        for i, s_uuid in enumerate(student_uuids):
            for el_code, rank in prefs_data[i]:
                pref = StudentElectivePreference(
                    id=uuid.uuid4(),
                    tenant_id=TENANT_ID,
                    student_id=s_uuid,
                    elective_id=elective_map[el_code],
                    block="Block 1",
                    rank_position=rank,
                    submitted_at=base_time + datetime.timedelta(seconds=i * 30),
                )
                session.add(pref)

        await session.commit()
        print("Successfully seeded electives and student preferences in the database!")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
