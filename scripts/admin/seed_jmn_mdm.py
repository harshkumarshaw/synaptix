"""Seed MDM configuration for JMN Medical College."""
import asyncio
import os
import json
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# JMN tenant_id
JMN_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")

DATABASE_URL = os.environ.get(
    "SNX_DATABASE_URL", "postgresql+asyncpg://snx:snx_dev_pass@localhost:5435/synaptix_dev"
)

MDM_CONFIGS = [
    # Subject code mapping
    {
        "config_key": "competency.prefix_to_subject_code",
        "config_value": {
            "AN": "ANAT", "PY": "PHYS", "BI": "BIOC", "MI": "MICR",
            "PA": "PATH", "PH": "PHAR", "FM": "FMED", "CM": "CMED",
            "GM": "GMED", "GS": "GSUR", "OG": "OBGY", "PE": "PEDI",
            "OR": "ORTH", "OP": "OPHT", "EN": "ENT",  "DE": "DERM",
            "PS": "PSYC", "RD": "RADI", "AS": "ANES",
        },
        "description": "NMC CBME 2019 competency prefix → subject code mapping",
    },
    # Medical onboarding templates
    {
        "config_key": "onboarding.template.medical",
        "config_value": {
            "institution_type": "medical",
            "regulatory_body": "NMC",
            "departments": ["Anatomy", "Physiology", "Biochemistry", "Pathology", "Pharmacology", "Microbiology", "Forensic Medicine", "Community Medicine"],
            "documents_required": ["NMC_Registration", "MBBS_Degree", "MD_MS_Degree"]
        },
        "description": "Default onboarding configuration template for medical colleges",
    },
    # Nursing onboarding templates
    {
        "config_key": "onboarding.template.nursing",
        "config_value": {
            "institution_type": "nursing",
            "regulatory_body": "INC",
            "departments": ["Fundamentals of Nursing", "Community Health Nursing", "Medical Surgical Nursing", "Pediatric Nursing", "Obstetric and Gynecological Nursing", "Psychiatric Nursing"],
            "documents_required": ["INC_Registration", "BSc_Nursing_Degree", "MSc_Nursing_Degree"]
        },
        "description": "Default onboarding configuration template for nursing colleges",
    },


    # IA configs per subject (Phase I subjects)
    *[
        {
            "config_key": f"ia_config.{subj}",
            "config_value": {"ia_weight_pct": 10.0, "subject_ia_max": 40.0},
            "description": f"IA configuration for {subj} (default 10% weight, 40 max marks)",
        }
        for subj in ["ANAT", "PHYS", "BIOC"]
    ],

    # IA configs (Phase II subjects — higher IA max for clinical)
    *[
        {
            "config_key": f"ia_config.{subj}",
            "config_value": {"ia_weight_pct": 15.0, "subject_ia_max": 60.0},
            "description": f"IA configuration for {subj} (15% weight, 60 max marks)",
        }
        for subj in ["PATH", "PHAR", "MICR", "FMED"]
    ],

    # Attendance thresholds (NMC defaults)
    *[
        {
            "config_key": f"attendance.threshold.{cat}",
            "config_value": threshold,
            "description": f"Attendance threshold for {cat} ({threshold}%)",
        }
        for cat, threshold in [
            ("theory", 75.00), ("practical", 80.00), ("clinical", 80.00),
            ("doap", 80.00), ("ece", 80.00), ("aetcom", 75.00),
            ("foundation_course", 75.00), ("elective", 75.00),
        ]
    ],

    # Elective allocation algorithm
    {
        "config_key": "elective.allocation_algorithm",
        "config_value": "ranked",
        "description": "Elective allocation algorithm: fcfs or ranked",
    },

    # Backdating thresholds
    {
        "config_key": "logbook.backdating.review_threshold_days",
        "config_value": 7,
        "description": "Logbook entries backdated more than N days require faculty review",
    },
    {
        "config_key": "logbook.backdating.hod_threshold_days",
        "config_value": 30,
        "description": "Logbook entries backdated more than N days route to HOD",
    },

    # Late attendance
    {
        "config_key": "attendance.late_threshold_minutes",
        "config_value": 15,
        "description": "Minutes after session start before marking as 'late'",
    },
    {
        "config_key": "attendance.late_counts_as_half",
        "config_value": False,
        "description": "Whether late arrival counts as 0.5 attendance",
    },

    # Correction window
    {
        "config_key": "attendance.correction_window_hours",
        "config_value": 24,
        "description": "Hours within which faculty can correct attendance without HOD approval",
    },
]


async def main():
    print(f"Connecting to database at {DATABASE_URL}...")
    engine = create_async_engine(DATABASE_URL)
    async_session = async_sessionmaker(engine)

    async with async_session() as session:
        for config in MDM_CONFIGS:
            val_str = json.dumps(config["config_value"])
            await session.execute(
                text("""
                    INSERT INTO mdm_configs (tenant_id, config_key, config_value, description)
                    VALUES (:tenant_id, :config_key, CAST(:config_value AS jsonb), :description)
                    ON CONFLICT (tenant_id, config_key) DO UPDATE
                    SET config_value = EXCLUDED.config_value,
                        description = EXCLUDED.description,
                        updated_at = NOW()
                """),
                {
                    "tenant_id": JMN_TENANT_ID,
                    "config_key": config["config_key"],
                    "config_value": val_str,
                    "description": config["description"],
                }
            )
        await session.commit()
        print(f"Seeded {len(MDM_CONFIGS)} MDM configs for JMN Medical College")


if __name__ == "__main__":
    asyncio.run(main())
