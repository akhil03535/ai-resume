import uuid

from app.users.models import User
from app.profiles.models import CandidateProfile
from app.profiles.service import add_candidate_skill, profile_to_dict
from app.profiles.models import SkillSource, SkillVerificationStatus
from app.analysis.service import _resume_body_text


def _make_user_and_profile(db_session):
    user = User(id=uuid.uuid4(), email="analysis@example.com", hashed_password="x", full_name="Analysis Test")
    db_session.add(user)
    db_session.flush()
    profile = CandidateProfile(id=uuid.uuid4(), user_id=user.id)
    db_session.add(profile)
    db_session.flush()
    return user, profile


def test_rejected_skill_does_not_appear_in_matching_body_text(db_session):
    """Reproduces the bug found via live testing: profile_dict['skills']
    includes every candidate_skill regardless of verification_status, so a
    REJECTED skill's name could leak into the token-overlap/semantic
    matching text and get scored as MATCHED - even though the candidate
    explicitly said they don't have it. The matching text must only ever
    include non-rejected skill names."""
    user, profile = _make_user_and_profile(db_session)

    add_candidate_skill(db_session, profile, "Java", source=SkillSource.MANUAL, verification_status=SkillVerificationStatus.VERIFIED)
    add_candidate_skill(db_session, profile, "Docker", source=SkillSource.VERIFICATION, verification_status=SkillVerificationStatus.REJECTED)
    db_session.flush()

    profile = db_session.get(CandidateProfile, profile.id)
    profile_dict = profile_to_dict(profile)

    # profile_dict['skills'] itself is unfiltered by design (it's the raw
    # candidate view) - the bug is in what gets passed to matching.
    assert "Docker" in profile_dict["skills"]

    non_rejected_labels = [
        cs.skill.name for cs in profile.candidate_skills
        if cs.verification_status != SkillVerificationStatus.REJECTED
    ]
    body = _resume_body_text(profile_dict, non_rejected_labels)

    assert "Java" in body
    assert "Docker" not in body
