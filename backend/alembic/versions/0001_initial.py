"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "candidate_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True),
        sa.Column("full_name", sa.String(255)),
        sa.Column("headline", sa.String(255)),
        sa.Column("summary", sa.Text()),
        sa.Column("email", sa.String(255)),
        sa.Column("phone", sa.String(50)),
        sa.Column("location", sa.String(255)),
        sa.Column("links", postgresql.JSON(), server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    def child_table(name, extra_cols):
        op.create_table(
            name,
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("candidate_profiles.id", ondelete="CASCADE")),
            *extra_cols,
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )

    child_table("educations", [
        sa.Column("institution", sa.String(255), nullable=False),
        sa.Column("degree", sa.String(255)),
        sa.Column("field_of_study", sa.String(255)),
        sa.Column("start_date", sa.Date()),
        sa.Column("end_date", sa.Date()),
        sa.Column("gpa", sa.String(20)),
    ])

    child_table("experiences", [
        sa.Column("company", sa.String(255), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("location", sa.String(255)),
        sa.Column("start_date", sa.Date()),
        sa.Column("end_date", sa.Date()),
        sa.Column("is_current", sa.Boolean(), server_default=sa.false()),
        sa.Column("bullets", postgresql.JSON(), server_default="[]"),
        sa.Column("technologies", postgresql.JSON(), server_default="[]"),
    ])

    child_table("projects", [
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("bullets", postgresql.JSON(), server_default="[]"),
        sa.Column("technologies", postgresql.JSON(), server_default="[]"),
        sa.Column("url", sa.String(500)),
        sa.Column("start_date", sa.Date()),
        sa.Column("end_date", sa.Date()),
    ])

    child_table("certifications", [
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("issuer", sa.String(255)),
        sa.Column("issue_date", sa.Date()),
        sa.Column("credential_url", sa.String(500)),
    ])

    child_table("achievements", [
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("date", sa.Date()),
    ])

    op.create_table(
        "skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False, unique=True),
        sa.Column("normalized_name", sa.String(150), nullable=False),
        sa.Column("category", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_skills_name", "skills", ["name"])
    op.create_index("ix_skills_normalized_name", "skills", ["normalized_name"])

    skill_source = sa.Enum("EXTRACTED", "MANUAL", "VERIFICATION", name="skillsource")
    skill_verification_status = sa.Enum("EXTRACTED", "VERIFIED", "BASIC", "REJECTED", name="skillverificationstatus")

    op.create_table(
        "candidate_skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("candidate_profiles.id", ondelete="CASCADE")),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("skills.id", ondelete="CASCADE")),
        sa.Column("proficiency", sa.String(50)),
        sa.Column("source", skill_source, nullable=False, server_default="EXTRACTED"),
        sa.Column("verification_status", skill_verification_status, nullable=False, server_default="EXTRACTED"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("profile_id", "skill_id", name="uq_candidate_skill"),
    )

    evidence_source_type = sa.Enum("PROJECT", "INTERNSHIP", "WORK", "COURSE", "OTHER", name="evidencesourcetype")

    op.create_table(
        "skill_verifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("candidate_skill_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("candidate_skills.id", ondelete="CASCADE"), unique=True),
        sa.Column("answer", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "verification_evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("verification_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("skill_verifications.id", ondelete="CASCADE")),
        sa.Column("source_type", evidence_source_type, nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "job_descriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("company_name", sa.String(255)),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("role_title", sa.String(255)),
        sa.Column("domain", sa.String(255)),
        sa.Column("experience_requirement", sa.String(255)),
        sa.Column("education_requirement", sa.String(255)),
        sa.Column("responsibilities", postgresql.JSON(), server_default="[]"),
        sa.Column("is_analyzed", sa.Boolean(), server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    requirement_type = sa.Enum("SKILL", "TECHNOLOGY", "KEYWORD", name="requirementtype")
    requirement_importance = sa.Enum("REQUIRED", "PREFERRED", name="requirementimportance")

    op.create_table(
        "job_requirements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_description_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("job_descriptions.id", ondelete="CASCADE")),
        sa.Column("label", sa.String(150), nullable=False),
        sa.Column("normalized_label", sa.String(150), nullable=False),
        sa.Column("requirement_type", requirement_type, nullable=False),
        sa.Column("importance", requirement_importance, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    resume_status = sa.Enum("UPLOADED", "PARSING", "PARSED", "FAILED", name="resumestatus")

    op.create_table(
        "resumes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("original_filename", sa.String(500), nullable=False),
        sa.Column("file_path", sa.String(1000), nullable=False),
        sa.Column("file_type", sa.String(10), nullable=False),
        sa.Column("status", resume_status, nullable=False, server_default="UPLOADED"),
        sa.Column("extracted_text", sa.Text()),
        sa.Column("parse_error", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "resume_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("is_ats_safe", sa.Boolean(), server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "generated_resumes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("job_description_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("job_descriptions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("template_slug", sa.String(100), server_default="ats_classic"),
        sa.Column("version_name", sa.String(255), nullable=False),
        sa.Column("target_role", sa.String(255)),
        sa.Column("target_company", sa.String(255)),
        sa.Column("content", postgresql.JSON(), nullable=False),
        sa.Column("ats_score", sa.Integer()),
        sa.Column("job_match_score", sa.Integer()),
        sa.Column("source_ats_score", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "resume_analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("resume_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("resumes.id", ondelete="CASCADE"), nullable=True),
        sa.Column("generated_resume_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("generated_resumes.id", ondelete="CASCADE"), nullable=True),
        sa.Column("job_description_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("job_descriptions.id", ondelete="CASCADE")),
        sa.Column("ats_score", sa.Integer(), nullable=False),
        sa.Column("job_match_score", sa.Integer(), nullable=False),
        sa.Column("completeness_score", sa.Integer(), nullable=False),
        sa.Column("ats_components", postgresql.JSON(), nullable=False),
        sa.Column("category_scores", postgresql.JSON(), nullable=False),
        sa.Column("section_scores", postgresql.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    match_status = sa.Enum("MATCHED", "PARTIAL", "MISSING", name="matchstatus")

    op.create_table(
        "skill_matches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("resume_analyses.id", ondelete="CASCADE")),
        sa.Column("requirement_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("job_requirements.id", ondelete="CASCADE")),
        sa.Column("skill_label", sa.String(150), nullable=False),
        sa.Column("status", match_status, nullable=False),
        sa.Column("similarity_score", sa.Float(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "keyword_matches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("resume_analyses.id", ondelete="CASCADE")),
        sa.Column("keyword", sa.String(150), nullable=False),
        sa.Column("status", match_status, nullable=False),
        sa.Column("occurrences", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    recommendation_severity = sa.Enum("STRENGTH", "ISSUE", "SUGGESTION", name="recommendationseverity")

    op.create_table(
        "recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("resume_analyses.id", ondelete="CASCADE")),
        sa.Column("severity", recommendation_severity, nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    for table in [
        "recommendations", "keyword_matches", "skill_matches", "resume_analyses",
        "generated_resumes", "resume_templates", "resumes", "job_requirements",
        "job_descriptions", "verification_evidence", "skill_verifications",
        "candidate_skills", "skills", "achievements", "certifications", "projects",
        "experiences", "educations", "candidate_profiles", "users",
    ]:
        op.drop_table(table)

    for enum_name in [
        "recommendationseverity", "matchstatus", "resumestatus", "requirementimportance",
        "requirementtype", "evidencesourcetype", "skillverificationstatus", "skillsource",
    ]:
        sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)
