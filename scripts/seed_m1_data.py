import asyncio
import os
import uuid

import bcrypt
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
            print("Seeding default tenant...")
            await session.execute(
                text("""
                    INSERT INTO tenants (id, code, name, institution_type, regulatory_body)
                    VALUES (:id, 'JMN', 'JMN Medical College', 'medical', 'NMC')
                    """),
                {"id": TENANT_ID},
            )
            await session.commit()

        # Seed Academic Year
        ay_id = uuid.uuid4()
        print("Seeding academic year...")
        await session.execute(
            text("""
                INSERT INTO academic_years (id, tenant_id, name, start_date, end_date, is_current)
                VALUES (:id, :tenant_id, '2026-2027', '2026-08-01', '2027-07-31', true)
                ON CONFLICT (tenant_id, name) DO NOTHING
                """),
            {"id": ay_id, "tenant_id": TENANT_ID},
        )

        # Get academic year ID if it already existed
        res = await session.execute(
            text(
                "SELECT id FROM academic_years WHERE tenant_id = :tenant_id AND name = '2026-2027'"
            ),
            {"tenant_id": TENANT_ID},
        )
        ay_id = res.scalar()

        # Seed Program
        prog_id = uuid.uuid4()
        print("Seeding program...")
        await session.execute(
            text("""
                INSERT INTO programs (id, tenant_id, name, code, type, duration_years)
                VALUES (:id, :tenant_id, 'MBBS', 'MBBS-CBME', 'professional_phase', 5)
                ON CONFLICT (tenant_id, code) DO NOTHING
                """),
            {"id": prog_id, "tenant_id": TENANT_ID},
        )
        res = await session.execute(
            text("SELECT id FROM programs WHERE tenant_id = :tenant_id AND code = 'MBBS-CBME'"),
            {"tenant_id": TENANT_ID},
        )
        prog_id = res.scalar()

        # Seed Curriculum
        curr_id = uuid.uuid4()
        print("Seeding curriculum...")
        await session.execute(
            text("""
                INSERT INTO curricula (id, tenant_id, program_id, name, version_code)
                VALUES (:id, :tenant_id, :program_id, 'NMC CBME 2023', 'CBME-2023')
                ON CONFLICT (program_id, version_code) DO NOTHING
                """),
            {"id": curr_id, "tenant_id": TENANT_ID, "program_id": prog_id},
        )
        res = await session.execute(
            text(
                "SELECT id FROM curricula WHERE program_id = :program_id AND version_code = 'CBME-2023'"
            ),
            {"program_id": prog_id},
        )
        curr_id = res.scalar()

        # Seed Departments
        depts = [
            ("Anatomy", "ANAT"),
            ("Physiology", "PHYS"),
            ("Biochemistry", "BIOC"),
        ]
        dept_ids = {}
        for name, code in depts:
            dept_id = uuid.uuid4()
            print(f"Seeding department {name} ({code})...")
            await session.execute(
                text("""
                    INSERT INTO departments (id, tenant_id, name, code)
                    VALUES (:id, :tenant_id, :name, :code)
                    ON CONFLICT (tenant_id, code) DO NOTHING
                    """),
                {"id": dept_id, "tenant_id": TENANT_ID, "name": name, "code": code},
            )
            res = await session.execute(
                text("SELECT id FROM departments WHERE tenant_id = :tenant_id AND code = :code"),
                {"tenant_id": TENANT_ID, "code": code},
            )
            dept_ids[code] = res.scalar()

        # Seed Batch & Section
        batch_id = uuid.uuid4()
        print("Seeding batch...")
        await session.execute(
            text("""
                INSERT INTO batches (id, tenant_id, academic_year_id, program_id, name, code)
                VALUES (:id, :tenant_id, :ay_id, :program_id, 'MBBS 2026 Batch', 'MBBS-2026')
                ON CONFLICT (tenant_id, academic_year_id, code) DO NOTHING
                """),
            {"id": batch_id, "tenant_id": TENANT_ID, "ay_id": ay_id, "program_id": prog_id},
        )
        res = await session.execute(
            text(
                "SELECT id FROM batches WHERE tenant_id = :tenant_id AND academic_year_id = :ay_id AND code = 'MBBS-2026'"
            ),
            {"tenant_id": TENANT_ID, "ay_id": ay_id},
        )
        batch_id = res.scalar()

        sect_id = uuid.uuid4()
        print("Seeding section...")
        await session.execute(
            text("""
                INSERT INTO sections (id, tenant_id, batch_id, name)
                VALUES (:id, :tenant_id, :batch_id, 'Section A')
                ON CONFLICT (batch_id, name) DO NOTHING
                """),
            {"id": sect_id, "tenant_id": TENANT_ID, "batch_id": batch_id},
        )
        res = await session.execute(
            text("SELECT id FROM sections WHERE batch_id = :batch_id AND name = 'Section A'"),
            {"batch_id": batch_id},
        )
        sect_id = res.scalar()

        # Seed Users
        password_hash = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode("utf-8")

        users_to_seed = [
            ("Admin User", "admin@jmn.edu", "+919999999999"),
            ("Dr. Jane Anatomist", "faculty_anat@jmn.edu", "+919888888888"),
            ("John Doe", "student_1@jmn.edu", "+919777777777"),
        ]
        user_ids = {}
        for name, email, mobile in users_to_seed:
            user_id = uuid.uuid4()
            print(f"Seeding user {name}...")
            await session.execute(
                text("""
                    INSERT INTO users (id, tenant_id, email, mobile, full_name, password_hash)
                    VALUES (:id, :tenant_id, :email, :mobile, :name, :hash)
                    ON CONFLICT (tenant_id, email) DO NOTHING
                    """),
                {
                    "id": user_id,
                    "tenant_id": TENANT_ID,
                    "email": email,
                    "mobile": mobile,
                    "name": name,
                    "hash": password_hash,
                },
            )
            res = await session.execute(
                text("SELECT id FROM users WHERE tenant_id = :tenant_id AND email = :email"),
                {"tenant_id": TENANT_ID, "email": email},
            )
            user_ids[email] = res.scalar()

        # Seed Roles mapping
        # Let's get role IDs
        res = await session.execute(
            text("SELECT id, name FROM roles WHERE tenant_id = :tenant_id"),
            {"tenant_id": TENANT_ID},
        )
        roles = {row[1]: row[0] for row in res.all()}

        roles_mapping = [
            ("admin@jmn.edu", "institution_admin"),
            ("faculty_anat@jmn.edu", "faculty"),
            ("student_1@jmn.edu", "student"),
        ]
        for email, role_name in roles_mapping:
            if role_name in roles and email in user_ids:
                u_id = user_ids[email]
                r_id = roles[role_name]
                print(f"Mapping role {role_name} to {email}...")
                await session.execute(
                    text("""
                        INSERT INTO user_roles (tenant_id, user_id, role_id)
                        VALUES (:tenant_id, :user_id, :role_id)
                        ON CONFLICT (user_id, role_id) DO NOTHING
                        """),
                    {"tenant_id": TENANT_ID, "user_id": u_id, "role_id": r_id},
                )

        # Seed Faculty Profile
        faculty_id = uuid.uuid4()
        print("Seeding faculty profile...")
        await session.execute(
            text("""
                INSERT INTO faculty (id, tenant_id, user_id, department_id, designation, employee_id)
                VALUES (:id, :tenant_id, :user_id, :dept_id, 'Professor & HOD', 'EMP-ANAT-001')
                ON CONFLICT (tenant_id, employee_id) DO NOTHING
                """),
            {
                "id": faculty_id,
                "tenant_id": TENANT_ID,
                "user_id": user_ids["faculty_anat@jmn.edu"],
                "dept_id": dept_ids["ANAT"],
            },
        )

        # Seed Student Profile
        student_id = uuid.uuid4()
        print("Seeding student profile...")
        await session.execute(
            text("""
                INSERT INTO students (id, tenant_id, user_id, batch_id, section_id, roll_number, admission_year, status)
                VALUES (:id, :tenant_id, :user_id, :batch_id, :sect_id, 'JMN-2026-001', 2026, 'active')
                ON CONFLICT (tenant_id, roll_number) DO NOTHING
                """),
            {
                "id": student_id,
                "tenant_id": TENANT_ID,
                "user_id": user_ids["student_1@jmn.edu"],
                "batch_id": batch_id,
                "sect_id": sect_id,
            },
        )

        await session.commit()
        print("M1 Seed data inserted successfully.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
