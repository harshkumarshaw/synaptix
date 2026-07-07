import asyncio
import os
import uuid
from datetime import datetime, time, UTC
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ.get(
    "SNX_DATABASE_URL", "postgresql+asyncpg://snx:snx_dev_pass@localhost:5435/synaptix_dev"
)

TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


async def seed_dashboard() -> None:
    print("Connecting to database to seed student data dynamically...")
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Fetch Student
        res = await session.execute(
            text("SELECT id, batch_id FROM students WHERE roll_number = 'JMN-2026-001' LIMIT 1")
        )
        row = res.fetchone()
        if not row:
            print("Error: Student JMN-2026-001 not found!")
            return
        student_id, batch_id = row[0], row[1]
        print(f"Found Student ID: {student_id}, Batch ID: {batch_id}")

        # Fetch Academic Year
        res = await session.execute(
            text("SELECT id FROM academic_years WHERE tenant_id = :tenant_id LIMIT 1"),
            {"tenant_id": TENANT_ID},
        )
        ay_id = res.scalar()
        if not ay_id:
            print("Error: Academic Year not found!")
            return
        print(f"Found Academic Year ID: {ay_id}")

        # Fetch Faculty
        res = await session.execute(text("SELECT id FROM faculty LIMIT 1"))
        faculty_id = res.scalar()
        if not faculty_id:
            print("Error: Faculty not found!")
            return
        print(f"Found Faculty ID: {faculty_id}")

        # Fetch Courses
        res = await session.execute(text("SELECT id, code FROM courses"))
        courses = {row[1]: row[0] for row in res.fetchall()}
        print(f"Found Courses: {courses}")

        anat_id = courses.get("ANAT-101")
        phys_id = courses.get("PHYS-101")
        bioc_id = courses.get("BIOC-101")

        # Clear old student-specific logs
        await session.execute(
            text("DELETE FROM attendance WHERE student_id = :id"), {"id": student_id}
        )
        await session.execute(
            text("DELETE FROM doap_session_records WHERE student_id = :id"), {"id": student_id}
        )
        await session.execute(
            text("DELETE FROM sessions WHERE tenant_id = :tenant_id"), {"tenant_id": TENANT_ID}
        )
        await session.execute(
            text(
                "DELETE FROM events WHERE tenant_id = :tenant_id AND description = 'Seeded Test Event'"
            ),
            {"tenant_id": TENANT_ID},
        )
        await session.execute(
            text("DELETE FROM attendance_summary WHERE student_id = :id"), {"id": student_id}
        )
        await session.execute(
            text("DELETE FROM logbook_entries WHERE student_id = :id"), {"id": student_id}
        )
        await session.commit()

        # Seed Attendance records for list view
        print("Seeding attendance records...")
        attendance_records = [
            (
                anat_id,
                "practical",
                "present",
                datetime(2026, 7, 1, 9, 0, tzinfo=UTC),
                "Anatomy Practical",
            ),
            (
                anat_id,
                "practical",
                "present",
                datetime(2026, 7, 2, 9, 0, tzinfo=UTC),
                "Anatomy Dissection",
            ),
            (
                anat_id,
                "practical",
                "absent",
                datetime(2026, 7, 3, 9, 0, tzinfo=UTC),
                "Anatomy Practical Lab",
            ),
            (
                anat_id,
                "practical",
                "present",
                datetime(2026, 7, 4, 9, 0, tzinfo=UTC),
                "Anatomy Lab Exam",
            ),
            (
                phys_id,
                "theory",
                "present",
                datetime(2026, 7, 1, 10, 0, tzinfo=UTC),
                "Physiology Lecture",
            ),
            (
                phys_id,
                "theory",
                "present",
                datetime(2026, 7, 2, 10, 0, tzinfo=UTC),
                "Cardiology Theory",
            ),
            (
                phys_id,
                "theory",
                "present",
                datetime(2026, 7, 3, 10, 0, tzinfo=UTC),
                "Physiology Seminar",
            ),
            (
                phys_id,
                "theory",
                "absent",
                datetime(2026, 7, 4, 10, 0, tzinfo=UTC),
                "Endocrine Lecture",
            ),
            (
                bioc_id,
                "theory",
                "present",
                datetime(2026, 7, 1, 11, 0, tzinfo=UTC),
                "Biochemistry Lecture",
            ),
            (
                bioc_id,
                "theory",
                "present",
                datetime(2026, 7, 2, 11, 0, tzinfo=UTC),
                "Enzymes Class",
            ),
            (
                bioc_id,
                "theory",
                "present",
                datetime(2026, 7, 3, 11, 0, tzinfo=UTC),
                "Biochemistry Practical Lecture",
            ),
            (
                bioc_id,
                "theory",
                "present",
                datetime(2026, 7, 4, 11, 0, tzinfo=UTC),
                "Lipid Metabolism Lecture",
            ),
        ]

        for course_id, category, status, marked_at, title in attendance_records:
            if not course_id:
                continue
            event_id = uuid.uuid4()

            # Insert event first
            await session.execute(
                text("""
                    INSERT INTO events (id, tenant_id, batch_id, academic_year_id, title, description, event_type, attendance_category, professional_phase, date, start_time, end_time, status)
                    VALUES (:id, :tenant_id, :batch_id, :ay_id, :title, 'Seeded Test Event', 'lecture', :category, 'Phase I', :date, :start, :end, 'conducted')
                """),
                {
                    "id": event_id,
                    "tenant_id": TENANT_ID,
                    "batch_id": batch_id,
                    "ay_id": ay_id,
                    "title": title,
                    "category": category,
                    "date": marked_at.date(),
                    "start": time(9, 0),
                    "end": time(10, 0),
                },
            )

            # Insert attendance mapping
            await session.execute(
                text("""
                    INSERT INTO attendance (id, tenant_id, student_id, event_id, status, attendance_category, professional_phase, method, marked_at)
                    VALUES (:id, :tenant_id, :student_id, :event_id, :status, :category, 'Phase I', 'manual', :marked_at)
                """),
                {
                    "id": uuid.uuid4(),
                    "tenant_id": TENANT_ID,
                    "student_id": student_id,
                    "event_id": event_id,
                    "status": status,
                    "category": category,
                    "marked_at": marked_at,
                },
            )

        # Seed Attendance Summary
        print("Seeding attendance summaries...")
        summaries = [
            (anat_id, "practical", 30, 26),
            (anat_id, "theory", 20, 18),
            (phys_id, "theory", 30, 24),
            (phys_id, "practical", 10, 9),
            (bioc_id, "theory", 30, 27),
            (bioc_id, "practical", 10, 8),
        ]
        for course_id, category, conducted, present in summaries:
            if not course_id:
                continue
            await session.execute(
                text("""
                    INSERT INTO attendance_summary (tenant_id, student_id, course_id, professional_phase, attendance_category, sessions_conducted, sessions_present, sessions_excused, sessions_official_duty, sessions_medical)
                    VALUES (:tenant_id, :student_id, :course_id, 'Phase I', :category, :conducted, :present, 0, 0, 0)
                """),
                {
                    "tenant_id": TENANT_ID,
                    "student_id": student_id,
                    "course_id": course_id,
                    "category": category,
                    "conducted": conducted,
                    "present": present,
                },
            )

        # Seed DOAP records
        print("Seeding DOAP session records...")
        doap_records = [
            ("AN-1.1", "D", "M", "C"),
            ("AN-1.1", "O", "M", "C"),
            ("AN-1.1", "A", "M", "C"),
            ("AN-1.1", "P", "E", "C"),
            ("AN-2.1", "D", "M", "C"),
            ("AN-2.1", "O", "M", "C"),
        ]
        for comp, stage, rating, decision in doap_records:
            # Create a session first for each DOAP record
            doap_event_id = uuid.uuid4()
            doap_session_id = uuid.uuid4()
            await session.execute(
                text("""
                    INSERT INTO events (id, tenant_id, batch_id, academic_year_id, title, description, event_type, attendance_category, professional_phase, date, start_time, end_time, status)
                    VALUES (:id, :tenant_id, :batch_id, :ay_id, 'DOAP Event', 'Seeded Test Event', 'practical', 'doap', 'Phase I', '2026-07-05', '09:00:00', '10:00:00', 'conducted')
                """),
                {"id": doap_event_id, "tenant_id": TENANT_ID, "batch_id": batch_id, "ay_id": ay_id},
            )
            await session.execute(
                text("""
                    INSERT INTO sessions (id, tenant_id, event_id, conducted_at, actual_hours)
                    VALUES (:id, :tenant_id, :event_id, NOW(), 1.0)
                """),
                {"id": doap_session_id, "tenant_id": TENANT_ID, "event_id": doap_event_id},
            )

            await session.execute(
                text("""
                    INSERT INTO doap_session_records (id, tenant_id, student_id, session_id, competency_code, nmc_level, is_core, stage, rating, attempt_type, faculty_decision, faculty_id, notes)
                    VALUES (:id, :tenant_id, :student_id, :session_id, :comp, 'P', true, :stage, :rating, 'F', :decision, :faculty_id, 'Well performed demonstration')
                """),
                {
                    "id": uuid.uuid4(),
                    "tenant_id": TENANT_ID,
                    "student_id": student_id,
                    "session_id": doap_session_id,
                    "comp": comp,
                    "stage": stage,
                    "rating": rating,
                    "decision": decision,
                    "faculty_id": faculty_id,
                },
            )

        # Seed Logbook Entries
        print("Seeding logbook entries...")
        logbook_entries = [
            ("AN-1.1", "Dissection of upper limb", "approved", "C", "M"),
            ("AN-2.1", "Histology of epithelial tissue", "approved", "C", "M"),
        ]
        for comp, activity, status, decision, rating in logbook_entries:
            await session.execute(
                text("""
                    INSERT INTO logbook_entries (id, tenant_id, student_id, subject_code, professional_phase, competency_code, nmc_level, is_core, activity_date, activity_name, reflection, status, rating, faculty_decision, faculty_initials, student_initials, signed_off_by, signed_off_at)
                    VALUES (:id, :tenant_id, :student_id, 'ANAT', 'Phase I', :comp, 'K', true, '2026-07-05', :activity, 'Reflective note on the anatomical dissection process.', :status, :rating, :decision, 'JA', 'JD', :faculty_id, NOW())
                """),
                {
                    "id": uuid.uuid4(),
                    "tenant_id": TENANT_ID,
                    "student_id": student_id,
                    "comp": comp,
                    "activity": activity,
                    "status": status,
                    "decision": decision,
                    "rating": rating,
                    "faculty_id": faculty_id,
                },
            )

        await session.commit()
        print("Seeding completed successfully!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_dashboard())
