import asyncio
import os
import uuid
import random
from datetime import date, time, timedelta, datetime, timezone
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import bcrypt

DATABASE_URL = os.environ.get(
    "SNX_DATABASE_URL", "postgresql+asyncpg://snx:snx_dev_pass@localhost:5435/synaptix_dev"
)

# Predictable IDs
TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
PROGRAM_ID = uuid.UUID("5614c7b6-6d54-4d20-b9ae-bf33099c260b")
CURRICULUM_ID = uuid.UUID("9f9d5554-7909-4bdf-bb7e-0789dc5706e5")
AY_ID = uuid.UUID("7fa4e0ec-2a6f-4840-8c63-46c9f18eca54")
BATCH_ID = uuid.UUID("149a9a57-fbc6-409e-bdf2-d6d98b7125fd")
SECTION_ID = uuid.UUID("e0164aac-0390-4e68-9249-73e82b81a0d8")

# Role IDs from roles table
ROLE_ADMIN = uuid.UUID("3314b0ee-499e-456d-8c2c-e3a45e2bca4d") # institution_admin
ROLE_FACULTY = uuid.UUID("a6b0fa52-c712-43f9-9817-ce9db2a37e5a")
ROLE_STUDENT = uuid.UUID("8bc53c9b-3f6b-4185-839c-068d60b881a4")

# Department IDs
DEPT_ANAT = uuid.UUID("7aba89ab-6dfe-4650-83e0-da3860fbc125")
DEPT_PHYS = uuid.UUID("b72a9f6e-a4a4-41b0-81ec-b047737fa76b")
DEPT_BIOC = uuid.UUID("f11a0e32-5734-4db2-9cd0-9b7b14d9c6ed")
DEPT_CMED = uuid.UUID("f11a0e32-5734-4db2-9cd0-9b7b14d9c6ee")
DEPT_PHAR = uuid.UUID("f11a0e32-5734-4db2-9cd0-9b7b14d9c6ef")

# User IDs
USER_ADMIN_ID = uuid.UUID("20000000-0000-0000-0000-000000000001")
USER_FACULTY_1_ID = uuid.UUID("20000000-0000-0000-0000-000000000002")
USER_FACULTY_2_ID = uuid.UUID("20000000-0000-0000-0000-000000000003")
USER_STUDENT_1_ID = uuid.UUID("30000000-0000-0000-0000-000000000001")
USER_STUDENT_2_ID = uuid.UUID("30000000-0000-0000-0000-000000000002")

# Profile IDs
FACULTY_1_ID = uuid.UUID("20000000-0000-0000-0000-000000000011")
FACULTY_2_ID = uuid.UUID("20000000-0000-0000-0000-000000000012")
STUDENT_1_ID = uuid.UUID("30000000-0000-0000-0000-000000000011")
STUDENT_2_ID = uuid.UUID("30000000-0000-0000-0000-000000000012")

# Course Details
COURSES = {
    "ANAT-101": {
        "id": uuid.UUID("8b4b8664-05b6-4c06-be7f-6a69ffd5a97b"),
        "name": "Human Anatomy",
        "category": "practical",
        "subject_code": "ANAT",
        "dept_id": DEPT_ANAT
    },
    "PHYS-101": {
        "id": uuid.UUID("de7b0d2c-8fd7-49f7-9251-751f42bc7f6c"),
        "name": "Human Physiology",
        "category": "theory",
        "subject_code": "PHYS",
        "dept_id": DEPT_PHYS
    },
    "BIOC-101": {
        "id": uuid.UUID("d0824461-0a58-4b18-8b78-69288fbe6968"),
        "name": "Biochemistry",
        "category": "theory",
        "subject_code": "BIOC",
        "dept_id": DEPT_BIOC
    },
    "CMED-101": {
        "id": uuid.UUID("60000000-0000-0000-0000-000000000004"),
        "name": "Community Medicine",
        "category": "theory",
        "subject_code": "CMED",
        "dept_id": DEPT_CMED
    },
    "PHAR-101": {
        "id": uuid.UUID("60000000-0000-0000-0000-000000000005"),
        "name": "Pharmacology",
        "category": "practical",
        "subject_code": "PHAR",
        "dept_id": DEPT_PHAR
    }
}

async def main():
    print(f"Connecting to database at {DATABASE_URL}...")
    engine = create_async_engine(DATABASE_URL)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as session:
        print("Seeding Tenant...")
        await session.execute(text("""
            INSERT INTO tenants (id, code, name, institution_type, regulatory_body, is_active, timezone, created_at, updated_at)
            VALUES (:id, 'JMN', 'JMN Medical College', 'medical', 'NMC', true, 'Asia/Kolkata', NOW(), NOW())
            ON CONFLICT (id) DO NOTHING
        """), {"id": TENANT_ID})

        print("Seeding Departments...")
        departments = [
            {"id": DEPT_ANAT, "name": "Anatomy", "code": "ANAT"},
            {"id": DEPT_PHYS, "name": "Physiology", "code": "PHYS"},
            {"id": DEPT_BIOC, "name": "Biochemistry", "code": "BIOC"},
            {"id": DEPT_CMED, "name": "Community Medicine", "code": "CMED"},
            {"id": DEPT_PHAR, "name": "Pharmacology", "code": "PHAR"}
        ]
        for dept in departments:
            await session.execute(text("""
                INSERT INTO departments (id, tenant_id, name, code, is_active, created_at, updated_at)
                VALUES (:id, :tenant_id, :name, :code, true, NOW(), NOW())
                ON CONFLICT (id) DO NOTHING
            """), {**dept, "tenant_id": TENANT_ID})

        print("Seeding Users...")
        pwd_hash = bcrypt.hashpw("Synaptix@2026".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        users = [
            {"id": USER_ADMIN_ID, "email": "admin@jmn.edu.in", "full_name": "Sila Singh Ghosh", "role_id": ROLE_ADMIN},
            {"id": USER_FACULTY_1_ID, "email": "dr.ray@jmn.edu.in", "full_name": "Prof. Dr. Amita Ray", "role_id": ROLE_FACULTY},
            {"id": USER_FACULTY_2_ID, "email": "dr.mukherjee@jmn.edu.in", "full_name": "Prof. Dr. P.P. Mukherjee", "role_id": ROLE_FACULTY},
            {"id": USER_STUDENT_1_ID, "email": "student1@jmn.edu.in", "full_name": "Rahul Sharma", "role_id": ROLE_STUDENT},
            {"id": USER_STUDENT_2_ID, "email": "student2@jmn.edu.in", "full_name": "Priya Patel", "role_id": ROLE_STUDENT}
        ]

        for u in users:
            await session.execute(text("""
                INSERT INTO users (id, tenant_id, email, full_name, password_hash, mfa_enabled, is_active, created_at, updated_at)
                VALUES (:id, :tenant_id, :email, :full_name, :pwd_hash, false, true, NOW(), NOW())
                ON CONFLICT (id) DO UPDATE SET email = EXCLUDED.email, full_name = EXCLUDED.full_name, password_hash = EXCLUDED.password_hash
            """), {
                "id": u["id"],
                "tenant_id": TENANT_ID,
                "email": u["email"],
                "full_name": u["full_name"],
                "pwd_hash": pwd_hash
            })

            # Check if user_role link exists
            res = await session.execute(text("""
                SELECT id FROM user_roles WHERE tenant_id = :tenant_id AND user_id = :user_id AND role_id = :role_id
            """), {"tenant_id": TENANT_ID, "user_id": u["id"], "role_id": u["role_id"]})
            if not res.scalar():
                await session.execute(text("""
                    INSERT INTO user_roles (id, tenant_id, user_id, role_id, granted_at, created_at, updated_at)
                    VALUES (:id, :tenant_id, :user_id, :role_id, NOW(), NOW(), NOW())
                """), {
                    "id": uuid.uuid4(),
                    "tenant_id": TENANT_ID,
                    "user_id": u["id"],
                    "role_id": u["role_id"]
                })

        print("Seeding Academic Structure (Program, Curriculum, AY, Batch, Section)...")
        await session.execute(text("""
            INSERT INTO programs (id, tenant_id, name, code, type, duration_years, is_active, created_at, updated_at)
            VALUES (:id, :tenant_id, 'MBBS', 'MBBS-CBME', 'professional_phase', 5, true, NOW(), NOW())
            ON CONFLICT (id) DO NOTHING
        """), {"id": PROGRAM_ID, "tenant_id": TENANT_ID})

        await session.execute(text("""
            INSERT INTO curricula (id, tenant_id, program_id, name, version_code, is_active, created_at, updated_at)
            VALUES (:id, :tenant_id, :program_id, 'NMC CBME 2023', 'CBME-2023', true, NOW(), NOW())
            ON CONFLICT (id) DO NOTHING
        """), {"id": CURRICULUM_ID, "tenant_id": TENANT_ID, "program_id": PROGRAM_ID})

        await session.execute(text("""
            INSERT INTO academic_years (id, tenant_id, name, start_date, end_date, is_current, created_at, updated_at)
            VALUES (:id, :tenant_id, '2026-2027', '2026-08-01', '2027-07-31', true, NOW(), NOW())
            ON CONFLICT (id) DO NOTHING
        """), {"id": AY_ID, "tenant_id": TENANT_ID})

        await session.execute(text("""
            INSERT INTO batches (id, tenant_id, academic_year_id, program_id, name, code, is_active, created_at, updated_at)
            VALUES (:id, :tenant_id, :ay_id, :program_id, 'MBBS 2026 Batch', 'MBBS-2026', true, NOW(), NOW())
            ON CONFLICT (id) DO NOTHING
        """), {"id": BATCH_ID, "tenant_id": TENANT_ID, "ay_id": AY_ID, "program_id": PROGRAM_ID})

        await session.execute(text("""
            INSERT INTO sections (id, tenant_id, batch_id, name, created_at, updated_at)
            VALUES (:id, :tenant_id, :batch_id, 'Section A', NOW(), NOW())
            ON CONFLICT (id) DO NOTHING
        """), {"id": SECTION_ID, "tenant_id": TENANT_ID, "batch_id": BATCH_ID})

        print("Seeding Faculty Profiles...")
        faculty_profiles = [
            {"id": FACULTY_1_ID, "user_id": USER_FACULTY_1_ID, "dept_id": DEPT_ANAT, "designation": "Professor & HOD", "emp_id": "EMP-ANAT-E2E-001"},
            {"id": FACULTY_2_ID, "user_id": USER_FACULTY_2_ID, "dept_id": DEPT_PHYS, "designation": "Professor", "emp_id": "EMP-PHYS-E2E-001"}
        ]
        for fac in faculty_profiles:
            await session.execute(text("""
                INSERT INTO faculty (id, tenant_id, user_id, department_id, designation, employee_id, is_active, created_at, updated_at)
                VALUES (:id, :tenant_id, :user_id, :dept_id, :designation, :emp_id, true, NOW(), NOW())
                ON CONFLICT (id) DO NOTHING
            """), {**fac, "tenant_id": TENANT_ID})

        print("Seeding Student Profiles...")
        student_profiles = [
            {"id": STUDENT_1_ID, "user_id": USER_STUDENT_1_ID, "roll": "JMN-2026-E2E-001"},
            {"id": STUDENT_2_ID, "user_id": USER_STUDENT_2_ID, "roll": "JMN-2026-E2E-002"}
        ]
        for stud in student_profiles:
            await session.execute(text("""
                INSERT INTO students (id, tenant_id, user_id, batch_id, section_id, roll_number, admission_year, status, created_at, updated_at)
                VALUES (:id, :tenant_id, :user_id, :batch_id, :section_id, :roll, 2026, 'active', NOW(), NOW())
                ON CONFLICT (id) DO NOTHING
            """), {
                **stud,
                "tenant_id": TENANT_ID,
                "batch_id": BATCH_ID,
                "section_id": SECTION_ID
            })

        print("Seeding Courses...")
        for code, info in COURSES.items():
            await session.execute(text("""
                INSERT INTO courses (id, tenant_id, curriculum_id, name, code, department_id, is_active, default_attendance_category, subject_code, created_at, updated_at)
                VALUES (:id, :tenant_id, :curriculum_id, :name, :code, :dept_id, true, :category, :subject_code, NOW(), NOW())
                ON CONFLICT (id) DO NOTHING
            """), {
                "id": info["id"],
                "tenant_id": TENANT_ID,
                "curriculum_id": CURRICULUM_ID,
                "name": info["name"],
                "code": code,
                "dept_id": info["dept_id"],
                "category": info["category"],
                "subject_code": info["subject_code"]
            })

        print("Seeding Events and Attendance...")
        # Set tenant context for RLS
        await session.execute(text("SELECT set_config('snx.current_tenant_id', :tenant_id, true)"), {"tenant_id": str(TENANT_ID)})
        await session.execute(text("DELETE FROM doap_session_records WHERE tenant_id = :tenant_id"), {"tenant_id": TENANT_ID})
        await session.execute(text("DELETE FROM attendance WHERE tenant_id = :tenant_id"), {"tenant_id": TENANT_ID})
        await session.execute(text("DELETE FROM sessions WHERE tenant_id = :tenant_id"), {"tenant_id": TENANT_ID})
        await session.execute(text("DELETE FROM event_courses WHERE tenant_id = :tenant_id"), {"tenant_id": TENANT_ID})
        await session.execute(text("DELETE FROM event_faculty WHERE tenant_id = :tenant_id"), {"tenant_id": TENANT_ID})
        await session.execute(text("DELETE FROM events WHERE tenant_id = :tenant_id"), {"tenant_id": TENANT_ID})

        today = date.today()
        event_count = 0
        
        for day_offset in range(30):
            event_date = today - timedelta(days=day_offset)
            if event_date.weekday() >= 5:
                continue
            if event_count >= 20:
                break
                
            course_keys = ["ANAT-101", "PHYS-101", "BIOC-101"]
            course_key = course_keys[event_count % 3]
            info = COURSES[course_key]
            
            event_id = uuid.uuid4()
            await session.execute(text("""
                INSERT INTO events (id, tenant_id, batch_id, academic_year_id, title, description, event_type, attendance_category, professional_phase, date, start_time, end_time, status, created_at, updated_at)
                VALUES (:id, :tenant_id, :batch_id, :ay_id, :title, 'Seeded Operational Event', 'lecture', :category, 'Phase I', :date, :start_time, :end_time, 'conducted', NOW(), NOW())
            """), {
                "id": event_id,
                "tenant_id": TENANT_ID,
                "batch_id": BATCH_ID,
                "ay_id": AY_ID,
                "title": f"{info['name']} Lecture",
                "category": info["category"],
                "date": event_date,
                "start_time": time(9, 0),
                "end_time": time(10, 0),
            })
            
            await session.execute(text("""
                INSERT INTO event_courses (id, tenant_id, event_id, course_id, is_primary, created_at, updated_at)
                VALUES (:id, :tenant_id, :event_id, :course_id, true, NOW(), NOW())
            """), {
                "id": uuid.uuid4(),
                "tenant_id": TENANT_ID,
                "event_id": event_id,
                "course_id": info["id"],
            })
            
            faculty_id = FACULTY_1_ID if course_key == "ANAT-101" else FACULTY_2_ID
            await session.execute(text("""
                INSERT INTO event_faculty (id, tenant_id, event_id, faculty_id, created_at, updated_at)
                VALUES (:id, :tenant_id, :event_id, :faculty_id, NOW(), NOW())
            """), {
                "id": uuid.uuid4(),
                "tenant_id": TENANT_ID,
                "event_id": event_id,
                "faculty_id": faculty_id,
            })
            
            for student_id, rate in [(STUDENT_1_ID, 0.80), (STUDENT_2_ID, 0.75)]:
                status = "present" if random.random() < rate else "absent"
                await session.execute(text("""
                    INSERT INTO attendance (id, tenant_id, student_id, event_id, status, attendance_category, professional_phase, method, marked_at, created_at, updated_at)
                    VALUES (:id, :tenant_id, :student_id, :event_id, :status, :category, 'Phase I', 'manual', NOW(), NOW(), NOW())
                """), {
                    "id": uuid.uuid4(),
                    "tenant_id": TENANT_ID,
                    "student_id": student_id,
                    "event_id": event_id,
                    "status": status,
                    "category": info["category"]
                })
                
            event_count += 1

        print("Seeding Logbook Entries...")
        await session.execute(text("DELETE FROM logbook_entries WHERE tenant_id = :tenant_id"), {"tenant_id": TENANT_ID})
        
        for student_id in [STUDENT_1_ID, STUDENT_2_ID]:
            await session.execute(text("""
                INSERT INTO logbook_entries (id, tenant_id, student_id, subject_code, professional_phase, competency_code, nmc_level, is_core, activity_date, activity_name, status, created_at, updated_at)
                VALUES (:id, :tenant_id, :student_id, 'ANAT', 'Phase I', 'AN-1.1', 'P', true, '2026-07-01', 'Anatomy Dissection Activity', 'approved', NOW(), NOW())
            """), {
                "id": uuid.uuid4(),
                "tenant_id": TENANT_ID,
                "student_id": student_id
            })
            await session.execute(text("""
                INSERT INTO logbook_entries (id, tenant_id, student_id, subject_code, professional_phase, competency_code, nmc_level, is_core, activity_date, activity_name, status, created_at, updated_at)
                VALUES (:id, :tenant_id, :student_id, 'PHYS', 'Phase I', 'PY-1.2', 'K', true, '2026-07-02', 'Physiology Lab Activity', 'approved', NOW(), NOW())
            """), {
                "id": uuid.uuid4(),
                "tenant_id": TENANT_ID,
                "student_id": student_id
            })

        await session.commit()
        print("JMN Operational Data Seeding successfully completed!")
        
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
