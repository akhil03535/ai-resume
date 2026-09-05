import uuid

from app.users.models import User
from app.profiles.models import CandidateProfile, SkillVerificationStatus
from app.profiles.service import add_candidate_skill
from app.skills.service import eligible_skills_for_generation, submit_skill_verification
from app.skills.schemas import EvidenceInput, SkillVerifyRequest


def _make_user_and_profile(db_session):
    user = User(id=uuid.uuid4(), email="test@example.com", hashed_password="x", full_name="Test User")
    db_session.add(user)
    db_session.flush()
    profile = CandidateProfile(id=uuid.uuid4(), user_id=user.id)
    db_session.add(profile)
    db_session.flush()
    return user, profile


def test_rejected_skill_is_excluded_from_generation(db_session):
    user, profile = _make_user_and_profile(db_session)

    submit_skill_verification(
        db_session, user.id, SkillVerifyRequest(skill_name="Kafka", answer="no")
    )
    db_session.flush()

    profile = db_session.get(CandidateProfile, profile.id)
    eligible = eligible_skills_for_generation(profile)

    eligible_names = {s["name"] for s in eligible["verified"]} | {s["name"] for s in eligible["basic"]}
    assert "Kafka" not in eligible_names


def test_verified_skill_with_evidence_is_eligible(db_session):
    user, profile = _make_user_and_profile(db_session)

    submit_skill_verification(
        db_session,
        user.id,
        SkillVerifyRequest(
            skill_name="Kafka",
            answer="yes",
            evidence=[EvidenceInput(source_type="PROJECT", description="Used Kafka for event-driven microservices.")],
        ),
    )
    db_session.flush()

    profile = db_session.get(CandidateProfile, profile.id)
    eligible = eligible_skills_for_generation(profile)
    verified_names = {s["name"] for s in eligible["verified"]}
    assert "Kafka" in verified_names


def test_basic_knowledge_never_listed_as_verified_experience(db_session):
    user, profile = _make_user_and_profile(db_session)

    submit_skill_verification(db_session, user.id, SkillVerifyRequest(skill_name="Docker", answer="basic"))
    db_session.flush()

    profile = db_session.get(CandidateProfile, profile.id)
    eligible = eligible_skills_for_generation(profile)

    verified_names = {s["name"] for s in eligible["verified"]}
    basic_names = {s["name"] for s in eligible["basic"]}
    assert "Docker" not in verified_names
    assert "Docker" in basic_names


def test_yes_without_evidence_is_rejected_with_clear_error(db_session):
    user, profile = _make_user_and_profile(db_session)
    from app.common.exceptions import AppError
    import pytest

    with pytest.raises(AppError):
        submit_skill_verification(db_session, user.id, SkillVerifyRequest(skill_name="AWS", answer="yes", evidence=[]))
