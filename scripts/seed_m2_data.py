import asyncio
import json
import os
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Database URL setup
DATABASE_URL = os.environ.get(
    "SNX_DATABASE_URL", "postgresql+asyncpg://snx:snx_dev_pass@localhost:5435/synaptix_dev"
)

# Core IDs
TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


async def seed() -> None:
    print(f"Connecting to database at {DATABASE_URL}...")
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Check tenant exists
        res = await session.execute(
            text("SELECT id FROM tenants WHERE id = :id"), {"id": TENANT_ID}
        )
        tenant = res.scalar()
        if not tenant:
            print("Default tenant JMN not found. Seeding first...")
            await session.execute(
                text("""
                    INSERT INTO tenants (id, code, name, institution_type, regulatory_body)
                    VALUES (:id, 'JMN', 'JMN Medical College', 'medical', 'NMC')
                    """),
                {"id": TENANT_ID},
            )
            await session.commit()

        # Resolve academic year
        res = await session.execute(
            text(
                "SELECT id FROM academic_years WHERE tenant_id = :tenant_id AND name = '2026-2027'"
            ),
            {"tenant_id": TENANT_ID},
        )
        ay_id = res.scalar()
        if not ay_id:
            ay_id = uuid.uuid4()
            await session.execute(
                text("""
                    INSERT INTO academic_years (id, tenant_id, name, start_date, end_date, is_current)
                    VALUES (:id, :tenant_id, '2026-2027', '2026-08-01', '2027-07-31', true)
                    """),
                {"id": ay_id, "tenant_id": TENANT_ID},
            )
            await session.commit()

        # Resolve Program
        res = await session.execute(
            text("SELECT id FROM programs WHERE tenant_id = :tenant_id AND code = 'MBBS-CBME'"),
            {"tenant_id": TENANT_ID},
        )
        prog_id = res.scalar()
        if not prog_id:
            prog_id = uuid.uuid4()
            await session.execute(
                text("""
                    INSERT INTO programs (id, tenant_id, name, code, type, duration_years)
                    VALUES (:id, :tenant_id, 'MBBS', 'MBBS-CBME', 'professional_phase', 5)
                    """),
                {"id": prog_id, "tenant_id": TENANT_ID},
            )
            await session.commit()

        # Seed Curricula (CBME 2019 and CBME 2023)
        curr_2019_id = uuid.uuid4()
        print("Seeding CBME 2019 Curriculum...")
        await session.execute(
            text("""
                INSERT INTO curricula (id, tenant_id, program_id, name, version_code, is_active)
                VALUES (:id, :tenant_id, :program_id, 'NMC CBME 2019', 'CBME-2019', true)
                ON CONFLICT (program_id, version_code) DO NOTHING
                """),
            {"id": curr_2019_id, "tenant_id": TENANT_ID, "program_id": prog_id},
        )
        res = await session.execute(
            text(
                "SELECT id FROM curricula WHERE program_id = :program_id AND version_code = 'CBME-2019'"
            ),
            {"program_id": prog_id},
        )
        curr_2019_id = res.scalar()

        curr_2023_id = uuid.uuid4()
        print("Seeding CBME 2023 Curriculum...")
        await session.execute(
            text("""
                INSERT INTO curricula (id, tenant_id, program_id, name, version_code, is_active)
                VALUES (:id, :tenant_id, :program_id, 'NMC CBME 2023', 'CBME-2023', true)
                ON CONFLICT (program_id, version_code) DO NOTHING
                """),
            {"id": curr_2023_id, "tenant_id": TENANT_ID, "program_id": prog_id},
        )
        res = await session.execute(
            text(
                "SELECT id FROM curricula WHERE program_id = :program_id AND version_code = 'CBME-2023'"
            ),
            {"program_id": prog_id},
        )
        curr_2023_id = res.scalar()

        # Seed Departments ANAT, PHYS, BIOC if not present
        depts = [("Anatomy", "ANAT"), ("Physiology", "PHYS"), ("Biochemistry", "BIOC")]
        dept_ids = {}
        for name, code in depts:
            res = await session.execute(
                text("SELECT id FROM departments WHERE tenant_id = :tenant_id AND code = :code"),
                {"tenant_id": TENANT_ID, "code": code},
            )
            d_id = res.scalar()
            if not d_id:
                d_id = uuid.uuid4()
                await session.execute(
                    text(
                        "INSERT INTO departments (id, tenant_id, name, code) VALUES (:id, :tenant_id, :name, :code)"
                    ),
                    {"id": d_id, "tenant_id": TENANT_ID, "name": name, "code": code},
                )
            dept_ids[code] = d_id
        await session.commit()

        # Seed Courses with default_attendance_category
        courses_to_seed = [
            ("Human Anatomy", "ANAT-101", dept_ids["ANAT"], "practical"),
            ("Human Physiology", "PHYS-101", dept_ids["PHYS"], "theory"),
            ("Medical Biochemistry", "BIOC-101", dept_ids["BIOC"], "theory"),
        ]
        course_ids = {}
        for name, code, dept_id, default_category in courses_to_seed:
            res = await session.execute(
                text("SELECT id FROM courses WHERE tenant_id = :tenant_id AND code = :code"),
                {"tenant_id": TENANT_ID, "code": code},
            )
            c_id = res.scalar()
            if not c_id:
                c_id = uuid.uuid4()
                # Insert with default_attendance_category
                await session.execute(
                    text("""
                        INSERT INTO courses (id, tenant_id, department_id, name, code, default_attendance_category)
                        VALUES (:id, :tenant_id, :dept_id, :name, :code, :category)
                        """),
                    {
                        "id": c_id,
                        "tenant_id": TENANT_ID,
                        "dept_id": dept_id,
                        "name": name,
                        "code": code,
                        "category": default_category,
                    },
                )
            else:
                # Update if already exists to ensure default_attendance_category is populated
                await session.execute(
                    text(
                        "UPDATE courses SET default_attendance_category = :category WHERE id = :id"
                    ),
                    {"category": default_category, "id": c_id},
                )
            course_ids[code] = c_id
        await session.commit()

        # Seed "lesson_plan_approval" workflow definition
        wfd_id = uuid.uuid4()
        wfd_steps = {
            "draft": {"name": "Draft", "required_role": "faculty", "next_steps": ["hod_review"]},
            "hod_review": {
                "name": "HOD Review",
                "required_role": "HOD",
                "next_steps": ["approved", "rejected"],
            },
            "approved": {"name": "Approved", "required_role": None, "next_steps": []},
            "rejected": {"name": "Rejected", "required_role": None, "next_steps": ["draft"]},
        }
        print("Seeding lesson plan approval workflow definition...")
        await session.execute(
            text("""
                INSERT INTO workflow_definitions (id, tenant_id, name, code, description, version, is_current, steps, is_active)
                VALUES (:id, :tenant_id, 'Lesson Plan Approval Workflow', 'lesson_plan_approval',
                        'Manages approval of lesson plans by HODs', 1, true, :steps, true)
                ON CONFLICT (tenant_id, code) WHERE is_current = true AND deleted_at IS NULL DO NOTHING
                """),
            {"id": wfd_id, "tenant_id": TENANT_ID, "steps": json.dumps(wfd_steps)},
        )
        await session.commit()

        # Seed Lesson Plan templates (one draft, one approved for CBME 2023; one approved for CBME 2019)
        # Note: We must ensure unique constraint is satisfied.
        lesson_plans = [
            (
                uuid.uuid4(),
                course_ids["ANAT-101"],
                curr_2023_id,
                "AN-1.1-LP1",
                "Introduction to Anatomical Terminology",
                "K",
                True,
                "draft",
            ),
            (
                uuid.uuid4(),
                course_ids["ANAT-101"],
                curr_2023_id,
                "AN-1.2-LP1",
                "Epithelial Tissue Structure",
                "KH",
                True,
                "approved",
            ),
            (
                uuid.uuid4(),
                course_ids["ANAT-101"],
                curr_2019_id,
                "AN-1.1-LP1",
                "Anatomical Basics in CBME 2019",
                "K",
                True,
                "approved",
            ),
        ]

        for (
            lp_id,
            course_id,
            curriculum_id,
            code,
            topic,
            comp_level,
            is_core,
            status,
        ) in lesson_plans:
            # Check if this lesson plan already exists
            res = await session.execute(
                text(
                    "SELECT id FROM lesson_plans "
                    "WHERE tenant_id = :tenant_id AND course_id = :course_id AND curriculum_id = :curriculum_id AND code = :code"
                ),
                {
                    "tenant_id": TENANT_ID,
                    "course_id": course_id,
                    "curriculum_id": curriculum_id,
                    "code": code,
                },
            )
            if not res.scalar():
                print(f"Seeding lesson plan {code}...")
                await session.execute(
                    text("""
                        INSERT INTO lesson_plans (id, tenant_id, course_id, curriculum_id, code, version, is_current,
                                                  topic, description, estimated_hours, competency_code, nmc_competency_level,
                                                  is_core, status)
                        VALUES (:id, :tenant_id, :course_id, :curriculum_id, :code, 1, true,
                                :topic, 'Description for ' || :topic, 1.0, :code, :comp_level, :is_core, :status)
                        """),
                    {
                        "id": lp_id,
                        "tenant_id": TENANT_ID,
                        "course_id": course_id,
                        "curriculum_id": curriculum_id,
                        "code": code,
                        "topic": topic,
                        "comp_level": comp_level,
                        "is_core": is_core,
                        "status": status,
                    },
                )

        await session.commit()
        print("M2 Seed data inserted successfully.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
